from __future__ import annotations

import hashlib
import json

import pytest

from config_manager.verification import (
    VerificationError,
    VerificationRegistry,
    backup_and_write,
    structural_fingerprint,
)


class _Response:
    def __init__(self, payload=None, content=b"", text=""):
        self.payload = payload
        self.content = content
        self.text = text

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_unknown_game_is_not_allowed_to_write(tmp_path):
    registry = VerificationRegistry("0.05.1", data_dir=tmp_path)
    registry.enable_test_writes()
    with pytest.raises(VerificationError, match="write_not_allowed:game_not_listed"):
        backup_and_write(
            "Unknown Game", "Steam", "1.0", [], {"vsync": "On"},
            lambda *_: [], registry,
        )


def test_verified_game_still_requires_test_write_consent(tmp_path):
    registry = VerificationRegistry("0.05.1", data_dir=tmp_path)
    fingerprint = structural_fingerprint([])
    registry.current_path.write_text(json.dumps({
        "format_version": 1,
        "manifest_version": "1.0.0",
        "minimum_client_version": "0.05.1",
        "games": [{
            "game": "Example", "platform": "Steam", "version": "1.0", "fingerprint": fingerprint,
            "status": "write_verified", "config_patterns": [], "supported_settings": [],
            "reader_id": "existing-parser", "writer_id": "existing-writer",
        }],
    }), encoding="utf-8")
    with pytest.raises(VerificationError, match="test_write_consent_required"):
        backup_and_write("Example", "Steam", "1.0", [], {"vsync": "On"}, lambda *_: [], registry)


def test_structural_fingerprint_ignores_setting_values():
    one = structural_fingerprint([{"expanded_path": "GameUserSettings.ini", "content": "VSync=True\n"}])
    two = structural_fingerprint([{"expanded_path": "GameUserSettings.ini", "content": "VSync=False\n"}])
    assert one == two


def test_release_update_installs_manifest_and_keeps_previous(tmp_path):
    manifest = {
        "format_version": 1,
        "manifest_version": "1.0.0",
        "minimum_client_version": "0.05.1",
        "games": [],
    }
    raw = json.dumps(manifest).encode("utf-8")
    checksum = hashlib.sha256(raw).hexdigest()
    responses = iter([
        _Response({"assets": [
            {"name": "verified-games.json", "browser_download_url": "manifest"},
            {"name": "verified-games.json.sha256", "browser_download_url": "checksum"},
        ]}),
        _Response(content=raw),
        _Response(text=checksum),
    ])
    registry = VerificationRegistry("0.05.1", data_dir=tmp_path, http_get=lambda *_args, **_kwargs: next(responses))

    assert registry.update()["updated"] is True
    assert registry.load()["manifest_version"] == "1.0.0"