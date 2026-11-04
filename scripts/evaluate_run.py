"""Evaluate an existing TREC run with explicit qrels; no training functions are imported."""
import argparse
import json
from pathlib import Path
from dualreform_audit.metrics import aggregate, ranking_metrics, read_trec
from dualreform_audit.io import write_json


def evaluate(run_path, qrels_path):
    run = read_trec(run_path)
    qrels = json.loads(Path(qrels_path).read_text(encoding="utf-8"))
    missing = sorted(set(qrels) - set(run))
    extra = sorted(set(run) - set(qrels))
    eligible, excluded = {}, []
    for qid, relevance in qrels.items():
        if not any(value > 0 for value in relevance.values()):
            excluded.append(qid)
            continue
        eligible[qid] = ranking_metrics([h["doc_id"] for h in run.get(qid, [])], relevance)
    return {"metrics": aggregate(list(eligible.values())), "metric_scale": "fraction",
            "eligible_queries": len(eligible), "missing_run_queries_scored_zero": missing,
            "extra_run_queries_ignored": extra, "queries_without_positive_qrels_excluded": excluded,
            "per_example": eligible, "status": "evaluated_supplied_run_not_a_model_execution"}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True)
    p.add_argument("--qrels", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    write_json(a.output, evaluate(a.run, a.qrels))
