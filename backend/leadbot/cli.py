"""Command-line interface for backend maintenance and local workflows."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Create the root CLI parser for leadbot."""
    parser = argparse.ArgumentParser(prog="leadbot", description="Leady backend CLI")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print package version and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the leadbot CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        from . import __version__

        print(__version__)
        return 0

    parser.print_help()
    return 0
