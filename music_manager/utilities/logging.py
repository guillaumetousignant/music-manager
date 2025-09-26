import logging
from pathlib import Path
from typing import Optional


def set_log_level(verbosity: int, log_file: Optional[Path] = None):
    match verbosity:
        case 0:
            log_level = logging.WARNING
        case 1:
            log_level = logging.INFO
        case 2:
            log_level = logging.DEBUG
        case _:
            raise RuntimeError(
                f"Unsupported log level {verbosity}. 0 for WARNING, 1 for INFO, 2 for DEBUG"
            )

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s:%(levelname)s:%(name)s:%(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        filename=log_file,
        filemode="a",
    )
