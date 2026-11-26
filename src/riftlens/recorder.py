"""Record a game's Live Client snapshots to disk as replayable JSON fixtures.

:class:`GameRecorder` is a small state machine driven by :meth:`GameRecorder.step`, one poll
per call and no sleeping, so the polling cadence lives in the caller (the CLI) and the
recorder can be tested deterministically.

States::

    WAITING ──(API answers)──▶ IN_GAME ──(N consecutive misses)──▶ ENDED ──▶ WAITING
"""

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from riftlens.live_client import AllGameData, parse_all_game_data

logger = logging.getLogger(__name__)


class GameSource(Protocol):
    """Anything that can fetch raw Live Client payloads (``LiveClient`` or a test fake)."""

    def fetch_raw(self, endpoint: str) -> dict[str, Any] | None:
        """Return the endpoint's JSON object, or ``None`` if no game is available."""
        ...


class RecorderState(StrEnum):
    """Lifecycle state reported after each poll."""

    WAITING = "waiting"
    IN_GAME = "in_game"
    ENDED = "ended"


@dataclass(frozen=True, slots=True)
class StepResult:
    """Outcome of a single :meth:`GameRecorder.step`."""

    state: RecorderState
    data: AllGameData | None = None
    saved: Path | None = None
    game_started: bool = False


class GameRecorder:
    """Poll a :class:`GameSource` and persist snapshots for each game.

    Args:
        source: Where payloads come from.
        out_root: Directory under which one ``game_YYYYmmdd_HHMMSS`` folder is created per game.
        save_every: Minimum in-game seconds between two saved snapshots.
        end_after_misses: Consecutive failed polls after which the game is considered over.
        now: Clock used to name game folders (injectable for tests).
    """

    def __init__(
        self,
        source: GameSource,
        out_root: Path,
        *,
        save_every: float = 30.0,
        end_after_misses: int = 5,
        now: Callable[[], datetime] = datetime.now,
    ) -> None:
        if save_every < 0:
            raise ValueError("save_every must be non-negative")
        if end_after_misses < 1:
            raise ValueError("end_after_misses must be at least 1")
        self._source = source
        self._out_root = out_root
        self._save_every = save_every
        self._end_after_misses = end_after_misses
        self._now = now
        self._reset()

    @property
    def game_dir(self) -> Path | None:
        """Folder of the game currently being recorded, or ``None`` when waiting."""
        return self._game_dir

    def step(self) -> StepResult:
        """Poll once, update state, and save a snapshot if one is due."""
        payload = self._source.fetch_raw("allgamedata")
        if payload is None:
            return self._on_miss()

        data = parse_all_game_data(payload)
        started = self._game_dir is None
        if started:
            self._game_dir = self._out_root / self._now().strftime("game_%Y%m%d_%H%M%S")
            self._game_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Game detected; recording to %s", self._game_dir)

        self._misses = 0
        self._last_payload = payload

        saved = None
        game_time = data.game_data.game_time
        if game_time - self._last_saved_game_time >= self._save_every:
            saved = self._write_snapshot(payload, f"t{int(game_time):05d}")
            self._last_saved_game_time = game_time

        return StepResult(RecorderState.IN_GAME, data=data, saved=saved, game_started=started)

    def finalise(self) -> Path | None:
        """Write the final snapshot and event log, then reset for the next game.

        Safe to call at any time (e.g. on Ctrl+C); returns ``None`` if nothing was recorded.
        """
        final = None
        if self._game_dir is not None and self._last_payload is not None:
            final = self._write_snapshot(self._last_payload, "final")
            events = self._last_payload.get("events", {}).get("Events", [])
            self._write_json(self._game_dir / "events.json", events)
            logger.info("Saved final snapshot and %d events to %s", len(events), self._game_dir)
        self._reset()
        return final

    # ------------------------------------------------------------------ internals

    def _on_miss(self) -> StepResult:
        if self._game_dir is None:
            return StepResult(RecorderState.WAITING)
        self._misses += 1
        if self._misses < self._end_after_misses:
            return StepResult(RecorderState.IN_GAME)
        return StepResult(RecorderState.ENDED, saved=self.finalise())

    def _reset(self) -> None:
        self._game_dir: Path | None = None
        self._last_payload: dict[str, Any] | None = None
        self._last_saved_game_time = float("-inf")
        self._misses = 0

    def _write_snapshot(self, payload: dict[str, Any], label: str) -> Path:
        assert self._game_dir is not None  # guaranteed by callers
        path = self._game_dir / f"{label}.json"
        self._write_json(path, payload)
        return path

    @staticmethod
    def _write_json(path: Path, obj: Any) -> None:
        path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
