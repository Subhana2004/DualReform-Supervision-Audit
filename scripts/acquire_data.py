"""Fetch only explicitly locked public dataset archives, with streaming size/hash checks."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


def acquire(lock_path="configs/data_sources.json", root="data/raw"):
    lock = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for item in lock["archives"]:
        dest = root / item["filename"]
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() == item["sha256"]:
            print(f"Verified existing {dest.name}")
            continue
        temp = dest.with_suffix(".partial")
        h, size = hashlib.sha256(), 0
        try:
            request = urllib.request.Request(item["url"], headers={"User-Agent": "DualReform-Audit"})
            with urllib.request.urlopen(request, timeout=90) as response, temp.open("wb") as out:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    size += len(chunk)
                    if size > item["size_bytes"]:
                        raise ValueError("Archive exceeds locked size")
                    h.update(chunk)
                    out.write(chunk)
            if size != item["size_bytes"] or h.hexdigest() != item["sha256"]:
                raise ValueError(f"Checksum/size mismatch for {item['filename']}")
            temp.replace(dest)
        finally:
            temp.unlink(missing_ok=True)
        print(f"Downloaded and verified {dest.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", default="configs/data_sources.json")
    parser.add_argument("--root", default="data/raw")
    args = parser.parse_args()
    acquire(args.lock, args.root)
