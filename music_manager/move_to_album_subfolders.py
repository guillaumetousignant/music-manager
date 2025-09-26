#!/bin/python

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from mutagen.id3 import ID3
from mutagen.mp4 import MP4

from music_manager.utilities.arguments import add_common_arguments_to_parser
from music_manager.utilities.constants import M3U_HEADER
from music_manager.utilities.logging import set_log_level


def get_mp3_album(path: Path) -> Optional[str]:
    music_file = ID3(path)
    albums = music_file.get("album")  # type: ignore
    return None if albums is None else albums[0]  # type: ignore


def get_m4a_album(path: Path) -> Optional[str]:
    music_file = MP4(path)
    albums = music_file.get("©alb")  # type: ignore
    return None if albums is None else albums[0]  # type: ignore


def move_to_album_subfolders(
    root: Path,
    input: Path,
    output: Path,
):
    logging.info(f"Processing path {root}")

    if input == output:
        raise RuntimeError(
            f"Input and output files are the same, {input}, this is not supported"
        )

    logging.info(f"Input playlist: {input}")
    logging.info(f"Output playlist: {output}")
    with open(input, "r", encoding="utf-8") as input_file:
        with open(output, "w", encoding="utf-8") as output_file:
            header = input_file.readline()
            if header != M3U_HEADER:
                raise RuntimeError(
                    f"Input input_file {input} does not start with m3u header"
                )

            output_file.write(M3U_HEADER)

            for line in input_file:
                filename = line.rstrip()
                filepath = root / filename
                logging.debug(f"Processing file {filename} at {filepath}")

                extension = filepath.suffix

                match extension.casefold():
                    case ".mp3":
                        album = get_mp3_album(filepath)
                    case ".m4a":
                        album = get_m4a_album(filepath)
                    case unknown_extension:
                        raise RuntimeError(
                            f"Unsupported extension {unknown_extension} for file {filename} at {filepath}"
                        )

                print(album)


def move_to_album_subfolders_main(args: argparse.Namespace):
    move_to_album_subfolders(args.root, args.input, args.output)


def main():
    parser = argparse.ArgumentParser(
        prog="Move to Album Subfolders",
        description="Creates subfolders for albums and moves music to it.",
    )
    parser.add_argument(
        "-r",
        "--root",
        type=Path,
        default=Path("."),
        help="Path to a directory where music is organised and to which playlists are relative",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("playlist.m3u"),
        help="Path to a m3u playlist with a list of songs",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output.m3u"),
        help="Path where the m3u playlist will be written",
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
