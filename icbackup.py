from pathlib import Path
from typing import List

import requests
from pyicloud import PyiCloudService
from tqdm import tqdm

from functions import get_account, DownloadTask

account = get_account()
api = PyiCloudService(account.username)
if not api.is_trusted_session:
    raise Exception("Session has not trusted. Please run icloud --username (email) to authenticate.")

album = api.photos.albums[account.album] if account.album else api.photos.all
dest = Path(account.dest).resolve()

session = requests.Session()
repeat_count = 0
for photo in tqdm(album.photos, total=len(album), desc=account.username, unit="p"):
    if repeat_count >= account.repeat_limit:
        print(f"Found {repeat_count} repeated images. Download stopped.")
        break

    download_list: List[DownloadTask] = []
    try:
        full_type = photo._asset_record["fields"]["resJPEGFullFileType"]["value"]    # "public.heic" or "public.jpeg"
        if full_type == "public.heic":
            filename = "photo.heic"
        elif full_type == "public.jpeg":
            filename = "photo.jpg"
        else:
            raise RuntimeError(f"Unknown full JPEG type for {photo}: {full_type}.")
        t = DownloadTask(photo.id, photo.created, filename,
                         photo._asset_record["fields"]["resJPEGFullRes"]["value"]["downloadURL"], suffix="_E")
    except KeyError:
        t = DownloadTask(photo.id, photo.created, photo.filename, photo.versions["original"]["url"])
    download_list.append(t)

    # Live photos
    try:
        if photo._master_record["fields"]["resOriginalVidComplFileType"]["value"] == "com.apple.quicktime-movie":
            t = DownloadTask(photo.id, photo.created, "live_video.mov",
                             photo._master_record["fields"]["resOriginalVidComplRes"]["value"]["downloadURL"])
            download_list.append(t)
            for t in download_list:
                t.suffix = "_LP"
    except KeyError:
        pass

    for task in download_list:
        photo_dest_path = task.get_path(dest)
        if photo_dest_path.exists():
            repeat_count += 1
            continue

        repeat_count = 0  # Reset repeat count if file does not exist.
        with session.get(task.url, stream=True) as req:
            req.raise_for_status()
            pbar = tqdm(total=int(req.headers["Content-Length"]), desc=photo_dest_path.name, leave=False,
                        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}")
            with photo_dest_path.open("wb") as fp, pbar:
                for chunk in req.iter_content(32768):
                    fp.write(chunk)
                    pbar.update(len(chunk))
