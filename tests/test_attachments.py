from unittest.mock import MagicMock

import pytest

import attachments


def test_download_falls_back_to_gaia_when_the_api_has_no_file(monkeypatch, tmp_path):
    monkeypatch.setattr(attachments, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(attachments.requests, "get", lambda *a, **k: MagicMock(ok=False, status_code=404))
    monkeypatch.setattr(attachments, "get_hf_token", lambda: "hf_dummy")
    calls = []

    def fake_hf_download(repo, filename, **kwargs):
        calls.append(filename)
        return str(tmp_path / "from_gaia.txt")

    monkeypatch.setattr(attachments, "hf_hub_download", fake_hf_download)

    path = attachments.download_attachment("id", "file.txt")

    assert path.name == "from_gaia.txt"
    assert calls == ["2023/validation/file.txt"]


def test_download_error_explains_how_to_get_access(monkeypatch, tmp_path):
    monkeypatch.setattr(attachments, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(attachments.requests, "get", lambda *a, **k: MagicMock(ok=False, status_code=404))
    monkeypatch.setattr(attachments, "get_hf_token", lambda: "hf_dummy")

    def denied(*a, **k):
        raise PermissionError("gated")

    monkeypatch.setattr(attachments, "hf_hub_download", denied)

    with pytest.raises(FileNotFoundError, match="gated.*accept its terms"):
        attachments.download_attachment("id", "file.txt")
