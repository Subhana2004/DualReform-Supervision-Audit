"""Small, explicit artifacts and environment recording without credential collection."""
import hashlib
import importlib.metadata
import json
import platform
import subprocess
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def git_sha():
    proc = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else None


def environment():
    versions = {}
    for name in ("torch", "transformers", "pyserini", "pytrec-eval", "pytest", "ruff"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    gpu = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Command nvidia-smi -ErrorAction SilentlyContinue"],
        capture_output=True, text=True,
    ) if platform.system() == "Windows" else None
    return {"python": platform.python_version(), "platform": platform.platform(),
            "packages": versions, "nvidia_smi_found": bool(gpu and gpu.stdout.strip()),
            "cuda": None, "cuda_note": "Not probed through PyTorch when not installed"}
