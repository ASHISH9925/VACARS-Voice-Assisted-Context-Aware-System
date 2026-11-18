import pyttsx3
import wave
import struct
import os
import subprocess
from config import SAY_WPM
from utils.logger import get_logger

logger = get_logger(__name__)
_engine = pyttsx3.init()
_engine.setProperty("rate", SAY_WPM)

def fix_wav_header(wav_path: str) -> bool:
    """Fix WAV file header to ensure it has proper RIFF header for aubio compatibility."""
    try:
        # Try to open the file to check if it's valid
        with wave.open(wav_path, 'rb') as wav_file:
            # If we can open it, it's already valid
            return True
    except wave.Error:
        # File doesn't have proper WAV header, try to fix it
        try:
            # Read the raw audio data
            with open(wav_path, 'rb') as f:
                raw_data = f.read()
            
            # If the file is too small or empty, return False
            if len(raw_data) < 44:  # Minimum WAV header size
                logger.error(f"WAV file {wav_path} is too small or corrupted")
                return False
            
            # Check if it already has RIFF header
            if raw_data[:4] == b'RIFF':
                return True
            
            # Create a new WAV file with proper header
            # Assume 16-bit, mono, 22050 Hz (common for TTS)
            sample_rate = 22050
            channels = 1
            bits_per_sample = 16
            
            # Calculate data size
            data_size = len(raw_data)
            file_size = 36 + data_size
            
            # Create proper WAV header
            wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
                b'RIFF',                    # ChunkID
                file_size,                 # ChunkSize
                b'WAVE',                   # Format
                b'fmt ',                   # Subchunk1ID
                16,                        # Subchunk1Size
                1,                         # AudioFormat (PCM)
                channels,                  # NumChannels
                sample_rate,               # SampleRate
                sample_rate * channels * bits_per_sample // 8,  # ByteRate
                channels * bits_per_sample // 8,  # BlockAlign
                bits_per_sample,           # BitsPerSample
                b'data',                   # Subchunk2ID
                data_size                  # Subchunk2Size
            )
            
            # Write the fixed WAV file
            with open(wav_path, 'wb') as f:
                f.write(wav_header)
                f.write(raw_data)
            
            logger.info(f"Fixed WAV header for {wav_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fix WAV header for {wav_path}: {e}")
            return False

def create_wav_with_espeak(text: str, wav_path: str) -> bool:
    """Create a WAV file using espeak as a fallback method."""
    try:
        # Use espeak to generate WAV file with proper headers
        cmd = [
            'espeak', 
            '-s', str(SAY_WPM),  # Speed in words per minute
            '-w', wav_path,       # Output WAV file
            text
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
            logger.info(f"Successfully created WAV file using espeak: {wav_path}")
            return True
        else:
            logger.error(f"espeak failed to create WAV file: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("espeak command timed out")
        return False
    except FileNotFoundError:
        logger.error("espeak not found. Please install espeak: sudo apt-get install espeak")
        return False
    except Exception as e:
        logger.error(f"Error using espeak: {e}")
        return False

def say(text: str) -> None:
    try:
        # --- Added reactive LED logic ---
        import tempfile, os, time, subprocess, math
        import aubio
        try:
            from gpiozero import PWMLED, Device
            try:
                # Prefer lgpio on Pi 5
                from gpiozero.pins.lgpio import LGPIOFactory
                Device.pin_factory = LGPIOFactory()
            except Exception:
                # If lgpio not available, let gpiozero choose another backend
                pass
        except Exception:
            PWMLED = None  # type: ignore

        WAV_PATH = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        GPIO_PIN = 18
        SAMPLE_RATE = 22050
        WIN_S, HOP_S = 2048, 512
        F_MIN, F_MAX = 80.0, 1000.0
        SMOOTH_ALPHA = 0.25
        UNVOICED_BRIGHTNESS = 0.02
        PWM_RANGE = 255

        # Normalize text (collapse newlines and excessive spaces)
        clean_text = " ".join((text or "").split())

        # Save speech to wav first
        _engine.save_to_file(clean_text, WAV_PATH)
        _engine.runAndWait()

        # Ensure WAV file is written before proceeding (cold-start race guard)
        try:
            import time as _time
            for _ in range(60):  # up to ~3s
                if os.path.exists(WAV_PATH) and os.path.getsize(WAV_PATH) > 44:
                    break
                _time.sleep(0.05)
        except Exception:
            pass

        # Fix WAV header if needed, or use espeak fallback
        if not fix_wav_header(WAV_PATH):
            logger.warning(f"pyttsx3 WAV file invalid, trying espeak fallback")
            if not create_wav_with_espeak(clean_text, WAV_PATH):
                logger.error(f"Failed to create valid WAV file at {WAV_PATH}")
                _engine.stop()
                return
            # After espeak, also ensure file exists
            try:
                import time as _time
                for _ in range(60):
                    if os.path.exists(WAV_PATH) and os.path.getsize(WAV_PATH) > 44:
                        break
                    _time.sleep(0.05)
            except Exception:
                pass

        # Extract pitch timeline
        try:
            src = aubio.source(WAV_PATH, samplerate=SAMPLE_RATE, hop_size=HOP_S)
        except Exception as e:
            logger.error(f"Failed to create aubio source from {WAV_PATH}: {e}")
            _engine.stop()
            return
            
        pitch_o = aubio.pitch("yin", WIN_S, HOP_S, src.samplerate)
        pitch_o.set_unit("Hz")
        pitch_o.set_silence(-40)

        timeline = []
        total_frames, prev_duty = 0, 0.0
        while True:
            samples, read = src()
            if read == 0:
                break
            total_frames += read
            t = (total_frames - read) / float(src.samplerate)
            pitch = pitch_o(samples)[0]
            if pitch < F_MIN or pitch != pitch or pitch <= 0:
                duty = UNVOICED_BRIGHTNESS
            else:
                log_f = math.log(pitch)
                norm = (log_f - math.log(F_MIN)) / (math.log(F_MAX) - math.log(F_MIN))
                duty = max(0.0, min(1.0, norm))
            smoothed = SMOOTH_ALPHA * duty + (1 - SMOOTH_ALPHA) * prev_duty
            prev_duty = smoothed
            timeline.append((t, smoothed))

        # Init gpiozero PWM LED (0..1 brightness)
        led = None
        try:
            if PWMLED is not None:
                led = PWMLED(GPIO_PIN, frequency=800)
            else:
                logger.warning("gpiozero not available; skipping LED animation")
        except Exception as e:
            logger.warning(f"GPIO not available, skipping LED animation: {e}")
            led = None

        # Play and follow timeline
        p = subprocess.Popen(["aplay", WAV_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        start = time.monotonic()
        idx = 0
        n = len(timeline)
        while p.poll() is None and idx < n:
            now = time.monotonic() - start
            while idx < n and timeline[idx][0] <= now:
                _, duty = timeline[idx]
                # gpiozero PWMLED takes value in 0..1
                if led is not None:
                    led.value = max(0.0, min(1.0, duty))
                idx += 1
            time.sleep(0.005)

        if led is not None:
            led.value = 0
            led.close()
        p.wait()

        os.remove(WAV_PATH)

    except Exception as e:
        try:
            logger.error(f"Error in say(): {e}")
            # Fallback: just use pyttsx3 without LED effects
            logger.info("Falling back to simple TTS without LED effects")
            # Reuse cleaned text for fallback too
            clean_text = " ".join((text or "").split())
            _engine.say(clean_text)
            _engine.runAndWait()
            _engine.stop()
        except Exception:
            pass
