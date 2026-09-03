"""Best-effort game version detection without customer-entered values."""

from __future__ import annotations

import os
import subprocess


def detect_game_version(install_path: str) -> str:
    """Read the first executable's Windows file version, or return ``unknown``."""
    if os.name != "nt" or not os.path.isdir(install_path):
        return "unknown"
    executables = []
    for root, _, files in os.walk(install_path):
        executables.extend(os.path.join(root, name) for name in files if name.lower().endswith(".exe"))
        if executables:
            break
    if not executables:
        return "unknown"
    command = "(Get-Item -LiteralPath $args[0]).VersionInfo.FileVersion"
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command, executables[0]],
            capture_output=True, text=True, timeout=5, check=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        ).stdout.strip()
        return result or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"