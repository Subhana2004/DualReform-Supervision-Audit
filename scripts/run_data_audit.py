"""Execute real-data schema and leakage checks; does not measure DualReform accuracy."""
import argparse
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import zipfile

from dualreform_audit.data import assert_disjoint, normalize, split_training, subset
from dualreform_audit.io import digest, environment, git_sha, write_json, write_jsonl


def execute(config_path="configs/phase1_baseline.yaml", output="results/phase1"):
    started, clock = datetime.now(timezone.utc).isoformat(), time.perf_counter()
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))  # JSON is valid YAML 1.2
    if config["stage"] != "data_integrity_only" or config["allow_paid_api"]:
        raise ValueError("This entrypoint only authorizes data integrity, without paid APIs")
    if not isinstance(config["seed"], int) or config["sample_conversations"] < 1:
        raise ValueError("Invalid sampling configuration")
    lock = json.loads(Path(config["data_lock"]).read_text(encoding="utf-8"))
    output, summaries, rows, selected = Path(output), {}, [], []
    archives = []
    for item in lock["archives"]:
        path = Path(config["raw_data_dir"]) / item["filename"]
        if not path.is_file() or digest(path) != item["sha256"]:
            raise ValueError(f"Missing or unverified archive: {path}")
        archives.append({**item, "local_sha256": digest(path)})
        loaded = {}
        with zipfile.ZipFile(path) as archive:
            for split, member in item["members"].items():
                records = json.loads(archive.read(member))
                turns, stats = normalize(records, item["dataset"], split,
                                         incomplete_history="exclude_conversation")
                loaded[split] = turns
                # Check raw provided context independently; differences are reported, not silently fixed.
                key = f"{item['dataset']}/{split}"
                source_by_key = {(f"{split}/{r['Conversation_no']}", r['Turn_no']): r
                                 for r in records}
                stats["context_mismatches"] = sum(
                    source_by_key[(turn.conversation_id, turn.turn_id)].get("Context", []) !=
                    [text for pair in turn.history for text in pair] for turn in turns)
                stats["raw_odd_length_contexts"] = sum(len(r.get("Context", [])) % 2 for r in records)
                # Exclusion details belong in a separate evidence artifact, not aggregate metrics.
                exclusions = stats.pop("excluded_conversations")
                stats["excluded_conversation_count"] = len(exclusions)
                stats["excluded_turn_count"] = sum(r["turns"] for r in exclusions)
                write_json(output / f"{item['dataset']}_{split}_excluded.json", exclusions)
                empty = stats.pop("empty_responses")
                stats["empty_response_count"] = len(empty)
                write_json(output / f"{item['dataset']}_{split}_empty_responses.json", empty)
                summaries[key] = stats
        train, validation = split_training(loaded["train"], config["validation_conversations"],
                                           config["seed"])
        validation = [replace(t, split="validation") for t in validation]
        evaluation = loaded[item["evaluation_split"]]
        assert_disjoint(train, validation, evaluation)
        for partition in (train, validation, evaluation):
                for turn in subset(partition, config["sample_conversations"], config["seed"]):
                    split = turn.split
                    payload = turn.training_input()
                    # Keep full benchmark text private locally; public artifacts contain only hashes.
                    selected.append(payload)
                    import hashlib
                    rows.append({"id": turn.id, "dataset": turn.dataset, "split": split,
                                 "turn_id": turn.turn_id, "history_turns": len(turn.history),
                                 "input_sha256": hashlib.sha256(json.dumps(
                                     payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
                                 "response_present": bool(turn.response.strip()),
                                 "status": "schema_validated", "model_executed": False})
        summaries[item["dataset"] + "/boundaries"] = {
            "train_turns": len(train), "validation_turns": len(validation),
            "evaluation_turns": len(evaluation), "conversation_overlap": 0,
            "duplicate_session_text_overlap": 0, "validation_source": "training only"}
    write_jsonl(Path(config["processed_dir"]) / "sample_inputs.jsonl", selected)
    metrics = {"experiment_type": "real_data_integrity", "retrieval_metrics": None,
               "model_executed": False, "datasets": summaries, "sample_turns": len(rows),
               "seed": config["seed"], "sample_conversations_per_split": config["sample_conversations"],
               "runtime_seconds": time.perf_counter() - clock}
    write_json(output / "metrics.json", metrics)
    write_jsonl(output / "per_example.jsonl", rows)
    write_json(output / "run_manifest.json", {
        "schema_version": 1, "execution_status": "completed_data_integrity_only",
        "timestamp_utc": started, "git_sha": git_sha(), "git_dirty": bool(__import__("subprocess").run(
            ["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()),
        "source_revision": config["source"], "dataset_versions": archives,
        "model_version": None, "model_status": "not_loaded", "gpu_execution": "NOT EXECUTED",
        "parameters": config, "config_sha256": digest(config_path), "environment": environment(),
        "result_paths": [str(output / x) for x in ("metrics.json", "per_example.jsonl")],
        "research_levels": {"0": "partial: adapters and real data only",
                            "1": "blocked: source authenticity, corpus and candidate artifacts",
                            "2": "blocked: trained checkpoint unavailable",
                            "3": "blocked: no approved GPU training environment"}})
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/phase1_baseline.yaml")
    parser.add_argument("--output", default="results/phase1")
    args = parser.parse_args()
    print(json.dumps(execute(args.config, args.output), indent=2))
