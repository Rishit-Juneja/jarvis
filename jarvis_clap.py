import sounddevice as sd
import numpy as np
import time
import whisper
import tempfile
import scipy.io.wavfile as wav
import requests
import edge_tts
import asyncio
import os
import subprocess
import re
 
THRESHOLD = 20.0
SAMPLE_RATE = 16000
SILENCE_DURATION = 3.0
CLAP_WINDOW = 1.5
STATE_FILE = '/tmp/jarvis_state'
clap_times = []
 
model = whisper.load_model("small")
 
def set_state(state):
    with open(STATE_FILE, 'w') as f:
        f.write(state)
 
async def speak_async(text):
    set_state('speaking')
    communicate = edge_tts.Communicate(text, voice="en-US-GuyNeural",rate="+50%")
    await communicate.save('/tmp/jarvis_response.mp3')
    os.system('mpg123 -q /tmp/jarvis_response.mp3')
    set_state('idle')
 
def speak(text):
    asyncio.run(speak_async(text))
 
def open_app(app_name):
    app = app_name.lower().strip().replace(" ", "")
    lookup = {
        "spotify": "spotify",
        "terminal": "konsole",
        "console": "konsole",
        "konsole": "konsole",
        "notepad": "kate",
        "notepad++": "kate",
        "kate": "kate",
        "brave": "brave",
        "chrome": "brave",
        "googlechrome": "brave",
        "files": "dolphin",
        "filemanager": "dolphin",
        "dolphin": "dolphin",
        "code": "code",
        "vscode": "code",
        "discord": "discord",
        "steam": "steam",
        "settings": "systemsettings",
        "systemsettings": "systemsettings",
    }
    cmd = lookup.get(app, app)
    try:
        subprocess.Popen([cmd])
        print(f"Opening {app_name}")
    except Exception as e:
        speak(f"Sorry, I couldn't open {app_name}")
        print(f"Error: {e}")
 
def open_brave_search(query):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    subprocess.Popen(['brave', url])
    print(f"Searching for {query}")
 
def daddys_home():
    speak("Hey boss, setting up your workspace")
    subprocess.Popen(["konsole", "-e", "cava"])
    time.sleep(0.5)
    subprocess.Popen(["spotify"])
    time.sleep(0.5)
    subprocess.Popen(["konsole","-e","cmatrix"])
    print("Workspace ready")
 
# ── Kill functions ─────────────────────────────────────────────────────────
KILL_MAP = {
    "brave":         ["pkill", "-f", "brave"],
    "spotify":       ["pkill", "-f", "spotify"],
    "discord":       ["pkill", "-f", "discord"],
    "steam":         ["pkill", "-f", "steam"],
    "terminal":      ["pkill", "-f", "konsole"],
    "konsole":       ["pkill", "-f", "konsole"],
    "code":          ["pkill", "-f", "code"],
    "vscode":        ["pkill", "-f", "code"],
    "dolphin":       ["pkill", "-f", "dolphin"],
    "files":         ["pkill", "-f", "dolphin"],
    "kate":          ["pkill", "-f", "kate"],
    "notepad":       ["pkill", "-f", "kate"],
    "systemmonitor": ["pkill", "-f", "plasma-systemmonitor"],
    "monitor":       ["pkill", "-f", "plasma-systemmonitor"],
    "cava":          ["pkill", "-f", "cava"],
}
 
def kill_app(app_name):
    key = app_name.lower().strip().replace(" ", "")
    cmd = KILL_MAP.get(key)
    if cmd:
        subprocess.run(cmd)
        speak(f"Closed {app_name}")
    else:
        speak(f"I don't know how to close {app_name}")
 
def kill_everything():
    speak("Closing everything, back to desktop.")
    for cmd in KILL_MAP.values():
        subprocess.run(cmd, stderr=subprocess.DEVNULL)
 
def is_kill_everything(text):
    triggers = ["kill everything", "close everything", "clean up",
                "clear everything", "close all", "kill all",
                "back to desktop", "clear the desktop"]
    return any(t in text for t in triggers)
 
def get_kill_target(text):
    for key in KILL_MAP:
        if key in text:
            return key
    return None
 
