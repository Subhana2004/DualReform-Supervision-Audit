"""Gold-blind conversational projections and conversation-level sampling."""
import hashlib
import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Turn:
    dataset: str
    split: str
    conversation_id: str
    turn_id: int
    query: str
    response: str
    history: tuple

    @property
    def id(self):
        return f"{self.dataset}:{self.conversation_id}:{self.turn_id}"

    def training_input(self):
        # Explicit allowlist: annotated rewrites, rationale, topics and gold IDs cannot enter.
        return asdict(self)


def normalize(records, dataset, split, incomplete_history="error"):
    if incomplete_history not in ("error", "exclude_conversation"):
        raise ValueError("Unknown incomplete history policy")
    if not isinstance(records, list) or not records:
        raise ValueError("Expected a nonempty list of conversation turns")
    grouped = {}
    missing = []
    for index, row in enumerate(records):
        if not isinstance(row, dict):
            raise ValueError(f"Record {index}: expected mapping")
        try:
            if dataset == "qrecc":
                cid, tid = str(row["Conversation_no"]), row["Turn_no"]
                question, answer = row["Question"], row["Answer"]
            elif dataset == "topiocqa":
                cid, tid = str(row["Conversation_no"]), row["Turn_no"]
                question, answer = row["Question"], row["Answer"]
            else:
                raise ValueError(f"Unsupported dataset: {dataset}")
        except KeyError as exc:
            raise ValueError(f"Record {index}: missing {exc}") from exc
        if not cid or isinstance(tid, bool) or not isinstance(tid, int) or tid < 1:
            raise ValueError(f"Record {index}: invalid conversation or turn ID")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"Record {index}: missing/malformed question")
        if not isinstance(answer, str):
            raise ValueError(f"Record {index}: malformed answer")
        if not answer.strip():
            missing.append(f"{cid}:{tid}")
        # Official train/dev/test releases restart numeric conversation IDs.
        # Preserve that namespace; never infer leakage from the integer alone.
        cid = f"{split}/{cid}"
        group = grouped.setdefault(cid, {})
        if tid in group:
            raise ValueError(f"Duplicate turn {cid}:{tid}")
        group[tid] = (question, answer)
    turns, excluded = [], []
    for cid in sorted(grouped):
        history = []
        group = grouped[cid]
        if sorted(group) != list(range(1, max(group) + 1)):
            if incomplete_history == "error":
                raise ValueError(f"Non-contiguous history in conversation {cid}")
            excluded.append({"conversation_id": cid, "turns": len(group),
                             "reason": "non_contiguous_turn_ids"})
            continue
        for tid in sorted(group):
            question, answer = group[tid]
            turns.append(Turn(dataset, split, cid, tid, question, answer, tuple(history)))
            history.append((question, answer))
    return turns, {"raw_turns": len(records), "raw_conversations": len(grouped),
                   "turns": len(turns), "conversations": len(grouped)-len(excluded),
                   "excluded_conversations": excluded,
                   "empty_responses": missing, "unanswerable_responses": sum(
                       t.response.strip().upper() == "UNANSWERABLE" for t in turns)}


def subset(turns, conversations, seed):
    ids = sorted({t.conversation_id for t in turns}, key=lambda cid: (
        hashlib.sha256(f"{seed}:{cid}".encode()).hexdigest(), cid))
    if not isinstance(conversations, int) or not 0 < conversations <= len(ids):
        raise ValueError("Invalid conversation sample size")
    selected = set(ids[:conversations])
    return [t for t in turns if t.conversation_id in selected]


def split_training(turns, validation_conversations, seed):
    validation = subset(turns, validation_conversations, seed)
    held = {t.conversation_id for t in validation}
    train = [t for t in turns if t.conversation_id not in held]
    if not train:
        raise ValueError("Empty training split")
    return train, validation


def assert_disjoint(*splits):
    for i, left in enumerate(splits):
        for right in splits[i + 1:]:
            a = {(t.dataset, t.conversation_id) for t in left}
            b = {(t.dataset, t.conversation_id) for t in right}
            if a & b:
                raise ValueError(f"Conversation leakage: {sorted(a & b)[:5]}")
            # Full-conversation text fingerprints catch duplicated sessions with changed IDs.
            def fingerprints(turns):
                groups = {}
                for t in turns:
                    groups.setdefault(t.conversation_id, []).append((t.turn_id, t.query, t.response))
                return {hashlib.sha256(json.dumps(sorted(v), ensure_ascii=False).encode()).hexdigest()
                        for v in groups.values()}
            if fingerprints(left) & fingerprints(right):
                raise ValueError("Duplicate conversation text across splits")
