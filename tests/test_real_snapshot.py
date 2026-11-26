"""Tests pinning down conventions observed in a real (anonymised) Live Client snapshot.

These document how the real API behaves, as opposed to what the documentation implies.
If Riot changes a convention, these tests are the ones that should fail.
"""

from typing import Any

import pytest

from touchstaune.live_client import AllGameData


@pytest.fixture
def game(real_practice_game: dict[str, Any]) -> AllGameData:
    return AllGameData.model_validate(real_practice_game)


def test_real_snapshot_parses(game: AllGameData) -> None:
    assert game.game_data.game_mode == "PRACTICETOOL"
    me = game.me()
    assert me is not None
    assert me.champion_name == "Quinn"
    assert len(me.equipment) == 6


def test_fixture_is_anonymised(real_practice_game: dict[str, Any]) -> None:
    game = AllGameData.model_validate(real_practice_game)
    for player in game.all_players:
        assert player.riot_id is not None
        assert player.riot_id.endswith("#ANON")
    assert real_practice_game["activePlayer"]["riotIdTagLine"] == "ANON"


def test_item_price_is_recipe_cost_not_total_cost(game: AllGameData) -> None:
    me = game.me()
    assert me is not None
    prices = {item.display_name: item.price for item in me.items}
    # Infinity Edge costs far more than 725 in total: `price` is the combine cost only.
    assert prices["Infinity Edge"] == 725
    assert prices["Bloodthirster"] == 325


def test_percent_penetration_is_a_remaining_resistance_multiplier(game: AllGameData) -> None:
    assert game.active_player is not None
    stats = game.active_player.champion_stats
    assert stats is not None
    # Lord Dominik's Regards: 0.65 in the API means 35 % armour penetration.
    assert stats.armor_penetration_percent == pytest.approx(0.65)
    assert stats.armor_penetration_fraction == pytest.approx(0.35)
    assert stats.magic_penetration_fraction == pytest.approx(0.0)


def test_mixed_units_for_crit(game: AllGameData) -> None:
    assert game.active_player is not None
    stats = game.active_player.champion_stats
    assert stats is not None
    assert stats.crit_chance == pytest.approx(1.0)  # fraction: 100 %
    assert stats.crit_damage == pytest.approx(230.0)  # percentage: 230 %
    assert stats.resource_type == "MANA"
