"""
JARVIS Web Server & Holographic HUD Interface
Provides a local web application on http://localhost:8000 with real-time voice input,
neural speech output, central glowing AI core, task execution pipeline, and computer control.
"""

from __future__ import annotations
import os
import sys
import time
import json
import asyncio
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import psutil
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import Config
from app.ai.planner import planner
from app.tools.registry import registry
from app.security.guardrails import SecurityGuardrails
from app.scheduler.timer_manager import timer_manager
from app.integrations.whatsapp.whatsapp_desktop import whatsapp_desktop
from app.integrations.email.gmail_client import gmail_client
from app.memory.memory_manager import memory_manager
from app.voice.tts import tts

app = FastAPI(title="JARVIS AI Interface")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CommandRequest(BaseModel):
    prompt: str


class ConfirmRequest(BaseModel):
    tool: str
    confirmed: bool
    payload: Optional[Dict[str, Any]] = None


class TTSRequest(BaseModel):
    text: str


@app.get("/", response_class=HTMLResponse)
def get_index():
    return HTML_CONTENT


@app.post("/api/chat")
def execute_chat_command(req: CommandRequest):
    prompt = req.prompt.strip()
    if not prompt:
        return {"status": "failed", "response": "Please provide a command."}

    # Auto-reset emergency stop so user can immediately issue new instructions
    SecurityGuardrails.reset_emergency_stop()

    # Run planner
    result = planner.plan_and_execute(prompt)
    return result


@app.post("/api/confirm")
def handle_confirmation(req: ConfirmRequest):
    tool = req.tool
    confirmed = req.confirmed

    if not confirmed:
        if tool == "whatsapp_draft_message":
            whatsapp_desktop.cancel_pending_message()
        elif tool == "gmail_draft_email":
            gmail_client.pending_email = None
        return {"status": "cancelled", "response": "Action cancelled per your instruction."}

    if tool == "whatsapp_draft_message":
        success, msg = whatsapp_desktop.send_confirmed_message()
        return {"status": "completed" if success else "failed", "response": msg}
    elif tool == "gmail_draft_email":
        success, msg = gmail_client.send_confirmed_email()
        return {"status": "completed" if success else "failed", "response": msg}

    return {"status": "failed", "response": f"Unknown confirmation tool: {tool}"}


@app.post("/api/tts")
async def generate_speech_audio(req: TTSRequest):
    """Generate speech audio file and return it."""
    text = req.text.strip()
    if not text:
        return JSONResponse({"error": "Empty text"}, status_code=400)

    try:
        import edge_tts
        temp_file = os.path.join(tempfile.gettempdir(), f"jarvis_web_tts_{int(time.time()*1000)}.mp3")
        comm = edge_tts.Communicate(text, Config.VOICE_NAME, rate=Config.VOICE_RATE)
        await comm.save(temp_file)
        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
            return FileResponse(temp_file, media_type="audio/mpeg")
    except Exception as e:
        print(f"[WebTTS] Edge-TTS error: {e}")

    return JSONResponse({"status": "fallback_client_speech", "text": text})


@app.get("/api/status")
def get_system_status():
    now = datetime.now()
    active_timers = list(timer_manager.active_timers)
    for t in active_timers:
        t["remaining"] = max(0, int((t["due_time"] - now).total_seconds()))

    return {
        "cpu": int(psutil.cpu_percent()),
        "ram": int(psutil.virtual_memory().percent),
        "time": now.strftime("%I:%M:%S %p"),
        "date": now.strftime("%A, %B %d, %Y"),
        "whatsapp_installed": whatsapp_desktop.is_installed(),
        "whatsapp_running": whatsapp_desktop.is_running(),
        "whatsapp_draft": whatsapp_desktop.pending_message,
        "gmail_authorized": gmail_client.is_authorized(),
        "ai_model": Config.AI_MODEL,
        "default_city": Config.DEFAULT_CITY,
        "active_timers": active_timers,
        "emergency_stopped": SecurityGuardrails.is_stopped()
    }


