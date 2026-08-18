"""Anonymize exported game configuration packages for local sharing."""

from __future__ import annotations

import copy
import json
import os
import re
from typing import Any, Dict

_SENSITIVE_KEY = re.compile(
    r"(token|secret|password|passwd|authorization|auth|access.?key|api.?key|credential|account.?id|steam.?id)",
    re.IGNORECASE,
)
_SENSITIVE_LINE = re.compile(
    r"(^|[\s\"'=])(token|secret|password|passwd|authorization|auth|access.?key|api.?key|credential|account.?id|steam.?id)([\s\"'=])",
    re.IGNORECASE,
)


def _anonymize_path(value: str) -> str:
    """Replace local user names and Steam account IDs in a path."""
    result = value
    home = os.path.expanduser("~").replace("\\", "/")
    home_pattern = re.escape(home.rstrip("/"))
    result = re.sub(home_pattern, "%USERPROFILE%", result.replace("\\", "/"), flags=re.IGNORECASE)
    result = re.sub(r"(/userdata/)(\d+)(/)", r"\1<STEAM_USER_ID>\3", result, flags=re.IGNORECASE)
    result = re.sub(r"(\\userdata\\)(\d+)(\\)", r"\1<STEAM_USER_ID>\3", result, flags=re.IGNORECASE)
    result = re.sub(r"([\\/])Users([\\/])[^\\/]+", r"\1Users\2<USER>", result, flags=re.IGNORECASE)
    return result


def _anonymize_text(value: str) -> str:
    value = _anonymize_path(value)
    lines = []
    for line in value.splitlines():
        if _SENSITIVE_LINE.search(line):
            lines.append("<REDACTED_SENSITIVE_SETTING>")
        else:
            lines.append(line)
    return "\n".join(lines)


def anonymize_value(value: Any, key: str = "") -> Any:
    """Recursively anonymize JSON-compatible values."""
    if _SENSITIVE_KEY.search(key):
        return "<REDACTED>"
    if isinstance(value, dict):
        return {name: anonymize_value(item, name) for name, item in value.items()}
    if isinstance(value, list):
        return [anonymize_value(item, key) for item in value]
    if isinstance(value, str):
        return _anonymize_text(value)
    return copy.deepcopy(value)


def anonymize_package(package: Dict[str, Any]) -> Dict[str, Any]:
    """Return an anonymized copy of an exported package."""
    result = anonymize_value(package)
    result["privacy"] = {
        "anonymized": True,
        "removed": ["local user names", "Steam user IDs", "sensitive key/value lines"],
    }
    return result


def anonymize_file(input_path: str, output_path: str) -> None:
    with open(input_path, "r", encoding="utf-8") as handle:
        package = json.load(handle)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(anonymize_package(package), handle, indent=2, ensure_ascii=False)