# ── News ───────────────────────────────────────────────────────────────────
NEWS_KEYWORDS = ["world", "news", "happening", "headlines", "global",
                 "latest news", "what's going on", "whats going on", "around the world"]
 
def is_news_query(text):
    return any(kw in text.lower() for kw in NEWS_KEYWORDS)
 
# ── Main handler ───────────────────────────────────────────────────────────
def ask_jarvis(text):
    t = text.lower()
 
    if "daddy's home" in t or "daddys home" in t:
        daddys_home()
        return
 
    if "bye jarvis" in t or "goodbye jarvis" in t:
        speak("Goodbye, shutting down.")
        os.system("fuser -k 5678/tcp")
        os.system("sudo pkill -u ollama")
        os.system("pkill -f jarvis_clap.py")
        return
 
    if is_kill_everything(t):
        kill_everything()
        return
 
    if "kill" in t or "close" in t:
        target = get_kill_target(t)
        if target:
            kill_app(target)
            return
 
    set_state('thinking')
    print("Thinking...")
 
    if is_news_query(t):
        print("[Intent] → World news scraper path")
        subprocess.Popen(["brave", "https://worldmonitor.app"])
    else:
        print("[Intent] → Normal AI Agent path")
 
    try:
        response = requests.post(
            os.environ.get("JARVIS_WEBHOOK_URL", "http://localhost:5678/webhook/YOUR_WEBHOOK_ID"),
            json={"chatInput": text},
            timeout=30
        )
        result = response.json()
 
        if isinstance(result, dict):
            response_text = (
                result.get('output')
                or result.get('text')
                or result.get('chatInput')
                or str(result)
            ).strip()
        else:
            response_text = str(result).strip()
 
        # strip gemma4 thinking tags
        response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
 
        print(f"Jarvis: {response_text}")
 
        lines = response_text.split('\n')
        spoke = False
        for line in lines:
            line = line.strip()
            if line.startswith("SEARCH:"):
                query = line.replace("SEARCH:", "").strip()
                open_brave_search(query)
            elif line.startswith("OPEN:"):
                app = line.replace("OPEN:", "").strip()
                open_app(app)
            elif line and not spoke:
                speak(line)
                spoke = True
 
        if not spoke:
            set_state('idle')
 
    except Exception as e:
        print(f"Error: {e}")
        speak("Sorry, something went wrong.")
 
def record_until_silence():
    set_state('listening')
    print("Recording... speak now")
    audio_chunks = []
    silence_start = None
    speech_detected = False
 
    def callback(indata, frames, time_info, status):
        nonlocal silence_start, speech_detected
        audio_chunks.append(indata.copy())
        energy = np.sqrt(np.mean(indata**2))
        if energy > 0.02:
            speech_detected = True
            silence_start = None
        else:
            if speech_detected and silence_start is None:
                silence_start = time.time()
 
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                        dtype='float32', callback=callback):
        while True:
            time.sleep(0.1)
            if silence_start and (time.time() - silence_start) > SILENCE_DURATION:
                break
            if not speech_detected and len(audio_chunks) > 50:
                print("No speech detected, ignoring...")
                set_state('idle')
                return
 
    if not speech_detected:
        set_state('idle')
        return
 
    audio = np.concatenate(audio_chunks, axis=0)
    set_state('thinking')
    print("Transcribing...")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav.write(f.name, SAMPLE_RATE, audio)
        result = model.transcribe(f.name, language="en")
        text = result['text'].strip()
        print(f"You said: {text}")
        if text:
            ask_jarvis(text)
        else:
            set_state('idle')
 
def detect_clap(indata, frames, time_info, status):
    volume = np.linalg.norm(indata)
    if volume > THRESHOLD:
        now = time.time()
        clap_times.append(now)
        recent = [t for t in clap_times if now - t < CLAP_WINDOW]
        clap_times.clear()
        clap_times.extend(recent)
        if len(clap_times) >= 2:
            print("Double clap detected!")
            clap_times.clear()
            record_until_silence()
 
set_state('idle')
print("Jarvis is online. Double clap to speak.")
with sd.InputStream(callback=detect_clap):
    while True:
        time.sleep(0.1)
