"""Create privacy-aware diagnostic ZIP files for unverified game configs."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .anonymizer import anonymize_value
from .verification import content_hash

MAX_PACKAGE_BYTES = 10 * 1024 * 1024
MAX_FILE_BYTES = 512 * 1024


def collect_windows_hardware() -> Dict[str, Any]:
    """Collect the approved Windows diagnostic fields, never a device name."""
    data: Dict[str, Any] = {"os_version": platform.platform()}
    if platform.system() != "Windows":
        data["status"] = "unavailable"
        return data
    commands = {
        "cpu_model": "(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)",
        "memory": "Get-CimInstance Win32_PhysicalMemory | Select-Object Capacity,ConfiguredClockSpeed",
        "gpu": "Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion,CurrentHorizontalResolution,CurrentVerticalResolution",
    }
    for key, command in commands.items():
        try:
            output = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command + " | ConvertTo-Json -Compress"],
                capture_output=True, text=True, timeout=5, check=True,
            ).stdout.strip()
            data[key] = json.loads(output) if output else "unavailable"
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
            data[key] = "unavailable"
    data["hdr_status"] = "unavailable"
    return data


def build_preview(games: Iterable[Dict[str, Any]], include_content: bool) -> Dict[str, Any]:
    """Build a serializable preview before the user confirms an export."""
    selected_games = []
    total_bytes = 0
    for game in games:
        files = []
        for config_file in game.get("config_files", []):
            content = config_file.get("content")
            if not config_file.get("found") or not isinstance(content, str):
                continue
            size = len(content.encode("utf-8"))
            if size > MAX_FILE_BYTES:
                continue
            total_bytes += size if include_content else 0
            files.append({
                "path": anonymize_value(config_file.get("expanded_path", "")),
                "size_bytes": size,
                "included": include_content,
                "content_hash": content_hash(content),
                "preview": anonymize_value(content)[:1000] if include_content else None,
            })
        selected_games.append({
            "name": game.get("name", ""), "platform": game.get("platform", ""),
            "version": game.get("version", "unknown"), "files": files,
            "parsed_settings": game.get("parsed_settings", {}),
        })
    return {"games": selected_games, "content_included": include_content, "content_bytes": total_bytes}


def export_diagnostic_package(
    games: Iterable[Dict[str, Any]],
    output_dir: Path,
    include_content: bool = False,
    include_hardware: bool = True,
) -> Path:
    """Export an anonymous ZIP under the approved per-file and total limits."""
    games = list(games)
    preview = build_preview(games, include_content)
    if preview["content_bytes"] > MAX_PACKAGE_BYTES:
        raise ValueError("diagnostic_package_too_large")
    report_id = str(uuid.uuid4())
    manifest = {
        "format_version": 1,
        "report_id": report_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "privacy": {"anonymized": True, "device_name_collected": False},
        "games": preview["games"],
        "hardware": collect_windows_hardware() if include_hardware else {"included": False},
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"game-tuner-report-{report_id}.zip"
    with tempfile.NamedTemporaryFile(dir=output_dir, suffix=".zip", delete=False) as temp:
        temporary_path = Path(temp.name)
    try:
        with zipfile.ZipFile(temporary_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
            if include_content:
                for game_index, game in enumerate(games):
                    for file_index, config_file in enumerate(game.get("config_files", [])):
                        content = config_file.get("content")
                        if not config_file.get("found") or not isinstance(content, str):
                            continue
                        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
                            continue
                        archive.writestr(
                            f"configs/{game_index}-{file_index}.txt",
                            anonymize_value(content),
                        )
        if temporary_path.stat().st_size > MAX_PACKAGE_BYTES:
            raise ValueError("diagnostic_package_too_large")
        os.replace(temporary_path, output_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    history_path = output_dir.parent / "exports-manifest.json"
    try:
        history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else []
    except (OSError, json.JSONDecodeError):
        history = []
    history.append({
        "report_id": report_id, "created_at": manifest["created_at"],
        "game_count": len(manifest["games"]), "includes_content": include_content,
        "includes_hardware": include_hardware,
    })
    history_path.write_text(json.dumps(history[-20:], indent=2), encoding="utf-8")
    return output_path