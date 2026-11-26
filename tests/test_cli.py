"""Tests for the command-line parser."""

from pathlib import Path

import pytest

from riftlens import __version__
from riftlens.cli import build_parser, run_probe


def test_probe_defaults() -> None:
    args = build_parser().parse_args(["probe"])
    assert args.handler is run_probe
    assert args.interval == 2.0
    assert args.save_every == 30.0
    assert args.out == Path("snapshots")
    assert args.cert is None
    assert args.once is False


def test_probe_options() -> None:
    args = build_parser().parse_args(
        ["probe", "--interval", "1", "--save-every", "10", "--once", "--out", "x"]
    )
    assert args.interval == 1.0
    assert args.save_every == 10.0
    assert args.once is True
    assert args.out == Path("x")


def test_command_is_required() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--version"])
    assert __version__ in capsys.readouterr().out
