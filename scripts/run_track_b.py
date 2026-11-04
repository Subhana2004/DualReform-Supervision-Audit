"""Execute independent paired BM25 retrieval on a small Wikipedia snapshot."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import time
import tracemalloc

from dualreform_audit.data import Turn
from dualreform_audit.io import digest, environment, git_sha, write_json, write_jsonl
from dualreform_audit.track_b import BM25, overlap, rank_of, tokens, turn_for_arm
from dualreform_audit.trace import trace_record, validate_hits
from paper_reimplementation.signals import pseudo_query, select_pseudo

from scripts.generate_track_b_pairs import load_jsonl


QUESTION_STOP = {"a", "an", "and", "by", "did", "does", "he", "in", "is", "it",
                 "its", "of", "she", "the", "this", "to", "was", "were", "what",
                 "when", "where", "which", "who"}


def title_filter(hits, docs_by_id, question, lookahead=10):
    anchor = set(tokens(question)) - QUESTION_STOP
    def matches(hit):
        title_terms = set(tokens(docs_by_id[hit["doc_id"]]["title"])) - QUESTION_STOP
        return len(title_terms) >= 2 and len(anchor & title_terms) >= 2 and (
            len(anchor & title_terms) / len(title_terms) >= 2 / 3)
    chosen = [h for h in hits[:lookahead] if matches(h)]
    return [{**hit, "rank": rank} for rank, hit in enumerate(chosen, 1)]


def run(config_path, pairs_path, output):
    started = datetime.now(timezone.utc).isoformat()
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    if config["official_topiocqa_corpus"] is not False:
        raise ValueError("Track B must identify the alternative corpus honestly")
    docs = load_jsonl(config["corpus_path"])
    expected = set(config["titles"])
    if len(docs) != len(expected) or any(
            d["title"] not in expected and d["title"] not in
            {"Operation Overlord", "Swift (bird)"} for d in docs):
        raise ValueError("Unexpected corpus coverage")
    import hashlib
    if any(hashlib.sha256(d["text"].encode()).hexdigest() != d["text_sha256"]
           for d in docs):
        raise ValueError("Corpus text hash mismatch")
    retr = config["retriever"]
    source_sha, corpus_sha = git_sha(), digest(config["corpus_path"])
    tracemalloc.start()
    build_clock = time.perf_counter()
    index = BM25(docs, retr["k1"], retr["b"])
    build_seconds = time.perf_counter() - build_clock
    by_id = {d["doc_id"]: d for d in docs}
    cases = load_jsonl(pairs_path)
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Missing or duplicate pair IDs")
    clock, records, summaries = time.perf_counter(), [], []
    for case in cases:
        case_runs = {}
        for arm, response in (("original", case["original_response"]),
                              ("counterfactual", case["modified_response"])):
            turn = Turn("topiocqa", "train", case["conversation_id"], case["turn_id"],
                        case["question"], response, tuple(tuple(pair) for pair in case["history"]))
            questions = " ".join(q for q, _ in turn.history) + " " + case["question"]
            queries = {"response_only": pseudo_query(response, 0),
                       "question_anchored": questions + " " + response}
            for method in ("response_only", "question_anchored", "title_filter"):
                query = queries["question_anchored" if method == "title_filter" else method]
                hits = index.search(query, retr["top_k"])
                if method == "title_filter":
                    hits = title_filter(hits, by_id, questions, lookahead=retr["top_k"])
                validate_hits(hits)
                # All searches are repeated immediately; deterministic ranking and scores must match.
                repeated = index.search(query, retr["top_k"])
                if method == "title_filter":
                    repeated = title_filter(repeated, by_id, questions, lookahead=retr["top_k"])
                if hits != repeated:
                    raise AssertionError("Nondeterministic retrieval")
                # A tiny alternative corpus can contain fewer than three matching articles.
                # Keep that coverage failure explicit; never invent zero-score pseudo refs.
                selected = select_pseudo(hits, retr["pseudo_k"]) if len(hits) >= 3 else [
                    h["doc_id"] for h in hits]
                provenance = {"experiment_id": config["experiment_id"],
                              "source_revision": source_sha, "model": "none",
                              "retriever": {**retr, "method": method},
                              "dataset_version": config["dataset_sha256"],
                              "corpus_sha256": corpus_sha}
                trace = trace_record(turn_for_arm(turn, response), "", hits, provenance)
                records.append({"case_id": case["id"], "category": case["category"],
                                "arm": arm, "method": method, "query": query,
                                "selected_ids": selected,
                                "pseudo_top3_complete": len(selected) == 3,
                                "trace": trace})
                case_runs[(arm, method)] = hits
        row = {"case_id": case["id"], "category": case["category"],
               "expected_original_ids": case["original_target_ids"],
               "expected_counterfactual_ids": case["modified_target_ids"],
               "methods": {}}
        for method in ("response_only", "question_anchored", "title_filter"):
            left = case_runs[("original", method)]
            right = case_runs[("counterfactual", method)]
            row["methods"][method] = {
                "top3_overlap": overlap(left, right, 3),
                "top10_overlap": overlap(left, right, 10),
                "pseudo_changed": [h["doc_id"] for h in left[:3]] !=
                                  [h["doc_id"] for h in right[:3]],
                "original_target_ranks": {d: rank_of(left, d)
                                          for d in case["original_target_ids"]},
                "counterfactual_target_ranks": {d: rank_of(right, d)
                                                for d in case["modified_target_ids"]},
                "original_top3": [h["doc_id"] for h in left[:3]],
                "counterfactual_top3": [h["doc_id"] for h in right[:3]]}
        summaries.append(row)
    counts = Counter(c["category"] for c in cases)
    baseline = {c["case_id"]: c["methods"]["response_only"] for c in summaries}
    a_cases = [c for c in cases if c["category"] == "A"]
    b_cases = [c for c in cases if c["category"] == "B"]
    d_cases = [c for c in cases if c["category"] == "D"]
    def in_top3(case, arm):
        ids = (case["original_target_ids"] if arm == "original"
               else case["modified_target_ids"])
        key = "original_top3" if arm == "original" else "counterfactual_top3"
        return any(doc_id in baseline[case["id"]][key] for doc_id in ids)
    target_losses = [c["id"] for c in a_cases if in_top3(c, "original")
                     and not in_top3(c, "counterfactual")]
    title_to_id = {d["title"]: d["doc_id"] for d in docs}
    contaminated = [c["id"] for c in a_cases
                    if c["intervention_new"] in title_to_id
                    and title_to_id[c["intervention_new"]] in
                    baseline[c["id"]]["counterfactual_top3"]
                    and not in_top3(c, "counterfactual")]
    metrics = {"experiment_type": "independent_paper_derived_iteration_zero_diagnostic",
               "official_baseline_reproduced": False, "dataset": "TopiOCQA train",
               "corpus_document_count": len(docs), "cases": len(cases),
               "category_counts": dict(sorted(counts.items())),
               "retrieval_calls": len(records) * 2,
               "trace_records": len(records),
               "incomplete_top3_records": sum(not r["pseudo_top3_complete"] for r in records),
               "peak_traced_python_bytes": tracemalloc.get_traced_memory()[1],
               "index_build_seconds": build_seconds,
               "retrieval_seconds": time.perf_counter() - clock,
               "a_target_preserved_top3": sum(in_top3(c, "counterfactual") for c in a_cases),
               "a_target_loss_proxy_ids": target_losses,
               "a_factual_contamination_proxy_ids": contaminated,
               "b_referent_change_responsive_top3": sum(
                   in_top3(c, "original") and in_top3(c, "counterfactual") for c in b_cases),
               "d_identical_top3": sum(not baseline[c["id"]]["pseudo_changed"] for c in d_cases),
               "cases_detail": summaries}
    tracemalloc.stop()
    out = Path(output)
    write_jsonl(out / "paired_rankings.jsonl", records)
    write_json(out / "metrics.json", metrics)
    write_json(out / "run_manifest.json", {
        "status": "executed", "timestamp_utc": started, "git_sha": source_sha,
        "experiment_id": config["experiment_id"], "source_type": "independent_paper_derived",
        "official_baseline_reproduced": False, "gpu_execution": "NOT EXECUTED",
        "config_sha256": digest(config_path), "pairs_sha256": digest(pairs_path),
        "case_spec_sha256": digest("configs/track_b_cases.json"),
        "manual_labels_sha256": digest("configs/track_b_manual_labels.json"),
        "dataset_archive_sha256": digest(config["dataset_archive"]),
        "corpus_sha256": corpus_sha,
        "corpus_documents": len(docs), "corpus_revision_ids": {d["doc_id"]: d["revision_id"]
                                                       for d in docs},
        "corpus_bytes": Path(config["corpus_path"]).stat().st_size,
        "parameters": retr, "diagnostics": config["diagnostics"],
        "seed": config["seed"], "environment": environment(),
        "platform": platform.platform(), "index_build_seconds": build_seconds,
        "retrieval_seconds": metrics["retrieval_seconds"],
        "peak_traced_python_bytes": metrics["peak_traced_python_bytes"],
        "rankings_sha256": digest(out / "paired_rankings.jsonl")})
    return metrics


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", default="configs/track_b.yaml")
    p.add_argument("--pairs", default="results/track_b/pairs_generated.jsonl")
    p.add_argument("--output", default="results/track_b")
    a = p.parse_args()
    result = run(a.config, a.pairs, a.output)
    print(json.dumps({k: v for k, v in result.items() if k != "cases_detail"}, indent=2))
