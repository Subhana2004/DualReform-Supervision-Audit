import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from scripts.run_data_audit import execute


def test_real_entrypoint_with_fixture_archives_preserves_partition_boundaries(tmp_path, monkeypatch):
    """Synthetic engineering integration, not a benchmark or accuracy experiment."""
    monkeypatch.chdir(tmp_path)
    raw = tmp_path / "raw"
    raw.mkdir()
    records = []
    for cid in (1, 2, 3):
        records.append({"Conversation_no": cid, "Turn_no": 1,
                        "Question": f"train q{cid}", "Answer": f"train a{cid}", "Context": []})
    evaluation = [{"Conversation_no": 1, "Turn_no": 1, "Question": "eval q",
                   "Answer": "eval a", "Context": [], "Rationale": "GOLD_NEVER_IN_INPUT"}]
    archive_path = raw / "fixture.zip"
    with zipfile.ZipFile(archive_path, "w") as z:
        z.writestr("train.json", json.dumps(records))
        z.writestr("dev.json", json.dumps(evaluation))
    lock = {"archives": [{"dataset": "topiocqa", "filename": "fixture.zip",
             "sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
             "members": {"train": "train.json", "dev": "dev.json"}, "evaluation_split": "dev"}]}
    Path("lock.json").write_text(json.dumps(lock))
    config = {"stage": "data_integrity_only", "allow_paid_api": False, "seed": 42,
              "sample_conversations": 1, "validation_conversations": 1, "data_lock": "lock.json",
              "raw_data_dir": "raw", "processed_dir": "projected", "source": {"official": False}}
    Path("config.yaml").write_text(json.dumps(config))
    result = execute("config.yaml", "result")
    assert result["sample_turns"] == 3
    inputs = [json.loads(x) for x in Path("projected/sample_inputs.jsonl").read_text().splitlines()]
    assert len({x["conversation_id"] for x in inputs}) == 3
    assert {x["split"] for x in inputs} == {"train", "validation", "dev"}
    assert "GOLD_NEVER_IN_INPUT" not in json.dumps(inputs)
    manifest = json.loads(Path("result/run_manifest.json").read_text())
    assert manifest["model_status"] == "not_loaded"
    assert result["retrieval_metrics"] is None
    assert len(Path("result/per_example.jsonl").read_text().splitlines()) == 3
    config["allow_paid_api"] = True
    Path("config.yaml").write_text(json.dumps(config))
    with pytest.raises(ValueError, match="only authorizes"):
        execute("config.yaml", "bad-result")


def test_bad_archive_hash_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("archive.zip").write_bytes(b"not trusted")
    Path("lock.json").write_text(json.dumps({"archives": [{"filename": "archive.zip", "sha256": "wrong"}]}))
    Path("config.yaml").write_text(json.dumps({"stage": "data_integrity_only", "seed": 42,
        "sample_conversations": 1, "allow_paid_api": False, "data_lock": "lock.json", "raw_data_dir": "."}))
    with pytest.raises(ValueError, match="unverified archive"):
        execute("config.yaml", "output")
