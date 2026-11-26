"""Tests for the snapshot recorder state machine."""

import copy
import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from touchstaune.recorder import GameRecorder, RecorderState

FIXED_NOW = datetime(2026, 11, 26, 15, 0, 0)


class FakeSource:
    """Replays a scripted sequence of payloads (``None`` = API unreachable)."""

    def __init__(self, responses: Iterable[dict[str, Any] | None]) -> None:
        self._responses = iter(responses)
        self.endpoints: list[str] = []

    def fetch_raw(self, endpoint: str) -> dict[str, Any] | None:
        self.endpoints.append(endpoint)
        return next(self._responses)


def at_game_time(payload: dict[str, Any], game_time: float) -> dict[str, Any]:
    clone = copy.deepcopy(payload)
    clone["gameData"]["gameTime"] = game_time
    return clone


def make_recorder(source: FakeSource, out: Path, **kwargs: Any) -> GameRecorder:
    return GameRecorder(source, out, now=lambda: FIXED_NOW, **kwargs)


def test_waits_while_no_game(tmp_path: Path) -> None:
    recorder = make_recorder(FakeSource([None, None]), tmp_path)
    assert recorder.step().state is RecorderState.WAITING
    assert recorder.step().state is RecorderState.WAITING
    assert recorder.game_dir is None
    assert list(tmp_path.iterdir()) == []


def test_full_game_lifecycle(tmp_path: Path, raw_game: dict[str, Any]) -> None:
    source = FakeSource(
        [
            None,
            at_game_time(raw_game, 0.0),
            at_game_time(raw_game, 10.0),
            at_game_time(raw_game, 40.0),
            None,
            None,
        ]
    )
    recorder = make_recorder(source, tmp_path, save_every=30.0, end_after_misses=2)

    assert recorder.step().state is RecorderState.WAITING

    first = recorder.step()
    assert first.state is RecorderState.IN_GAME
    assert first.game_started is True
    assert first.data is not None
    assert first.saved is not None
    assert first.saved.name == "t00000.json"

    second = recorder.step()
    assert second.game_started is False
    assert second.saved is None  # only 10 s since the last snapshot

    third = recorder.step()
    assert third.saved is not None
    assert third.saved.name == "t00040.json"

    miss = recorder.step()
    assert miss.state is RecorderState.IN_GAME  # one miss is tolerated
    assert miss.data is None

    end = recorder.step()
    assert end.state is RecorderState.ENDED
    assert end.saved is not None
    assert end.saved.name == "final.json"
    assert recorder.game_dir is None

    game_dir = tmp_path / "game_20261126_150000"
    assert sorted(p.name for p in game_dir.iterdir()) == [
        "events.json",
        "final.json",
        "t00000.json",
        "t00040.json",
    ]
    final = json.loads((game_dir / "final.json").read_text(encoding="utf-8"))
    assert final["gameData"]["gameTime"] == 40.0
    events = json.loads((game_dir / "events.json").read_text(encoding="utf-8"))
    assert [e["EventName"] for e in events] == ["GameStart", "MinionsSpawning", "ChampionKill"]
    assert set(source.endpoints) == {"allgamedata"}


def test_successful_poll_resets_miss_counter(tmp_path: Path, raw_game: dict[str, Any]) -> None:
    source = FakeSource([raw_game, None, raw_game, None])
    recorder = make_recorder(source, tmp_path, end_after_misses=2)
    states = [recorder.step().state for _ in range(4)]
    assert RecorderState.ENDED not in states


def test_finalise_without_game_is_noop(tmp_path: Path) -> None:
    recorder = make_recorder(FakeSource([]), tmp_path)
    assert recorder.finalise() is None
    assert list(tmp_path.iterdir()) == []


def test_finalise_mid_game_writes_final_snapshot(tmp_path: Path, raw_game: dict[str, Any]) -> None:
    recorder = make_recorder(FakeSource([raw_game]), tmp_path)
    recorder.step()
    final = recorder.finalise()
    assert final is not None
    assert final.exists()
    assert recorder.game_dir is None


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"save_every": -1.0}, "save_every"),
        ({"end_after_misses": 0}, "end_after_misses"),
    ],
)
def test_rejects_invalid_settings(tmp_path: Path, kwargs: dict[str, Any], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        make_recorder(FakeSource([]), tmp_path, **kwargs)
