"""TREC-style linear-gain nDCG, reciprocal rank and set recall; fractions, not percent."""
import math


def ranking_metrics(ranking, qrels, cutoffs=(5, 20), ndcg_k=3):
    if len(ranking) != len(set(ranking)):
        raise ValueError("Duplicate document IDs in ranking")
    if any(not isinstance(d, str) or not d for d in ranking):
        raise ValueError("Document IDs must be nonempty strings")
    if any(not math.isfinite(v) or v < 0 for v in qrels.values()):
        raise ValueError("Invalid relevance grade")
    relevant = {d for d, grade in qrels.items() if grade > 0}
    if not relevant:
        raise ValueError("No positive qrels: evaluation eligibility must be explicit")
    if ndcg_k < 1 or any(k < 1 for k in cutoffs):
        raise ValueError("Metric cutoffs must be positive")
    rr = next((1 / rank for rank, doc in enumerate(ranking, 1) if doc in relevant), 0.0)
    dcg = sum(qrels.get(doc, 0) / math.log2(rank + 1)
              for rank, doc in enumerate(ranking[:ndcg_k], 1))
    ideal = sum(grade / math.log2(rank + 1) for rank, grade in enumerate(
        sorted(qrels.values(), reverse=True)[:ndcg_k], 1))
    return {"recip_rank": rr, "ndcg_cut_3" if ndcg_k == 3 else f"ndcg_cut_{ndcg_k}":
            dcg / ideal if ideal else 0.0,
            **{f"recall_{k}": len(set(ranking[:k]) & relevant) / len(relevant) for k in cutoffs}}


def aggregate(records):
    if not records:
        raise ValueError("Cannot aggregate an empty evaluation")
    keys = set(records[0])
    if any(set(row) != keys for row in records):
        raise ValueError("Inconsistent metric schema")
    return {key: sum(row[key] for row in records) / len(records) for key in sorted(keys)}


def read_trec(path, allow_legacy_seven_columns=False):
    """Read standard six-column runs; copied source's seven-column runs require opt-in."""
    runs, seen_ranks = {}, {}
    with open(path, encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            fields = line.split()
            if not fields:
                continue
            if len(fields) not in ((6, 7) if allow_legacy_seven_columns else (6,)):
                raise ValueError(f"TREC line {line_number}: wrong number of columns")
            qid, _, docid, rank, order_score = fields[:5]
            rank, order_score = int(rank), float(order_score)
            if rank < 1 or not math.isfinite(order_score):
                raise ValueError(f"TREC line {line_number}: invalid rank/score")
            group = runs.setdefault(qid, {})
            ranks = seen_ranks.setdefault(qid, set())
            if docid in group or rank in ranks:
                raise ValueError(f"TREC line {line_number}: duplicate document/rank")
            ranks.add(rank)
            group[docid] = {"doc_id": docid, "rank": rank, "score": order_score}
            if len(fields) == 7:
                group[docid]["retriever_score"] = float(fields[5])
    output = {}
    for qid, group in runs.items():
        hits = sorted(group.values(), key=lambda x: x["rank"])
        if [h["rank"] for h in hits] != list(range(1, len(hits) + 1)):
            raise ValueError(f"Non-contiguous ranks for {qid}")
        if any(a["score"] < b["score"] for a, b in zip(hits, hits[1:])):
            raise ValueError(f"Score/rank order mismatch for {qid}")
        output[qid] = hits
    return output
