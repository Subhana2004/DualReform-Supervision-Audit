"""Measure four pre-existing known article ranks, without claiming full qrels."""
import json
from pathlib import Path

from dualreform_audit.io import write_json
from scripts.run_track_b2 import load_jsonl


def run(root="results/track_b2"):
    root = Path(root)
    rows = load_jsonl(root / "legacy_rankings.jsonl")
    labels = json.loads(Path("configs/track_b2_historical_qrels.json").read_text(
        encoding="utf-8"))["cases"]
    detail = []
    for row in rows:
        target = labels[row["case_id"]]["known_relevant_article_id"]
        rank = next((hit["rank"] for hit in row["ranking_top100"]
                     if hit["doc_id"] == target), None)
        detail.append({"case_id": row["case_id"], "method": row["method"],
                       "arm": row["arm"], "known_relevant_article_id": target,
                       "known_article_rank_top100": rank,
                       "known_article_in_top3": rank is not None and rank <= 3,
                       "positive_score_hits": row["positive_score_hits"],
                       "selected_titles": [r["title"] for r in
                                           row["selected_pseudo_references"]]})
    summary = {"scope": "four historically selected cases, one known relevant article each",
               "independent_reviewers": 0,
               "comprehensive_qrels": False,
               "detail": detail,
               "known_article_top3_by_method_arm": [
                   {"method": method, "arm": arm,
                    "count": sum(r["known_article_in_top3"] for r in detail
                                 if r["method"] == method and r["arm"] == arm),
                    "denominator": len(labels)}
                   for method in ("response_only", "question_anchored", "question_only")
                   for arm in ("original", "counterfactual")],
               "response_only_known_article_top3_original": sum(
                   r["known_article_in_top3"] for r in detail
                   if r["method"] == "response_only" and r["arm"] == "original"),
               "response_only_known_article_top3_counterfactual": sum(
                   r["known_article_in_top3"] for r in detail
                   if r["method"] == "response_only" and r["arm"] == "counterfactual")}
    write_json(root / "legacy_analysis.json", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
