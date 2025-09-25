#!/bin/python

import argparse
import logging
import sys
from pathlib import Path

from music_manager.utilities.arguments import add_common_arguments_to_parser
from music_manager.utilities.logging import set_log_level


def create_playlist(
    path: Path,
    output: Path,
):
    logging.info(f"Processing path {path}")

    files = [file for file in path.iterdir() if file.is_file()]
    files.sort(key=lambda file: file.stat().st_birthtime)

    with open(output, "w", encoding="utf-8") as output_file:
        output_file.write("#EXTM3U\n")
        for file in files:
            logging.debug(f"Writing file {file}")
            output_file.write(f"{file.name}\n")


def create_playlist_main(args: argparse.Namespace):
    create_playlist(args.path, args.output)


def main():
    parser = argparse.ArgumentParser(
        prog="Create Playlist",
        description="Creates a playlist from the content of a directory, sorted by age.",
    )
    parser.add_argument(
        "-p",
        "--path",
        type=Path,
        default=Path("."),
        help="Path to a directory containing files to add to a playlist",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("playlist.m3u"),
        help="Path where the m3u playlist will be written",
    )
    add_common_arguments_to_parser(parser)
    parser.set_defaults(func=create_playlist_main)

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
