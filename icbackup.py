import time
from pathlib import Path
from typing import List

import requests
from pyicloud import PyiCloudService
from tqdm import tqdm

import arguments
from functions import get_account, DownloadTask, datetime_to_string

logger = arguments.logger
account = get_account(arguments.account_file, arguments.selected_account)
api = PyiCloudService(account.username)
if not api.is_trusted_session:
    raise Exception("Session has not trusted. Please run \"icloud --username email\" to authenticate.")

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
        t = DownloadTask(photo.id, datetime_to_string(photo.created), filename,
                         photo._asset_record["fields"]["resJPEGFullRes"]["value"]["downloadURL"], suffix="_E")
    except KeyError:
        t = DownloadTask(photo.id, datetime_to_string(photo.created), photo.filename, photo.versions["original"]["url"])
    download_list.append(t)

    # Live photos
    try:
        if photo._master_record["fields"]["resOriginalVidComplFileType"]["value"] == "com.apple.quicktime-movie":
            t = DownloadTask(photo.id, datetime_to_string(photo.created), "live_video.mov",
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
            logger.debug(f"Skipping existing file {photo_dest_path.name}; {repeat_count=}.")
            continue

        repeat_count = 0  # Reset repeat count if file does not exist.
        attempts = 0    # Record how many attempts it has tried.
        ok = False
        while not ok:
            attempts += 1
            with session.get(task.url, stream=True) as req:
                try:
                    req.raise_for_status()
                    pbar = tqdm(total=int(req.headers["content-length"]), desc=photo_dest_path.name, leave=False,
                                bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}")
                    with photo_dest_path.open("wb") as fp, pbar:
                        for chunk in req.iter_content(32768):
                            fp.write(chunk)
                            pbar.update(len(chunk))
                    ok = True
                except (requests.exceptions.HTTPError, ConnectionError):
                    logger.exception(f"Attempt #{attempts} for {task} failed.")
                    if attempts <= 3:
                        if photo_dest_path.exists():
                            logger.info(f"Removing partial download {photo_dest_path.name}...")
                            photo_dest_path.unlink()
                        logger.debug("Waiting for retry...")
                        time.sleep(20)
                        session = requests.Session()
                    else:
                        raise
