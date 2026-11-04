"""Read-only trace capture: no response editing, guard, or counterfactual generation."""
from copy import deepcopy
import math


def validate_hits(hits):
    ids = set()
    for expected, hit in enumerate(hits, 1):
        if not isinstance(hit.get("doc_id"), str) or not hit["doc_id"]:
            raise ValueError("Malformed document ID")
        if hit["doc_id"] in ids or hit.get("rank") != expected:
            raise ValueError("Duplicate document or invalid rank order")
        if not math.isfinite(hit.get("score", float("nan"))):
            raise ValueError("Non-finite retrieval score")
        ids.add(hit["doc_id"])
    return hits


def trace_record(turn, refined_response, hits, configuration, candidates=(), preferences=()):
    validate_hits(hits)
    if not isinstance(refined_response, str):
        raise ValueError("Refined response must be text")
    required = {"experiment_id", "source_revision", "model", "retriever", "dataset_version"}
    if not required <= configuration.keys():
        raise ValueError("Missing trace provenance")
    return deepcopy({"schema_version": 1, "id": turn.id, "input": turn.training_input(),
                     "original_response": turn.response, "refined_response": refined_response,
                     "pseudo_reference_ids": [h["doc_id"] for h in hits[:3]],
                     "pseudo_reference_ranking": hits, "candidates": list(candidates),
                     "preferences": list(preferences), "configuration": configuration})
