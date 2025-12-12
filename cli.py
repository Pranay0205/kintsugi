import argparse

from utils.constants import BATCH_SIZE


def main() -> None:

    parser = argparse.ArgumentParser(description="Knowledge Tracer CLI")
    subparser = parser.add_subparsers(
        dest="command", help="Available Commands")

    analyze_parser = subparser.add_parser(
        "analyze", help="Analyze code submissions using LLMs")

    analyze_parser.add_argument(
        "--limit", type=int, default=BATCH_SIZE,
        help="Limit the number of submissions to analyze (default: 50)")

    args = parser.parse_args()

    match args.command:
        case "analyze":
            from commands.analyze import analyze_command
            analyze_command(args.limit)
        case _:
            parser.print_help()


if __name__ == "__main__":
    main()
