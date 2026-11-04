"""Equations 8, 9, 18–21 and strict-order pairs from ICML paper, pp. 5 and 17.

Unknown weights/cutoffs are mandatory inputs. This module does not silently emulate
the inconsistent, stateful third-party preference notebooks.
"""
import math
from dualreform_audit.metrics import ranking_metrics
from dualreform_audit.trace import validate_hits


def response_template(response):
    return ("Can you clearly state the main points of the last response "
            f"({response}), contextualizing them and resolving coreferences?")


def pseudo_query(response, iteration, refined_response=None):
    if not isinstance(response, str) or not response.strip():
        raise ValueError("A nonempty observed response is required")
    if not isinstance(iteration, int) or iteration < 0:
        raise ValueError("Invalid iteration")
    if iteration == 0:
        if refined_response not in (None, ""):
            raise ValueError("Algorithm 1 prohibits refinement in iteration zero")
        return response
    if not isinstance(refined_response, str) or not refined_response.strip():
        raise ValueError("A previously trained CQR refinement is required")
    return response + " " + refined_response


def select_pseudo(hits, count=3):
    validate_hits(hits)
    if count < 1 or len(hits) < count:
        raise ValueError("Insufficient unique pseudo-reference hits")
    return [h["doc_id"] for h in hits[:count]]


def candidate_score(ranking, pseudo_ids, *, weights, cutoffs):
    if weights is None or cutoffs is None:
        raise ValueError("Paper omits concrete score weights/cutoffs; supply reviewed values")
    if (len(weights) != 3 or any(not math.isfinite(w) or w < 0 for w in weights)
            or not math.isclose(sum(weights), 1.0)):
        raise ValueError("Need three nonnegative weights summing to one")
    if not cutoffs or not pseudo_ids or len(set(pseudo_ids)) != len(pseudo_ids):
        raise ValueError("Need distinct pseudo-reference IDs and nonempty cutoffs")
    m = ranking_metrics(ranking, {d: 1 for d in pseudo_ids}, cutoffs=tuple(cutoffs))
    coverage = sum(m[f"recall_{k}"] for k in cutoffs) / len(cutoffs)
    return weights[0]*coverage + weights[1]*m["recip_rank"] + weights[2]*m["ndcg_cut_3"]


def strict_preference_pairs(candidates):
    """Paper Eq. 4 strict ordering, not the copy's undocumented sampling thresholds."""
    if not candidates:
        raise ValueError("No candidates")
    seen = set()
    for c in candidates:
        if not isinstance(c.get("query"), str) or not c["query"].strip():
            raise ValueError("Empty candidate")
        if c["id"] in seen or not math.isfinite(c["score"]):
            raise ValueError("Duplicate candidate or invalid score")
        seen.add(c["id"])
    return [{"chosen": a["id"], "rejected": b["id"], "gap": a["score"] - b["score"]}
            for a in candidates for b in candidates
            if a["score"] > b["score"] and a["query"] != b["query"]]
