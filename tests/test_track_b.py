"""Track B controls are engineering checks; no benchmark result is fabricated here."""
from dataclasses import replace
import json
from pathlib import Path
import os
import subprocess
import sys

import pytest

from dualreform_audit.data import Turn, assert_disjoint
from dualreform_audit.track_b import BM25, overlap, validate_pair
from dualreform_audit.trace import trace_record
from scripts.run_track_b import title_filter


DOCS = [{"doc_id": "p:1", "title": "Red Planet", "text": "Mars is a red planet."},
        {"doc_id": "p:2", "title": "Blue Planet", "text": "Earth is a blue planet."},
        {"doc_id": "p:3", "title": "Red Apple", "text": "The apple is red."}]


def turn(response="Red Planet", tid=1, cid="train/1"):
    return Turn("topiocqa", "train", cid, tid, "Which planet is red?", response, ())


def test_bm25_known_order_and_deterministic_scores():
    index = BM25(DOCS, 0.9, 0.4)
    first = index.search("red planet", 3)
    assert [h["doc_id"] for h in first] == ["p:1", "p:3", "p:2"]
    assert first == index.search("red planet", 3)
    assert [h["rank"] for h in first] == [1, 2, 3]
    assert all(a["score"] >= b["score"] for a, b in zip(first, first[1:]))


def test_scores_identical_across_hash_seeds():
    code = ("import json; from dualreform_audit.track_b import BM25; "
            "d=[{'doc_id':'1','title':'red planet','text':'blue planet red'},"
            "{'doc_id':'2','title':'blue planet','text':'red apple blue'}]; "
            "print(json.dumps(BM25(d).search('red blue planet')))" )
    outputs = []
    for seed in ("1", "999"):
        env = {**os.environ, "PYTHONHASHSEED": seed,
               "PYTHONPATH": f"src{os.pathsep}."}
        result = subprocess.run([sys.executable, "-c", code], capture_output=True,
                                text=True, env=env, check=True)
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1]


def test_missing_corpus_and_invalid_passage_ids():
    with pytest.raises(ValueError):
        BM25([])
    with pytest.raises(ValueError):
        BM25(DOCS + [DOCS[0]])
    with pytest.raises(ValueError):
        BM25([{"doc_id": "", "title": "x", "text": "x"}])


def test_pair_categories_and_alignment():
    mapping = {"Red Planet": "p:1", "Blue Planet": "p:2", "Mars": "p:3"}
    base = {"id": "a", "category": "A", "old": "Red Planet", "new": "Blue Planet"}
    labels = {"original_targets": ["Mars"],
              "counterfactual_targets": ["Mars"], "rationale": "same subject"}
    original = turn()
    followup = replace(turn("Mars", 2), query="Where was he born?",
                       history=((original.query, original.response),))
    assert validate_pair(base, original, followup, labels, mapping)[
        "modified_response"] == "Blue Planet"
    with pytest.raises(ValueError, match="aligned"):
        validate_pair(base, original, turn("Mars", 3), labels, mapping)
    with pytest.raises(ValueError, match="passage"):
        validate_pair(base, original, followup,
                      {**labels, "original_targets": ["Missing"]}, mapping)
    with pytest.raises(ValueError, match="unchanged subject"):
        validate_pair(base, original, followup,
                      {**labels, "counterfactual_targets": ["Blue Planet"]}, mapping)
    changed = {**base, "category": "B"}
    assert validate_pair(changed, original, followup,
                         {**labels, "original_targets": ["Red Planet"],
                          "counterfactual_targets": ["Blue Planet"]}, mapping)[
        "modified_target_ids"] == ["p:2"]
    ambiguous = {**base, "category": "C", "new": "Red Planet and Blue Planet"}
    assert len(validate_pair(ambiguous, original, followup,
                             {**labels, "original_targets": ["Red Planet"],
                              "counterfactual_targets":
                              ["Red Planet", "Blue Planet"]}, mapping)[
        "modified_target_ids"]) == 2
    control = {**base, "category": "D", "new": "Red Planet!"}
    assert validate_pair(control, original, followup, labels, mapping)[
        "modified_response"] == "Red Planet!"
    with pytest.raises(ValueError, match="lexical"):
        validate_pair({**control, "new": "Blue Planet"}, original, followup,
                      labels, mapping)


def test_split_leakage_and_original_counterfactual_alignment():
    with pytest.raises(ValueError, match="leakage"):
        assert_disjoint([turn()], [replace(turn(), response="Changed")])


def test_overlap_and_negative_control_rank_stability():
    index = BM25(DOCS)
    a = index.search("Red Planet")
    b = index.search("Red Planet!")
    assert a == b
    assert overlap(a, b, 3) == 1.0
    assert overlap(a, index.search("Blue Planet"), 3) < 1.0


def test_trace_completeness_and_filter_failure_is_explicit():
    index = BM25(DOCS)
    hits = index.search("Red Planet")
    trace = trace_record(turn(), "", hits, {
        "experiment_id": "test", "source_revision": "test", "model": "none",
        "retriever": {"algorithm": "BM25"}, "dataset_version": "fixture"})
    assert trace["original_response"] == "Red Planet"
    assert trace["pseudo_reference_ranking"] == hits
    assert trace["pseudo_reference_ids"] == [h["doc_id"] for h in hits[:3]]
    filtered = title_filter(hits, {d["doc_id"]: d for d in DOCS}, "Who wrote it?")
    assert filtered == []


def test_committed_corpus_has_valid_ids_hashes_and_revisions():
    import hashlib
    docs = [json.loads(line) for line in Path("data/track_b_wikipedia_leads.jsonl").read_text(
        encoding="utf-8").splitlines()]
    assert len(docs) == 58
    assert len({d["doc_id"] for d in docs}) == len(docs)
    assert all(d["revision_url"].endswith(str(d["revision_id"])) for d in docs)
    assert all(hashlib.sha256(d["text"].encode()).hexdigest() == d["text_sha256"]
               for d in docs)
