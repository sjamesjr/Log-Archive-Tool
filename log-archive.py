#!/usr/bin/env python3

"""
log-archive - simple tool to archive logs into timestamped tar.gz
Usage:
log-archive <log-dir> [--days DAYS] [--dest DEST] [--move] [--retain RETAIN_DAYS] [--dry-run]
"""

import argparse
import os
import tarfile
import tempfile
import time
from datetime import datetime, timedelta
import shutil
import sys


def parse_args():
    p = argparse.ArgumentParser(description="Archive log files into a timestamped tar.gz")
    p.add_argument("lod_dir", help="Directory containing logs to archive")
    p.add_argument("--days", type=int, default=None,
                   help="Only include files older than DAYS (recommended)")
    p.add_argument("--dest", default=None, help="Destination directory for archives")
    p.add_argument("--move", action="store_true", help="Remove original files after successful archive")
    p.add_argument("--retain", type=int, default=None, help="Delete archives older than RETAIN days")
    p.add_argument("--logfile", default=None, help="Path to archive history log file")
    return p.parse_args()


def find_files(root, older_than_days=None)
    threshold = None
    if older_than_days is not None
        threshold = time.time() - older_than_days * 86400
    files = []
    for dirpath, _, filenames in os.walk(root)
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.isfile(fp)
                continue
            if threshold and os.path.getmtime(fp) > threshold:
                continue
            files.append(fp)
    return files


def make_archive_name():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"logs_archive_{ts}.tar.gz"


def write_archive(files, src_root, dest_dir, archive_name, dry_run=False):
    if not files:
        return None
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=archive_name + ".", dir=dest_dir)
    os.close(tmp_fd)
    if dry_run:
        os.remove(tmp_path)
        return os.path.join(dest_dir,archive_name)
    try:
        with tarfile.open(tmp_path, "w:gz") as tar:
            for f in files:
                arcname = os.path.relpath(f, start=src_root)
                tar.add(f,arcname=arcname)
