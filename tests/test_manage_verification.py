from __future__ import annotations

import hashlib
import json

from tools.manage_verification import build_release


def test_build_release_writes_matching_checksum(tmp_path):
    rules = tmp_path / "rules.json"
    rules.write_text(json.dumps([{
        "game": "Example", "platform": "Steam", "version": "1.0", "fingerprint": "abc",
        "status": "read_verified", "config_patterns": [], "supported_settings": [],
        "reader_id": "existing-parser", "writer_id": None,
    }]), encoding="utf-8")
    build_release(rules, tmp_path / "release", "1.0.0", "0.05.1")
    payload = (tmp_path / "release" / "verified-games.json").read_bytes()
    checksum = (tmp_path / "release" / "verified-games.json.sha256").read_text().split()[0]
    assert checksum == hashlib.sha256(payload).hexdigest()