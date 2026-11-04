"""Generate predeclared, gold-blind counterfactual pairs and validate manual labels."""
import argparse
import json
from pathlib import Path
import zipfile

from dualreform_audit.data import assert_disjoint, normalize, split_training
from dualreform_audit.io import digest, write_jsonl
from dualreform_audit.track_b import validate_pair


def load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


def generate(config_path, cases_path, labels_path, output):
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    if digest(config["dataset_archive"]) != config["dataset_sha256"]:
        raise ValueError("Missing or changed benchmark archive")
    with zipfile.ZipFile(config["dataset_archive"]) as archive:
        raw = json.loads(archive.read(config["dataset_member"]))
    turns, _ = normalize(raw, "topiocqa", "train")
    train, validation = split_training(turns, 8, config["seed"])
    assert_disjoint(train, validation)
    by_key = {(t.conversation_id, t.turn_id): t for t in train}
    cases = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    labels = json.loads(Path(labels_path).read_text(encoding="utf-8"))["cases"]
    if len({c["id"] for c in cases}) != len(cases) or set(labels) != {c["id"] for c in cases}:
        raise ValueError("Case/annotation alignment failure")
    docs = load_jsonl(config["corpus_path"])
    title_to_id = {d["title"]: d["doc_id"] for d in docs}
    pairs = []
    for spec in cases:
        key = (f"train/{spec['conversation_no']}", spec["turn_no"])
        turn = by_key.get(key)
        followup = by_key.get((key[0], spec["followup_turn_no"]))
        if turn is None or followup is None:
            raise ValueError(f"Case is missing or in validation split: {spec['id']}")
        pairs.append(validate_pair(spec, turn, followup, labels[spec["id"]], title_to_id))
    write_jsonl(output, pairs)
    return pairs


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", default="configs/track_b.yaml")
    p.add_argument("--cases", default="configs/track_b_cases.json")
    p.add_argument("--labels", default="configs/track_b_manual_labels.json")
    p.add_argument("--output", default="results/track_b/pairs_generated.jsonl")
    a = p.parse_args()
    print(json.dumps({"pairs": len(generate(a.config, a.cases, a.labels, a.output))}))
