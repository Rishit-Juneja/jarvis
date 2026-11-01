# Jarvis

**It listens before you speak.** A local voice assistant: double-clap to wake it, talk, and it answers out loud. The core loop needs no cloud.

```
double clap → record until silence → Whisper (small) STT
            → n8n webhook → Ollama agent with Redis memory
            → edge-tts reply  ·  SEARCH: / OPEN: lines become actions
            → state file → state server :7777 → holographic HUD
```

## Voice commands

- **"Daddy's home"** sets up the workspace: Spotify, cava and cmatrix.
- **"Close spotify"** or **"kill brave"** closes that app. **"Kill everything"** closes them all and leaves you on the desktop.
- **"What's happening in the world"** opens the news.
- **"Bye Jarvis"** shuts down n8n, Ollama and Jarvis itself.
- Anything else goes to the agent.

## Run it

Needs Ollama, Redis and n8n running locally, and an n8n workflow with a webhook trigger.

```bash
pip install -r requirements.txt          # plus mpg123 for audio playback
export JARVIS_WEBHOOK_URL=http://localhost:5678/webhook/<your-id>
python3 jarvis_state_server.py &         # HUD state on :7777
python3 jarvis_clap.py                   # "Jarvis is online. Double clap to speak."
```

Open `jarvis_hud.html` on a second screen for the HUD. It's mirrored for a reflective hologram display.

Tune `THRESHOLD` in `jarvis_clap.py` for your mic. App names in `open_app` / `KILL_MAP` are for KDE (konsole, dolphin, kate).

---
<sub>Part of <a href="https://github.com/Rishit-Juneja">The Rishit Experience</a> · 🟡 Signal</sub>
