import hashlib
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
    created: str
    cloud_filename: str
    url: str
    suffix: str = ""

    def get_path(self, dest: Path) -> Path:
        photo_sha1_id = sha1_id(self.photo_id)
        ext = Path(self.cloud_filename).suffix.lower()
        return dest / f"{self.created}_{photo_sha1_id}{self.suffix}{ext}"


def sha1_id(s: str, length=7) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:length]


def datetime_to_string(d: datetime) -> str:
    return d.strftime("%Y%m%d_%H%M%S")
