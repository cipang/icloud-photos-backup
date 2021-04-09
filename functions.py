import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Account:
    username: str
    dest: str
    album: Optional[str]
    repeat_limit: int


@dataclass()
class DownloadTask:
    photo_id: str
    create_date: datetime
    cloud_filename: str
    url: str
    suffix: str = ""

    def get_path(self, dest: Path) -> Path:
        photo_sha1_id = sha1_id(self.photo_id)
        date_part = self.create_date.strftime("%Y%m%d_%H%M%S")
        ext = Path(self.cloud_filename).suffix.lower()
        return dest / f"{date_part}_{photo_sha1_id}{self.suffix}{ext}"


def sha1_id(s: str, length=7) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:length]


def get_account() -> Account:
    if len(sys.argv) < 2 or not sys.argv[1].isnumeric():
        raise Exception(f"Please specify a valid account index.")
    selected_account = int(sys.argv[1])
    with open("accounts.json", "r") as accounts_fp:
        account = json.load(accounts_fp)[selected_account]
        return Account(username=account["username"], dest=account["dest"], album=account["album"] or None,
                       repeat_limit=int(account["repeat_limit"]))
