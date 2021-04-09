import hashlib
from datetime import datetime
from pathlib import Path


def sha1_id(s: str, length=7) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:length]


def get_path(photo_id: str, create_date: datetime, filename: str, dest: Path) -> Path:
    photo_sha1_id = sha1_id(photo_id)
    date_part = create_date.strftime("%Y%m%d_%H%M%S")
    ext = Path(filename).suffix.lower()
    return dest / f"{date_part}_{photo_sha1_id}{ext}"
