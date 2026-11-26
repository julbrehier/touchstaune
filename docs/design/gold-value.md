# Design: live gold value

**Status:** draft · **Phase:** 3 · **Last updated:** 2026-11-26

## 1. Goal

Show, live, what each player is **really worth in gold**. That is more than the shop price
of their items. It includes:

- **item modifiers**: multiplicative passives such as Rabadon's Deathcap;
- **item stacks**: Mejai's Soulstealer, Hubris, and similar;
- **champion stacking**: Thresh's souls, Veigar, Cho'Gath, Sion, and so on;
- *(later, if compliant)* **augments** in modes that have them.

The number answers one question: *"how much gold would a player need to spend on
pure-stat items to buy the stats this champion currently has from sources other than
its base stats?"*

## 2. Gold per stat

Every stat `s` gets a gold rate `g_s` (gold per point). The **gold value** of a stat
vector `x` is linear:

```
V(x) = Σ_s g_s · x_s
```

**Estimating `g_s`.** Rates are not hard-coded. They are re-derived from Data Dragon on
every patch:

1. Take the *reference items*: purchasable Summoner's Rift items whose cost is
   (as far as we know) entirely in stats. These are basic components and items with no
   passive or active.
2. Each reference item `i` gives one linear equation: `cost_i = Σ_s g_s · x_{i,s}`.
3. Solve the overdetermined system `X g ≈ c` by **non-negative least squares**.
   For single-stat basics such as Long Sword or Amplifying Tome this gives the classic
   "gold efficiency" rates exactly. Items with several stats then constrain the rates
   no single basic item covers, such as ability haste or lethality.
4. Report the fit residuals. A large residual means an item's price includes something
   that isn't a stat, which is useful information in itself.

## 3. Value of a player

For each player we compute a breakdown, not a single number:

| Component | Definition | Available for |
|---|---|---|
| **Shop value** | Σ `gold.total` of owned items (Data Dragon) | everyone (scoreboard items) |
| **Item stat value** | `V(Σ item base stats)` | everyone |
| **Modifier value** | gold value of the stats added by multiplicative passives | everyone (from items) / you (exact) |
| **Stack value** | gold value of item and champion stacks | see §4 |
| **Live stat value** | `V(live stats − champion base stats at current level)` | **you only** |

**Live stat value (active player).** The Live Client API gives your champion's live stats.
Data Dragon gives champion base stats and growth. Base stats at level `n` follow Riot's
growth formula:

```
stat(n) = base + growth · (n − 1) · (0.7025 + 0.0175 · (n − 1))
```

`V(live − base(n))` therefore captures *everything* at once: items, modifiers, stacks and
runes. The other components are then an **attribution** of that total. Whatever cannot be
attributed is reported as *"unexplained"*, which also tells us when the model is missing
something.

**Multiplicative modifiers.** For an amplifier of `m` on stat `s` (for example
Rabadon's `+m` total AP), the gold credited to the modifier is the value of what it
adds:

```
ΔV_modifier = g_s · x_s^total · m / (1 + m)
```

where `x_s^total` is the stat *after* amplification. Modifier coefficients live in a small,
versioned registry (`modifiers.toml`), checked against the patch notes.

## 4. Stacks

| Source | Your champion | Other players |
|---|---|---|
| Item stacks driven by takedowns and deaths (Mejai, Hubris) | exact, from live stats | **reconstructed from `ChampionKill` events** (kills, assists, deaths) |
| Champion stacks (Thresh, Veigar...) | exact, from live stats | not estimated: the API doesn't expose them and they can't be derived from events |
| Augments | ⚠️ compliance check first | ⚠️ compliance check first |

Reconstructed values are always labelled **estimated** in the UI.

## 5. Compliance (see COMPLIANCE.md)

- Every input is either visible in the client (scoreboard items, KDA, kill feed) or is
  the player's own data. **No hidden information is revealed.**
- The display is **passive**: numbers and breakdowns only, with **no alerts** such as
  "enemy just spiked", which Riot bans as power-spike notifications.
- **Augments:** Riot restricts augment data (win rates for augments and Arena items are
  explicitly banned). Showing augment values must be checked against the current
  policy before it is built.

## 6. Findings from real data

From the first recorded snapshot (Practice Tool, 2026-11-26):

- **The Live Client `price` field is the recipe (combine) cost**, not the total cost
  (Infinity Edge reports 725). Shop value **must** use Data Dragon's `gold.total`.
- **Units are mixed.** Crit chance and vamps are fractions, crit damage is a percentage, and
  percent penetration is a *remaining-resistance multiplier* (`0.65` = 35 % penetration).
  The stat catalogue (plan step 2.4) must normalise them before any gold rate is applied.
- **Live stats include temporary buffs** (Ghost was showing 725 movement speed). The live
  stat value needs either a list of transient stats to exclude, or smoothing over time.

## 7. Known limitations

- Effects that aren't stats (actives, on-hit damage, shields, unique passives) are worth
  something but have no stat equivalent. They are **out of scope for v1** and appear
  only through fit residuals. Valuing them is the "beyond gold efficiency" research
  question (portfolio Project 2), and the decomposition above is designed to extend to it.
- Gold rates depend on which items are used as references. That choice is documented
  and versioned with each patch.

## 8. Implementation plan (one PR each)

1. `ddragon`: versioned client and on-disk cache for `versions.json`, `item.json` and `champion/*.json`.
2. `value.rates`: reference-item selection and NNLS solver for `g_s`, with a residual report.
3. `value.player`: shop and item-stat value for all ten players; a scoreboard column.
4. Base-stat growth and live stat value for the active player; "unexplained" remainder.
5. Modifier registry and attribution (Rabadon first).
6. Event-based stack reconstruction (Mejai, Hubris) for all players.
7. Champion stack models for the active player (Thresh first).
8. Overlay window rendering of the breakdown (Phase 2 UI).
