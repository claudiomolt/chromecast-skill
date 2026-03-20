---
name: chromecast
description: Control Cast devices (Chromecast AND Samsung SmartTV) on the local network. Use when the user asks to play a YouTube video on TV, pause/resume, change volume, or list available screens. Discovers all devices automatically using multiple protocols (mDNS for Chromecast, SSDP/DIAL for Samsung). Requires being on the same Wi-Fi network as the devices.
---

# Chromecast + Samsung SmartTV Skill ⚡

Control any screen on your local network — Chromecast, Samsung SmartTV, or any DIAL-compatible device.

## Quick Reference

```bash
# Discover ALL devices on the network (Chromecast + Samsung)
python3 {baseDir}/scripts/cast.py discover

# Play a YouTube video — interactive device picker
python3 {baseDir}/scripts/cast.py play <video_id_or_url>

# Play on a specific Chromecast
python3 {baseDir}/scripts/cast.py play <url> --device "Family Room"

# Play on Samsung TV (by IP)
python3 {baseDir}/scripts/cast.py play <url> --samsung 192.168.1.126

# Pause / Resume / Stop
python3 {baseDir}/scripts/cast.py pause [--device X | --samsung X]
python3 {baseDir}/scripts/cast.py resume [--device X | --samsung X]
python3 {baseDir}/scripts/cast.py stop [--device X | --samsung X]

# Volume (0.0 to 1.0)
python3 {baseDir}/scripts/cast.py volume 0.7 [--device X | --samsung X]
```

## Setup

```bash
pip3 install pychromecast samsungtvws --break-system-packages
```

**First time with Samsung:** run `discover` or `play` — a pairing popup will appear on the TV. Accept it once and the token is saved permanently.

## Discovery protocols

| Protocol | Devices | Port |
|----------|---------|------|
| mDNS `_googlecast._tcp` | Chromecast, Chromecast built-in | 8009 |
| SSDP DIAL | Samsung SmartTV (Tizen), other DIAL TVs | 7678/8001 |

## Known devices (local network)
| Device | Type | IP | Port |
|--------|------|-----|------|
| Family Room | Chromecast | 192.168.1.164 | 8009 |
| Samsung Living | Samsung SmartTV (70TA, 4K) | 192.168.1.126 | 8001 |

## Agent usage

When the user says "put X on the TV" or "cast this to the screen":
1. Run `discover` to find all available devices
2. Present the list to the user (if multiple)
3. Run `play <video_id>` on the chosen device

## Samsung via YouTube Lounge API (RECOMMENDED)

The most reliable way to cast to Samsung TVs — same protocol Android uses.

```bash
pip3 install pyytlounge --break-system-packages
```

```python
# Quick cast to Samsung via YouTube Lounge
import asyncio, urllib.request, re
from pyytlounge import YtLoungeApi

async def cast_to_samsung(video_id, tv_ip='192.168.1.126'):
    r = urllib.request.urlopen(f'http://{tv_ip}:8080/ws/apps/YouTube', timeout=5)
    screen_id = re.search(r'<screenId>([^<]+)</screenId>', r.read().decode()).group(1)
    async with YtLoungeApi('Claudio') as api:
        await api.pair_with_screen_id(screen_id)
        await api.connect()
        await api.play_video(video_id)

asyncio.run(cast_to_samsung('VIDEO_ID'))
```
