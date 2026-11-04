"""Independent small-corpus BM25 and controlled counterfactual validation.

This is neither official DualReform code nor its original passage index.
"""
from collections import Counter
from dataclasses import replace
import math
import re


def tokens(text):
    if not isinstance(text, str):
        raise ValueError("Expected text")
    return re.findall(r"\w+", text.casefold(), flags=re.UNICODE)


class BM25:
    def __init__(self, documents, k1=0.9, b=0.4):
        if not documents or k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("Invalid corpus or BM25 parameters")
        self.documents = documents
        ids = [d.get("doc_id") for d in documents]
        if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
            raise ValueError("Invalid or duplicate passage IDs")
        if any(not isinstance(d.get("title"), str) or not isinstance(d.get("text"), str)
               or not d["text"] for d in documents):
            raise ValueError("Missing document text/title")
        self.k1, self.b = k1, b
        self.vectors = [Counter(tokens(d["title"] + " " + d["text"])) for d in documents]
        self.lengths = [sum(v.values()) for v in self.vectors]
        self.average_length = sum(self.lengths) / len(documents)
        self.df = Counter(term for vector in self.vectors for term in vector)

    def search(self, query, k=100):
        if k < 1 or not tokens(query):
            raise ValueError("Invalid query or cutoff")
        n, qterms = len(self.documents), sorted(set(tokens(query)))
        ranking = []
        for doc, vector, length in zip(self.documents, self.vectors, self.lengths):
            score = 0.0
            for term in qterms:
                tf = vector.get(term, 0)
                if tf:
                    df = self.df[term]
                    idf = math.log1p((n - df + 0.5) / (df + 0.5))
                    score += idf * tf * (self.k1 + 1) / (
                        tf + self.k1 * (1 - self.b + self.b * length / self.average_length))
            if score > 0:
                ranking.append((doc["doc_id"], score))
        ranking.sort(key=lambda pair: (-pair[1], pair[0]))
        return [{"doc_id": doc_id, "rank": rank, "score": score}
                for rank, (doc_id, score) in enumerate(ranking[:k], 1)]


def validate_pair(spec, turn, followup, labels, title_to_id):
    category = spec["category"]
    if category not in ("A", "B", "C", "D") or turn.split != "train" or turn.dataset != "topiocqa":
        raise ValueError("Only labeled TopiOCQA training pairs are eligible")
    if (turn.conversation_id != followup.conversation_id
            or followup.turn_id != turn.turn_id + 1
            or not followup.history or followup.history[-1] != (turn.query, turn.response)):
        raise ValueError("Missing aligned next turn")
    old, new = spec["old"], spec["new"]
    if not old or turn.response.count(old) != 1 or not new or new == old:
        raise ValueError("Intervention must replace exactly one observed span")
    modified = turn.response.replace(old, new, 1)
    original_targets = labels["original_targets"]
    changed_targets = labels["counterfactual_targets"]
    if not original_targets or not changed_targets or any(
            title not in title_to_id for title in original_targets + changed_targets):
        raise ValueError("Missing corpus passage for a manually labeled referent")
    if category == "A":
        if original_targets != changed_targets or old in original_targets or new in changed_targets:
            raise ValueError("Same-referent factual change requires an unchanged subject")
        if tokens(old) == tokens(new) or old not in title_to_id or new not in title_to_id:
            raise ValueError("A needs a substantive factual change")
    elif category == "B":
        if (len(original_targets) != 1 or len(changed_targets) != 1
                or original_targets == changed_targets or old != original_targets[0]
                or new != changed_targets[0]):
            raise ValueError("B must replace the sole named referent")
        if not (set(tokens(followup.query)) & {"he", "she", "this", "it", "they"}):
            raise ValueError("B follow-up must refer to the changed entity")
    elif category == "C":
        if (len(original_targets) != 1 or len(changed_targets) != 2
                or original_targets[0] not in changed_targets
                or any(title not in new for title in changed_targets)):
            raise ValueError("C must introduce a second plausible referent")
    else:
        if tokens(turn.response) != tokens(modified) or original_targets != changed_targets:
            raise ValueError("D must preserve lexical content and referent")
    return {"id": spec["id"], "category": category, "source": "TopiOCQA train",
            "conversation_id": turn.conversation_id, "turn_id": turn.turn_id,
            "followup_turn_id": followup.turn_id, "question": turn.query,
            "followup_question": followup.query, "original_response": turn.response,
            "modified_response": modified, "history": turn.history,
            "intervention_old": old, "intervention_new": new,
            "original_target_ids": [title_to_id[t] for t in original_targets],
            "modified_target_ids": [title_to_id[t] for t in changed_targets],
            "manual_rationale": labels["rationale"]}


def turn_for_arm(turn, response):
    return replace(turn, response=response)


def overlap(left, right, k):
    a, b = ({h["doc_id"] for h in hits[:k]} for hits in (left, right))
    return len(a & b) / len(a | b) if a | b else None


def rank_of(hits, doc_id):
    return next((h["rank"] for h in hits if h["doc_id"] == doc_id), None)
