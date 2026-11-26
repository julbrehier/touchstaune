# RiftLens

[![CI](https://github.com/julbrehier/riftlens/actions/workflows/ci.yml/badge.svg)](https://github.com/julbrehier/riftlens/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A League of Legends overlay, in the spirit of Porofessor, designed from day one to be
**compliant with Riot's developer and third-party application policies**:

- **Official data only.** The Live Client Data API, the Riot Web API and Data Dragon.
  No memory reading, no injection and no process hooks.
- **Only what the player could already know.** No enemy cooldown tracking, no
  power-spike alerts, and no de-anonymising of champion select.
- **Supports decisions without making them.** It highlights options and never
  automates a choice.

The rules each feature must follow are in [COMPLIANCE.md](COMPLIANCE.md). The design is in
[docs/architecture.md](docs/architecture.md).

> **Status:** pre-alpha. Phase 1 (live data ingestion and recording) is in progress.

## Roadmap

| Phase | Scope | Status |
|------:|-------|--------|
| 1 | Live Client Data API client, typed models, snapshot recorder, `riftlens probe` CLI | ✅ in progress |
| 2 | Transparent, click-through overlay window (PySide6) showing the player's own stats | ⏳ |
| 3 | Static data layer (Data Dragon): item costs, stats, item value model | ⏳ |
| 4 | League Client (LCU) connector: game phase detection, own-team draft view | ⏳ |
| 5 | Loading-screen scouting via the Riot Web API (rank, mastery, recent form) | ⏳ |
| 6 | Compliance review, Riot Developer Portal registration, first release | ⏳ |

## Quickstart (Windows)

```powershell
git clone https://github.com/julbrehier/riftlens.git
cd riftlens
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"

# Start a game (Practice Tool is ideal), then:
riftlens probe
```

`riftlens probe` waits for a game and prints a live scoreboard. It saves JSON snapshots to
`snapshots/`, which git ignores because they contain other players' Riot IDs.

```text
riftlens probe --once                 # stop after the first game ends
riftlens probe --interval 1 --save-every 10
riftlens probe --cert riotgames.pem   # verify Riot's local TLS certificate
riftlens --help
```

## Development

```powershell
pre-commit install        # run ruff + mypy on every commit
ruff check .              # lint
ruff format .             # format
mypy                      # strict type-check of src/
pytest --cov              # tests with coverage
```

Work happens in small, reviewable steps: one feature per branch and pull request. CI runs
lint, type-checking and tests on Windows and Linux for Python 3.11 to 3.13.

## Project layout

```text
src/riftlens/
├── live_client/     # Live Client Data API: HTTP client + typed pydantic models
├── recorder.py      # records game snapshots to disk (replayable fixtures)
├── render.py        # pure text rendering (scoreboard)
└── cli.py           # `riftlens` command-line entry point
tests/
├── fixtures/        # synthetic / anonymised API payloads
└── test_*.py
```

## Legal

RiftLens isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games
or anyone officially involved in producing or managing Riot Games properties. Riot Games, and
all associated properties are trademarks or registered trademarks of Riot Games, Inc.

Code licensed under the [MIT License](LICENSE).
