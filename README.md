# iCloud Photos Backup Python Script

Backup iCloud Photos to a local directory. Supports photos, videos, live photos and slow motion videos.

## Usage

Note: For first time users, please run ``icloud --username your_apple_id`` to login first.

``python icbackup.py [-h] [-a ALBUM] [-l SKIP_LIMIT] [--log LOG] [--loglevel LOG_LEVEL] your_apple_id dest``

## Requirements

* Python 3.10
* pyicloud
* tqdm
