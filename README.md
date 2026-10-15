# J.A.R.V.I.S. — Complete Personal AI Voice Assistant (Windows 10 & 11)

**JARVIS** (*Just A Rather Very Intelligent System*) is a futuristic, voice-controlled personal AI desktop assistant built specifically for Windows. It implements the fundamental operating loop:
$$\text{Listen} \longrightarrow \text{Understand} \longrightarrow \text{Plan} \longrightarrow \text{Execute} \longrightarrow \text{Verify} \longrightarrow \text{Respond}$$

When commanded, JARVIS does not simply provide instructions or mock responses — it executes real, verified computer actions, provides live telemetry, and requires authorization for sensitive operations.

---

## Key Features & Capabilities

1. **Futuristic Holographic HUD (PySide6)**
   - High-frame-rate **animated AI Core** with concentric rotating rings, particle ticks, radial energy glows, and audio-reactive waveforms.
   - Dynamic visual states: `Idle`, `Listening`, `Processing`, `Speaking`, `Executing`, `Success`, `Error`.
   - Live speech transcription display and scrollable conversation history.
   - Step-by-step progress tracking for multi-step tasks.
   - Controls: Push-To-Talk, Wake Word toggle, Stop Speaking, and **Emergency Stop**.

2. **Cinematic Initialization Sequence**
   - Startup sequence with live diagnostics:
     - Audio Transducer (Microphone check)
     - Neural Inference (OpenRouter / OpenAI connectivity)
     - Vocal Synthesis (Edge-TTS / pyttsx3 fallback)
     - Subsystems (WhatsApp Desktop, Gmail OAuth, OpenWeatherMap, NewsAPI, YouTube Data API)
   - Spoken greeting upon successful initialization before loading the dashboard.

3. **Natural Voice Interaction & Dual TTS**
   - **Speech Recognition**: Continuous background listener with wake-word detection (`"JARVIS"` / `"Hey JARVIS"`) and Push-to-Talk.
   - **Vocal Synthesis**: Online Microsoft Edge neural voices (`en-US-ChristopherNeural`, `en-GB-RyanNeural`, etc.) with automatic offline fallback to Windows SAPI5 (`pyttsx3`).

4. **Personal WhatsApp Desktop Integration**
   - Direct integration with the installed Windows **WhatsApp Desktop** application.
   - Launches or brings WhatsApp Desktop to the foreground.
   - Disambiguates contacts and prepares message drafts.
   - **Explicit Confirmation Safeguard**: Prompts the user before dispatching external messages.
   - Dispatches via deep-link protocol (`whatsapp://send?phone=...&text=...`) and Windows UI Automation.

5. **Gmail OAuth2 Integration**
   - Connects using `credentials.json` via Google OAuth2.
   - Summarizes unread emails and searches mailboxes.
   - Dictates, drafts, and confirms outbound emails with strict security approval.

6. **Live Real-World Information**
   - **Weather**: Live OpenWeatherMap integration (temperature, feels-like, humidity, rain probability, wind speed, sunrise/sunset, forecasts for today and tomorrow).
   - **Live News**: Real-time NewsAPI integration with headlines, technology, AI, cybersecurity, publication dates, and source links.
   - **YouTube Media**: Google YouTube Data API v3 integration to search and play tutorials, songs, and videos.

7. **System & Filesystem Control**
   - Creates, verifies, reads, and inspects files and directories.
   - Prepares nested development project structures (`frontend/`, `backend/`, `README.md`).
   - Path-traversal protection and restricted directory sandboxing (`Desktop`, `Documents`, `Downloads`, workspace).
   - Application launcher for VS Code, Notepad, Calculator, File Explorer, ChatGPT, etc.

8. **Timers & Persistent Reminders**
   - Real countdown timers with visual HUD countdown.
   - SQLite-persisted calendar reminders that survive application restarts.
   - Background scheduler daemon triggers visual alerts and spoken notifications.

---

## Project Structure

