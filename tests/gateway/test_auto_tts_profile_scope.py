"""Base-adapter auto-TTS must synthesize under the ROUTED profile's config.

The post-handler auto-TTS block in ``_process_message_background`` runs AFTER the runner's
message handler returned, and that handler is where ``_profile_runtime_scope`` is installed
for a multiplexed turn. Without re-entering the routed scope the TTS tool loads the DEFAULT
profile's ``tts`` section, so a routed profile's own provider/voice silently never applies.
"""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from gateway.config import Platform
from gateway.platforms.base import BasePlatformAdapter
from gateway.session import SessionSource


def _fake_adapter(runner):
    """Minimal stand-in carrying the real methods under test (BasePlatformAdapter is abstract)."""
    adapter = SimpleNamespace(
        name="telegram",
        platform=Platform.TELEGRAM,
        gateway_runner=runner,
        prepare_tts_text=lambda text: text,
    )
    adapter._auto_tts_profile_scope = lambda source: (
        BasePlatformAdapter._auto_tts_profile_scope(adapter, source))
    return adapter


def _recording_tts(seen):
    def fake_tts(*, text, output_path):
        from hermes_constants import get_hermes_home
        seen.append(str(get_hermes_home()))
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"audio")
        return json.dumps({"success": True, "file_path": output_path})
    return fake_tts


@pytest.mark.asyncio
async def test_auto_tts_synthesizes_under_routed_profile_home(tmp_path, monkeypatch):
    profile_home = tmp_path / "profiles" / "kid"
    profile_home.mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))

    source = SessionSource(platform=Platform.TELEGRAM, chat_id="chat-1", profile="kid")
    runner = SimpleNamespace(
        config=SimpleNamespace(multiplex_profiles=True),
        _resolve_profile_home_for_source=lambda _source: profile_home,
    )
    seen = []

    with patch("tools.tts_tool.text_to_speech_tool", side_effect=_recording_tts(seen)), \
            patch("tools.tts_tool.check_tts_requirements", return_value=True):
        paths, _requested = await BasePlatformAdapter._synthesize_auto_tts(
            _fake_adapter(runner), "boof boof", source)

    assert paths, "auto-TTS produced no audio"
    assert seen == [str(profile_home)], (
        f"auto-TTS synthesized under {seen} instead of the routed profile home {profile_home}")


@pytest.mark.asyncio
async def test_auto_tts_without_multiplex_stays_in_ambient_scope(tmp_path, monkeypatch):
    """Single-profile gateways must not acquire a profile override they never had."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    source = SessionSource(platform=Platform.TELEGRAM, chat_id="chat-1")
    runner = SimpleNamespace(
        config=SimpleNamespace(multiplex_profiles=False),
        _resolve_profile_home_for_source=lambda _source: tmp_path / "never",
    )
    seen = []

    with patch("tools.tts_tool.text_to_speech_tool", side_effect=_recording_tts(seen)), \
            patch("tools.tts_tool.check_tts_requirements", return_value=True):
        await BasePlatformAdapter._synthesize_auto_tts(_fake_adapter(runner), "boof boof", source)

    assert seen == [str(tmp_path)]
