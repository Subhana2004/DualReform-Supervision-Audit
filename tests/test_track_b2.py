"""Integrity checks for the preregistered, non-equivalent Track B2 diagnostic."""
import json
from pathlib import Path
import sqlite3

import pytest

from dualreform_audit.io import digest
from scripts.run_track_b2 import fts_query, query_text, search


ROOT = Path("results/track_b2")


def read_lines(name):
    return [json.loads(x) for x in (ROOT / name).read_text(encoding="utf-8").splitlines()]


def test_preregistration_integrity_and_split_separation():
    manifest = json.loads((ROOT / "preregistration.json").read_text(encoding="utf-8"))
    config = json.loads(Path("configs/track_b2.json").read_text(encoding="utf-8"))
    cases = read_lines("preregistered_pairs.jsonl")
    assert digest(ROOT / "preregistered_pairs.jsonl") == manifest["pairs_sha256"]
    assert manifest["independent_conversations"] == 30
    assert len(cases) == 60
    assert len({x["id"] for x in cases}) == 60
    assert len({x["conversation_id"] for x in cases}) == 30
    assert {x["split"] for x in cases} == {"train"}
    assert config["benchmark"]["validation_conversations"] == 8
    assert not manifest["selection_uses_gold_fields"]
    assert not manifest["future_turns_used"]
    for left, right in zip(cases[::2], cases[1::2]):
        assert left["category"] == "A" and right["category"] == "D"
        assert left["conversation_id"] == right["conversation_id"]
        assert left["question"] == left["modified_question"]
        assert right["question"] == right["modified_question"]
        assert right["modified_response"] == right["original_response"] + "."
        assert fts_query(right["original_response"]) == fts_query(right["modified_response"])


def test_current_turn_alignment_and_blind_review_status():
    cases = read_lines("preregistered_pairs.jsonl") + read_lines("supplementary_cases.jsonl")
    worksheet = read_lines("blind_review_worksheet.jsonl")
    assert len(worksheet) == 36
    assert {x["case_id"] for x in worksheet} == {
        x["id"] for x in cases if x["category"] != "D"}
    assert all(x["reviewer_id"] is None and x["response_claim_support"] == "unreviewed"
               and x["relevant_passage_ids"] == [] for x in worksheet)
    screen = json.loads((ROOT / "semantic_screening.json").read_text(encoding="utf-8"))
    assert len(screen["flagged_case_ids"]) == 5
    assert not screen["unflagged_claims_independently_verified"]
    for case in cases:
        assert case["history"] and isinstance(case["history"], list) or case["history"] == []
        assert "followup_question" not in case
        assert "rationale" not in case
        if case["category"] in ("A", "D"):
            assert not case["current_intent_changed"]
        if case["category"] == "B":
            assert case["current_intent_changed"]
            assert case["question"] != case["modified_question"]
        if case["category"] == "C":
            assert len(case["plausible_interpretations"]) > 1


def test_queries_use_current_question_response_only_and_prior_questions():
    case = {"question": "Who designed Mars?", "modified_question": "Who designed Venus?",
            "original_response": "Alice", "modified_response": "Bob",
            "history": [["Where is Earth?", "private preceding reply"]]}
    assert query_text(case, "original", "response_only") == "Alice"
    assert query_text(case, "counterfactual", "response_only") == "Bob"
    assert "Mars" in query_text(case, "original", "question_anchored")
    assert "Venus" in query_text(case, "counterfactual", "question_only")
    assert "private preceding reply" not in query_text(case, "original", "question_anchored")
    with pytest.raises(ValueError):
        fts_query("!?;")


def test_fts_retrieval_deterministic_complete_and_missing_evidence():
    con = sqlite3.connect(":memory:")
    con.execute("CREATE VIRTUAL TABLE wiki_3 USING fts5(doc_id UNINDEXED,title,body, "
                "tokenize='unicode61')")
    con.executemany("INSERT INTO wiki_3 VALUES (?,?,?)", [
        ("simplewiki:1", "Mars", "Mars is red."),
        ("simplewiki:2", "Venus", "Venus is bright."),
        ("simplewiki:3", "Earth", "Earth is blue.")])
    first = search(con, "wiki_3", "Mars", 100)
    assert first == search(con, "wiki_3", "Mars", 100)
    _, hits, selected = first
    assert hits[0]["doc_id"] == "simplewiki:1"
    assert len(hits) == len(selected) == 1
    assert hits[0]["score"] > 0
    _, empty, pseudo = search(con, "wiki_3", "nonexistent", 100)
    assert empty == pseudo == []


def test_real_corpus_manifest_integrity_if_index_present():
    manifest = json.loads((ROOT / "corpus_manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_rows"] == manifest["indexed_rows"] == 241787
    assert manifest["prefix_document_counts"] == {
        "10000": 10000, "50000": 50000, "241787": 241787}
    assert manifest["integrity_check"] == "ok"
    path = Path(manifest["index_local_path"])
    if not path.exists():
        pytest.skip("Large ignored corpus is not committed")
    assert path.stat().st_size == manifest["index_size_bytes"]
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    assert con.execute("SELECT count(*) FROM wiki_241787").fetchone()[0] == 241787
    assert con.execute("SELECT count(distinct doc_id) FROM wiki_241787").fetchone()[0] == 241787
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    con.close()


def test_executed_trace_and_manifest_if_present():
    path = ROOT / "run_manifest.json"
    if not path.exists():
        pytest.skip("Track B2 retrieval has not finished")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    metrics = json.loads((ROOT / "metrics.json").read_text(encoding="utf-8"))
    rankings = read_lines("rankings.jsonl")
    comparisons = read_lines("comparisons.jsonl")
    assert len(rankings) == metrics["retrieval_records"] == 876
    assert len(comparisons) == metrics["comparisons"] == 438
    assert digest(ROOT / "rankings.jsonl") == manifest["rankings_sha256"]
    assert digest(ROOT / "comparisons.jsonl") == manifest["comparisons_sha256"]
    assert manifest["gpu_execution"] == "NOT EXECUTED"
    assert not manifest["official_baseline_reproduced"]
    assert metrics["relevance_recall_at_k"] is None
    assert metrics["harmful_factual_changes"] is None
    assert metrics["incomplete_top3_records"] == 6
    assert all(r["complete_top3"] for r in rankings
               if r["corpus_documents"] == 241787)
    for row in rankings:
        assert len(row["ranking_top100"]) <= 100
        assert len(row["selected_pseudo_references"]) <= 3
        assert row["positive_score_hits"] >= len(row["ranking_top100"])
        assert [h["rank"] for h in row["ranking_top100"]] == list(
            range(1, len(row["ranking_top100"]) + 1))
        assert row["query_fts"] and row["current_question"] and row["observed_response"]


def test_porter_analyzer_sensitivity_manifest_if_present():
    path = ROOT / "porter_manifest.json"
    if not path.exists():
        pytest.skip("Exploratory Porter check has not run")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    comparison = json.loads((ROOT / "porter_comparison.json").read_text(encoding="utf-8"))
    rows = read_lines("porter_rankings.jsonl")
    assert manifest["document_count"] == comparison["same_corpus_documents"] == 241787
    assert manifest["tokenizer"] == "porter unicode61"
    assert len(rows) == comparison["records"] == 136
    assert digest(ROOT / "porter_rankings.jsonl") == manifest["rankings_sha256"]
    assert comparison["top3_set_differs_between_analyzers"] == sum(
        x["top3_set_changed_by_analyzer"] for x in comparison["detail"])
    assert manifest["gpu_execution"] == "NOT EXECUTED"