```
jarvis/
├── main.py                     # Main application entry point & cinematic launcher
├── credentials.json            # Google OAuth2 client credentials
├── .env                        # Live API keys and environment configuration
├── .env.example                # Environment variables template
├── requirements.txt            # Python dependencies
├── README.md                   # System documentation
├── app/
│   ├── config.py               # Paths, environment configuration & settings
│   ├── ai/
│   │   └── planner.py          # AI reasoning, multi-step planner & fallback router
│   ├── voice/
│   │   ├── stt.py              # Speech-to-Text engine (SpeechRecognition)
│   │   ├── tts.py              # Dual TTS engine (Edge-TTS + pyttsx3 fallback)
│   │   └── listener.py         # Background listener & wake-word detection
│   ├── tools/
│   │   ├── base.py             # Tool base classes & ToolResult contracts
│   │   ├── registry.py         # Central tool registry & OpenAI function schemas
│   │   ├── filesystem_tools.py # Folder, file, project workspace creators
│   │   ├── system_tools.py     # Windows application launchers & URL openers
│   │   └── time_tools.py       # Local time, world time zones & date calculators
│   ├── browser/
│   │   └── playwright_controller.py # Playwright Chromium browser automator
│   ├── integrations/
│   │   ├── weather/            # OpenWeatherMap client & tool
│   │   ├── news/               # NewsAPI client & tool
│   │   ├── youtube/            # YouTube Data API v3 search & playback
│   │   ├── whatsapp/           # Personal WhatsApp Desktop controller
│   │   └── email/              # Gmail OAuth2 client & tools
│   ├── scheduler/
│   │   └── timer_manager.py    # Background timer & reminder manager
│   ├── storage/
│   │   └── database.py         # SQLite persistence (reminders, tasks, memory)
│   ├── memory/
│   │   └── memory_manager.py   # User facts, preferred city & preferences
│   ├── security/
│   │   └── guardrails.py       # Path validation & emergency stop safeguards
│   └── ui/
│       ├── styles.py           # Futuristic HUD QSS styles & color palette
│       ├── core_widget.py      # Holographic animated AI Core (QPainter)
│       ├── sound_wave.py       # Audio equalizer visualizer
│       ├── init_screen.py      # Cinematic initialization screen
│       ├── confirmation_dialog.py # Sensitive action approval modal
│       ├── settings_dialog.py  # System configuration dialog
│       └── dashboard.py        # Main HUD desktop interface
└── tests/
    ├── test_acceptance.py      # 20 Mandatory Acceptance Tests (Section 21)
    ├── test_filesystem.py      # Directory & file operations test suite
    ├── test_time_and_scheduler.py # Time, dates, timers & reminders test suite
    ├── test_weather_and_news.py # Weather and News live API test suite
    ├── test_youtube.py         # YouTube Data API test suite
    ├── test_whatsapp.py        # WhatsApp Desktop integration test suite
    ├── test_gmail.py           # Gmail OAuth & draft test suite
    └── test_planner.py         # Intent parsing & execution test suite
```

---

## Getting Started

### 1. Prerequisites
- Windows 10 or Windows 11
- Python 3.10+ (tested on Python 3.13)
- WhatsApp Desktop installed (Microsoft Store or desktop installer)

### 2. Installation
Ensure all dependencies are installed:
```powershell
pip install -r requirements.txt
python -m playwright install chromium
```

### 3. Launching JARVIS
To start JARVIS:
```powershell
python main.py
```
JARVIS will open with the cinematic initialization screen, verify your microphone and service connections, speak the greeting, and transition to the HUD dashboard.

### 4. Running the Test Suite
All 42 tests, including the 20 Mandatory Acceptance Tests, can be run with:
```powershell
python -m pytest tests/ -v
```

---

## Security & Safety Guardrails
- **Destructive Action Confirmation**: Deleting files or sending WhatsApp messages / emails requires explicit user confirmation via the HUD modal dialog.
- **Filesystem Sandboxing**: File and directory operations are restricted to approved user spaces (`Desktop`, `Documents`, `Downloads`, workspace). Path traversal attempts (e.g. `C:\Windows`) are rejected with explicit access denial.
- **Emergency Stop**: Instantly accessible in the UI to immediately cancel all active background operations, audio speech, and automation tasks.
