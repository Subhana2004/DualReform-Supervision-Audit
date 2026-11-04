"""Execute paper-derived iteration-zero and question-based FTS5 diagnostics.

This is an independent retrieval experiment, not official DualReform or
TopiOCQA BM25 reproduction. No evaluation label enters a query.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import re
import sqlite3
import time

from dualreform_audit.io import digest, environment, git_sha, write_json, write_jsonl


STOP = {"a", "an", "and", "are", "as", "at", "be", "by", "did", "do", "does",
        "for", "from", "he", "her", "his", "how", "i", "in", "is", "it", "its",
        "of", "on", "or", "she", "the", "them", "they", "this", "to", "was",
        "were", "what", "when", "where", "which", "who", "with"}


def load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


def query_text(case, arm, method):
    question = case["question"] if arm == "original" else case["modified_question"]
    response = case["original_response"] if arm == "original" else case["modified_response"]
    previous_questions = " ".join(pair[0] for pair in case["history"])
    if method == "response_only":
        return response
    if method == "question_anchored":
        return previous_questions + " " + question + " " + response
    if method == "question_only":
        return previous_questions + " " + question
    raise ValueError(method)


def fts_query(raw):
    words = re.findall(r"[^\W_]+", raw.casefold(), flags=re.UNICODE)
    unique = list(dict.fromkeys(word for word in words if word not in STOP and len(word) > 1))
    if not unique:
        unique = list(dict.fromkeys(word for word in words if len(word) > 1))
    if not unique:
        raise ValueError("No query terms")
    return " OR ".join('"' + word + '"' for word in unique)


def search(con, table, raw, top_k):
    expression = fts_query(raw)
    rows = con.execute(f"SELECT doc_id,title,body,bm25({table}) AS score "
                       f"FROM {table} WHERE {table} MATCH ? "
                       "ORDER BY score ASC, doc_id ASC LIMIT ?",
                       (expression, top_k)).fetchall()
    hits = [{"rank": rank, "doc_id": doc_id, "title": title,
             "score": -float(score), "snippet": body[:240]}
            for rank, (doc_id, title, body, score) in enumerate(rows, 1)]
    if any(hit["score"] <= 0 for hit in hits):
        raise ValueError("Nonpositive score among FTS5 matches")
    selected = [{"doc_id": row[0], "title": row[1], "text": row[2],
                 "score": -float(row[3]), "rank": rank}
                for rank, row in enumerate(rows[:3], 1)]
    return expression, hits, selected


def run(config_path="configs/track_b2.json", out="results/track_b2"):
    started = datetime.now(timezone.utc).isoformat()
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
    root = Path(out)
    prereg = json.loads((root / "preregistration.json").read_text(encoding="utf-8"))
    if digest(root / "preregistered_pairs.jsonl") != prereg["pairs_sha256"]:
        raise ValueError("Preregistered cases changed")
    corpus_manifest = json.loads((root / "corpus_manifest.json").read_text(encoding="utf-8"))
    index_path = Path(cfg["corpus"]["index_path"])
    if not index_path.exists() or digest(index_path) != corpus_manifest["index_sha256"]:
        raise ValueError("Indexed corpus missing or changed")
    cases = load_jsonl(root / "preregistered_pairs.jsonl") + load_jsonl(
        root / "supplementary_cases.jsonl")
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate case ID")
    con = sqlite3.connect(f"file:{index_path.as_posix()}?mode=ro", uri=True)
    full = cfg["corpus"]["prefix_sizes"][-1]
    top_k = cfg["retrieval"]["top_k"]
    clock = time.perf_counter()
    records = []
    for case in cases:
        for size in cfg["corpus"]["prefix_sizes"]:
            # Sensitivity analyses share the same source order and parameters.
            # B/C probes use the complete corpus only; smaller prefixes are
            # assessed on the conversation-disjoint systematic sample.
            if size != full and case["category"] in ("B", "C"):
                continue
            table = f"wiki_{size}"
            methods = cfg["retrieval"]["methods"] if size == full else (
                "response_only", "question_anchored")
            for method in methods:
                for arm in ("original", "counterfactual"):
                    raw = query_text(case, arm, method)
                    expression, hits, selected = search(con, table, raw, top_k)
                    # Full-query match count records coverage beyond top_k.
                    positive_hits = con.execute(
                        f"SELECT count(*) FROM {table} WHERE {table} MATCH ?",
                        (expression,)).fetchone()[0]
                    if positive_hits < len(hits):
                        raise AssertionError("FTS hit count below ranking length")
                    records.append({"case_id": case["id"], "category": case["category"],
                                    "conversation_id": case["conversation_id"],
                                    "turn_id": case["turn_id"], "arm": arm,
                                    "method": method, "corpus_documents": size,
                                    "current_question": case["question"] if arm == "original"
                                    else case["modified_question"],
                                    "observed_response": case["original_response"] if arm == "original"
                                    else case["modified_response"],
                                    "query_raw": raw, "query_fts": expression,
                                    "positive_score_hits": positive_hits,
                                    "complete_top3": len(selected) == 3,
                                    "selected_pseudo_references": selected,
                                    "ranking_top100": hits})
    con.close()
    # Reopen and repeat one deterministic query after all retrieval work.
    con = sqlite3.connect(f"file:{index_path.as_posix()}?mode=ro", uri=True)
    first = records[0]
    _, repeat, _ = search(con, f"wiki_{first['corpus_documents']}",
                          first["query_raw"], top_k)
    con.close()
    if repeat != first["ranking_top100"]:
        raise AssertionError("Repeated retrieval changed scores or order")
    by_key = {(r["case_id"], r["corpus_documents"], r["method"], r["arm"]): r
              for r in records}
    comparisons = []
    for case in cases:
        for size in cfg["corpus"]["prefix_sizes"]:
            if size != full and case["category"] in ("B", "C"):
                continue
            methods = cfg["retrieval"]["methods"] if size == full else (
                "response_only", "question_anchored")
            for method in methods:
                left, right = (by_key[(case["id"], size, method, arm)]
                               for arm in ("original", "counterfactual"))
                l3 = [r["doc_id"] for r in left["selected_pseudo_references"]]
                r3 = [r["doc_id"] for r in right["selected_pseudo_references"]]
                union = set(l3) | set(r3)
                comparisons.append({"case_id": case["id"], "category": case["category"],
                                    "conversation_id": case["conversation_id"],
                                    "corpus_documents": size, "method": method,
                                    "top3_changed": l3 != r3,
                                    "top3_jaccard": len(set(l3) & set(r3)) / len(union)
                                    if union else None,
                                    "original_top3": l3, "counterfactual_top3": r3,
                                    "original_positive_hits": left["positive_score_hits"],
                                    "counterfactual_positive_hits": right["positive_score_hits"]})
    write_jsonl(root / "rankings.jsonl", records)
    write_jsonl(root / "comparisons.jsonl", comparisons)
    counts = Counter((r["category"], r["method"], r["corpus_documents"],
                      r["top3_changed"]) for r in comparisons)
    metrics = {"status": "retrieval_executed_qrels_pending_independent_review",
               "official_baseline_reproduced": False,
               "complete_corpus_documents": full,
               "independent_sampled_conversations": prereg["independent_conversations"],
               "sampled_pairs": len([c for c in cases if c["category"] in ("A", "D")]),
               "supplementary_probes": len([c for c in cases if c["category"] in ("B", "C")]),
               "retrieval_records": len(records), "comparisons": len(comparisons),
               "incomplete_top3_records": sum(not r["complete_top3"] for r in records),
               "change_counts": [{"category": k[0], "method": k[1], "corpus_documents": k[2],
                                  "top3_changed": k[3], "count": v}
                                 for k, v in sorted(counts.items())],
               "relevance_recall_at_k": None, "pseudo_reference_support_quality": None,
               "harmful_factual_changes": None,
               "reason_unscored": "No independent blinded passage qrels or fact verification",
               "retrieval_seconds": time.perf_counter() - clock}
    write_json(root / "metrics.json", metrics)
    write_json(root / "run_manifest.json", {
        "status": "executed", "started_utc": started, "git_sha": git_sha(),
        "config_sha256": digest(config_path),
        "preregistered_pairs_sha256": prereg["pairs_sha256"],
        "supplementary_cases_sha256": digest(root / "supplementary_cases.jsonl"),
        "corpus_manifest_sha256": digest(root / "corpus_manifest.json"),
        "index_sha256": corpus_manifest["index_sha256"],
        "rankings_sha256": digest(root / "rankings.jsonl"),
        "comparisons_sha256": digest(root / "comparisons.jsonl"),
        "source_type": "independent paper-derived diagnostic",
        "official_baseline_reproduced": False, "gpu_execution": "NOT EXECUTED",
        "retrieval_engine": cfg["retrieval"], "environment": environment(),
        "platform": platform.platform(), "runtime_seconds": metrics["retrieval_seconds"]})
    return metrics


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", default="configs/track_b2.json")
    p.add_argument("--output", default="results/track_b2")
    a = p.parse_args()
    print(json.dumps(run(a.config, a.output), indent=2))
