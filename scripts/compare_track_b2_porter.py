"""Exploratory same-corpus FTS5 unicode61 versus Porter-tokenizer sensitivity."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import time

import pyarrow.parquet as pq

from dualreform_audit.io import digest, write_json, write_jsonl
from scripts.run_track_b2 import load_jsonl, query_text, search


def run():
    root = Path("results/track_b2")
    cfg = json.loads(Path("configs/track_b2.json").read_text(encoding="utf-8"))
    source = cfg["corpus"]
    if digest(source["local_path"]) != source["sha256"]:
        raise ValueError("Source corpus differs")
    index_path = Path("work/track_b2/simplewiki_fts5_porter.sqlite")
    started = datetime.now(timezone.utc).isoformat()
    clock = time.perf_counter()
    if not index_path.exists():
        con = sqlite3.connect(index_path)
        con.execute("PRAGMA journal_mode=OFF")
        con.execute("PRAGMA synchronous=OFF")
        con.execute("PRAGMA cache_size=-8192")
        con.execute("CREATE VIRTUAL TABLE wiki_241787 USING fts5("
                    "doc_id UNINDEXED,title,body,tokenize='porter unicode61')")
        count = 0
        for batch in pq.ParquetFile(source["local_path"]).iter_batches(
                batch_size=128, columns=["id", "title", "text"]):
            for row in batch.to_pylist():
                if not row["id"] or not row["title"] or not row["text"]:
                    raise ValueError("Unexpected empty source row")
                con.execute("INSERT INTO wiki_241787 VALUES (?,?,?)",
                            ("simplewiki:" + str(row["id"]), row["title"], row["text"]))
                count += 1
            if count % 1024 == 0:
                con.commit()
        con.commit()
        con.execute("INSERT INTO wiki_241787(wiki_241787) VALUES ('integrity-check')")
        con.commit()
        if count != source["prefix_sizes"][-1] or con.execute(
                "PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Porter index integrity failure")
        con.close()
    con = sqlite3.connect(f"file:{index_path.as_posix()}?mode=ro", uri=True)
    count = con.execute("SELECT count(*) FROM wiki_241787").fetchone()[0]
    if count != source["prefix_sizes"][-1]:
        raise ValueError("Porter index count differs")
    porter_sha = digest(index_path)
    sample = [x for x in load_jsonl(root / "preregistered_pairs.jsonl")
              if x["category"] == "A"]
    old = [x for x in load_jsonl("results/track_b/pairs_generated.jsonl")
           if x["category"] == "A"]
    legacy = [{"id": x["id"], "question": x["question"],
               "modified_question": x["question"], "history": x["history"],
               "original_response": x["original_response"],
               "modified_response": x["modified_response"]} for x in old]
    records = []
    for case in sample + legacy:
        for method in ("response_only", "question_anchored"):
            for arm in ("original", "counterfactual"):
                raw = query_text(case, arm, method)
                expression, hits, selected = search(con, "wiki_241787", raw, 100)
                records.append({"case_id": case["id"], "method": method,
                                "arm": arm, "query_raw": raw,
                                "query_fts": expression,
                                "ranking_top100": hits,
                                "selected_pseudo_references": selected})
    con.close()
    write_jsonl(root / "porter_rankings.jsonl", records)
    unicode = {(x["case_id"], x["method"], x["arm"]): x for x in (
        load_jsonl(root / "rankings.jsonl") + load_jsonl(root / "legacy_rankings.jsonl"))
        if x["corpus_documents"] == count and x["method"] in (
            "response_only", "question_anchored")}
    detail = []
    for row in records:
        key = row["case_id"], row["method"], row["arm"]
        left = [x["doc_id"] for x in unicode[key]["selected_pseudo_references"]]
        right = [x["doc_id"] for x in row["selected_pseudo_references"]]
        detail.append({"case_id": key[0], "method": key[1], "arm": key[2],
                       "unicode61_top3": left, "porter_top3": right,
                       "top3_set_changed_by_analyzer": set(left) != set(right)})
    write_json(root / "porter_comparison.json", {
        "status": "exploratory_post_preregistration_analyzer_sensitivity",
        "same_corpus_documents": count, "same_sqlite_bm25_k1": 1.2,
        "same_sqlite_bm25_b": 0.75, "analyzers": ["unicode61", "porter unicode61"],
        "sampled_independent_conversations": 30, "historical_cases": 4,
        "records": len(records),
        "top3_set_differs_between_analyzers": sum(
            x["top3_set_changed_by_analyzer"] for x in detail),
        "detail": detail})
    write_json(root / "porter_manifest.json", {
        "status": "executed", "started_utc": started, "corpus_sha256": source["sha256"],
        "index_sha256": porter_sha, "index_size_bytes": index_path.stat().st_size,
        "document_count": count, "tokenizer": "porter unicode61",
        "rankings_sha256": digest(root / "porter_rankings.jsonl"),
        "runtime_seconds": time.perf_counter() - clock,
        "index_committed": False, "gpu_execution": "NOT EXECUTED"})
    return count, len(records)


if __name__ == "__main__":
    print(run())
