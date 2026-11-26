"""Tests for snapshot anonymisation."""

import json
from pathlib import Path
from typing import Any

import pytest

from touchstaune.anonymise import anonymise_file, anonymise_snapshot, build_alias_map
from touchstaune.cli import main
from touchstaune.live_client import AllGameData

ORIGINAL_NAMES = ("Tester", "AllyOne", "EnemyOne", "EnemyTwo")


def test_alias_map_numbers_players_in_scoreboard_order(raw_game: dict[str, Any]) -> None:
    aliases = build_alias_map(raw_game)
    assert aliases["Tester#EUW"] == "Player1#ANON"
    assert aliases["Tester"] == "Player1"
    assert aliases["AllyOne#EUW"] == "Player2#ANON"
    assert aliases["EnemyTwo"] == "Player4"


def test_no_original_identifier_survives(raw_game: dict[str, Any]) -> None:
    dumped = json.dumps(anonymise_snapshot(raw_game))
    for name in ORIGINAL_NAMES:
        assert name not in dumped


def test_identifiers_in_events_are_replaced_consistently(raw_game: dict[str, Any]) -> None:
    kill = anonymise_snapshot(raw_game)["events"]["Events"][2]
    assert kill["KillerName"] == "Player1"
    assert kill["VictimName"] == "Player3"
    assert kill["Assisters"] == ["Player2"]


def test_other_strings_are_untouched(raw_game: dict[str, Any]) -> None:
    result = anonymise_snapshot(raw_game)
    assert result["allPlayers"][0]["championName"] == "Garen"
    assert result["allPlayers"][0]["items"][0]["displayName"] == "Doran's Blade"
    assert result["gameData"] == raw_game["gameData"]


def test_tag_line_is_replaced(raw_game: dict[str, Any]) -> None:
    raw_game["activePlayer"]["riotIdTagLine"] = "EUW"
    assert anonymise_snapshot(raw_game)["activePlayer"]["riotIdTagLine"] == "ANON"


def test_original_payload_is_not_modified(raw_game: dict[str, Any]) -> None:
    anonymise_snapshot(raw_game)
    assert raw_game["activePlayer"]["riotId"] == "Tester#EUW"


def test_anonymised_payload_still_identifies_active_player(raw_game: dict[str, Any]) -> None:
    game = AllGameData.model_validate(anonymise_snapshot(raw_game))
    me = game.me()
    assert me is not None
    assert me.champion_name == "Garen"
    assert me.display_id == "Player1#ANON"


def test_anonymise_file_round_trip(tmp_path: Path, raw_game: dict[str, Any]) -> None:
    source = tmp_path / "in.json"
    source.write_text(json.dumps(raw_game), encoding="utf-8")
    destination = tmp_path / "out" / "anon.json"

    assert anonymise_file(source, destination) == 4
    text = destination.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert b"\r\n" not in destination.read_bytes()  # LF line endings, even on Windows
    assert "Tester" not in text


def test_anonymise_file_rejects_non_object(tmp_path: Path) -> None:
    source = tmp_path / "list.json"
    source.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        anonymise_file(source, tmp_path / "out.json")


def test_cli_refuses_to_overwrite_source(tmp_path: Path, raw_game: dict[str, Any]) -> None:
    source = tmp_path / "snap.json"
    source.write_text(json.dumps(raw_game), encoding="utf-8")
    assert main(["anonymise", str(source), str(source)]) == 2
    assert "Tester" in source.read_text(encoding="utf-8")  # untouched
