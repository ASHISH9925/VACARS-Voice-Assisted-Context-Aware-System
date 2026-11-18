import pyttsx3
import wave
import pyaudio
import audioop
import numpy as np

engine = pyttsx3.init()
engine.setProperty("rate", 120)
engine.save_to_file("""
hello yes 
""", "part1.wav")
engine.save_to_file(".", "part2.wav")
engine.runAndWait()

def play_wav(path, vb_index=11):
    wf = wave.open(path, 'rb')
    p = pyaudio.PyAudio()

    channels = wf.getnchannels()
    rate = wf.getframerate()
    width = wf.getsampwidth()

    stream = p.open(format=p.get_format_from_width(width),
                    channels=channels,
                    rate=rate,
                    output=True,
                    output_device_index=vb_index)

    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)

    stream.stop_stream()
    stream.close()
    wf.close()
    p.terminate()

def play_silence(duration_sec, rate=22050, vb_index=15):
    # Generate silent PCM frames
    num_samples = int(rate * duration_sec)
    silence = (np.zeros(num_samples)).astype(np.int16).tobytes()

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=rate,
                    output=True,
                    output_device_index=vb_index)
    stream.write(silence)
    stream.stop_stream()
    stream.close()
    p.terminate()

# Play "computer"
# play_wav("part1.wav")

# # Insert 0.5s pause
# play_silence(0.5)

# # Play "hello what is your name"
# play_wav("part2.wav")

# play_wav("./verstappen.wav")
