import json
import sys
from pathlib import Path

import requests
from pyicloud import PyiCloudService
from tqdm import tqdm

from functions import get_path

try:
    selected_account = int(sys.argv[1])
except ValueError:
    print(f"Invalid account index {sys.argv[1]}.")
    sys.exit(1)
except IndexError:
    print(f"Please specify account index.")
    sys.exit(2)

with open("accounts.json", "r") as accounts_fp:
    account = json.load(accounts_fp)[selected_account]

api = PyiCloudService(account["username"])
album = api.photos.albums[account["album"]] if account["album"] else api.photos.all
dest = Path(account["dest"]).resolve()

session = requests.Session()
for photo in tqdm(album.photos, total=len(album), desc=account["username"], unit="p"):
    try:
        filename = photo._asset_record["fields"]["resJPEGFullFileType"]["value"]    # "public.heic" or "public.jpeg"
        photo_dest_path = get_path(photo.id, photo.created, filename, dest, "_E")
        url = photo._asset_record["fields"]["resJPEGFullRes"]["value"]["downloadURL"]
    except KeyError:
        photo_dest_path = get_path(photo.id, photo.created, photo.filename, dest)
        url = photo.versions["original"]["url"]

    if photo_dest_path.exists():
        continue

    with session.get(url, stream=True) as req:
        req.raise_for_status()
        with photo_dest_path.open("wb") as fp:
            pbar = tqdm(total=int(req.headers["Content-Length"]), desc=photo_dest_path.name,
                        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}")
            for chunk in req.iter_content(32768):
                fp.write(chunk)
                pbar.update(len(chunk))
            pbar.close()
