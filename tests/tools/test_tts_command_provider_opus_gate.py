"""A voice-compatible command/plugin provider must not be Opus-converted off Opus platforms.

``_finalize_voice_delivery`` used to force every ``voice_compatible`` command/plugin result
through ffmpeg into Ogg/Opus regardless of the session platform. iMessage (photon) and other
non-``OPUS_VOICE_PLATFORMS`` clients cannot decode an Opus voice bubble, so the opt-in turned a
perfectly playable AAC/MP3 note into an unplayable one — while the built-in-provider branch
right above already gates conversion on ``want_opus``.
"""

import json
from pathlib import Path

import pytest

from gateway.session_context import _UNSET, _VAR_MAP
from tools import tts_tool


def _reset_session_context() -> None:
    for var in _VAR_MAP.values():
        var.set(_UNSET)


@pytest.fixture(autouse=True)
def _clean_session_platform(monkeypatch):
    _reset_session_context()
    monkeypatch.delenv("HERMES_SESSION_PLATFORM", raising=False)
    yield
    _reset_session_context()


def _copy_command() -> str:
    return (
        "python3 -c \"import shutil,sys;open(sys.argv[2],'wb').write(b'fake audio')\" "
        "{input_path} {output_path}"
    )


def _config(output_format: str) -> dict:
    return {
        "provider": "local-cmd",
        "providers": {
            "local-cmd": {
                "type": "command",
                "command": _copy_command(),
                "output_format": output_format,
                "voice_compatible": True,
            },
        },
    }


def test_non_opus_platform_keeps_provider_container(tmp_path, monkeypatch):
    """photon/iMessage: keep the AAC the provider wrote, still flagged as a voice bubble."""
    monkeypatch.setenv("HERMES_SESSION_PLATFORM", "photon")
    monkeypatch.setattr(tts_tool, "_load_tts_config", lambda: _config("m4a"))
    monkeypatch.setattr(tts_tool, "_convert_to_opus",
                        lambda path: pytest.fail(f"converted {path} to Opus off an Opus platform"))

    result = json.loads(tts_tool.text_to_speech_tool(
        "hello", output_path=str(tmp_path / "clip.m4a")))

    assert result["success"] is True, result
    assert result["file_path"].endswith(".m4a")
    assert result["voice_compatible"] is True
    assert result["media_tag"].startswith("[[audio_as_voice]]")


def test_opus_platform_still_converts(tmp_path, monkeypatch):
    """Telegram & co. still require real Ogg/Opus for a native voice bubble."""
    converted = []

    def fake_convert(path: str) -> str:
        opus = Path(path).with_suffix(".ogg")
        opus.write_bytes(b"ogg")
        converted.append(path)
        return str(opus)

    monkeypatch.setenv("HERMES_SESSION_PLATFORM", "telegram")
    monkeypatch.setattr(tts_tool, "_load_tts_config", lambda: _config("m4a"))
    monkeypatch.setattr(tts_tool, "_convert_to_opus", fake_convert)

    result = json.loads(tts_tool.text_to_speech_tool(
        "hello", output_path=str(tmp_path / "clip.m4a")))

    assert result["success"] is True, result
    assert converted, "Opus platform did not convert the provider's output"
    assert result["file_path"].endswith(".ogg")
    assert result["voice_compatible"] is True


def test_opt_out_provider_is_still_a_document(tmp_path, monkeypatch):
    cfg = _config("m4a")
    cfg["providers"]["local-cmd"]["voice_compatible"] = False
    monkeypatch.setenv("HERMES_SESSION_PLATFORM", "photon")
    monkeypatch.setattr(tts_tool, "_load_tts_config", lambda: cfg)

    result = json.loads(tts_tool.text_to_speech_tool(
        "hello", output_path=str(tmp_path / "clip.m4a")))

    assert result["voice_compatible"] is False
    assert not result["media_tag"].startswith("[[audio_as_voice]]")
    assert Path(result["file_path"]).exists()
