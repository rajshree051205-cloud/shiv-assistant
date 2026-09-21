# 🧠 Shiv — Your Personal Offline Voice Assistant

<p align="center">
  <img src="./assets/shiv-banner.png" width="850">
</p>

<p align="center">
  <b>Listen. Understand. Remember. Respond.</b>
</p>

<p align="center">
  A personal AI voice assistant built from scratch with Python, Vosk, Flask and offline speech processing.
</p>

---

## ✨ What is Shiv?

**Shiv** is my personal voice assistant project, built to experiment with **speech recognition, text-to-speech, automation, memory, and AI-agent style interactions**.

Instead of depending completely on cloud APIs, Shiv is designed around **local and offline-first components** wherever possible.

> 🎙️ Say **"Shiv"** → Shiv wakes up → listens to your command → processes it → speaks the response.

---

## 🎬 The Idea

Imagine your laptop having its own little assistant.

You say:

```text
"Shiv"
```

And it responds:

```text
"Haanji Rajshree, bolo."
```

Then you can say things like:

```text
"What time is it?"
"What's the weather?"
"Play some music"
"Remember this..."
"Show my notes"
"Set a reminder"
"Open YouTube"
```

Shiv processes the command and responds through voice.

---

## 🧩 How Shiv Works

```text
                 🎙️ YOUR VOICE
                       │
                       ▼
              ┌─────────────────┐
              │  Vosk Speech    │
              │   Recognition   │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Command        │
              │  Processing     │
              └────────┬────────┘
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       Dynamic Intents       Static Q&A
             │                   │
             └─────────┬─────────┘
                       ▼
              ┌─────────────────┐
              │   Functions /   │
              │    Database     │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   pyttsx3 TTS   │
              └────────┬────────┘
                       │
                       ▼
                  🔊 SHIV SPEAKS
```

---

## ⚡ Features

### 🎙️ Voice Interaction

* Offline speech recognition with **Vosk**
* Microphone input
* Continuous listening mode
* Wake-word based activation
* Voice responses using `pyttsx3`

### 🧠 Command Engine

Shiv separates commands into different layers:

```text
1. Control Commands
2. Dynamic Intents
3. Static Q&A Bank
4. Google Search Fallback
```

This allows the assistant to handle both predefined commands and unknown questions.

### ⏰ Smart Utilities

* Time
* Date
* Weather
* YouTube
* Video playback
* Notes
* Reminders
* Command history

### 📝 Memory & Data

Shiv uses a local database for:

* Notes
* Reminders
* Preferences
* Command history

### 🌐 Web Dashboard

A Flask dashboard allows interaction with Shiv through a browser.

```text
Browser
   │
   ▼
Flask API
   │
   ▼
Command Engine
   │
   ▼
Database / Functions
```

### 🔒 Offline-First

The core voice pipeline uses local components:

```text
Microphone
    ↓
Vosk
    ↓
Local Command Engine
    ↓
Local Database
    ↓
pyttsx3
    ↓
Voice Response
```

No cloud speech API is required for the basic voice pipeline.

---

## 🛠️ Tech Stack

| Technology     | Purpose                |
| -------------- | ---------------------- |
| 🐍 Python      | Core application       |
| 🎙️ Vosk       | Offline Speech-to-Text |
| 🔊 pyttsx3     | Text-to-Speech         |
| 🌐 Flask       | Web dashboard & APIs   |
| 🗄️ SQLite     | Local data storage     |
| 🎤 SoundDevice | Microphone input       |
| 🖥️ PyStray    | System tray            |
| 🪟 PyWin32     | Windows integration    |
| 🎨 HTML/CSS/JS | Dashboard              |

---

## 📁 Project Structure

```text
shiv-assistant/
│
├── voice_agent.py       # Voice assistant
├── engine.py            # Command processing brain
├── web_app.py           # Flask dashboard
├── launcher.py          # Project launcher
├── database.py          # Database operations
├── functions.py         # Assistant functions
├── answer_bank.py       # Static Q&A
├── config.py            # Configuration
│
├── templates/
│   └── index.html       # Dashboard UI
│
├── static/
│   ├── css/
│   └── js/
│
├── vosk-model-en/       # Offline speech model
│
└── README.md
```

---

## 🚀 Getting Started

### 1️⃣ Clone the repository

```bash
git clone https://github.com/rajshree051205-cloud/shiv-assistant.git
```

### 2️⃣ Open the project

```bash
cd shiv-assistant
```

### 3️⃣ Create virtual environment

```bash
python -m venv .venv
```

### 4️⃣ Activate it

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 6️⃣ Start Shiv

```bash
python voice_agent.py
```

Or start the web dashboard:

```bash
python web_app.py
```

Then open:

```text
http://127.0.0.1:5000
```

---

## 🎤 Example Conversation

```text
You: Shiv

Shiv: Haanji Rajshree, bolo.

You: What time is it?

Shiv: It is 8:30 PM.

You: Shiv, open YouTube

Shiv: Opening YouTube.

You: Shiv, remember that I have a DSA test tomorrow.

Shiv: Note saved.
```

---

## 🧠 Command Processing

Shiv's `engine.py` acts as the central brain.

```text
                 USER INPUT
                     │
                     ▼
             ┌───────────────┐
             │ Normalize     │
             │ Input         │
             └───────┬───────┘
                     │
                     ▼
             ┌───────────────┐
             │ Dynamic       │
             │ Intent?       │
             └───────┬───────┘
                     │
              Yes ───┴─── No
               │           │
               ▼           ▼
          Execute       Static Q&A?
          Function          │
                            │
                       Yes ─┴─ No
                        │       │
                        ▼       ▼
                     Answer   Google
                              Search
```

---

## 🔥 Why I Built Shiv

This project started as a way to understand how a **real voice assistant works behind the scenes**.

While building it, I explored:

* Speech recognition
* Audio streams
* Text-to-speech
* Intent detection
* Fuzzy matching
* APIs
* Databases
* Flask
* Background threads
* System tray applications
* Windows events
* Offline AI models

The goal isn't just to make Shiv answer questions.

The goal is to keep improving it into a more capable **personal AI agent**.

---

## 🛣️ Roadmap

### ✅ Completed

* [x] Offline speech recognition
* [x] Voice responses
* [x] Wake-word system
* [x] Dynamic commands
* [x] Static Q&A system
* [x] Notes
* [x] Reminders
* [x] SQLite database
* [x] Flask dashboard
* [x] System tray integration
* [x] Windows lock/unlock awareness

### 🚧 In Progress

* [ ] Better wake-word detection
* [ ] More natural conversations
* [ ] Improved Hindi/Hinglish recognition
* [ ] Better microphone handling
* [ ] Persistent conversational memory
* [ ] More automation tools

### 🔮 Future Ideas

* [ ] AI-powered reasoning
* [ ] Personal task management
* [ ] Desktop automation
* [ ] Smarter contextual memory
* [ ] Multi-language support
* [ ] More natural voice
* [ ] Agent-style tool calling

---

## 🧪 Current Status

> 🚧 **Shiv is an actively developing personal project.**

The architecture is intentionally modular so new capabilities can be added without rewriting the entire assistant.

---

## 👩‍💻 Built By

### Rajshree Kavia

**B.Tech CSE Student | Full Stack Developer | AI & Agent Enthusiast**

Building projects, breaking bugs, and learning how things work under the hood.

---

<p align="center">

### 🖤 One voice. One assistant. One project.

**Shiv is still learning. So am I.**

</p>
