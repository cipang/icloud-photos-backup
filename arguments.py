import argparse
import logging
from typing import Optional

_parser = argparse.ArgumentParser(description="Backup iCloud Photos to a local directory.")
_parser.add_argument("username", help="username of the iCloud account")
_parser.add_argument("dest", help="destination directory to store photos")
_parser.add_argument("-a", "--album", help="name of the album to download; download all photos when not specified")
_parser.add_argument("-l", "--skip-limit", help="specify how many existing photos should be skipped before exiting",
                     type=int, default=0)
_parser.add_argument("--log", help="enable logging and specify the location of the log file")
_parser.add_argument("--loglevel", help="logging level", choices=["debug", "info", "warning", "error", "fatal"],
                     default="info")
_args = _parser.parse_args()

username: str = _args.username
dest: str = _args.dest
album: Optional[str] = _args.album
skip_limit: int = _args.skip_limit

# Setting up logging.
logger = logging.getLogger(_parser.prog or __name__)
if _args.log:
    fh = logging.FileHandler(_args.log)
    fh.setFormatter(logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s"))
    logger.addHandler(fh)
    logger.setLevel(_args.loglevel.upper())
    logger.info(f"Started with arguments: {_args}.")
    del fh
