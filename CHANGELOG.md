# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Project scaffold: packaging (hatchling, src layout), ruff, strict mypy, pytest, pre-commit,
  GitHub Actions CI on Windows/Linux for Python 3.11–3.13, Dependabot.
- `COMPLIANCE.md` mapping Riot's developer policy to concrete feature rules.
- `riftlens.live_client`: typed pydantic models and an httpx client for the Live Client Data API.
- `riftlens.recorder.GameRecorder`: records game snapshots to disk as replayable JSON.
- `riftlens probe` CLI command with a live text scoreboard.
