#!/usr/bin/env python3
"""Create review candidates and signed-by-hash GitHub Release assets locally."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config_manager.verification import MANIFEST_FORMAT_VERSION, validate_manifest


def create_candidate(report_path: Path, output_path: Path) -> None:
    with zipfile.ZipFile(report_path) as archive:
        report = json.loads(archive.read("manifest.json"))
    candidate = {
        "status": "candidate",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "report_id": report["report_id"],
        "games": report["games"],
        "review_notes": "",
    }
    output_path.write_text(json.dumps(candidate, indent=2, ensure_ascii=False), encoding="utf-8")


def build_release(source_path: Path, output_dir: Path, version: str, client_version: str) -> None:
    rules = json.loads(source_path.read_text(encoding="utf-8"))
    manifest = {
        "format_version": MANIFEST_FORMAT_VERSION,
        "manifest_version": version,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "generator_version": "manage_verification.py",
        "minimum_client_version": client_version,
        "games": rules,
    }
    validate_manifest(manifest, client_version)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "verified-games.json"
    raw = json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")
    json_path.write_bytes(raw)
    (output_dir / "verified-games.json.sha256").write_text(
        hashlib.sha256(raw).hexdigest() + "  verified-games.json\n", encoding="ascii"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare verification candidates and Release assets")
    commands = parser.add_subparsers(dest="command", required=True)
    candidate = commands.add_parser("candidate")
    candidate.add_argument("report", type=Path)
    candidate.add_argument("--output", type=Path, required=True)
    release = commands.add_parser("build-release")
    release.add_argument("rules", type=Path, help="Human-reviewed array of verification rules")
    release.add_argument("--output-dir", type=Path, required=True)
    release.add_argument("--version", required=True)
    release.add_argument("--minimum-client-version", required=True)
    args = parser.parse_args()
    if args.command == "candidate":
        create_candidate(args.report, args.output)
    else:
        build_release(args.rules, args.output_dir, args.version, args.minimum_client_version)


if __name__ == "__main__":
    main()