#!/bin/python

import argparse
import logging
import sys
from pathlib import Path

import mutagen

from music_manager.utilities.arguments import add_common_arguments_to_parser
from music_manager.utilities.logging import set_log_level


def move_to_album_subfolders(
    path: Path,
):
    logging.info(f"Processing path {path}")

    for file in path.iterdir():
        if not file.is_file():
            continue
        logging.debug(f"Processing file {file}")

        music_file = mutagen.File(file)  # type: ignore
        if music_file is None:
            logging.warning(f"File of unknown type, skipping: {file}")

        print(music_file.info.pprint())  # type: ignore
        print(music_file.tags.pprint())  # type: ignore


def move_to_album_subfolders_main(args: argparse.Namespace):
    move_to_album_subfolders(args.path)


def main():
    parser = argparse.ArgumentParser(
        prog="Move to Album Subfolders",
        description="Creates subfolders for albums and moves music to it.",
    )
    parser.add_argument(
        "-p",
        "--path",
        type=Path,
        default=Path("."),
        help="Path to a configuration file to use",
    )
    add_common_arguments_to_parser(parser)
    parser.set_defaults(func=move_to_album_subfolders_main)

    args = parser.parse_args(sys.argv[1:])
    set_log_level(args.verbosity)

    try:
        args.func(args)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received")
    except Exception as e:
        logging.exception("Unhandled exception")
        if args.verbosity >= 1:
            raise e


if __name__ == "__main__":
    main()
