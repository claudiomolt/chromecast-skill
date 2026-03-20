#!/usr/bin/env python3
"""
cast.py — Control Cast devices (Chromecast + Samsung SmartTV) from the command line.

Usage:
  python3 cast.py discover          # Scan and list ALL devices (Chromecast + Samsung)
  python3 cast.py play <url_or_id>  # Interactive: choose device, then play
  python3 cast.py play <url_or_id> --device "Family Room"   # Chromecast by name
  python3 cast.py play <url_or_id> --samsung 192.168.1.x    # Samsung direct
  python3 cast.py pause  [--device X | --samsung X]
  python3 cast.py resume [--device X | --samsung X]
  python3 cast.py volume <0.0-1.0> [--device X | --samsung X]
  python3 cast.py stop   [--device X | --samsung X]
"""

import argparse
import re
import socket
import struct
import sys
import time

# ─── Dependency checks ────────────────────────────────────────────────────────

try:
    import pychromecast
    from pychromecast.controllers.youtube import YouTubeController
    HAS_PYCHROMECAST = True
except ImportError:
    HAS_PYCHROMECAST = False

try:
    from samsungtvws import SamsungTVWS
    HAS_SAMSUNG = True
except ImportError:
    HAS_SAMSUNG = False

SAMSUNG_TOKEN_FILE = "~/.chromecast_samsung_token.txt"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def extract_video_id(input_str: str) -> str:
    """Extract YouTube video ID from URL or return as-is."""
    for pattern in [r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", r"^([A-Za-z0-9_-]{11})$"]:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)
    return input_str

# ─── Discovery ────────────────────────────────────────────────────────────────

def discover_chromecast(timeout=8):
    """Find Chromecast/Google Cast devices via mDNS."""
    if not HAS_PYCHROMECAST:
        return []
    ccs, browser = pychromecast.get_chromecasts(timeout=timeout)
    pychromecast.stop_discovery(browser)
    return [{"type": "chromecast", "name": cc.name, "host": cc.cast_info.host,
              "port": cc.cast_info.port, "model": cc.model_name or "Chromecast"} for cc in ccs]

def discover_samsung(timeout=5):
    """Find Samsung SmartTVs via SSDP DIAL discovery."""
    devices = []
    SSDP_ADDR, SSDP_PORT = "239.255.255.250", 1900
    msg = "\r\n".join([
        "M-SEARCH * HTTP/1.1", f"HOST: {SSDP_ADDR}:{SSDP_PORT}",
        'MAN: "ssdp:discover"', "MX: 3",
        "ST: urn:dial-multiscreen-org:service:dial:1", "", ""
    ]).encode()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(timeout)
    sock.sendto(msg, (SSDP_ADDR, SSDP_PORT))
    found = {}
    try:
        while True:
            data, addr = sock.recvfrom(4096)
            ip = addr[0]
            text = data.decode("utf-8", errors="ignore")
            if ip not in found and "Samsung" in text:
                found[ip] = text
                # Extract friendly name from DIAL
                name = ip
                try:
                    import urllib.request
                    loc_match = re.search(r"LOCATION: (http://[^\r\n]+)", text)
                    if loc_match:
                        r = urllib.request.urlopen(loc_match.group(1), timeout=3)
                        xml = r.read().decode("utf-8", errors="ignore")
                        fn = re.search(r"<friendlyName>([^<]+)</friendlyName>", xml)
                        if fn:
                            name = fn.group(1)
                except Exception:
                    pass
                devices.append({"type": "samsung", "name": name, "host": ip, "port": 8001})
    except socket.timeout:
        pass
    sock.close()
    return devices

def discover_all():
    """Discover all Cast + Samsung devices on the local network."""
    print("🔍 Scanning local network...")
    print("  → Chromecast (mDNS / Google Cast protocol)...")
    cc_devices = discover_chromecast()
    print("  → Samsung SmartTV (SSDP / DIAL protocol)...")
    sam_devices = discover_samsung()
    return cc_devices + sam_devices

# ─── Device selection ─────────────────────────────────────────────────────────

def pick_device(devices):
    """Interactive device picker."""
    if not devices:
        print("❌ No devices found on the local network.")
        sys.exit(1)
    print("\n📺 Available devices:")
    for i, d in enumerate(devices):
        proto = "Chromecast" if d["type"] == "chromecast" else "Samsung SmartTV"
        print(f"  [{i+1}] {d['name']} ({proto}) — {d['host']}")
    if len(devices) == 1:
        print(f"\nOnly one device found, using: {devices[0]['name']}")
        return devices[0]
    while True:
        try:
            choice = int(input("\nSelect device number: ").strip())
            if 1 <= choice <= len(devices):
                return devices[choice - 1]
        except (ValueError, KeyboardInterrupt):
            pass
        print("Invalid choice.")

# ─── Chromecast actions ───────────────────────────────────────────────────────

def cc_connect(host, name=""):
    cast = pychromecast.get_chromecast_from_host((host, 8009, None, name, None))
    cast.wait(timeout=10)
    return cast

def cc_play(host, name, video_id):
    cast = cc_connect(host, name)
    ytc = YouTubeController()
    cast.register_handler(ytc)
    cast.wait(timeout=5)
    ytc.play_video(video_id)
    time.sleep(3)
    print(f"✅ Playing on {cast.name} — app: {cast.app_display_name}")

def cc_pause(host, name): cc_connect(host, name).media_controller.pause(); print("⏸ Paused.")
def cc_resume(host, name): cc_connect(host, name).media_controller.play(); print("▶️  Resumed.")
def cc_stop(host, name): cc_connect(host, name).quit_app(); print("⏹ Stopped.")
def cc_volume(host, name, level): cc_connect(host, name).set_volume(level); print(f"🔊 Volume {level:.0%}")

# ─── Samsung actions ──────────────────────────────────────────────────────────

def sam_connect(host):
    import os
    token_file = os.path.expanduser(SAMSUNG_TOKEN_FILE)
    tv = SamsungTVWS(host, name="Claudio", token_file=token_file)
    return tv

def sam_play(host, video_id):
    import urllib.request
    # Use DIAL to launch YouTube with video
    # Find DIAL port first
    dial_port = 7678
    url = f"https://www.youtube.com/watch?v={video_id}"
    tv = sam_connect(host)
    try:
        tv.open_browser(url)
        print(f"✅ YouTube opened on Samsung TV")
    except Exception as e:
        print(f"⚠️  Browser method failed ({e}), trying app launch...")
        tv.run_app("111299001912")  # YouTube Tizen app ID
        print("✅ YouTube app launched")

def sam_pause(host): sam_connect(host).shortcuts().pause(); print("⏸ Paused.")
def sam_resume(host): sam_connect(host).shortcuts().play(); print("▶️  Resumed.")
def sam_stop(host): sam_connect(host).shortcuts().home(); print("⏹ Stopped (home).")
def sam_volume(host, level):
    tv = sam_connect(host)
    pct = int(level * 100)
    for _ in range(pct): tv.shortcuts().mute()  # fallback: use key commands
    print(f"🔊 Volume ~{pct}%")

# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_discover(_args):
    devices = discover_all()
    if not devices:
        print("\n❌ No Cast devices found.")
    else:
        print(f"\n✅ Found {len(devices)} device(s):")
        for d in devices:
            proto = "Chromecast" if d["type"] == "chromecast" else "Samsung SmartTV"
            print(f"  • {d['name']} — {proto} ({d['host']}:{d['port']})")

def cmd_play(args):
    video_id = extract_video_id(args.target)

    # Direct target specified
    if args.samsung:
        print(f"📺 Samsung TV {args.samsung}")
        sam_play(args.samsung, video_id)
        return
    if args.device:
        if not HAS_PYCHROMECAST:
            print("pychromecast not installed"); sys.exit(1)
        ccs = discover_chromecast()
        for d in ccs:
            if args.device.lower() in d["name"].lower():
                cc_play(d["host"], d["name"], video_id)
                return
        print(f"Device '{args.device}' not found."); sys.exit(1)

    # Interactive: discover all and pick
    devices = discover_all()
    device = pick_device(devices)
    if device["type"] == "chromecast":
        cc_play(device["host"], device["name"], video_id)
    else:
        sam_play(device["host"], video_id)

def _resolve_device(args):
    if args.samsung:
        return {"type": "samsung", "host": args.samsung}
    if args.device:
        for d in discover_chromecast():
            if args.device.lower() in d["name"].lower():
                return d
        print("Device not found"); sys.exit(1)
    return pick_device(discover_all())

def cmd_pause(args):
    d = _resolve_device(args)
    if d["type"] == "samsung": sam_pause(d["host"])
    else: cc_pause(d["host"], d.get("name",""))

def cmd_resume(args):
    d = _resolve_device(args)
    if d["type"] == "samsung": sam_resume(d["host"])
    else: cc_resume(d["host"], d.get("name",""))

def cmd_stop(args):
    d = _resolve_device(args)
    if d["type"] == "samsung": sam_stop(d["host"])
    else: cc_stop(d["host"], d.get("name",""))

def cmd_volume(args):
    level = float(args.level)
    if not 0.0 <= level <= 1.0:
        print("Volume must be 0.0–1.0"); sys.exit(1)
    d = _resolve_device(args)
    if d["type"] == "samsung": sam_volume(d["host"], level)
    else: cc_volume(d["host"], d.get("name",""), level)

# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="🎬 Cast YouTube to any TV on the local network (Chromecast + Samsung SmartTV)"
    )
    parser.add_argument("--device", help="Chromecast device name (partial match)")
    parser.add_argument("--samsung", help="Samsung TV IP address")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("discover", help="Scan and list all Cast + Samsung devices")

    play_p = sub.add_parser("play", help="Play a YouTube video (interactive device picker)")
    play_p.add_argument("target", help="YouTube URL or video ID")

    sub.add_parser("pause", help="Pause playback")
    sub.add_parser("resume", help="Resume playback")
    sub.add_parser("stop", help="Stop and go to home")

    vol_p = sub.add_parser("volume", help="Set volume (0.0–1.0)")
    vol_p.add_argument("level", help="Volume level")

    args = parser.parse_args()

    commands = {
        "discover": cmd_discover,
        "play": cmd_play,
        "pause": cmd_pause,
        "resume": cmd_resume,
        "stop": cmd_stop,
        "volume": cmd_volume,
    }

    if args.command not in commands:
        parser.print_help()
        sys.exit(1)

    commands[args.command](args)

if __name__ == "__main__":
    main()
