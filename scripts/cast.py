#!/usr/bin/env python3
"""
cast.py — Control a Chromecast/Google Cast device from the command line.

Usage:
  python3 cast.py list
  python3 cast.py play <video_id_or_url> [--device "Family Room"] [--ip 192.168.1.x]
  python3 cast.py pause [--device "Family Room"]
  python3 cast.py resume [--device "Family Room"]
  python3 cast.py volume <0.0-1.0> [--device "Family Room"]
  python3 cast.py stop [--device "Family Room"]
"""

import argparse
import re
import sys
import time

try:
    import pychromecast
    from pychromecast.controllers.youtube import YouTubeController
except ImportError:
    print("pychromecast not installed. Run: pip3 install pychromecast --break-system-packages")
    sys.exit(1)


DEFAULT_IP = "192.168.1.164"
DEFAULT_PORT = 8009
DEFAULT_NAME = "Family Room"


def extract_video_id(input_str: str) -> str:
    """Extract YouTube video ID from URL or return as-is if already an ID."""
    patterns = [
        r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})",
        r"^([A-Za-z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)
    return input_str


def get_cast(ip: str = DEFAULT_IP, name: str = DEFAULT_NAME) -> pychromecast.Chromecast:
    """Connect to a Cast device by IP."""
    cast = pychromecast.get_chromecast_from_host((ip, DEFAULT_PORT, None, name, None))
    cast.wait(timeout=10)
    return cast


def cmd_list(_args):
    """Discover all Cast devices on the local network."""
    print("Scanning for Cast devices (up to 10 seconds)...")
    chromecasts, browser = pychromecast.get_chromecasts(timeout=10)
    if not chromecasts:
        print("No Cast devices found.")
    for cc in chromecasts:
        print(f"  - {cc.name} | {cc.cast_type} | {cc.cast_info.host}:{cc.cast_info.port}")
    pychromecast.stop_discovery(browser)


def cmd_play(args):
    """Play a YouTube video."""
    video_id = extract_video_id(args.target)
    ip = args.ip or DEFAULT_IP
    name = args.device or DEFAULT_NAME

    print(f"Connecting to '{name}' ({ip})...")
    cast = get_cast(ip=ip, name=name)

    ytc = YouTubeController()
    cast.register_handler(ytc)
    cast.wait(timeout=5)

    print(f"Playing YouTube video: {video_id}")
    ytc.play_video(video_id)
    time.sleep(3)
    print(f"Done. App: {cast.app_display_name}")


def cmd_pause(args):
    ip = args.ip or DEFAULT_IP
    name = args.device or DEFAULT_NAME
    cast = get_cast(ip=ip, name=name)
    cast.media_controller.pause()
    print("Paused.")


def cmd_resume(args):
    ip = args.ip or DEFAULT_IP
    name = args.device or DEFAULT_NAME
    cast = get_cast(ip=ip, name=name)
    cast.media_controller.play()
    print("Resumed.")


def cmd_stop(args):
    ip = args.ip or DEFAULT_IP
    name = args.device or DEFAULT_NAME
    cast = get_cast(ip=ip, name=name)
    cast.quit_app()
    print("Stopped.")


def cmd_volume(args):
    ip = args.ip or DEFAULT_IP
    name = args.device or DEFAULT_NAME
    level = float(args.level)
    if not 0.0 <= level <= 1.0:
        print("Volume must be between 0.0 and 1.0")
        sys.exit(1)
    cast = get_cast(ip=ip, name=name)
    cast.set_volume(level)
    print(f"Volume set to {level:.0%}")


def main():
    parser = argparse.ArgumentParser(description="Control a Chromecast/Google Cast device.")
    parser.add_argument("--device", help="Device name (default: Family Room)")
    parser.add_argument("--ip", help="Device IP (default: 192.168.1.164)")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List Cast devices on the network")

    play_parser = subparsers.add_parser("play", help="Play a YouTube video")
    play_parser.add_argument("target", help="YouTube video ID or URL")

    subparsers.add_parser("pause", help="Pause playback")
    subparsers.add_parser("resume", help="Resume playback")
    subparsers.add_parser("stop", help="Stop and close app")

    vol_parser = subparsers.add_parser("volume", help="Set volume (0.0 to 1.0)")
    vol_parser.add_argument("level", help="Volume level (0.0 to 1.0)")

    args = parser.parse_args()

    commands = {
        "list": cmd_list,
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