@app.post("/api/emergency_stop")
def trigger_emergency_stop():
    SecurityGuardrails.trigger_emergency_stop()
    tts.stop()
    return {"status": "stopped", "message": "All operations halted immediately."}


@app.post("/api/emergency_reset")
def reset_emergency_stop():
    SecurityGuardrails.reset_emergency_stop()
    return {"status": "ready", "message": "Security clearance restored."}


HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS // MARK VII AI INTERFACE</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #070B11;
            --bg-panel: rgba(13, 19, 29, 0.88);
            --bg-card: rgba(18, 26, 39, 0.75);
            --cyan: #00F0FF;
            --blue: #0077FF;
            --amber: #FFB703;
            --red: #FF3366;
            --text: #E0F7FA;
            --text-dim: #7B9EA8;
            --border-glow: rgba(0, 240, 255, 0.3);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-dark);
            color: var(--text);
            font-family: 'Rajdhani', sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 50% 20%, rgba(0, 240, 255, 0.08) 0%, transparent 60%),
                radial-gradient(circle at 10% 80%, rgba(0, 119, 255, 0.05) 0%, transparent 50%);
        }

        /* Top HUD Bar */
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 24px;
            background: var(--bg-panel);
            border-bottom: 1px solid var(--border-glow);
            backdrop-filter: blur(10px);
        }

        .logo-box {
            display: flex;
            align-items: baseline;
            gap: 12px;
        }

        .logo {
            font-family: 'Orbitron', sans-serif;
            font-size: 24px;
            font-weight: 900;
            color: var(--cyan);
            letter-spacing: 4px;
            text-shadow: 0 0 15px rgba(0, 240, 255, 0.6);
        }

        .sub-logo {
            font-family: 'Share Tech Mono', monospace;
            font-size: 11px;
            color: var(--text-dim);
            letter-spacing: 2px;
        }

        .telemetry {
            display: flex;
            align-items: center;
            gap: 20px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 13px;
            color: var(--cyan);
        }

        .badge {
            padding: 4px 10px;
            border-radius: 4px;
            border: 1px solid var(--border-glow);
            background: rgba(0, 240, 255, 0.05);
        }

        /* Main Workspace Grid */
        main {
            display: grid;
            grid-template-columns: 360px 1fr 380px;
            gap: 16px;
            padding: 16px 24px;
            flex: 1;
        }

        @media (max-width: 1100px) {
            main {
                grid-template-columns: 1fr;
            }
        }

        .panel {
            background: var(--bg-panel);
            border: 1px solid var(--border-glow);
            border-radius: 12px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            backdrop-filter: blur(12px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        }

        .panel-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 13px;
            font-weight: 700;
            color: var(--cyan);
            letter-spacing: 2px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid rgba(0, 240, 255, 0.15);
            padding-bottom: 8px;
        }

        /* Chat / Conversation Timeline */
        .chat-box {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-height: 480px;
            padding-right: 6px;
        }

        .bubble {
            background: var(--bg-card);
            border: 1px solid rgba(0, 240, 255, 0.15);
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 14px;
            line-height: 1.4;
        }

        .bubble.user {
            border-left: 3px solid var(--blue);
            align-self: flex-start;
            width: 95%;
        }

        .bubble.jarvis {
            border-left: 3px solid var(--cyan);
            align-self: flex-start;
            width: 95%;
        }

        .sender-tag {
            font-family: 'Share Tech Mono', monospace;
            font-size: 11px;
            font-weight: bold;
            margin-bottom: 4px;
        }

        .sender-tag.user { color: var(--blue); }
        .sender-tag.jarvis { color: var(--cyan); }

        /* Central Core Panel */
        .center-panel {
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        canvas#coreCanvas {
            width: 260px;
            height: 260px;
        }

        canvas#waveCanvas {
            width: 320px;
            height: 48px;
            margin-top: 10px;
        }

        .state-tag {
            font-family: 'Orbitron', sans-serif;
            font-size: 14px;
            font-weight: 700;
            color: var(--cyan);
            letter-spacing: 3px;
            margin-top: 6px;
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
        }

        .transcription-card {
            width: 100%;
            max-width: 520px;
            background: var(--bg-card);
            border: 1px solid var(--border-glow);
            border-radius: 8px;
            padding: 12px 16px;
            margin-top: 14px;
            font-size: 15px;
            font-style: italic;
            color: var(--text);
            min-height: 54px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Voice & Emergency Controls */
        .btn-cluster {
            display: flex;
            gap: 12px;
            margin-top: 14px;
            flex-wrap: wrap;
            justify-content: center;
        }

        button {
            font-family: 'Rajdhani', sans-serif;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            outline: none;
            border: 1px solid var(--border-glow);
            background: rgba(0, 240, 255, 0.08);
            color: var(--cyan);
        }

        button:hover {
            background: rgba(0, 240, 255, 0.2);
            box-shadow: 0 0 12px rgba(0, 240, 255, 0.4);
        }

        button.primary-btn {
            background: linear-gradient(90deg, #0077FF, #00F0FF);
            color: #070B11;
            border: none;
            font-weight: 800;
        }

        button.primary-btn:hover {
            box-shadow: 0 0 16px rgba(0, 240, 255, 0.7);
        }

        button.danger-btn {
            border-color: rgba(255, 51, 102, 0.5);
            background: rgba(255, 51, 102, 0.15);
            color: var(--red);
        }

        button.danger-btn:hover {
            background: rgba(255, 51, 102, 0.3);
            box-shadow: 0 0 12px rgba(255, 51, 102, 0.5);
        }

        button.active-rec {
            animation: pulse-red 1s infinite alternate;
            background: rgba(255, 51, 102, 0.4) !important;
            color: #FFF !important;
            border-color: var(--red) !important;
        }

        @keyframes pulse-red {
            from { box-shadow: 0 0 4px var(--red); }
            to { box-shadow: 0 0 20px var(--red); }
        }

        /* Task Progress Card */
        .task-card {
            background: var(--bg-card);
            border: 1px solid rgba(0, 240, 255, 0.15);
            border-radius: 8px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .task-status {
            font-family: 'Share Tech Mono', monospace;
            font-size: 12px;
            color: var(--cyan);
        }

        .progress-bar {
            width: 100%;
            height: 6px;
            background: rgba(7, 11, 17, 0.8);
            border-radius: 3px;
            overflow: hidden;
            border: 1px solid rgba(0, 240, 255, 0.2);
        }

        .progress-fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, var(--blue), var(--cyan));
            transition: width 0.3s ease;
        }

        /* Subsystems Card */
        .subsystem-item {
            background: var(--bg-card);
            border: 1px solid rgba(0, 240, 255, 0.15);
            border-radius: 8px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .sub-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: bold;
            font-size: 13px;
            color: var(--cyan);
        }

        /* Bottom Command Input Bar */
        footer {
            background: var(--bg-panel);
            border-top: 1px solid var(--border-glow);
            padding: 14px 24px;
            display: flex;
            gap: 12px;
            align-items: center;
        }

        input#cmdInput {
            flex: 1;
            background: rgba(7, 11, 17, 0.9);
            border: 1px solid var(--border-glow);
            border-radius: 6px;
            padding: 12px 16px;
            color: var(--text);
            font-family: 'Rajdhani', sans-serif;
            font-size: 16px;
            outline: none;
        }

        input#cmdInput:focus {
            border-color: var(--cyan);
            box-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
        }

        /* Confirmation Modal */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(7, 11, 17, 0.85);
            backdrop-filter: blur(8px);
            z-index: 999;
            align-items: center;
            justify-content: center;
        }

        .modal-card {
            background: #0D131D;
            border: 2px solid var(--amber);
            border-radius: 12px;
            padding: 24px;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 0 30px rgba(255, 183, 3, 0.3);
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .modal-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 16px;
            color: var(--amber);
            letter-spacing: 2px;
        }

        .modal-body {
            font-size: 14px;
            line-height: 1.5;
            color: var(--text);
            background: rgba(7, 11, 17, 0.6);
            padding: 12px;
            border-radius: 6px;
            border: 1px solid rgba(255, 183, 3, 0.2);
            white-space: pre-wrap;
        }

        .modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
        }
    </style>
