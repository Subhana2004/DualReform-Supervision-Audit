"""Fetch the pinned Wikimedia Parquet shard into ignored work/, then verify SHA-256."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen


def acquire(config_path):
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))["corpus"]
    path = Path(config["local_path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        if path.stat().st_size == config["size_bytes"] and hash_file(path) == config["sha256"]:
            return path
        raise ValueError("Existing corpus differs from pinned size or SHA-256")
    partial = path.with_suffix(path.suffix + ".partial")
    request = Request(config["url"], headers={"User-Agent": "DualReform-B2/1.0"})
    try:
        with urlopen(request, timeout=60) as response, partial.open("wb") as target:
            while chunk := response.read(1024 * 1024):
                target.write(chunk)
        if partial.stat().st_size != config["size_bytes"] or hash_file(partial) != config["sha256"]:
            raise ValueError("Downloaded corpus size or SHA-256 mismatch")
        partial.replace(path)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return path


def hash_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", default="configs/track_b2.json")
    print(acquire(p.parse_args().config))
