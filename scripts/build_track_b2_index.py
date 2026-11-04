"""Stream the complete pinned Simple Wikipedia shard into disk-backed FTS5 indexes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import time

import pyarrow
import pyarrow.parquet as pq

from dualreform_audit.io import digest, write_json


def build(config_path="configs/track_b2.json", output="results/track_b2/corpus_manifest.json"):
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    source = config["corpus"]
    path = Path(source["local_path"])
    if not path.is_file() or path.stat().st_size != source["size_bytes"] or (
            digest(path) != source["sha256"]):
        raise ValueError("Pinned corpus Parquet missing or changed")
    target = Path(source["index_path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise ValueError("Index already exists; preserve it or version a new path")
    partial = target.with_suffix(".partial.sqlite")
    if partial.exists():
        raise ValueError("Partial index exists; inspect before retrying")
    par = pq.ParquetFile(path)
    if par.metadata.num_rows != source["prefix_sizes"][-1]:
        raise ValueError("Parquet row count differs from predeclared corpus")
    started, clock = datetime.now(timezone.utc).isoformat(), time.perf_counter()
    con = sqlite3.connect(partial)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    con.execute("PRAGMA cache_size=-8192")
    con.execute("PRAGMA temp_store=FILE")
    con.execute("CREATE TABLE ids (doc_id TEXT PRIMARY KEY)")
    sizes = source["prefix_sizes"]
    tables = {size: f"wiki_{size}" for size in sizes}
    for table in tables.values():
        con.execute(f"CREATE VIRTUAL TABLE {table} USING fts5("
                    "doc_id UNINDEXED, title, body, tokenize='unicode61')")
    seen, inserted, skipped, text_bytes = 0, 0, 0, 0
    sample_ids = []
    try:
        for batch in par.iter_batches(batch_size=128, columns=["id", "url", "title", "text"]):
            for row in batch.to_pylist():
                seen += 1
                doc_id = "simplewiki:" + str(row["id"])
                if not row["id"] or not row["title"] or not row["text"]:
                    skipped += 1
                    continue
                if not str(row["url"]).startswith("https://simple.wikipedia.org/wiki/"):
                    raise ValueError(f"Unexpected article URL for {doc_id}")
                con.execute("INSERT INTO ids VALUES (?)", (doc_id,))
                if len(sample_ids) < 5:
                    sample_ids.append({"doc_id": doc_id, "url": row["url"],
                                       "title": row["title"]})
                values = (doc_id, row["title"], row["text"])
                con.execute(f"INSERT INTO {tables[sizes[-1]]} VALUES (?,?,?)", values)
                for size in sizes[:-1]:
                    if seen <= size:
                        con.execute(f"INSERT INTO {tables[size]} VALUES (?,?,?)", values)
                inserted += 1
                text_bytes += len(row["text"].encode("utf-8"))
            if seen % 1024 == 0:
                con.commit()
        con.commit()
        counts = {str(size): con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                  for size, table in tables.items()}
        if seen != par.metadata.num_rows or counts[str(sizes[-1])] != inserted:
            raise ValueError("Indexed rows do not match source rows")
        for table in tables.values():
            con.execute(f"INSERT INTO {table}({table}) VALUES ('integrity-check')")
        con.commit()
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError(f"SQLite integrity failure: {integrity}")
    except Exception:
        con.close()
        partial.unlink(missing_ok=True)
        raise
    con.close()
    partial.replace(target)
    manifest = {
        "status": "indexed", "timestamp_utc": started,
        "source_url": source["url"], "source_revision": source["revision"],
        "source_size_bytes": source["size_bytes"], "source_sha256": source["sha256"],
        "source_rows": seen, "indexed_rows": inserted, "skipped_empty_rows": skipped,
        "indexed_utf8_text_bytes": text_bytes, "prefix_document_counts": counts,
        "index_size_bytes": target.stat().st_size, "index_sha256": digest(target),
        "document_id_rule": "simplewiki:<Parquet id>; all nonempty rows",
        "sample_ids": sample_ids,
        "schema": "FTS5(doc_id UNINDEXED,title,body) with unicode61; title/body weights 1",
        "bm25_k1": 1.2, "bm25_b": 0.75,
        "source_software": {"python_sqlite": sqlite3.sqlite_version,
                            "pyarrow": pyarrow.__version__},
        "config_sha256": hashlib.sha256(Path(config_path).read_bytes()).hexdigest(),
        "build_seconds": time.perf_counter() - clock,
        "integrity_check": integrity,
        "license": source["license"],
        "index_local_path": str(target), "index_committed": False}
    write_json(output, manifest)
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", default="configs/track_b2.json")
    p.add_argument("--output", default="results/track_b2/corpus_manifest.json")
    a = p.parse_args()
    x = build(a.config, a.output)
    print(json.dumps({k: x[k] for k in ("source_rows", "indexed_rows",
                                           "index_size_bytes", "build_seconds")}, indent=2))
