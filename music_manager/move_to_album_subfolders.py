#!/bin/python

import argparse
import logging
import shutil
import sys
from pathlib import Path
from typing import Optional

from mutagen.id3 import ID3
from mutagen.mp4 import MP4
from pathvalidate import ValidationError, sanitize_filename, validate_filename

from music_manager.utilities.arguments import add_common_arguments_to_parser
from music_manager.utilities.constants import (
    DELIMITER,
    M3U_HEADER,
    MP3_ALBUM_KEY,
    MP3_ARTIST_KEY,
    MP4_ALBUM_KEY,
    MP4_ARTIST_KEY,
)
from music_manager.utilities.logging import set_log_level


def get_mp3_artist_and_album(path: Path) -> tuple[Optional[str], Optional[str]]:
    music_file = ID3(path)

    albums = music_file.get(MP3_ALBUM_KEY)  # type: ignore
    album = None if albums is None else albums.text[0]  # type: ignore

    artists = music_file.get(MP3_ARTIST_KEY)  # type: ignore
    artist = None if artists is None else artists.text[0]  # type: ignore

    return (album, artist)  # type: ignore


def get_m4a_artist_and_album(path: Path) -> tuple[Optional[str], Optional[str]]:
    music_file = MP4(path)

    albums = music_file.get(MP4_ALBUM_KEY)  # type: ignore
    album = None if albums is None else albums[0]  # type: ignore

    artists = music_file.get(MP4_ARTIST_KEY)  # type: ignore
    artist = None if artists is None else artists[0]  # type: ignore

    return (album, artist)  # type: ignore


def sanitise_string_for_path(string: str, name: str) -> str:
    try:
        validate_filename(string)
    except ValidationError as e:
        replaced_string = sanitize_filename(string)
        logging.info(
            f'Validation of {name} with value "{string}" failed, replacing by "{replaced_string}". Error: {e}'
        )
        string = replaced_string
    return string


def move_to_album_subfolders(
    root: Path,
    new_root: Path,
    input: Path,
    output: Path,
):
    logging.info(f"Processing path {root}, copying to path {new_root}")

    if input == output:
        raise RuntimeError(
            f"Input and output files are the same, {input}, this is not supported"
        )

    if root == new_root:
        raise RuntimeError(
            f"Original and new roots are the same, {root}, this is not supported"
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
                        album, artist = get_mp3_artist_and_album(filepath)
                    case ".m4a":
                        album, artist = get_m4a_artist_and_album(filepath)
                    case unknown_extension:
                        raise RuntimeError(
                            f"Unsupported extension {unknown_extension} for file {filename} at {filepath}"
                        )

                if artist is None:
                    raise RuntimeError(
                        f"Missing artist for file {filename} at {filepath}"
                    )

                if album is None:
                    raise RuntimeError(
                        f"Missing album for file {filename} at {filepath}"
                    )

                album = sanitise_string_for_path(album, "album")
                artist = sanitise_string_for_path(artist, "artist")

                new_folder = new_root / artist / album
                new_folder.mkdir(parents=True, exist_ok=True)

                new_path = new_folder / filename
                new_entry = DELIMITER.join([artist, album, filename])

                output_file.write(f"{new_entry}\n")

                logging.debug(f"Copying entry {filename} to {new_entry}")
                shutil.copy(filepath, new_path)


def move_to_album_subfolders_main(args: argparse.Namespace):
    move_to_album_subfolders(args.root, args.new_root, args.input, args.output)


def main():
    parser = argparse.ArgumentParser(
        prog="Move to Album Subfolders",
        description="Creates subfolders for albums and moves music to it.",
    )
    parser.add_argument(
        "-r",
        "--root",
        type=Path,
        default=Path("Flat/"),
        help="Path to a directory where music is organised in a flat fashion and to which the input playlist is relative",
    )
    parser.add_argument(
        "-n",
        "--new-root",
        type=Path,
        default=Path("Sorted/"),
        help="Path to a directory where music is to be organised per artist and album and to which the output playlist is relative",
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
    set_log_level(args.verbosity, args.logfile)

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
