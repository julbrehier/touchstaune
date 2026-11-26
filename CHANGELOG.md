# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Project scaffold: packaging (hatchling, src layout), ruff, strict mypy, pytest, pre-commit,
  GitHub Actions CI on Windows/Linux for Python 3.11–3.13, Dependabot.
- `COMPLIANCE.md` mapping Riot's developer policy to concrete feature rules.
- `touchstaune.live_client`: typed pydantic models and an httpx client for the Live Client Data API.
- `touchstaune.recorder.GameRecorder`: records game snapshots to disk as replayable JSON.
- `touchstaune probe` CLI command with a live text scoreboard.
- `touchstaune anonymise` CLI command: replaces every player identifier in a recorded
  snapshot with stable placeholders (`Player1#ANON`, ...), including inside events.
- First real (anonymised) fixture, and tests pinning down conventions of the real API.
- `ChampionStats` now models every stat the API reports, with units documented.
