import json
from pathlib import Path

import pytest

from dualreform_audit.data import assert_disjoint, normalize, split_training, subset
from dualreform_audit.device import select_device
from dualreform_audit.metrics import aggregate, ranking_metrics, read_trec
from dualreform_audit.trace import trace_record
from paper_reimplementation.signals import (
    candidate_score, pseudo_query, response_template, select_pseudo, strict_preference_pairs,
)
from scripts.evaluate_run import evaluate


def rows(cid=1):
    return [{"Conversation_no": cid, "Turn_no": i, "Question": f"q{cid}-{i}",
             "Answer": f"a{cid}-{i}", "Context": [x for j in range(1, i)
                       for x in (f"q{cid}-{j}", f"a{cid}-{j}")],
             "Rationale": "SECRET_GOLD", "Rewrite": "SECRET_GOLD"} for i in (1, 2, 3)]


def turn():
    return normalize(rows(), "topiocqa", "train")[0][-1]


def test_schema_and_history_order():
    turns, stats = normalize(list(reversed(rows())), "topiocqa", "train")
    assert turns[-1].history == (("q1-1", "a1-1"), ("q1-2", "a1-2"))
    assert stats["turns"] == 3
    assert "SECRET_GOLD" not in json.dumps(turns[-1].training_input())


@pytest.mark.parametrize("change", [lambda r: r.pop("Question"),
                                    lambda r: r.update(Turn_no=-1),
                                    lambda r: r.update(Answer=[]),
                                    lambda r: r.update(Question="")])
def test_malformed_records(change):
    data = rows()
    change(data[0])
    with pytest.raises(ValueError):
        normalize(data, "topiocqa", "train")


def test_duplicate_turn_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        normalize(rows()+rows()[:1], "topiocqa", "train")


def test_missing_history_is_never_silently_repaired():
    with pytest.raises(ValueError, match="Non-contiguous"):
        normalize(rows()[1:], "qrecc", "train")
    turns, stats = normalize(rows()[1:]+rows(2), "qrecc", "train", "exclude_conversation")
    assert len(turns) == 3
    assert stats["raw_turns"] == 5
    assert stats["excluded_conversations"][0]["reason"] == "non_contiguous_turn_ids"


def test_sampling_order_independence_and_whole_conversations():
    turns, _ = normalize(rows(1)+rows(2)+rows(3), "topiocqa", "train")
    a, b = subset(turns, 2, 42), subset(list(reversed(turns)), 2, 42)
    assert {t.id for t in a} == {t.id for t in b}
    assert len(a) == 6
    train, val = split_training(turns, 1, 42)
    assert_disjoint(train, val)


def test_leakage_and_reassigned_ids():
    a, _ = normalize(rows(), "topiocqa", "train")
    with pytest.raises(ValueError, match="leakage"):
        assert_disjoint(a, a)
    other = rows()
    for row in other:
        row["Conversation_no"] = 99
    b, _ = normalize(other, "topiocqa", "dev")
    with pytest.raises(ValueError, match="Duplicate conversation"):
        assert_disjoint(a, b)


def test_split_numeric_ids_are_scoped():
    a, _ = normalize(rows(1), "qrecc", "train")
    data = rows(1)
    data[0]["Question"] = "different first question"
    b, _ = normalize(data, "qrecc", "test")
    assert_disjoint(a, b)


def test_known_binary_metrics():
    m = ranking_metrics(["x", "a", "b"], {"a": 1, "b": 1})
    assert m["recip_rank"] == 0.5
    assert m["recall_5"] == 1
    import math
    assert m["ndcg_cut_3"] == pytest.approx((1/math.log2(3)+0.5)/(1+1/math.log2(3)))


def test_ndcg_uses_trec_linear_not_exponential_gains():
    import math
    m = ranking_metrics(["b", "a"], {"a": 3, "b": 1})
    assert m["ndcg_cut_3"] == pytest.approx((1+3/math.log2(3))/(3+1/math.log2(3)))


