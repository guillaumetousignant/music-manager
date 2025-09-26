#!/bin/python

import argparse
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt

from music_manager.utilities.arguments import add_common_arguments_to_parser
from music_manager.utilities.constants import DELIMITER, M3U_HEADER
from music_manager.utilities.logging import set_log_level


def get_filename(
    console: Console, root: Path, artist: str, album: str, filename: str
) -> tuple[str, str, str]:
    while not (root / artist / album / filename).is_file():
        logging.warning(
            f"File {filename} at {root / artist / album / filename} does not exist"
        )
        files = [
            file.name for file in (root / artist / album).iterdir() if file.is_file()
        ]

        matches = [
            file for file in files if file.casefold().endswith(filename.casefold())
        ]

        if len(matches) == 1:
            logging.info(f"Automatically found {filename} as {matches[0]}")
            filename = matches[0]
        else:
            indices = [str(i) for i in range(len(files) + 2)]
            console.print("[blue]0: [Change artist][/blue]")
            console.print("[blue]1: [Change album][/blue]")
            for i, file_entry in enumerate(files):
                console.print(f"[blue]{i + 2}: {file_entry}[/blue]")

            file_index = Prompt.ask(
                f'[yellow]File "{filename}" in artist "{artist}" and album "{album}" does not exist, enter filename[/yellow]',
                choices=indices,
                console=console,
            )
            if file_index == "0":
                artist = Prompt.ask(
                    f'[green]Enter artist to replace "{artist}"[/green]',
                    console=console,
                )
                artist = get_artist(console, root, artist)
            elif file_index == "1":
                albums = [
                    directory.name
                    for directory in (root / artist).iterdir()
                    if directory.is_dir()
                ]

                indices = [str(i) for i in range(len(albums))]
                for i, album_entry in enumerate(albums):
                    console.print(f"[blue]{i}: {album_entry}[/blue]")

                album_index = Prompt.ask(
                    f'[green]Enter album to replace "{album}"[/green]',
                    choices=indices,
                    console=console,
                )
                album = albums[int(album_index)]

                artist, album = get_album(console, root, artist, album, filename)
            else:
                filename = files[int(file_index) - 2]

    return (artist, album, filename)


def get_album(
    console: Console, root: Path, artist: str, album: str, filename: str
) -> tuple[str, str]:
    while not (root / artist / album).is_dir():
        logging.info(f"Album {album} at {root / artist / album} does not exist")

        albums = [
            directory.name
            for directory in (root / artist).iterdir()
            if directory.is_dir()
        ]

        indices = [str(i) for i in range(len(albums) + 1)]
        console.print("[blue]0: [Change artist][/blue]")
        for i, album_entry in enumerate(albums):
            console.print(f"[blue]{i + 1}: {album_entry}[/blue]")

        album_index = Prompt.ask(
            f'[yellow]Album "{album}" in artist "{artist}" for filename "{filename}" does not exist, enter album[/yellow]',
            choices=indices,
            console=console,
        )
        if album_index == "0":
            artist = Prompt.ask(
                f'[green]Enter artist to replace "{artist}"[/green]',
                console=console,
            )
            artist = get_artist(console, root, artist)
        else:
            album = albums[int(album_index) - 1]

    return (artist, album)


def get_artist(console: Console, root: Path, artist: str) -> str:
    while not (root / artist).is_dir():
        logging.warning(f"Artist {artist} at {root / artist} does not exist")

        artist = Prompt.ask(
            f'[yellow]Artist "{artist}" does not exist, enter artist[/yellow]',
            console=console,
        )

    return artist


def playlist_find_missing(
    root: Path,
    input: Path,
    output: Path,
):
    logging.info(f"Processing root {root}")

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

            console = Console()

            for line in input_file:
                relative_path = line.rstrip()
                absolute_path = root / relative_path

                logging.debug(f"Processing file {relative_path} at {absolute_path}")

                parts = relative_path.split(DELIMITER)
                if len(parts) != 3:
                    raise RuntimeError(
                        f"Relative path {relative_path} does not have three parts"
                    )

                # File exists
                if absolute_path.is_file():
                    output_file.write(line)
                    continue

                # File does not exist
                logging.info(f"File {relative_path} at {absolute_path} does not exist")

                artist = parts[0]
                album = parts[1]
                filename = parts[2]

                artist = get_artist(console, root, artist)
                artist, album = get_album(console, root, artist, album, filename)
                artist, album, filename = get_filename(
                    console, root, artist, album, filename
                )

                output_file.write(f"{DELIMITER.join([artist, album, filename])}\n")


def playlist_find_missing_main(args: argparse.Namespace):
    playlist_find_missing(args.root, args.input, args.output)


def main():
    parser = argparse.ArgumentParser(
        prog="Playlist Find Missing",
        description="Verifies that all entries in a playlist are valid paths.",
    )
    parser.add_argument(
        "-r",
        "--root",
        type=Path,
        default=Path("."),
        help="Path to a directory containing music organised as artists and albums",
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
    parser.set_defaults(func=playlist_find_missing_main)

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
