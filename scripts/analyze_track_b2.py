"""Summarize paired lexical changes with conversation-clustered uncertainty."""
from collections import defaultdict
import json
from pathlib import Path
import random
import statistics

from dualreform_audit.io import write_json


def load(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


def interval(values, seed=20261105, replicates=10000):
    if not values:
        return None
    rng = random.Random(seed)
    n = len(values)
    draws = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n
                   for _ in range(replicates))
    return {"estimate": sum(values) / n, "bootstrap_95_percent":
            [draws[int(0.025 * replicates)], draws[int(0.975 * replicates)]],
            "unit": "independent conversation", "replicates": replicates}


def run(root="results/track_b2"):
    root = Path(root)
    rows = load(root / "comparisons.jsonl")
    ranks = load(root / "rankings.jsonl")
    full = max(r["corpus_documents"] for r in rows)
    groups = defaultdict(list)
    for row in rows:
        key = (row["category"], row["method"], row["corpus_documents"])
        groups[key].append(row)
    table = []
    for (category, method, size), items in sorted(groups.items()):
        table.append({"category": category, "method": method,
                      "corpus_documents": size, "pairs": len(items),
                      "independent_conversations": len({x["conversation_id"] for x in items}),
                      "top3_changed": sum(x["top3_changed"] for x in items),
                      "top3_set_changed": sum(x["top3_jaccard"] != 1 for x in items),
                      "top3_order_only_changed": sum(x["top3_changed"] and
                                                     x["top3_jaccard"] == 1 for x in items),
                      "change_rate_cluster_bootstrap": interval(
                          [int(x["top3_changed"]) for x in items])
                      if category in ("A", "D") else None})
    by_key = {(r["case_id"], r["method"], r["corpus_documents"]): r for r in rows}
    paired = []
    for case_id in sorted({r["case_id"] for r in rows if r["category"] == "A"}):
        base = by_key[(case_id, "response_only", full)]
        anchor = by_key[(case_id, "question_anchored", full)]
        paired.append(int(base["top3_changed"]) - int(anchor["top3_changed"]))
    positive = [r["positive_score_hits"] for r in ranks if r["corpus_documents"] == full]
    full_ranks = [r for r in ranks if r["corpus_documents"] == full]
    tied_top3 = sum(any(a["score"] == b["score"] for a, b in zip(
        r["ranking_top100"][:3], r["ranking_top100"][1:3])) for r in full_ranks)
    tied_top100 = sum(any(a["score"] == b["score"] for a, b in zip(
        r["ranking_top100"], r["ranking_top100"][1:])) for r in full_ranks)
    tied_boundary = sum(len(r["ranking_top100"]) >= 4 and
                        r["ranking_top100"][2]["score"] ==
                        r["ranking_top100"][3]["score"] for r in full_ranks)
    result = {"scope": "lexical ranking diagnostics, not factual support or relevance",
              "full_corpus_documents": full, "group_table": table,
              "A_response_only_minus_question_anchored_change_rate": interval(paired),
              "full_corpus_positive_hit_count_min": min(positive),
              "full_corpus_positive_hit_count_median": statistics.median(positive),
              "full_corpus_positive_hit_count_max": max(positive),
              "full_corpus_records_with_adjacent_equal_score_top3": tied_top3,
              "full_corpus_records_with_adjacent_equal_score_top100": tied_top100,
              "full_corpus_records_with_exact_score_tie_at_3_4_boundary": tied_boundary,
              "known_relevant_article_recall_at_3": None,
              "sample_relevance_qrels_available": False}
    write_json(root / "analysis.json", result)
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