def test_missing_run_is_zero_and_no_qrels_is_excluded(tmp_path):
    (tmp_path/"run").write_text("q1 Q0 a 1 3.0 tag\n")
    (tmp_path/"qrels").write_text(json.dumps({"q1": {"a": 1}, "q2": {"b": 1}, "q3": {}}))
    result = evaluate(tmp_path/"run", tmp_path/"qrels")
    assert result["metrics"]["recip_rank"] == 0.5
    assert result["eligible_queries"] == 2
    assert result["queries_without_positive_qrels_excluded"] == ["q3"]


@pytest.mark.parametrize("ranking,qrels", [(["a", "a"], {"a": 1}), (["a"], {}),
                                          (["a"], {"a": float("nan")})])
def test_invalid_metrics(ranking, qrels):
    with pytest.raises(ValueError):
        ranking_metrics(ranking, qrels)


def test_aggregate_empty_fails():
    with pytest.raises(ValueError):
        aggregate([])


def test_trec_legacy_format_explicit(tmp_path):
    p = tmp_path/"run"
    p.write_text("q Q0 doc001 1 199 2.5 bm25\n")
    with pytest.raises(ValueError):
        read_trec(p)
    assert read_trec(p, True)["q"][0]["doc_id"] == "doc001"
    assert read_trec(p, True)["q"][0]["retriever_score"] == 2.5


def test_trec_duplicate_rejected(tmp_path):
    p = tmp_path/"run"
    p.write_text("q Q0 a 1 2 tag\nq Q0 a 2 1 tag\n")
    with pytest.raises(ValueError):
        read_trec(p)


def test_paper_initialization_and_no_silent_refiner():
    assert pseudo_query("original", 0) == "original"
    assert pseudo_query("original", 1, "refined") == "original refined"
    with pytest.raises(ValueError):
        pseudo_query("original", 0, "refined")
    with pytest.raises(ValueError):
        pseudo_query("original", 1)
    assert "(original)" in response_template("original")


def test_pseudo_selection_and_deep_copy():
    hits = [{"doc_id": str(i), "rank": i, "score": 10-i} for i in range(1, 5)]
    assert select_pseudo(hits) == ["1", "2", "3"]
    config = {"experiment_id": "synthetic_test", "source_revision": None,
              "model": None, "retriever": "fixture", "dataset_version": "fixture"}
    trace = trace_record(turn(), "", hits, config)
    hits[0]["score"] = -10
    assert trace["pseudo_reference_ranking"][0]["score"] == 9
    assert trace["original_response"] == turn().response
    assert json.loads(json.dumps(trace))["pseudo_reference_ids"] == ["1", "2", "3"]
    with pytest.raises(ValueError):
        trace_record(turn(), "", [], {})


def test_scoring_and_no_guessed_hyperparameters():
    with pytest.raises(ValueError, match="omits"):
        candidate_score(["a"], ["a"], weights=None, cutoffs=None)
    assert candidate_score(["a"], ["a"], weights=(0.2, 0.3, 0.5), cutoffs=(1, 5)) == 1
    with pytest.raises(ValueError):
        candidate_score(["a"], ["a"], weights=(1, 1, 1), cutoffs=(1,))


def test_strict_pairs_ties_and_identical_queries_excluded():
    pairs = strict_preference_pairs([{"id": "a", "query": "x", "score": 1},
                                    {"id": "b", "query": "y", "score": 0.2},
                                    {"id": "c", "query": "y", "score": 0.2}])
    assert [(p["chosen"], p["rejected"]) for p in pairs] == [("a", "b"), ("a", "c")]


def test_device_fallback():
    assert select_device() == "cpu"
    assert select_device("auto", True) == "cuda"
    assert select_device("cpu", True) == "cpu"
    with pytest.raises(RuntimeError, match="unavailable"):
        select_device("cuda")


def test_configuration_unknown_scoring_is_explicit():
    c = json.loads(Path("configs/phase1_baseline.yaml").read_text())
    assert c["paper_settings"]["score_weights"] is None
    assert c["allow_paid_api"] is False
    assert len(c["models"]["backbone"]["revision"]) == 40
