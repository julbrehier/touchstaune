"""Command-line entry point: ``touchstaune <command>``."""

import argparse
import logging
import time
from collections.abc import Sequence
from pathlib import Path

from touchstaune import __version__
from touchstaune.anonymise import anonymise_file
from touchstaune.live_client import LiveClient, LiveClientError
from touchstaune.recorder import GameRecorder, RecorderState
from touchstaune.render import format_scoreboard

logger = logging.getLogger("touchstaune")


def build_parser() -> argparse.ArgumentParser:
    """Argument parser for all sub-commands."""
    parser = argparse.ArgumentParser(
        prog="touchstaune",
        description="Riot-policy-compliant League of Legends overlay (official APIs only).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="enable debug logging")
    commands = parser.add_subparsers(dest="command", required=True)

    probe = commands.add_parser(
        "probe",
        help="poll the Live Client Data API, print a scoreboard and record snapshots",
    )
    probe.add_argument("--interval", type=float, default=2.0, help="seconds between polls in game")
    probe.add_argument(
        "--wait-poll", type=float, default=3.0, help="seconds between polls while no game runs"
    )
    probe.add_argument(
        "--save-every", type=float, default=30.0, help="in-game seconds between saved snapshots"
    )
    probe.add_argument(
        "--end-after-misses",
        type=int,
        default=5,
        help="consecutive failed polls before the game is considered over",
    )
    probe.add_argument("--out", type=Path, default=Path("snapshots"), help="output directory")
    probe.add_argument("--cert", type=Path, default=None, help="Riot root cert (riotgames.pem)")
    probe.add_argument("--once", action="store_true", help="exit after the first game ends")
    probe.add_argument("--quiet", action="store_true", help="record without printing scoreboards")
    probe.set_defaults(handler=run_probe)

    anonymise = commands.add_parser(
        "anonymise",
        help="copy a recorded snapshot with every player identifier replaced by a placeholder",
    )
    anonymise.add_argument("source", type=Path, help="recorded snapshot (JSON)")
    anonymise.add_argument("destination", type=Path, help="where to write the anonymised copy")
    anonymise.set_defaults(handler=run_anonymise)

    return parser


def run_anonymise(args: argparse.Namespace) -> int:
    """Run the ``anonymise`` command."""
    if args.source.resolve() == args.destination.resolve():
        logger.error("Refusing to overwrite the original snapshot: choose another destination.")
        return 2
    count = anonymise_file(args.source, args.destination)
    logger.info("Anonymised %d player(s) into %s", count, args.destination)
    return 0


def run_probe(args: argparse.Namespace) -> int:
    """Run the ``probe`` command until interrupted (or until one game ends with ``--once``)."""
    with LiveClient(ca_cert=args.cert) as client:
        recorder = GameRecorder(
            client,
            args.out,
            save_every=args.save_every,
            end_after_misses=args.end_after_misses,
        )
        logger.info("Waiting for a game on the Live Client Data API... (Ctrl+C to stop)")
        try:
            while True:
                result = recorder.step()
                if result.data is not None and not args.quiet:
                    print(format_scoreboard(result.data), flush=True)
                if result.state is RecorderState.ENDED:
                    logger.info("Game over.")
                    if args.once:
                        return 0
                    logger.info("Waiting for the next game...")
                in_game = recorder.game_dir is not None
                time.sleep(args.interval if in_game else args.wait_poll)
        except KeyboardInterrupt:
            recorder.finalise()
            logger.info("Stopped.")
            return 0
        except LiveClientError:
            logger.exception("The Live Client Data API returned an unexpected payload.")
            recorder.finalise()
            return 1


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, configure logging and dispatch to the chosen command."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    exit_code: int = args.handler(args)
    return exit_code
