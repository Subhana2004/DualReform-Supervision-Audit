"""Run bounded project checks and retain exact command/output/return-code evidence."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

from dualreform_audit.io import git_sha, write_json


def verify():
    logs = Path("results/verification")
    logs.mkdir(parents=True, exist_ok=True)
    commands = [
        ("pytest", [sys.executable, "-m", "pytest", "-q"]),
        ("ruff", [sys.executable, "-m", "ruff", "check", "src", "scripts", "paper_reimplementation", "tests"]),
        ("compile", [sys.executable, "-m", "compileall", "-q", "src", "scripts", "paper_reimplementation"]),
        ("notebook_cpu_setup", [sys.executable, "scripts/validate_notebook.py", "--execute-cpu"]),
    ]
    records = []
    for name, command in commands:
        result = subprocess.run(command, capture_output=True, text=True)
        (logs / f"{name}.log").write_text(result.stdout + "\nSTDERR\n" + result.stderr, encoding="utf-8")
        records.append({"name": name, "command": command, "returncode": result.returncode,
                        "log": str(logs / f"{name}.log")})
        print(name, result.returncode, result.stdout[-250:])
    report = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "git_sha": git_sha(),
              "checks": records, "all_passed": all(r["returncode"] == 0 for r in records),
              "scope": "engineering verification; no GPU or model accuracy claim"}
    write_json(logs / "verification.json", report)
    print(json.dumps(report, indent=2))
    return report["all_passed"]


if __name__ == "__main__":
    raise SystemExit(0 if verify() else 1)
