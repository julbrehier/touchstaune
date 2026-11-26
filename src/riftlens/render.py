"""Pure text rendering of game state. No I/O: every function returns a string."""

from riftlens.live_client import AllGameData, Player, Team

_WIDTH = 80


def format_clock(seconds: float) -> str:
    """Format in-game seconds as ``MM:SS`` (minutes may exceed 59)."""
    total = max(0, int(seconds))
    return f"{total // 60:02d}:{total % 60:02d}"


def _side_label(player: Player, my_team: Team | None) -> str:
    if my_team is None:  # spectating: fall back to the map side
        return player.team.value
    return "ALLY" if player.team == my_team else "ENEMY"


def format_scoreboard(data: AllGameData) -> str:
    """Render a compact scoreboard: allies first, then enemies, then the player's own stats."""
    game = data.game_data
    me = data.active_player
    my_team = data.my_team()

    header = f" {game.game_mode} | {format_clock(game.game_time)}"
    if me is not None and me.identities:
        header += f" | {me.display_id} | lvl {me.level} | gold {me.current_gold:.0f}"

    lines = [
        "=" * _WIDTH,
        header,
        "=" * _WIDTH,
        f" {'side':<6}{'champion':<14}{'lvl':>4}{'K/D/A':>10}{'CS':>6}{'ward':>6}{'items':>6}"
        "  player",
        "-" * _WIDTH,
    ]

    # sorted() is stable: allies (False) before enemies (True), original order otherwise.
    for player in sorted(data.all_players, key=lambda p: my_team is not None and p.team != my_team):
        dead = " (dead)" if player.is_dead else ""
        lines.append(
            f" {_side_label(player, my_team):<6}{player.champion_name:<14}{player.level:>4}"
            f"{player.scores.kda_string:>10}{player.scores.creep_score:>6}"
            f"{player.scores.ward_score:>6.0f}{len(player.equipment):>6}"
            f"  {player.display_id}{dead}"
        )

    if me is not None and me.champion_stats is not None:
        s = me.champion_stats
        lines += [
            "-" * _WIDTH,
            f" you  AD {s.attack_damage:.0f}  AP {s.ability_power:.0f}  AS {s.attack_speed:.2f}"
            f"  armor {s.armor:.0f}  MR {s.magic_resist:.0f}"
            f"  HP {s.current_health:.0f}/{s.max_health:.0f}  haste {s.ability_haste:.0f}",
        ]

    return "\n".join(lines)
