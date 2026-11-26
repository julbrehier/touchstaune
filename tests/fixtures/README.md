# Test fixtures

| File | Origin |
|---|---|
| `allgamedata_synthetic.json` | **Synthetic.** Hand-written from the documented `/allgamedata` schema. It is reduced to 2v2 and includes a few unknown fields to check that the parser tolerates them. |

To add real recorded snapshots (from `riftlens probe`), **anonymise them first**: replace every
`riotId`, `riotIdGameName` and `summonerName`, and any names inside events, with placeholders.
See COMPLIANCE.md §3.
