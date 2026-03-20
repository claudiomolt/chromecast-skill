---
name: chromecast
description: Control a Chromecast or Google Cast device on the local network. Use when the user asks to play a YouTube video on TV, pause/resume playback, change volume, or control any Cast-enabled device (Chromecast, Android TV, Samsung with Chromecast built-in). Requires being on the same Wi-Fi network as the device.
---

# Chromecast Skill ⚡

Control any Google Cast device on your local network via Python — play YouTube videos, control playback, change volume. All with a voice note.

## Quick Reference

```bash
# Play a YouTube video on TV
python3 {baseDir}/scripts/cast.py play <video_id_or_url> [--device "Family Room"]

# Pause / Resume
python3 {baseDir}/scripts/cast.py pause [--device "Family Room"]
python3 {baseDir}/scripts/cast.py resume [--device "Family Room"]

# Volume (0.0 to 1.0)
python3 {baseDir}/scripts/cast.py volume 0.5 [--device "Family Room"]

# Stop / Disconnect
python3 {baseDir}/scripts/cast.py stop [--device "Family Room"]

# List all Cast devices on the network
python3 {baseDir}/scripts/cast.py list
```

## Setup (first time only)

```bash
pip3 install pychromecast --break-system-packages
```

That's it. No API keys, no config files.

## How it works

1. Scans local network for Cast devices via mDNS (port 8009)
2. Connects directly to the device by IP
3. Launches the YouTube app on the TV
4. Sends the video ID via the Cast protocol

## Known devices (local network)
| Device | IP | Port |
|--------|----|------|
| Family Room | 192.168.1.164 | 8009 |

## Notes
- Must be on the same Wi-Fi as the Chromecast
- YouTube video ID can be extracted from any YouTube URL
- Works with Chromecast, Chromecast built-in TVs (Samsung, Sony, etc.), Android TV
