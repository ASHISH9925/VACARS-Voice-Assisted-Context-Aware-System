# VACARS — Voice-Assisted Context-Aware System

> **Research Implementation:** [Integrating Computer Vision and Large Language Models for Real-Time Blind Navigation](https://doi.org/10.7759/s44389-026-00265-x)  
> *Cureus Journal of Computer Science, Vol. 3, September 2026* · DOI: `10.7759/s44389-026-00265-x`

A wearable, hands-free AI assistant for visually impaired individuals — combining on-device wake-word detection, cloud multimodal reasoning (Google Gemini), IoT actuation, and synchronized audio/visual/haptic feedback on a Raspberry Pi 4.

---

## Table of Contents

- [Overview](#overview)
- [Research Context](#research-context)
- [System Architecture](#system-architecture)
- [Features](#features)
- [Hardware](#hardware)
- [Software Stack](#software-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Performance](#performance)
- [Limitations](#limitations)
- [Citation](#citation)
- [License](#license)

---

## Overview

Approximately 2.2 billion people worldwide have some form of vision impairment. Existing assistive tools are either single-function, require manual phone handling, or rely on expensive proprietary hardware. VACARS addresses this gap by combining:

- **On-device wake-word detection** (Porcupine) — works offline, zero cloud latency
- **Cloud multimodal LLM reasoning** (Google Gemini) — real-time scene understanding and contextual conversation
- **Agentic tool calling** (LangGraph) — email, media playback, web search, and IoT actuation in one unified pipeline
- **Synchronized multimodal feedback** — speech synthesis + pitch-timed LED + servo haptics

All of this runs hands-free on a helmet-mounted Raspberry Pi 4, designed for real-world blind navigation.

---

## Research Context

This codebase is the proof-of-concept implementation described in the peer-reviewed paper published in the *Cureus Journal of Computer Science*:

| Field | Detail |
|---|---|
| **Title** | Integrating Computer Vision and Large Language Models for Real-Time Blind Navigation |
| **Authors** | Ashish Sharma, Dhiraj Rajput, Sushant Kumar, Yashraj Narke, Dhanashri Wategaonkar |
| **Institution** | Dr. Vishwanath Karad MIT World Peace University, Pune, India |
| **Published** | September 07, 2026 |
| **Journal** | Cureus Journal of Computer Science |
| **DOI** | [10.7759/s44389-026-00265-x](https://doi.org/10.7759/s44389-026-00265-x) |
| **License** | CC-BY 4.0 |

### Key Results

| Metric | Result |
|---|---|
| Wake-word detection latency | **0.6 s** |
| End-to-end response time | **3.8 s** (95% CI: 3.61–3.99 s) |
| Speech recognition accuracy (quiet) | **93%** (95% CI: 82.5–97.4%) |
| Speech recognition accuracy (moderate noise) | **75%** (95% CI: 61.5–84.9%) |
| Object/scene recognition accuracy | **88%** (95% CI: 76.2–94.4%) |
| User satisfaction score (n=10) | **8.5 / 10** |
| Voice interaction rated intuitive | **80%** of participants |
| Confidence in surroundings improved | **70%** of participants |

---

## System Architecture

The system is organized as a **five-layer closed signal-flow loop**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                              │
│          Microphone (Bluetooth)  ·  Camera Module 3            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     PROCESSING LAYER  (Raspberry Pi 4)          │
│  Wake-Word Detection (Porcupine) → STT (Google Cloud) →        │
│  LLM Agent (Google Gemini) → Tool Invocation (LangGraph)       │
└──────────────────────────┬──────────────────────────────────────┘
                           │  HTTPS/TLS
┌──────────────────────────▼──────────────────────────────────────┐
│                       CLOUD / API LAYER                         │
│    Google Gemini Vision  ·  Google Cloud STT  ·  Resend Email  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                       OUTPUT LAYER                              │
│   TTS Speech (pyttsx3/eSpeak)  ·  Pitch-synced LED  ·  Servos │
└─────────────────────────────────────────────────────────────────┘
```

### State Machine

The system runs as an explicit state machine:

```
IDLE ──(wake word)──► WAKE_DETECTED ──► LISTENING ──► TRANSCRIBING
  ▲                                                         │
  │                                                         ▼
  └────(done)─── RESPONDING ◄── TOOL_EXECUTION ◄── REASONING
  
  Any cloud state ──(timeout/error)──► ERROR_RECOVERY ──► IDLE
```

- **On-device states** (no network): `IDLE`, `WAKE_DETECTED`, `RESPONDING`
- **Cloud-dependent states**: `LISTENING`, `TRANSCRIBING`, `REASONING`, `TOOL_EXECUTION`
- **Fault-tolerant**: all cloud states have bounded timeouts; failures fall back to offline TTS error message

---

## Features

| Feature | Description |
|---|---|
| 🎙️ **Wake-word activation** | "Jarvis" triggers the system (on-device, offline-capable) |
| 👁️ **Scene description** | Camera captures frame → Gemini Vision describes surroundings in detail |
| 🔍 **Object identification** | Identify specific objects within the camera's field of view |
| 🌐 **Web search** | Grounded Google Search via Gemini for real-time information retrieval |
| 📧 **Email composition** | Dictate and send emails via voice (Resend API) |
| 🎵 **Music playback** | Search and play audio from YouTube by voice |
| 🔧 **IoT actuation** | Servo motor control (e.g., helmet faceplate open/close) |
| 💡 **Pitch-synced LED** | LED brightness pulse-width modulated to speech amplitude envelope |
| 🔇 **Offline fallback** | eSpeak TTS works without internet for status/error messages |
| 🧠 **Multi-turn memory** | Short-term conversation buffer for coherent follow-up questions |

---

## Hardware

### Bill of Materials

| Component | Specification |
|---|---|
| Compute | Raspberry Pi 4 Model B, 4 GB RAM, 1.5 GHz quad-core ARM Cortex-A72 |
| Camera | Raspberry Pi Camera Module 3 (12 MP Sony IMX708, autofocus), mounted at eye level |
| Microphone | Bluetooth microphone |
| Speaker | Bluetooth speaker headset |
| Servo motors (×2) | SG90 micro servo (PWM-controlled, faceplate actuation) |
| Status LEDs (×2) | Blue LED via 220–330 Ω current-limiting resistors |
| Power | 5V/3A USB-C adapter for Pi; external regulated 5V rail for servos |

### GPIO Pin Assignments

| Component | Signal | GPIO | Physical Pin |
|---|---|---|---|
| Pi Camera Module 3 | CSI | CSI ribbon | CSI port |
| SG90 Servo (SRV1) | PWM | GPIO4 | Pin 7 |
| Blue LED D1 | Anode | GPIO27 (via 220–330 Ω) | Pin 13 |
| Blue LED D2 | Anode | GPIO23 (via 220–330 Ω) | Pin 16 |
| Status LED (say.py) | PWM | GPIO18 | Pin 12 |

> [!IMPORTANT]
> Servo motors **must** be powered from an external regulated 5V supply, not the Raspberry Pi's 5V rail, to prevent brownout under peak servo current draw. Maintain a common ground between the Pi, servos, and external supply.

### Power Budget

| Component | Current Draw |
|---|---|
| Raspberry Pi 4 Model B | ~600 mA (idle) – 1.2 A (sustained) |
| Pi Camera Module 3 | ~250 mA (active) |
| SG90 Servo ×2 | ~100–250 mA each; up to 650 mA stall |
| Status LEDs ×2 | ~20 mA each |
| **System total (excl. servos)** | **~1.0–1.7 A** |

---

## Software Stack

| Layer | Technology |
|---|---|
| Wake-word detection | [Picovoice Porcupine](https://picovoice.ai/platform/porcupine/) |
| Speech-to-text | Google Web Speech API via `speechrecognition` library |
| LLM reasoning | [Google Gemini](https://ai.google.dev/) (`gemini-2.5-flash`) via `google-genai` |
| Agent orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) ReAct agent with function calling |
| Vision / VQA | Google Gemini Vision (query-time frame capture via `picamzero`) |
| Web search | Gemini grounded Google Search tool |
| Email | [Resend](https://resend.com/) REST API |
| Music playback | `yt-dlp` + `ffplay` (audio-only streaming) |
| Text-to-speech | `pyttsx3` + eSpeak backend (fully offline) |
| LED animation | `gpiozero` PWMLED + `aubio` pitch extraction |
| IoT / GPIO | `lgpio` (Raspberry Pi 5-compatible) |
| Dependency management | [uv](https://docs.astral.sh/uv/) |

---

## Getting Started

### Prerequisites

- Raspberry Pi 4 Model B (4 GB recommended) running Raspberry Pi OS (64-bit)
- Python 3.11 or 3.12
- `uv` package manager
- System packages: `espeak`, `ffmpeg` (for `ffplay`)

```bash
sudo apt-get update
sudo apt-get install -y espeak ffmpeg libportaudio2
```

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd "VACARS (Voice-Assisted Context-Aware System)"

# Install Python dependencies with uv
uv sync
```

### Environment Setup

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

```ini
# .env
PORCUPINE_ACCESS_KEY="your_picovoice_key_here"   # https://console.picovoice.ai/
GOOGLE_API_KEY="your_google_ai_key_here"          # https://aistudio.google.com/
RESEND_API_KEY="your_resend_key_here"             # https://resend.com/
RESEND_MAIL_FROM="Your Name <you@yourdomain.com>"
CAMERA_URL="http://<esp-cam-ip>"                  # optional, for ESP-CAM

# LangSmith tracing (optional)
LANGSMITH_TRACING="true"
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY="your_langsmith_key"
LANGSMITH_PROJECT="vacars"

# Contacts for email tool (newline-separated, \n between entries)
# CONTACTS_LIST="- Alice: alice@example.com\n- Bob: bob@example.com"
```

### Running

```bash
# Activate the virtual environment and run
uv run python src/main.py
```

Say **"Jarvis"** to wake the system, then speak a command such as:
- *"What's in front of me?"*
- *"Send an email to Alice saying I'll be late"*
- *"Play some jazz music"*
- *"Search for the nearest hospital"*

### Checking Audio Devices

```bash
uv run python check_devices.py
```

---

## Configuration

All runtime configuration is loaded from environment variables (via `.env`). Key settings in [`src/config.py`](src/config.py):

| Variable | Default | Description |
|---|---|---|
| `MODEL` | `gemini-2.5-flash` | Gemini model for LLM reasoning |
| `SAY_WPM` | `130` | TTS speech rate in words per minute |
| `RESEND_MAIL_FROM` | `Helmet AI <onboarding@resend.dev>` | Sender address for emails |
| `CAMERA_URL` | `http://192.168.0.225` | ESP-CAM URL (unused when using Pi Camera) |
| `BLUE_LED_PIN` | `18` | GPIO pin for status LED |
| `CONTACTS_LIST` | placeholder example | Newline-separated contact list for email tool |

---

## Project Structure

```
.
├── src/
│   ├── main.py                   # Entry point — wake-word loop
│   ├── config.py                 # Runtime configuration (env-driven)
│   ├── agent/
│   │   ├── llm.py                # LangGraph ReAct agent + conversation memory
│   │   ├── prompts.py            # System prompt + contact list injection
│   │   └── tools/
│   │       ├── ask_photo.py      # Vision tool — capture frame + Gemini VQA
│   │       ├── google_search.py  # Grounded web search via Gemini
│   │       ├── send_email.py     # Email composition + send via Resend API
│   │       ├── play_music.py     # YouTube audio search + ffplay streaming
│   │       └── remove_frontplate.py  # Servo motor actuation
│   ├── audio/
│   │   ├── wake.py               # Porcupine wake-word detection
│   │   ├── listen.py             # SpeechRecognition → Google STT
│   │   └── say.py                # TTS + aubio pitch-sync LED animation
│   ├── hardware/
│   │   └── led.py                # gpiozero LED control helpers
│   └── utils/
│       └── logger.py             # Rich-formatted logging
├── .env.example                  # Environment variable template
├── .gitignore
├── pyproject.toml                # Project metadata and dependencies
├── uv.lock                       # Locked dependency tree
├── check_devices.py              # List available PyAudio devices
├── tts.py                        # Standalone TTS + audio device test script
├── deps.txt                      # System-level dependency notes
└── README.md
```

---

## Performance

| Stage | Median Latency |
|---|---|
| Wake-word detection | 0.6 s |
| Speech-to-text | 1.2 s |
| LLM reasoning (+ tool calls) | 1.3 s |
| Text-to-speech synthesis | 0.8 s |
| **End-to-end total** | **3.8 s** (SD 0.4 s) |

> [!NOTE]
> All measurements were taken under stable indoor Wi-Fi (≥10 Mbps). Performance degrades on slow or intermittent networks. The system transitions to `ERROR_RECOVERY` on timeout, speaking an offline error message via eSpeak.

---

## Limitations

- **Cloud dependency**: STT and LLM reasoning require internet access. Network outages trigger an offline fallback message.
- **Response latency**: 3.8 s mean end-to-end may feel slow for fast-moving navigation hazards.
- **Noise sensitivity**: Speech recognition drops from 93% (quiet) to 75% at 60–70 dB ambient noise.
- **Low-light performance**: Object recognition degrades in poor lighting (not formally benchmarked).
- **Weight**: Raspberry Pi 4 + battery is heavy for extended head-worn use.
- **Field of view**: Standard Camera Module 3 has a narrow horizontal FoV; wide-angle variant recommended.
- **Testing scope**: Validated only in controlled indoor environments with n=10 participants; not tested outdoors.

### Future Directions (from the paper)

- Migrate object detection to on-device NPU using **Raspberry Pi AI HAT+ 2** (Hailo-10H, 40 TOPS) to reduce latency by 40–50% and enable offline obstacle feedback.
- Add a small on-device language model for lightweight intent triage, escalating only complex queries to cloud Gemini.
- Improve noise robustness with adaptive microphone arrays or noise-cancellation preprocessing.
- Ergonomic redesign for a lighter, more compact form factor.

---

## Citation

If you use this code or the associated research in your work, please cite:

```bibtex
@article{sharma2026vacars,
  title   = {Integrating Computer Vision and Large Language Models for Real-Time Blind Navigation},
  author  = {Ashish Sharma and Dhiraj Rajput and Sushant Kumar and Yashraj Narke and Dhanashri Wategaonkar},
  journal = {Cureus Journal of Computer Science},
  volume  = {3},
  year    = {2026},
  month   = {September},
  doi     = {10.7759/s44389-026-00265-x},
  url     = {https://doi.org/10.7759/s44389-026-00265-x}
}
```

---

## License

This project is released as open-source in conjunction with the research paper published under [Creative Commons Attribution 4.0 International (CC-BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

You are free to use, distribute, and adapt this work for any purpose, provided the original authors and source are credited.

