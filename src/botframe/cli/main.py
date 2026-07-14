from __future__ import annotations

import argparse
from collections.abc import Sequence

from botframe.cli.i18n import (
    add_locale,
    build_catalogs,
    compile_catalogs,
    extract_catalog,
    initialize_i18n,
    update_catalogs,
)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="botframe",
        description="Bot Frame command line interface.",
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    i18n_parser = commands.add_parser(
        "i18n",
        help="Manage localization catalogs.",
    )

    i18n_commands = i18n_parser.add_subparsers(
        dest="i18n_command",
        required=True,
    )

    init_parser = i18n_commands.add_parser(
        "init",
        help="Create Bot Frame localization configuration.",
    )
    init_parser.add_argument(
        "--source",
        default=".",
        help="Directory containing Python source files.",
    )
    init_parser.add_argument(
        "--directory",
        default="locales",
        help="Directory for translation catalogs.",
    )
    init_parser.add_argument(
        "--domain",
        default="messages",
        help="Translation domain.",
    )
    init_parser.add_argument(
        "--default-locale",
        default="en",
        help="Default application locale.",
    )

    add_parser = i18n_commands.add_parser(
        "add",
        help="Add a new translation locale.",
    )
    add_parser.add_argument(
        "locale",
        help="Locale code, for example ru, en or de.",
    )

    i18n_commands.add_parser(
        "extract",
        help="Extract messages from source files.",
    )

    i18n_commands.add_parser(
        "update",
        help="Extract messages and update existing catalogs.",
    )

    i18n_commands.add_parser(
        "compile",
        help="Compile PO catalogs into MO files.",
    )

    i18n_commands.add_parser(
        "build",
        help="Extract, update and compile translation catalogs.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command != "i18n":
        parser.error(f"Unknown command: {args.command}")

    match args.i18n_command:
        case "init":
            initialize_i18n(
                source=args.source,
                directory=args.directory,
                domain=args.domain,
                default_locale=args.default_locale,
            )

        case "add":
            add_locale(args.locale)

        case "extract":
            extract_catalog()

        case "update":
            update_catalogs()

        case "compile":
            compile_catalogs()

        case "build":
            build_catalogs()

        case _:
            parser.error(
                f"Unknown i18n command: {args.i18n_command}"
            )