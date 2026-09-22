# MARK-1-# J.A.R.V.I.S. — Mark 1: Core

> **Just A Rather Very Intelligent System**

J.A.R.V.I.S. Mark 1 is the first working version of my personal AI assistant, inspired by the J.A.R.V.I.S. system from Iron Man.

Mark 1 focuses on building the **core AI communication system** using Google's Gemini Live API.

The assistant can listen through the microphone, understand what is being said, see through the camera, and respond using real-time AI-generated speech.

## Features

* Real-time voice conversation
* Microphone input
* AI-generated voice responses
* Camera vision
* Real-time Gemini Live connection
* Low-latency responses
* Optional screen-sharing mode
* Text input as an additional interaction method

## Technology

* **Python**
* **Google Gemini Live API**
* **Google GenAI SDK**
* **OpenCV**
* **PyAudio**
* **Pillow**
* **MSS**

## Requirements

* Python 3.11+ recommended
* Working microphone
* Working speakers/headphones
* Webcam for camera mode
* Internet connection
* Gemini API key

## Installation

Clone the repository:

```bash
git clone YOUR_REPOSITORY_URL
cd JARVIS
```

Install the required packages:

```bash
pip install google-genai opencv-python pyaudio pillow mss
```

## API Key

Set your Gemini API key as an environment variable.

### Windows PowerShell

```powershell
$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

Then run J.A.R.V.I.S.

## Running J.A.R.V.I.S.

### Camera Mode

```bash
python main.py --mode camera
```

This enables microphone input, voice responses, and camera vision.

### Screen Mode

```bash
python main.py --mode screen
```

This allows J.A.R.V.I.S. to receive screenshots of the computer screen.

### Audio Only

```bash
python main.py --mode none
```

This runs J.A.R.V.I.S. without camera or screen input.

## How It Works

```text
             ┌──────────────┐
             │  Microphone  │
             └──────┬───────┘
                    │
                    ▼
             ┌──────────────┐
             │ Gemini Live  │
             │     API      │
             └──────┬───────┘
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
     AI Processing         Camera
          │                   │
          ▼                   ▼
      AI Response       Visual Context
          │
          ▼
       Speaker
```

## Mark 1 Goal

The goal of Mark 1 is simple:

**Build a stable core for J.A.R.V.I.S. that can hear, understand, see, think, and speak in real time.**

This version is the foundation for the future J.A.R.V.I.S. system.

## Development Roadmap

### Mark 1 — Core

* Gemini Live
* Microphone
* Speaker
* Camera
* Real-time conversation

### Mark 2 — Intelligence

* Wake word
* J.A.R.V.I.S. personality
* Memory
* Information tools

### Mark 3 — Computer

* Application control
* Screenshots
* File operations
* Safe computer commands

### Mark 4 — Vision

* Advanced camera understanding
* Screen understanding
* Object and workspace analysis

### Mark 5 — Identity

* Face recognition
* User authorization
* Protected commands

### Mark 6 — Advanced

* Advanced tools
* Automation
* Multi-tool workflows
* Expanded J.A.R.V.I.S. capabilities

## Project Status

**Mark 1 — Core: WORKING**

The core voice, camera, and Gemini Live system is operational.

More features will be added progressively in future Mark versions.

---

## Important

Never upload your Gemini API key to GitHub.

Keep API keys in environment variables or a local `.env` file that is excluded through `.gitignore`.

## License

This project is a personal learning and development project.
