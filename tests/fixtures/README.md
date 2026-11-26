# Test fixtures

| File | Origin |
|---|---|
| `allgamedata_practicetool.json` | **Real, anonymised.** A Practice Tool game (Quinn, 6 items, ~80 s), recorded with `touchstaune probe` and passed through `touchstaune anonymise`. |
| `allgamedata_synthetic.json` | **Synthetic.** Hand-written from the documented `/allgamedata` schema. It is reduced to 2v2 and includes a few unknown fields to check that the parser tolerates them. |

To add a real recorded snapshot, **always anonymise it first**:

```powershell
touchstaune anonymise snapshots\<game>\final.json tests\fixtures\<name>.json
```

Then open the result and check by eye that no Riot ID is left. See COMPLIANCE.md §3.
