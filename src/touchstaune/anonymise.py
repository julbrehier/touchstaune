"""Anonymise recorded Live Client snapshots before they are shared or committed.

Every player identifier (Riot ID, game name, tag line, legacy summoner name) is replaced by
a stable placeholder (``Player1#ANON``, ``Player2#ANON``, ...) everywhere it appears in the
payload as a whole string value, including inside game events (``KillerName``,
``VictimName``, ``Assisters``...). Players are numbered in scoreboard order, so the same
player always gets the same placeholder within one snapshot.

Limitation: identifiers embedded *inside* longer strings are not detected. The Live Client
API does not currently produce any.
"""

import json
from pathlib import Path
from typing import Any

PLACEHOLDER_TAG = "ANON"
_IDENTITY_KEYS = ("riotId", "riotIdGameName", "summonerName")
_TAG_LINE_KEY = "riotIdTagLine"


def _player_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """All objects describing a player: scoreboard entries first, then the active player."""
    entries = [p for p in payload.get("allPlayers", []) if isinstance(p, dict)]
    active = payload.get("activePlayer")
    if isinstance(active, dict):
        entries.append(active)
    return entries


def _game_name(entry: dict[str, Any]) -> str:
    """The game name (part before ``#``) of a player entry, or ``""`` if it has none."""
    name = entry.get("riotIdGameName")
    if isinstance(name, str) and name:
        return name
    for key in ("riotId", "summonerName"):
        value = entry.get(key)
        if isinstance(value, str) and value:
            return value.split("#", 1)[0]
    return ""


def build_alias_map(payload: dict[str, Any]) -> dict[str, str]:
    """Map every player identifier found in ``payload`` to its placeholder."""
    aliases: dict[str, str] = {}
    next_index = 1
    for entry in _player_entries(payload):
        game_name = _game_name(entry)
        if not game_name:
            continue
        alias = aliases.get(game_name)
        if alias is None:  # first time we see this player
            alias = f"Player{next_index}"
            next_index += 1
            aliases[game_name] = alias
        for key in _IDENTITY_KEYS:
            value = entry.get(key)
            if isinstance(value, str) and value:
                aliases[value] = f"{alias}#{PLACEHOLDER_TAG}" if "#" in value else alias
    return aliases


def _replace(node: Any, aliases: dict[str, str]) -> Any:
    if isinstance(node, dict):
        return {
            key: PLACEHOLDER_TAG if key == _TAG_LINE_KEY else _replace(value, aliases)
            for key, value in node.items()
        }
    if isinstance(node, list):
        return [_replace(item, aliases) for item in node]
    if isinstance(node, str):
        return aliases.get(node, node)
    return node


def anonymise_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """Return an anonymised deep copy of an ``/allgamedata`` payload."""
    result: dict[str, Any] = _replace(payload, build_alias_map(payload))
    return result


def anonymise_file(source: Path, destination: Path) -> int:
    """Anonymise the snapshot at ``source`` into ``destination``.

    Returns:
        The number of distinct players that were anonymised.

    Raises:
        ValueError: If ``source`` does not contain a JSON object.
    """
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{source} does not contain a JSON object")
    aliases = build_alias_map(payload)
    anonymised = _replace(payload, aliases)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(anonymised, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",  # LF on every OS (the project standard), never CRLF
    )
    return len({alias.split("#", 1)[0] for alias in aliases.values()})
