"""Shared pytest fixtures."""

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict[str, Any]:
    """Load a JSON fixture from ``tests/fixtures``."""
    data: dict[str, Any] = json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))
    return data


@pytest.fixture
def raw_game() -> dict[str, Any]:
    """A fresh copy of the synthetic ``/allgamedata`` payload."""
    return load_fixture("allgamedata_synthetic.json")
