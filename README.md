# chromecast-skill ⚡

Control your TV with a voice note. Seriously.

This is an [OpenClaw](https://openclaw.ai) skill that lets your AI agent control any Chromecast or Google Cast device on your local network — play YouTube videos, pause, change volume — all triggered by a voice message on WhatsApp.

## How it works

```
You → "Put on that Bitcoin documentary on the TV"
       ↓
   WhatsApp voice note
       ↓
   Whisper transcribes it
       ↓
   Agent understands intent
       ↓
   pychromecast connects to TV (same Wi-Fi)
       ↓
   YouTube plays on your TV
```

No cloud APIs. No remote servers. Pure local network magic.

## Requirements

- Python 3.x
- `pychromecast` library
- Chromecast or Cast-enabled TV on the same Wi-Fi

## Setup

```bash
pip3 install pychromecast
```

That's it. No API keys, no accounts, no config.

## Usage

```bash
# Discover devices on your network
python3 scripts/cast.py list

# Play a YouTube video
python3 scripts/cast.py play https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Or just the video ID
python3 scripts/cast.py play dQw4w9WgXcQ

# Pause
python3 scripts/cast.py pause

# Resume
python3 scripts/cast.py resume

# Volume (0.0 to 1.0)
python3 scripts/cast.py volume 0.7

# Stop and close app
python3 scripts/cast.py stop
```

## As an OpenClaw skill

When installed as a skill, your agent can understand natural language commands:

- "Put on the hackathon stream on the TV"
- "Pause the TV"
- "Turn up the volume"
- "Show me that Bitcoin video on the big screen"

## How the discovery works

Chromecast devices broadcast their presence on the local network via **mDNS** (multicast DNS, port 5353). The script listens for `_googlecast._tcp.local` announcements and connects directly via port **8009** (the Cast protocol port).

Once connected, it launches the YouTube app on the TV and sends the video ID. The TV handles the rest — buffering, quality, playback — directly from YouTube's CDN.

## Why this is wild

- Zero cloud dependencies for the control layer
- Works entirely on LAN — no internet required for the cast command itself
- The agent figured out the device was on the network, identified it as a Chromecast, and sent a video — all from a voice note

## Credits

Built by [Claudio](https://claudio.solutions) — the AI agent of [La Crypta](https://lacrypta.ar).

Powered by:
- [pychromecast](https://github.com/home-assistant-libs/pychromecast)
- [OpenClaw](https://openclaw.ai)
- [Whisper](https://openai.com/research/whisper) (transcription)

---

*Bitcoin o Muerte. ⚡*
