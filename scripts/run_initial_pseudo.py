"""Paper-derived iteration-zero response retrieval using an externally supplied Lucene index.

This is a partial reconstruction, not execution of the official DualReform code.
No gold-label path is accepted. Corpus metadata must identify the external index.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from dualreform_audit.data import Turn
from dualreform_audit.io import digest, environment, git_sha, write_json, write_jsonl
from dualreform_audit.trace import trace_record
from paper_reimplementation.signals import pseudo_query, select_pseudo


def execute(inputs, index, corpus_manifest, output, limit=32):
    meta = json.loads(Path(corpus_manifest).read_text(encoding="utf-8"))
    for field in ("dataset", "corpus_version", "index_sha256_manifest", "doc_id_prefix"):
        if field not in meta:
            raise ValueError(f"Missing corpus provenance: {field}")
    if meta["dataset"] != "topiocqa" or not meta["index_sha256_manifest"]:
        raise ValueError("Expected a documented TopiOCQA corpus index")
    # Caller attaches an already acquired index; this runner never downloads a multi-GB corpus.
    if not Path(index).is_dir() or limit < 1:
        raise ValueError("Missing index or invalid limit")
    from pyserini.search.lucene import LuceneSearcher
    searcher = LuceneSearcher(str(index))
    searcher.set_bm25(0.9, 0.4)
    clock, traces, excluded = time.perf_counter(), [], []
    rows = [json.loads(line) for line in Path(inputs).read_text(encoding="utf-8").splitlines()]
    allowed = set(Turn.__dataclass_fields__)
    if any(set(r) != allowed or r["split"] != "train" or r["dataset"] != "topiocqa" for r in rows):
        raise ValueError("Only gold-blind TopiOCQA training inputs are allowed")
    configuration = {"experiment_id": "paper-derived-initial-pseudo", "source_revision": None,
                     "model": "none: Algorithm 1 iteration zero", "retriever":
                     {"backend": "pyserini.lucene", "k1": 0.9, "b": 0.4, "top_k": 100},
                     "dataset_version": meta, "iteration": 0}
    for row in rows[:limit]:
        turn = Turn(**row)
        if not turn.response.strip():
            excluded.append({"id": turn.id, "reason": "empty_response"})
            continue
        query = pseudo_query(turn.response, 0)
        retrieved = searcher.search(query, k=100)
        prefix = meta["doc_id_prefix"]
        hits = []
        for rank, hit in enumerate(retrieved, 1):
            if prefix and not hit.docid.startswith(prefix):
                raise ValueError("Index ID namespace mismatch; refusing implicit prefix removal")
            hits.append({"doc_id": hit.docid[len(prefix):], "rank": rank, "score": hit.score})
        select_pseudo(hits)
        traces.append(trace_record(turn, "", hits, configuration))
    out = Path(output)
    write_jsonl(out / "per_example.jsonl", traces)
    write_json(out / "metrics.json", {"experiment_type": "paper_derived_initial_pseudo_only",
               "examples": len(traces), "excluded": excluded, "retrieval_accuracy": None,
               "runtime_seconds": time.perf_counter() - clock})
    write_json(out / "run_manifest.json", {"execution_status": "completed_partial_reconstruction",
               "timestamp_utc": datetime.now(timezone.utc).isoformat(), "git_sha": git_sha(),
               "model_version": None, "source_revision": None, "dataset_version": meta,
               "input_sha256": digest(inputs), "parameters": configuration,
               "environment": environment(), "result_paths": [str(out / "per_example.jsonl")],
               "gpu_execution": "NOT EXECUTED: sparse retrieval uses CPU"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("inputs", "index", "corpus-manifest", "output"):
        parser.add_argument("--" + arg, required=True)
    parser.add_argument("--limit", type=int, default=32)
    a = parser.parse_args()
    execute(a.inputs, a.index, a.corpus_manifest, a.output, a.limit)
