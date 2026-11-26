"""Tests for the Live Client Data API models."""

from typing import Any

import pytest
from pydantic import ValidationError

from riftlens.live_client import AllGameData, Team


@pytest.fixture
def game(raw_game: dict[str, Any]) -> AllGameData:
    return AllGameData.model_validate(raw_game)


def test_parses_game_metadata(game: AllGameData) -> None:
    assert game.game_data.game_mode == "CLASSIC"
    assert game.game_data.game_time == pytest.approx(425.7)
    assert game.game_data.map_number == 11


def test_parses_all_players(game: AllGameData) -> None:
    assert [p.champion_name for p in game.all_players] == ["Garen", "Lux", "Darius", "Ahri"]


def test_item_alias_and_consumables(game: AllGameData) -> None:
    garen = game.all_players[0]
    assert garen.items[0].item_id == 1055
    assert garen.items[1].consumable is True
    assert [i.display_name for i in garen.equipment] == ["Doran's Blade", "Stealth Ward"]


def test_scores(game: AllGameData) -> None:
    garen = game.all_players[0]
    assert garen.scores.creep_score == 64
    assert garen.scores.kda_string == "2/1/3"


def test_identifies_active_player_and_teams(game: AllGameData) -> None:
    me = game.me()
    assert me is not None
    assert me.champion_name == "Garen"
    assert game.my_team() is Team.ORDER
    assert [p.champion_name for p in game.allies()] == ["Garen", "Lux"]
    assert [p.champion_name for p in game.enemies()] == ["Darius", "Ahri"]


def test_active_player_stats(game: AllGameData) -> None:
    assert game.active_player is not None
    stats = game.active_player.champion_stats
    assert stats is not None
    assert stats.attack_damage == pytest.approx(98.0)
    assert stats.max_health == pytest.approx(1020.0)


def test_unknown_fields_are_ignored(raw_game: dict[str, Any]) -> None:
    raw_game["brandNewTopLevelField"] = {"anything": True}
    raw_game["allPlayers"][0]["brandNewPlayerField"] = 42
    game = AllGameData.model_validate(raw_game)
    assert game.all_players[0].model_extra is None  # extra="ignore": nothing retained


def test_events_keep_type_specific_fields(game: AllGameData) -> None:
    events = game.events.events
    assert [e.event_name for e in events] == ["GameStart", "MinionsSpawning", "ChampionKill"]
    kill = events[2]
    assert kill.model_extra is not None
    assert kill.model_extra["KillerName"] == "Tester"


def test_falls_back_to_game_name_when_riot_id_missing(raw_game: dict[str, Any]) -> None:
    del raw_game["activePlayer"]["riotId"]
    del raw_game["activePlayer"]["summonerName"]
    game = AllGameData.model_validate(raw_game)
    me = game.me()
    assert me is not None
    assert me.champion_name == "Garen"


def test_spectator_payload_has_no_team(raw_game: dict[str, Any]) -> None:
    # When spectating, the API returns an error object instead of the active player.
    raw_game["activePlayer"] = {"error": "Spectator mode doesn't currently support this feature"}
    game = AllGameData.model_validate(raw_game)
    assert game.me() is None
    assert game.my_team() is None
    assert game.allies() == ()
    assert game.enemies() == ()


def test_models_are_immutable(game: AllGameData) -> None:
    with pytest.raises(ValidationError):
        game.game_data.game_time = 0.0  # type: ignore[misc]


def test_missing_game_data_is_rejected(raw_game: dict[str, Any]) -> None:
    del raw_game["gameData"]
    with pytest.raises(ValidationError):
        AllGameData.model_validate(raw_game)
