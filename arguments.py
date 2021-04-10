import argparse
import logging

_parser = argparse.ArgumentParser(description="Backup iCloud Photos to a local directory.")
_parser.add_argument("account", help="index of the selected iCloud account defined in the account settings", type=int)
_parser.add_argument("-a", help="path to the account settings (accounts.json)", default="accounts.json", metavar="file")
_parser.add_argument("--log", help="enable logging and specify the location of the log file")
_parser.add_argument("--loglevel", help="logging level", choices=["debug", "info", "warning", "error", "fatal"],
                     default="info")

_args = _parser.parse_args()

selected_account: int = _args.account
account_file: str = _args.a

# Set up logging.
logger = logging.getLogger(_parser.prog or __name__)
if _args.log:
    fh = logging.FileHandler(_args.log)
    fh.setFormatter(logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s"))
    logger.addHandler(fh)
    logger.setLevel(_args.loglevel.upper())
    del fh
