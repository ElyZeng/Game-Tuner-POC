"""Read-only customer configuration collector.

Usage:
    python tools/collect_configs.py --game "F1 25" --output local_exports/f1.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config_manager import detect_config_files
from config_manager.config_exporter import _is_expanded_registry_path, _read_registry_key, _try_read_file
from config_manager.anonymizer import anonymize_package
from config_manager.settings_parser import extract_key_settings
from wiki_api import PCGamingWikiClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only anonymized game config collector")
    parser.add_argument("--game", required=True, help="Game title used by PCGamingWiki")
    parser.add_argument("--install-path", default="", help="Optional game installation path")
    parser.add_argument("--platform", default="unknown")
    parser.add_argument("--game-version", "--version", default="unknown", dest="game_version")
    parser.add_argument("--output", required=True, help="Local JSON output path")
    return parser


def collect(args: argparse.Namespace) -> dict:
    client = PCGamingWikiClient()
    wiki = client.get_config_info(args.game, install_path=args.install_path)
    paths = wiki.get("expanded_paths") or []
    found_paths = detect_config_files(paths)
    config_files = []
    for path in found_paths:
        if _is_expanded_registry_path(path):
            config_files.append(_read_registry_key(path))
        else:
            config_files.append(_try_read_file(path))
    readable = [entry for entry in config_files if entry.get("found") and entry.get("content")]
    package = {
        "collector_version": "1.0",
        "collection_time": datetime.now(timezone.utc).isoformat(),
        "game": args.game,
        "platform": args.platform,
        "game_version": args.game_version,
        "pcgamingwiki": wiki,
        "config_files": config_files,
        "parsed_settings": extract_key_settings(args.game, readable),
    }
    return anonymize_package(package)


def main() -> None:
    args = build_parser().parse_args()
    package = collect(args)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(package, handle, indent=2, ensure_ascii=False)
    print(json.dumps({"status": "ok", "output": os.path.abspath(args.output), "game": args.game}, ensure_ascii=False))


if __name__ == "__main__":
    main()