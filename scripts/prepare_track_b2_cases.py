"""Freeze supplementary probes and a blank, ranking-blind review worksheet."""
import json
from pathlib import Path

from dualreform_audit.io import write_json, write_jsonl


def prepare(out="results/track_b2"):
    root = Path(out)
    sampled = [json.loads(line) for line in (root / "preregistered_pairs.jsonl").read_text(
        encoding="utf-8").splitlines()]
    old = {r["id"]: r for r in (json.loads(line) for line in Path(
        "results/track_b/pairs_generated.jsonl").read_text(encoding="utf-8").splitlines())}
    # Each current-question edit names a different target explicitly. These are
    # synthetic diagnostic probes, not naturally occurring conversation turns.
    changes = [
        ("B_scott", "A_scott_actor", "who played Black Widow in the Marvel films?",
         "Scarlett Johansson"),
        ("B_space", "A_space_developer", "who created Super Mario Bros.?",
         "Shigeru Miyamoto"),
        ("B_carol", "A_carol_author", "who wrote Pride and Prejudice?", "Jane Austen"),
        ("B_blade", "A_blade_director", "who directed the 1979 film Alien?", "Ridley Scott"),
    ]
    probes = []
    for ident, source_id, question, response in changes:
        source = old[source_id]
        probes.append({"id": ident, "category": "B", "conversation_id": source["conversation_id"],
                       "turn_id": source["turn_id"], "dataset": "topiocqa", "split": "train",
                       "question": source["question"], "history": source["history"],
                       "original_response": source["original_response"],
                       "modified_question": question, "modified_response": response,
                       "current_intent_changed": True,
                       "source": "synthetic current-question edit of a real TopiOCQA turn",
                       "intervention": "change explicit current question and response together"})
    # Ambiguity probes intentionally have no single target. They are analyzed
    # descriptively, never scored as a unique correct retrieval target.
    source = old["A_scott_actor"]
    probes.append({"id": "C_scott_character", "category": "C",
                   "conversation_id": source["conversation_id"], "turn_id": source["turn_id"],
                   "dataset": "topiocqa", "split": "train", "question": source["question"],
                   "history": source["history"], "original_response": source["original_response"],
                   "modified_question": "who played the main character in Scott Pilgrim vs. the World?",
                   "modified_response": "Mary Elizabeth Winstead",
                   "current_intent_changed": True,
                   "plausible_interpretations": ["Scott Pilgrim", "Ramona Flowers"],
                   "source": "synthetic ambiguity probe from a real TopiOCQA turn",
                   "intervention": "replace explicit character with ambiguous main character"})
    source = old["B_yttrium_person"]
    probes.append({"id": "C_yttrium_discoverer", "category": "C",
                   "conversation_id": source["conversation_id"], "turn_id": source["turn_id"],
                   "dataset": "topiocqa", "split": "train", "question": source["question"],
                   "history": source["history"], "original_response": source["original_response"],
                   "modified_question": "who first found or isolated this element?",
                   "modified_response": "Carl Axel Arrhenius",
                   "current_intent_changed": True,
                   "plausible_interpretations": ["first identification", "first isolation"],
                   "source": "synthetic ambiguity probe from a real TopiOCQA turn",
                   "intervention": "conflate distinct discovery and isolation relations"})
    write_jsonl(root / "supplementary_cases.jsonl", probes)
    # Reviewer fields stay blank; agreement and factuality cannot be inferred
    # from the benchmark answer or from retrieval rankings.
    worksheet = []
    for case in sampled + probes:
        if case["category"] == "D":
            continue
        worksheet.append({"case_id": case["id"], "conversation_id": case["conversation_id"],
                          "current_question": case["question"],
                          "history": case["history"],
                          "observed_response": case["original_response"],
                          "edited_question": case["modified_question"],
                          "edited_response": case["modified_response"],
                          "intended_information_need": None,
                          "relevant_passage_ids": [],
                          "response_claim_support": "unreviewed",
                          "counterfactual_claim_support": "unreviewed",
                          "counterfactual_validity": "unreviewed",
                          "reviewer_id": None, "reviewer_notes": None})
    write_jsonl(root / "blind_review_worksheet.jsonl", worksheet)
    write_json(root / "case_preparation.json", {"sampled_cases": len(sampled),
               "supplementary_cases": len(probes), "review_items": len(worksheet),
               "independent_completed_reviews": 0,
               "supplementary_probes_are_conversation_disjoint": False,
               "retrieval_rankings_visible_during_preparation": False})
    return len(probes), len(worksheet)


if __name__ == "__main__":
    print(prepare())
