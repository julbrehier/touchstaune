## What does this change?

<!-- One or two sentences. Link the roadmap phase if relevant. -->

## Compliance check (see COMPLIANCE.md)

- [ ] Uses only official data sources (Live Client Data API, Riot Web API, Data Dragon, LCU with notice)
- [ ] Shows no information the player could not already see in the game client
- [ ] Tracks no enemy cooldowns (abilities, ultimates, summoner spells) and sends no power-spike alerts
- [ ] Suggests options but never makes or automates a decision for the player
- [ ] No raw snapshots or other players' Riot IDs committed

## Quality

- [ ] Tests added or updated
- [ ] `ruff check .`, `ruff format --check .`, `mypy` and `pytest` pass locally
- [ ] CHANGELOG.md updated
