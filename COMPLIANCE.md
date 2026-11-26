# Compliance

RiftLens must stay within Riot's
[Developer API Policy](https://developer.riotgames.com/docs/lol) and
[third-party application stance](https://support-leagueoflegends.riotgames.com/hc/en-us/articles/225266848).
This file turns those policies into rules for the code. **Every feature PR is checked against it**
(see the pull request template).

Riot changes these rules over time. Re-read the official pages before each release, and update
this file when they change. *Last reviewed: 2026-11-26.*

## 1. Data sources

| Source | Status | Notes |
|---|---|---|
| Live Client Data API (`https://127.0.0.1:2999/liveclientdata`) | ✅ Official | Served by the game client during a match. |
| Riot Web API (`*.api.riotgames.com`) | ✅ Official | Requires a registered app and an API key. Respect the rate limits. |
| Data Dragon / static data | ✅ Official | Static game data (items, champions, runes). |
| League Client API (LCU) | ⚠️ Tolerated, unsupported | Riot must be notified of the endpoints used, through the Developer Portal app. |
| Game memory, DLL injection, packet sniffing, process hooks | ❌ Never | Blocked by Riot for unknown apps since 6 Oct 2026, and incompatible with Vanguard. |

## 2. Features

### Allowed
- The player's own stats, both live and historical.
- Static information that is available before the game starts.
- Information that is already visible in the game client, such as the scoreboard: items, levels and KDA.
- Aggregate statistics that do not identify specific players.
- Loading-screen scouting through the official Web API (once names are public).
- Build and rune *suggestions* that offer several options and leave the choice to the player.

### Forbidden
- Tracking or timing enemy **ability, ultimate or summoner-spell cooldowns**.
- **Power-spike alerts**, such as "enemy Annie hit level 6".
- **Directive alerts** that tell the player what to do ("gank top now").
- Automating any decision, for example auto-buying items or auto-levelling skills.
- MMR, ELO or any alternative ranking system.
- Identifying or analysing players the game hides, including anonymous ranked champion select.
- Augment or Arena item win rates. Any Brawl or League Classic data.
- Advertising inside the client, on loading screens or in game.
- A UI that imitates Riot's own interface.

### Grey zone (not implemented unless Riot's policy clearly allows it)
- Jungle camp and objective timers.
- Automatic rune-page import through the LCU.

## 3. Player data and privacy
- Recorded snapshots contain other players' Riot IDs. They stay local: `snapshots/` is git-ignored.
- Test fixtures must be **synthetic or anonymised** (Riot IDs replaced with placeholders) before they are committed.
- Nothing is sent to third-party servers.

## 4. Release requirements
- Register the product on the Riot Developer Portal, and list any LCU endpoints it uses.
- Show the "isn't endorsed by Riot Games" notice where users can easily see it (README and app UI).
