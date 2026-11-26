"""Tests for pure text rendering."""

from typing import Any

import pytest

from riftlens.live_client import AllGameData
from riftlens.render import format_clock, format_scoreboard


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(0, "00:00"), (59.9, "00:59"), (75, "01:15"), (3725, "62:05"), (-3, "00:00")],
)
def test_format_clock(seconds: float, expected: str) -> None:
    assert format_clock(seconds) == expected


def test_scoreboard_lists_allies_before_enemies(raw_game: dict[str, Any]) -> None:
    text = format_scoreboard(AllGameData.model_validate(raw_game))
    rows = [line for line in text.splitlines() if "ALLY" in line or "ENEMY" in line]
    assert [row.split()[0] for row in rows] == ["ALLY", "ALLY", "ENEMY", "ENEMY"]
    assert "Garen" in rows[0]
    assert "2/1/3" in rows[0]
    assert "(dead)" in rows[1]  # Lux is dead in the fixture


def test_scoreboard_header_and_own_stats(raw_game: dict[str, Any]) -> None:
    text = format_scoreboard(AllGameData.model_validate(raw_game))
    assert "CLASSIC | 07:05 | Tester#EUW" in text
    assert "AD 98" in text
    assert "HP 812/1020" in text


def test_scoreboard_when_spectating_uses_map_sides(raw_game: dict[str, Any]) -> None:
    raw_game["activePlayer"] = {"error": "spectator"}
    text = format_scoreboard(AllGameData.model_validate(raw_game))
    assert "ALLY" not in text
    assert "ORDER" in text
    assert "CHAOS" in text
    assert "AD " not in text
