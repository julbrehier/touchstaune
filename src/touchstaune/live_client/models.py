"""Typed models for Live Client Data API payloads.

Riot adds fields to this API without notice. Every model therefore ignores unknown keys
and declares only the fields the project uses. Attribute names follow Python conventions;
aliases map them to Riot's camelCase JSON keys. Models are frozen: a parsed snapshot is an
immutable record of the game at one instant.

Reference: https://developer.riotgames.com/docs/lol#game-client-api
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _RiotModel(BaseModel):
    """Base model: camelCase aliases, unknown fields ignored, immutable."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
        frozen=True,
    )


class Team(StrEnum):
    """Map side. ORDER is blue side, CHAOS is red side."""

    ORDER = "ORDER"
    CHAOS = "CHAOS"
    NEUTRAL = "NEUTRAL"


class GameData(_RiotModel):
    """Match-level metadata."""

    game_mode: str
    game_time: float
    map_name: str = ""
    map_number: int = 0
    map_terrain: str = "Default"


class Item(_RiotModel):
    """An item in a player's inventory, as shown on the scoreboard.

    Warning: ``price`` is the item's **recipe (combine) cost**, not its total cost
    (e.g. Infinity Edge reports 725). Total gold cost must come from Data Dragon.
    """

    item_id: int = Field(alias="itemID")
    display_name: str
    slot: int
    count: int = 1
    price: int = 0
    consumable: bool = False
    can_use: bool = False


class Scores(_RiotModel):
    """Scoreboard numbers for one player."""

    kills: int = 0
    deaths: int = 0
    assists: int = 0
    creep_score: int = 0
    ward_score: float = 0.0

    @property
    def kda_string(self) -> str:
        """Scoreboard-style ``K/D/A`` string."""
        return f"{self.kills}/{self.deaths}/{self.assists}"


class _Identified(_RiotModel):
    """Fields shared by everything that identifies a player.

    ``riot_id`` (``GameName#TAG``) is the authoritative identifier since Riot's 2023
    migration away from summoner names; ``summoner_name`` is kept as a fallback.
    """

    riot_id: str | None = None
    riot_id_game_name: str | None = None
    riot_id_tag_line: str | None = None
    summoner_name: str | None = None

    @property
    def identities(self) -> frozenset[str]:
        """Every non-empty identifier this player is known by."""
        candidates = (self.riot_id, self.riot_id_game_name, self.summoner_name)
        return frozenset(c for c in candidates if c)

    @property
    def display_id(self) -> str:
        """Best human-readable identifier."""
        return self.riot_id or self.summoner_name or self.riot_id_game_name or "?"


class Player(_Identified):
    """One of the (usually ten) players in ``allPlayers``."""

    champion_name: str
    team: Team
    level: int = 1
    position: str = ""
    is_bot: bool = False
    is_dead: bool = False
    respawn_timer: float = 0.0
    items: tuple[Item, ...] = ()
    scores: Scores = Field(default_factory=Scores)

    @property
    def equipment(self) -> tuple[Item, ...]:
        """Non-consumable items (what a build is made of)."""
        return tuple(item for item in self.items if not item.consumable)


class ChampionStats(_RiotModel):
    """Live stats of the active player's champion (the in-game "C" panel).

    Values are **totals** (base + level growth + items + runes + buffs), including temporary
    effects such as Ghost's movement speed. Units are not uniform across fields; the
    conventions below were observed on real snapshots (see tests/test_real_snapshot.py):

    - ``crit_chance``, ``life_steal``, ``omnivamp``, ``physical_vamp``, ``spell_vamp``,
      ``heal_shield_power``: fractions (``1.0`` = 100 %).
    - ``crit_damage``: a percentage (``230.0`` = 230 % of attack damage).
    - ``*_penetration_percent``: a **multiplier on the target's remaining resistance**
      (``1.0`` = no penetration, ``0.65`` = 35 % penetration). Use the ``*_fraction``
      properties for the penetration itself.
    - ``ability_haste``, ``tenacity``: plain points / percentage points.
    """

    ability_haste: float = 0.0
    ability_power: float = 0.0
    armor: float = 0.0
    armor_penetration_flat: float = 0.0
    armor_penetration_percent: float = 1.0
    attack_damage: float = 0.0
    attack_range: float = 0.0
    attack_speed: float = 0.0
    bonus_armor_penetration_percent: float = 1.0
    bonus_magic_penetration_percent: float = 1.0
    crit_chance: float = 0.0
    crit_damage: float = 0.0
    current_health: float = 0.0
    heal_shield_power: float = 0.0
    health_regen_rate: float = 0.0
    life_steal: float = 0.0
    magic_lethality: float = 0.0
    magic_penetration_flat: float = 0.0
    magic_penetration_percent: float = 1.0
    magic_resist: float = 0.0
    max_health: float = 0.0
    move_speed: float = 0.0
    omnivamp: float = 0.0
    physical_lethality: float = 0.0
    physical_vamp: float = 0.0
    resource_max: float = 0.0
    resource_regen_rate: float = 0.0
    resource_type: str = ""
    resource_value: float = 0.0
    spell_vamp: float = 0.0
    tenacity: float = 0.0

    @property
    def armor_penetration_fraction(self) -> float:
        """Percent armour penetration as a fraction (``0.35`` = 35 %)."""
        return 1.0 - self.armor_penetration_percent

    @property
    def magic_penetration_fraction(self) -> float:
        """Percent magic penetration as a fraction (``0.35`` = 35 %)."""
        return 1.0 - self.magic_penetration_percent


class ActivePlayer(_Identified):
    """The player running this client.

    In spectator mode the API returns an error object here; every field therefore
    has a default so that payload still parses, with no identities.
    """

    level: int = 1
    current_gold: float = 0.0
    champion_stats: ChampionStats | None = None


class GameEvent(BaseModel):
    """A game event such as ``GameStart`` or ``ChampionKill``.

    Event payloads vary by type (``KillerName``, ``VictimName``...); fields other than
    the three common ones are kept and are available through ``model_extra``.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow", frozen=True)

    event_id: int = Field(alias="EventID")
    event_name: str = Field(alias="EventName")
    event_time: float = Field(alias="EventTime")


class EventLog(BaseModel):
    """Wrapper matching the API's ``{"Events": [...]}`` shape."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore", frozen=True)

    events: tuple[GameEvent, ...] = Field(default=(), alias="Events")


class AllGameData(_RiotModel):
    """Full payload of the ``/allgamedata`` endpoint."""

    game_data: GameData
    active_player: ActivePlayer | None = None
    all_players: tuple[Player, ...] = ()
    events: EventLog = Field(default_factory=EventLog)

    def me(self) -> Player | None:
        """The active player's entry in ``all_players``, if it can be matched."""
        if self.active_player is None:
            return None
        if self.active_player.riot_id:
            for player in self.all_players:
                if player.riot_id == self.active_player.riot_id:
                    return player
        identities = self.active_player.identities
        if not identities:
            return None
        return next((p for p in self.all_players if p.identities & identities), None)

    def my_team(self) -> Team | None:
        """The active player's team, or ``None`` (e.g. when spectating)."""
        me = self.me()
        return me.team if me else None

    def allies(self) -> tuple[Player, ...]:
        """Players on the active player's team (including the active player)."""
        team = self.my_team()
        return tuple(p for p in self.all_players if team is not None and p.team == team)

    def enemies(self) -> tuple[Player, ...]:
        """Players not on the active player's team."""
        team = self.my_team()
        return tuple(p for p in self.all_players if team is not None and p.team != team)
