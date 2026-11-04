"""Select whole training conversations before retrieval, using only Q/A inputs."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import zipfile

from dualreform_audit.data import assert_disjoint, normalize, split_training
from dualreform_audit.io import digest, write_json, write_jsonl


PERSON = re.compile(r"^[A-Z][a-z]+(?: [A-Z][a-z]+){1,3}$")


def select(config_path="configs/track_b2.json", out="results/track_b2"):
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    rule = config["benchmark"]
    if digest(rule["path"]) != rule["sha256"]:
        raise ValueError("Missing or changed TopiOCQA archive")
    with zipfile.ZipFile(rule["path"]) as stream:
        records = json.loads(stream.read(rule["member"]))
    turns, _ = normalize(records, "topiocqa", "train")
    train, validation = split_training(turns, rule["validation_conversations"],
                                       rule["validation_seed"])
    assert_disjoint(train, validation)
    by_conversation = {}
    for turn in train:
        by_conversation.setdefault(turn.conversation_id, []).append(turn)
    ordered = sorted(by_conversation, key=lambda cid: (
        hashlib.sha256(f"{rule['study_seed']}:{cid}".encode()).hexdigest(), cid))
    pairs, scanned = [], 0
    for cid in ordered:
        scanned += 1
        eligible = next((t for t in sorted(by_conversation[cid], key=lambda t: t.turn_id)
                         if re.match(r"^who\b", t.query.strip(), flags=re.I)
                         and PERSON.fullmatch(t.response.strip())
                         and t.response not in config["replacement_pool"]), None)
        if eligible is None:
            continue
        index = int(hashlib.sha256(f"{rule['study_seed']}:{eligible.id}".encode()).hexdigest(), 16)
        replacement = config["replacement_pool"][index % len(config["replacement_pool"])]
        if replacement == eligible.response:
            raise ValueError("Replacement pool collision")
        key = len(pairs) // 2 + 1
        base = {"conversation_id": eligible.conversation_id, "turn_id": eligible.turn_id,
                "dataset": "topiocqa", "split": "train", "question": eligible.query,
                "history": eligible.history, "original_response": eligible.response,
                "current_intent_changed": False, "source": "deterministic TopiOCQA training sample"}
        pairs.append({**base, "id": f"A_{key:03d}", "category": "A",
                      "modified_question": eligible.query,
                      "modified_response": replacement,
                      "intervention": "replace one person-name answer with a fixed-pool person name"})
        pairs.append({**base, "id": f"D_{key:03d}", "category": "D",
                      "modified_question": eligible.query,
                      "modified_response": eligible.response + ".",
                      "intervention": "append terminal period only"})
        if key == rule["first_eligible_conversations"]:
            break
    if len(pairs) != 2 * rule["first_eligible_conversations"]:
        raise ValueError("Not enough eligible conversations")
    output = Path(out)
    write_jsonl(output / "preregistered_pairs.jsonl", pairs)
    manifest = {"status": "preregistered_before_track_b2_retrieval",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "benchmark_sha256": rule["sha256"], "config_sha256": digest(config_path),
                "pairs_sha256": digest(output / "preregistered_pairs.jsonl"),
                "conversations_scanned": scanned,
                "independent_conversations": rule["first_eligible_conversations"],
                "pairs": len(pairs), "selection_uses_gold_fields": False,
                "future_turns_used": False,
                "sampling_rule": rule["eligibility"]}
    write_json(output / "preregistration.json", manifest)
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", default="configs/track_b2.json")
    p.add_argument("--output", default="results/track_b2")
    a = p.parse_args()
    print(json.dumps(select(a.config, a.output), indent=2))
