import argparse
import sys

from rich.console import Console
from rich_tools import df_to_table

from .api import amateur_draft_data
from .logger import initialize_logger


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLI for pybaseball. Pull current and historical baseball statistics using Python (Statcast, Baseball Reference, FanGraphs)"
    )
    subparsers = parser.add_subparsers(dest="command")

    # add subparser for amateur draft
    draft_parser = subparsers.add_parser("draft", help="get amateur draft results")
    draft_parser.add_argument("year", type=int, help="the year of the draft")
    draft_parser.add_argument("round", type=int, help="the round of the draft")
    draft_parser.add_argument(
        "--team", type=str, help="the team to get draft results for"
    )
    draft_parser.add_argument(
        "--keep-stats", action="store_true", help="keep stats in the results"
    )
    draft_parser.set_defaults(func=amateur_draft_data)

    parser.add_argument(
        "--log-level",
        "-ll",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="set the logging level (default: INFO)",
    )
    parser.add_argument(
        "--log-file",
        "-lf",
        default=".pybaseball_logs/pybaseball.log",
        help="set the logging file (default: .pybaseball_logs/pybaseball.log)",
    )
    parser.add_argument(
        "-p", "--plain", action="store_true", help="output plain text rather than rich"
    )

    args = parser.parse_args()

    initialize_logger(
        console_level=args.log_level,
        log_filepath=args.log_file,
        plain=args.plain,
    )

    console = Console()
    if args.command == "draft":
        try:
            results = amateur_draft_data(
                args.year, args.round, args.team, args.keep_stats
            )
            if args.plain:
                print(results)
            else:
                table = df_to_table(results)
                console.print(table)
            sys.exit(0)
        except Exception as e:
            print(f"error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
