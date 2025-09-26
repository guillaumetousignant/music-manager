import argparse
import tomllib
from importlib import metadata
from pathlib import Path


def get_version() -> str:
    try:
        return metadata.version("music-manager")
    except Exception:
        try:
            with open("pyproject.toml", "rb") as f:
                pyproject = tomllib.load(f)
            return pyproject["project"]["version"]
        except Exception:
            return "develop"


def add_common_arguments_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        dest="verbosity",
        default=0,
        help="verbose output (repeat to increase verbosity)",
    )
    parser.add_argument(
        "-l",
        "--logfile",
        type=Path,
        help="log to a file instead of the console",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {get_version()}"
    )
