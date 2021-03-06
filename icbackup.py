import time
from pathlib import Path
from typing import List

import requests
from pyicloud import PyiCloudService
from tqdm import tqdm

import arguments
from functions import DownloadTask, datetime_to_string

logger = arguments.logger
api = PyiCloudService(arguments.username)
if not api.is_trusted_session:
    raise Exception(f"Session has not trusted. Please run \"icloud --username {arguments.username}\" to authenticate.")

album = api.photos.albums[arguments.album] if arguments.album else api.photos.all
dest = Path(arguments.dest).resolve(strict=True)

session = requests.Session()
skip_count = 0
for photo in (main_pbar := tqdm(album.photos, total=len(album), desc=arguments.username, unit="p")):
    if 0 < arguments.skip_limit <= skip_count:
        main_pbar.close()
        logger.info(msg := f"Found {skip_count} repeated images. Download stopped.")
        print(msg)
        break

    download_list: List[DownloadTask] = []
    try:
        file_type = photo._asset_record["fields"]["resJPEGFullFileType"]["value"]    # "public.heic" or "public.jpeg"
        if file_type == "public.heic":
            filename = "photo.heic"
        elif file_type == "public.jpeg":
            filename = "photo.jpg"
        else:
            logger.error(msg := f"Unknown full JPEG type for {photo}: {file_type}.")
            raise RuntimeError(msg)
        t = DownloadTask(photo.id, datetime_to_string(photo.created), filename,
                         photo._asset_record["fields"]["resJPEGFullRes"]["value"]["downloadURL"], suffix="_E")
    except KeyError:
        t = DownloadTask(photo.id, datetime_to_string(photo.created), photo.filename, photo.versions["original"]["url"])
    download_list.append(t)

    # Live photos
    try:
        file_type = photo._master_record["fields"]["resOriginalVidComplFileType"]["value"]
        if file_type == "com.apple.quicktime-movie":
            t = DownloadTask(photo.id, datetime_to_string(photo.created), "live_video.mov",
                             photo._master_record["fields"]["resOriginalVidComplRes"]["value"]["downloadURL"])
            download_list.append(t)
            for t in download_list:
                t.suffix = "_LP"    # Add LP suffix to both the photo and the video.
        else:
            logger.error(msg := f"Unknown live photo type for {photo}: {file_type}.")
            raise RuntimeError(msg)
    except KeyError:
        pass

    # Slow motions
    try:
        if photo._asset_record["fields"]["adjustmentType"]["value"] == "com.apple.video.slomo":
            file_type = photo._asset_record["fields"]["resVidMedFileType"]["value"]
            if file_type == "public.mpeg-4":
                t = DownloadTask(photo.id, datetime_to_string(photo.created), "slow_motion.mp4",
                                 photo._asset_record["fields"]["resVidMedRes"]["value"]["downloadURL"], "_SL")
                download_list.append(t)
            else:
                logger.error(msg := f"Unknown slow motion type for {photo}: {file_type}.")
                raise RuntimeError(msg)
    except KeyError:
        pass

    logger.debug(f"Proceed with {len(download_list)} task(s):")
    for task in download_list:
        logger.debug(f"Task: {t.photo_id=}; {t.created=}; {t.cloud_filename=}; {t.suffix=}.")
        photo_dest_path = task.get_path(dest)
        if photo_dest_path.exists():
            skip_count += 1
            logger.debug(f"Skipping existing file {photo_dest_path.name}; {skip_count=}.")
            continue

        skip_count = 0  # Reset skip count if file does not exist.
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
                        for chunk in req.iter_content(65536):
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
                        session = requests.Session()    # Do not use the old connection for retries.
                    else:
                        raise

logger.info("Stopped.")
