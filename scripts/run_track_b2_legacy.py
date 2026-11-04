"""Recheck every historical Track B A case on the larger alternative corpus."""
import json
from pathlib import Path
import sqlite3

from dualreform_audit.io import digest, write_jsonl
from scripts.run_track_b2 import query_text, search


def run():
    root = Path("results/track_b2")
    cfg = json.loads(Path("configs/track_b2.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "corpus_manifest.json").read_text(encoding="utf-8"))
    if digest(cfg["corpus"]["index_path"]) != manifest["index_sha256"]:
        raise ValueError("Index changed")
    original = [json.loads(x) for x in Path("results/track_b/pairs_generated.jsonl").read_text(
        encoding="utf-8").splitlines()]
    cases = []
    for old in original:
        if old["category"] != "A":
            continue
        cases.append({"id": old["id"], "category": "A_legacy",
                      "conversation_id": old["conversation_id"], "turn_id": old["turn_id"],
                      "question": old["question"], "modified_question": old["question"],
                      "history": old["history"],
                      "original_response": old["original_response"],
                      "modified_response": old["modified_response"]})
    con = sqlite3.connect(f"file:{Path(cfg['corpus']['index_path']).as_posix()}?mode=ro",
                          uri=True)
    size = cfg["corpus"]["prefix_sizes"][-1]
    records = []
    for case in cases:
        for method in cfg["retrieval"]["methods"]:
            for arm in ("original", "counterfactual"):
                raw = query_text(case, arm, method)
                expression, hits, selected = search(con, f"wiki_{size}", raw,
                                                    cfg["retrieval"]["top_k"])
                count = con.execute(
                    f"SELECT count(*) FROM wiki_{size} WHERE wiki_{size} MATCH ?",
                    (expression,)).fetchone()[0]
                records.append({"case_id": case["id"], "category": "A_legacy",
                                "conversation_id": case["conversation_id"],
                                "arm": arm, "method": method,
                                "corpus_documents": size, "query_raw": raw,
                                "query_fts": expression, "positive_score_hits": count,
                                "selected_pseudo_references": selected,
                                "ranking_top100": hits})
    con.close()
    write_jsonl(root / "legacy_rankings.jsonl", records)
    return len(records)


if __name__ == "__main__":
    print(run())
