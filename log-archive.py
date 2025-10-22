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


def find_files(root, older_than_days=None):
    threshold = None
    if older_than_days is not None:
        threshold = time.time() - older_than_days * 86400
    files = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.isfile(fp):
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
        final_path = os.path.join(dest_dir, archive_name)
        os.replace(tmp_path, final_path) # atomic rename
        return final_path
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

def append_history(logfile, entry):
    with open(logfile, "a", encoding="utf-8") as fh:
        fh.write(entry +"\n")


def delete_files(files, dry_run=False):
    for f in files:
        if dry_run:
            print("[dry-run] would remove:", f)
        else:
            os.remove(f)


def cleanup_archives(dest_dir, pattern="log_archive_", retain_days=None, dry_run=False):
    if retain_days is None:
        return
    cutoff = time.time() - retain_days * 86400
    for name in os.listdir(dest_dir):
        if not name.startswith(pattern) or not name.endswith(".tar.gz"):
            continue
        fp = os.path.join(dest_dir, name)
        if os.path.getmtime(fp) < cutoff:
            if dry_run:
                print("[dry-run] would delete archive:", fp)
            else:
                os.remove(fp)


def ensure_dir(path, dry_run=False):
    if not os.path.exists(path):
        if dry_run:
            print("[dry-run] would create dir:", path)
        else:
            os.makedirs(path, exist_ok=True)


def main():
    args = parse_args()
    src = os.path.abspath(args.log_dir)
    if not os.path.isdir(src):
        print("Source directory does not exist:", src, file=sys.stderr)
        sys.exit(2)
    dest = args.dest or os.path.join(src, "archives")
    logfile = args.logfile or os.path.join(dest, "archive_history.log")

    ensure_dir(dest, dry_run=args.dry_run)

    files = find_files(src, older_than_days=args.days)
    # avoid archiving the archives dir itself
    files = [f for f in files if not os.path.commonpath([f, dest]) == os.path.abspath(dest)]

    if not files:
        print("No files matched for archiving. Exiting.")
        sys.exit(0)

    archive_name = make_archive_name()
    print("Archiving", len(files), "files to", archive_name)
    archive_path = write_archive(files, src, dest, archive_name, dry_run=args.dry_run)
    if archive_path:
        size = 0
        if not args.dry_run:
            size = os.path.getsize(archive_path)
        entry = f"{datetime.now().isoformat()} | {archive_name} | files={len(files)} | size={size} | src={src}"
        if args.dry_run:
            print("[dry-run] would append history:", entry)
        else:
            append_history(logfile, entry)
        if args.move:
            print("Removing original files...")
            delete_files(files, dry_run=args.dry_run)
        if args.retain:
            cleanup_archives(dest, retain_days=args.retain, dry_run=args.dry_run)
    print("Done.")


if __name__ == "__main__":
    main()