</head>
<body>

    <header>
        <div class="logo-box">
            <div class="logo">J.A.R.V.I.S.</div>
            <div class="sub-logo">// MARK VII WEB INTERFACE</div>
        </div>
        <div class="telemetry">
            <span id="telCpu" class="badge">CPU: 0%</span>
            <span id="telRam" class="badge">RAM: 0%</span>
            <span id="telTime" class="badge">00:00:00</span>
            <span id="telStatus" class="badge" style="color: #00F0FF;">[ ONLINE ]</span>
        </div>
    </header>

    <main>
        <!-- Left Column: Timeline & Progress -->
        <section class="panel">
            <div class="panel-title">
                <span>CONVERSATION TIMELINE</span>
                <span style="font-size: 10px; color: var(--text-dim);">LIVE DIALOG</span>
            </div>
            <div class="chat-box" id="chatBox">
                <div class="bubble jarvis">
                    <div class="sender-tag jarvis">[JARVIS]</div>
                    Greetings, sir. All core systems are operational. Speak via your microphone or type your command below.
                </div>
            </div>

            <div class="panel-title" style="margin-top: 10px;">
                <span>TASK PIPELINE</span>
            </div>
            <div class="task-card">
                <div class="task-status" id="taskStatusText">STATE: IDLE</div>
                <div class="progress-bar">
                    <div class="progress-fill" id="taskProgressBar"></div>
                </div>
                <div id="taskStepDetail" style="font-size: 12px; color: var(--text-dim);">Ready for incoming commands.</div>
            </div>
        </section>

        <!-- Center Column: Holographic AI Core & Voice Controls -->
        <section class="panel center-panel">
            <canvas id="coreCanvas" width="260" height="260"></canvas>
            <div class="state-tag" id="coreStateTag">IDLE</div>
            <canvas id="waveCanvas" width="320" height="48"></canvas>

            <div class="transcription-card" id="transcriptionCard">
                "Speak 'Hey JARVIS' or click Push-to-Talk"
            </div>

            <div class="btn-cluster">
                <button class="primary-btn" id="btnPtt" onclick="togglePushToTalk()">PUSH TO TALK</button>
                <button id="btnStopSpeech" onclick="stopSpeech()">STOP SPEAKING</button>
                <button class="danger-btn" onclick="triggerEmergencyStop()">EMERGENCY STOP</button>
                <button id="btnResetStop" class="primary-btn" style="display:none; background:#00F0FF; color:#070B11;" onclick="resetEmergencyStop()">RESUME / RESET STOP</button>
            </div>
        </section>

        <!-- Right Column: Subsystems (WhatsApp Desktop, Gmail, Weather/News) -->
        <section class="panel">
            <div class="panel-title">
                <span>SUBSYSTEMS & PERIPHERALS</span>
            </div>

            <!-- WhatsApp Desktop Subsystem -->
            <div class="subsystem-item">
                <div class="sub-header">
                    <span>WHATSAPP DESKTOP</span>
                    <button style="padding: 4px 8px; font-size: 11px;" onclick="sendCommand('open whatsapp')">OPEN</button>
                </div>
                <div id="waStatus" style="font-size: 11px; color: var(--text-dim);">Installed & Ready</div>
                <div id="waDraftText" style="font-size: 12px; color: var(--text); font-style: italic;">No pending draft.</div>
            </div>

            <!-- Gmail Subsystem -->
            <div class="subsystem-item">
                <div class="sub-header">
                    <span>GMAIL OAUTH</span>
                    <button style="padding: 4px 8px; font-size: 11px;" onclick="sendCommand('check unread emails')">UNREAD</button>
                </div>
                <div id="gmailStatus" style="font-size: 11px; color: var(--text-dim);">OAuth Credentials Ready</div>
            </div>

            <!-- Active Timers & Reminders -->
            <div class="subsystem-item">
                <div class="sub-header">
                    <span>TIMERS & REMINDERS</span>
                </div>
                <div id="timersList" style="font-size: 12px; color: var(--text-dim);">No active countdowns.</div>
            </div>

            <!-- Quick Command Triggers -->
            <div class="panel-title" style="margin-top: 10px;">
                <span>QUICK DIRECT COMMANDS</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                <button onclick="sendCommand('Open YouTube')">YOUTUBE</button>
                <button onclick="sendCommand('Open Google Chrome')">CHROME</button>
                <button onclick="sendCommand('Open Notepad')">NOTEPAD</button>
                <button onclick="sendCommand('Open Calculator')">CALCULATOR</button>
                <button onclick="sendCommand('Open folder Gromighty')">GROMIGHTY FOLDER</button>
                <button onclick="sendCommand('Open VS Code')">VS CODE</button>
                <button onclick="sendCommand('What is the weather today?')">WEATHER</button>
                <button onclick="sendCommand('Give me the latest technology news.')">LIVE NEWS</button>
            </div>
        </section>
    </main>

    <footer>
        <input type="text" id="cmdInput" placeholder="Enter voice command or prompt (e.g. 'What is the weather today?', 'Open YouTube', 'Create folder Gromighty on desktop')..." onkeydown="if(event.key==='Enter') submitCommand()">
        <button class="primary-btn" onclick="submitCommand()">EXECUTE</button>
    </footer>

    <!-- Confirmation Modal Dialog -->
    <div class="modal-overlay" id="confirmModal">
        <div class="modal-card">
            <div class="modal-title">SECURITY AUTHORIZATION REQUIRED</div>
            <div class="modal-body" id="modalPrompt"></div>
            <div class="modal-actions">
                <button class="danger-btn" onclick="resolveConfirmation(false)">CANCEL</button>
                <button class="primary-btn" onclick="resolveConfirmation(true)">AUTHORIZE & SEND</button>
            </div>
        </div>
    </div>

    <script>
        // --- 1. CORE ANIMATION (Canvas QPainter Equivalent) ---
        const coreCanvas = document.getElementById('coreCanvas');
        const ctx = coreCanvas.getContext('2d');
        let angleOuter = 0;
        let angleInner = 0;
        let pulse = 0;
        let pulseDir = 1;
        let currentState = 'idle';

        function drawCore() {
            ctx.clearRect(0, 0, coreCanvas.width, coreCanvas.height);
            const cx = coreCanvas.width / 2;
            const cy = coreCanvas.height / 2;
            const radius = 100;

            let primary = '#00F0FF';
            let secondary = '#0077FF';
            let speed = 1.0;

            if (currentState === 'listening') { primary = '#0077FF'; secondary = '#00F0FF'; speed = 2.0; }
            else if (currentState === 'processing') { primary = '#9D4EDD'; secondary = '#00F0FF'; speed = 3.5; }
            else if (currentState === 'speaking') { primary = '#00F0FF'; secondary = '#52B788'; speed = 2.5; }
            else if (currentState === 'executing') { primary = '#FFB703'; secondary = '#00F0FF'; speed = 2.8; }
            else if (currentState === 'error') { primary = '#FF3366'; secondary = '#FFB703'; speed = 1.0; }

            angleOuter += 0.02 * speed;
            angleInner -= 0.03 * speed;
            pulse += 0.02 * pulseDir * speed;
            if (pulse >= 1.0) { pulse = 1.0; pulseDir = -1; }
            if (pulse <= 0.0) { pulse = 0.0; pulseDir = 1; }

            // Outer Radial Glow
            const glow = ctx.createRadialGradient(cx, cy, 20, cx, cy, radius);
            glow.addColorStop(0, primary + '33');
            glow.addColorStop(0.8, secondary + '11');
            glow.addColorStop(1, 'transparent');
            ctx.fillStyle = glow;
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, Math.PI * 2);
            ctx.fill();

            // Outer Ring with Ticks
            ctx.strokeStyle = primary;
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.arc(cx, cy, radius * 0.9, 0, Math.PI * 2);
            ctx.stroke();

            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(angleOuter);
            for (let i = 0; i < 24; i++) {
                ctx.beginPath();
                ctx.moveTo(0, -radius * 0.9);
                ctx.lineTo(0, -radius * (i % 4 === 0 ? 0.82 : 0.86));
                ctx.stroke();
                ctx.rotate((Math.PI * 2) / 24);
            }
            ctx.restore();

            // Rotating Segmented Arcs
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(angleInner);
            ctx.strokeStyle = secondary;
            ctx.lineWidth = 3.5;
            for (let i = 0; i < 3; i++) {
                ctx.beginPath();
                ctx.arc(0, 0, radius * 0.75, 0, 1.2);
                ctx.stroke();
                ctx.rotate((Math.PI * 2) / 3);
            }
            ctx.restore();

            // Inner Pulsing Core
            const coreR = radius * (0.35 + 0.08 * pulse);
            const coreGlow = ctx.createRadialGradient(cx, cy, 2, cx, cy, coreR);
            coreGlow.addColorStop(0, '#FFFFFF');
            coreGlow.addColorStop(0.5, primary);
            coreGlow.addColorStop(1, secondary + '22');
            ctx.fillStyle = coreGlow;
            ctx.beginPath();
            ctx.arc(cx, cy, coreR, 0, Math.PI * 2);
            ctx.fill();

            requestAnimationFrame(drawCore);
        }
        drawCore();

        // --- 2. AUDIO WAVE VISUALIZER ---
        const waveCanvas = document.getElementById('waveCanvas');
        const wCtx = waveCanvas.getContext('2d');
        const numBars = 32;

        function drawWave() {
            wCtx.clearRect(0, 0, waveCanvas.width, waveCanvas.height);
            const barW = (waveCanvas.width / numBars) - 2;
            const isWaveActive = currentState === 'listening' || currentState === 'speaking';

            for (let i = 0; i < numBars; i++) {
                const lvl = isWaveActive ? Math.random() * 0.85 + 0.15 : 0.08;
                const h = waveCanvas.height * lvl;
                const y = (waveCanvas.height - h) / 2;
                wCtx.fillStyle = '#00F0FF';
                wCtx.fillRect(i * (barW + 2), y, barW, h);
            }
            setTimeout(drawWave, 50);
        }
        drawWave();

        function setCoreState(st) {
            currentState = st.toLowerCase();
            document.getElementById('coreStateTag').innerText = st.toUpperCase();
            document.getElementById('telStatus').innerText = `[ ${st.toUpperCase()} ]`;
        }

        // --- 3. SPEECH RECOGNITION (WEB SPEECH API) ---
        let recognition = null;
        let isListening = false;

        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRec();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            recognition.onstart = () => {
                isListening = true;
                setCoreState('listening');
                document.getElementById('btnPtt').classList.add('active-rec');
                document.getElementById('transcriptionCard').innerText = "Listening to your voice...";
            };

            recognition.onresult = (event) => {
                let interim = '';
                let finalTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript;
                    } else {
                        interim += event.results[i][0].transcript;
                    }
                }

                if (interim) {
                    document.getElementById('transcriptionCard').innerText = `"${interim}"`;
                }

                if (finalTranscript) {
                    document.getElementById('transcriptionCard').innerText = `"${finalTranscript}"`;
                    // Submit recognized voice command
                    sendCommand(finalTranscript.trim());
                }
            };

            recognition.onerror = (err) => {
                console.log("SpeechRec error:", err);
            };

            recognition.onend = () => {
                isListening = false;
                document.getElementById('btnPtt').classList.remove('active-rec');
                if (currentState === 'listening') setCoreState('idle');
            };
        }

        function togglePushToTalk() {
            if (!recognition) {
                alert("Speech recognition is not supported in this browser. Please use Google Chrome or Edge.");
                return;
            }
            if (isListening) {
                recognition.stop();
            } else {
                recognition.start();
            }
        }

        // --- 4. SPEECH SYNTHESIS (EDGE TTS AUDIO & FALLBACK) ---
        let currentAudio = null;

        async function speakText(text) {
            setCoreState('speaking');
            try {
                const res = await fetch('/api/tts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text })
                });

                if (res.ok && res.headers.get('content-type')?.includes('audio')) {
                    const blob = await res.blob();
                    const audioUrl = URL.createObjectURL(blob);
                    if (currentAudio) currentAudio.pause();
                    currentAudio = new Audio(audioUrl);
                    currentAudio.onended = () => { setCoreState('idle'); };
                    currentAudio.play();
                    return;
                }
            } catch (e) {
                console.log("TTS audio error, using web synthesis fallback:", e);
            }

            // Web Speech API fallback
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utter = new SpeechSynthesisUtterance(text);
                utter.onend = () => setCoreState('idle');
                window.speechSynthesis.speak(utter);
            } else {
                setCoreState('idle');
            }
        }

        function stopSpeech() {
            if (currentAudio) { currentAudio.pause(); currentAudio = null; }
            if ('speechSynthesis' in window) window.speechSynthesis.cancel();
            setCoreState('idle');
        }

        // --- 5. COMMAND EXECUTION & CONFIRMATION ---
        let pendingConfirmation = null;

        async function sendCommand(text) {
            if (!text) return;
            addChatBubble('USER', text);
            setCoreState('processing');

            document.getElementById('taskStatusText').innerText = "STATE: EXECUTING";
            document.getElementById('taskProgressBar').style.width = "40%";
            document.getElementById('taskStepDetail').innerText = "Understanding intent and planning tools...";

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: text })
                });
                const data = await res.json();

                document.getElementById('taskProgressBar').style.width = "100%";
                document.getElementById('taskStatusText').innerText = `STATE: ${data.status.toUpperCase()}`;
                document.getElementById('taskStepDetail').innerText = "Execution completed.";

                // Auto-open requested web application / URL or folder
                let urlToOpen = null;
                let folderPath = null;
                if (data.steps_executed) {
                    for (const st of data.steps_executed) {
                        if (st.data) {
                            if (st.data.open_url || st.data.url) {
                                urlToOpen = st.data.open_url || st.data.url;
                            }
                            if (st.data.path) {
                                folderPath = st.data.path;
                            }
                        }
                    }
                }
                if (!urlToOpen && data.response) {
                    const match = data.response.match(/https?:\/\/[^\s\)\'\"]+/);
                    if (match && (data.response.toLowerCase().includes('opened') || data.response.toLowerCase().includes('playing') || data.response.toLowerCase().includes('navigated'))) {
                        urlToOpen = match[0];
                    }
                }

                // Immediately open tab in browser
                if (urlToOpen) {
                    try {
                        const win = window.open(urlToOpen, '_blank');
                        if (!win) {
                            console.log("Popup blocked by browser policy");
                        }
                    } catch (e) {
                        console.error("Window open error:", e);
                    }
                }

                addChatBubble('JARVIS', data.response, urlToOpen, folderPath);

                // Handle Confirmation if required (WhatsApp / Email)
                if (data.requires_confirmation && data.confirmation_info) {
                    pendingConfirmation = data.confirmation_info;
                    document.getElementById('modalPrompt').innerText = data.confirmation_info.prompt;
                    document.getElementById('confirmModal').style.display = 'flex';
                }

                // Speak response
                speakText(data.response);
            } catch (err) {
                setCoreState('error');
                addChatBubble('JARVIS', "Error executing command: " + err.message);
            }
        }

        function submitCommand() {
            const input = document.getElementById('cmdInput');
            const val = input.value.trim();
            if (val) {
                input.value = '';
                sendCommand(val);
            }
        }

        async function resolveConfirmation(approved) {
            document.getElementById('confirmModal').style.display = 'none';
            if (!pendingConfirmation) return;

            const tool = pendingConfirmation.tool;
            pendingConfirmation = null;

            const res = await fetch('/api/confirm', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tool, confirmed: approved })
            });
            const data = await res.json();
            addChatBubble('JARVIS', data.response);
            speakText(data.response);
        }

        function addChatBubble(sender, message, urlToOpen = null, folderPath = null) {
            const box = document.getElementById('chatBox');
            const b = document.createElement('div');
            b.className = `bubble ${sender.toLowerCase()}`;

            let extraHtml = '';
            if (urlToOpen) {
                extraHtml += `
                    <div style="margin-top: 10px; padding: 10px 14px; background: rgba(0, 240, 255, 0.12); border: 1px solid var(--cyan); border-radius: 6px; display: flex; align-items: center; justify-content: space-between; gap: 12px;">
                        <div>
                            <div style="font-size: 11px; color: var(--cyan); font-weight: bold; letter-spacing: 1px;">🚀 BROWSER LAUNCHED</div>
                            <div style="font-size: 12px; color: #fff; word-break: break-all;">${urlToOpen}</div>
                        </div>
                        <a href="${urlToOpen}" target="_blank" style="padding: 6px 14px; background: var(--cyan); color: #070B11; text-decoration: none; font-weight: bold; font-size: 12px; border-radius: 4px; white-space: nowrap; box-shadow: 0 0 10px rgba(0,240,255,0.6);">OPEN TAB ↗</a>
                    </div>
                `;
            }
            if (folderPath) {
                extraHtml += `
                    <div style="margin-top: 10px; padding: 10px 14px; background: rgba(255, 183, 3, 0.12); border: 1px solid var(--amber); border-radius: 6px; display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 22px;">📂</span>
                        <div>
                            <div style="font-size: 11px; color: var(--amber); font-weight: bold; letter-spacing: 1px;">FOLDER OPENED IN FILE EXPLORER</div>
                            <div style="font-size: 12px; color: #fff; word-break: break-all;">${folderPath}</div>
                        </div>
                    </div>
                `;
            }

            b.innerHTML = `<div class="sender-tag ${sender.toLowerCase()}">[${sender}]</div>${message.replace(/\\n/g, '<br>')}${extraHtml}`;
            box.appendChild(b);
            box.scrollTop = box.scrollHeight;
        }

        // --- 6. TELEMETRY & STATUS POLLING ---
        async function updateStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                document.getElementById('telCpu').innerText = `CPU: ${data.cpu}%`;
                document.getElementById('telRam').innerText = `RAM: ${data.ram}%`;
                document.getElementById('telTime').innerText = data.time;

                if (data.whatsapp_draft) {
                    document.getElementById('waDraftText').innerText = `Draft for ${data.whatsapp_draft.recipient}: "${data.whatsapp_draft.message}"`;
                }

                // Timers
                if (data.active_timers && data.active_timers.length > 0) {
                    const lines = data.active_timers.map(t => {
                        const m = Math.floor(t.remaining / 60);
                        const s = t.remaining % 60;
                        return `⏱ ${t.title}: ${m}m ${s}s`;
                    });
                    document.getElementById('timersList').innerText = lines.join('\\n');
                } else {
                    document.getElementById('timersList').innerText = "No active countdowns.";
                }
            } catch (e) {}
        }
        setInterval(updateStatus, 1000);

        async function triggerEmergencyStop() {
            await fetch('/api/emergency_stop', { method: 'POST' });
            stopSpeech();
            setCoreState('error');
            document.getElementById('btnResetStop').style.display = 'inline-block';
            addChatBubble('JARVIS', 'EMERGENCY STOP TRIGGERED: Operations halted.');
        }

        async function resetEmergencyStop() {
            await fetch('/api/emergency_reset', { method: 'POST' });
            document.getElementById('btnResetStop').style.display = 'none';
            setCoreState('idle');
            addChatBubble('JARVIS', 'Emergency Stop cleared. System online.');
        }
    </script>
</body>
</html>
"""


def start_server(port: int = 8080):
    """Starts the FastAPI web server on port 8080 and opens browser."""
    print("=" * 60)
    print(f"JARVIS Holographic AI Interface starting at http://localhost:{port}")
    print("=" * 60)
    # Automatically open user's default browser to JARVIS HUD
    webbrowser.open(f"http://localhost:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    start_server(8080)
