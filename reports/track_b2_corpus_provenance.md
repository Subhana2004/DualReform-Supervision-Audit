# Track B2 corpus provenance and feasibility

## Original TopiOCQA corpus

The [TopiOCQA author repository](https://github.com/McGill-NLP/topiocqa) points to
[Zenodo record 6149599](https://zenodo.org/records/6149599) for the segmented
Wikipedia corpus. The record currently offers a JSONL file of 13,609,578,305
bytes (MD5 `336610342930e19c493542e4df11dfb7`) and a TSV of
12,825,331,146 bytes (MD5 `e02914a92ec55df9f7aa72877b0179a5`). HTTP range
requests for the first 4 KiB of each returned 206 and advertised the expected
lengths. This verifies current partial download availability, not full-file
integrity. The local probes in `work/topiocqa-corpus-prefix.bin` and
`work/topiocqa-tsv-prefix.bin` are **not the corpus**.

The JSONL probe has `title`, `sub_title`, and `contents`, with no explicit
passage ID. The TSV probe has `id`, `text`, and `title`; the first row has ID
`1` and title `Eliza Fletcher [SEP] Introduction`. The author's
[`BM25/convert_to_pyserini_format.py`](https://github.com/McGill-NLP/topiocqa/blob/main/BM25/convert_to_pyserini_format.py)
skips the header, joins the TSV title around ` [SEP] `, prepends it to text,
and creates `doc{i}` from the enumerated row number. The first converted
identifier is therefore `doc1`. The author
[`BM25/create_index.sh`](https://github.com/McGill-NLP/topiocqa/blob/main/BM25/create_index.sh)
uses Pyserini `JsonCollection` and `DefaultLuceneDocumentGenerator` with 20
threads; it does not pin a Pyserini/Lucene version or analyzer configuration.
The README describes roughly 25.7 million passages. The benchmark files at
[Zenodo 6193037](https://zenodo.org/records/6193037) were separately obtained
in Phase 1; the archive SHA-256 is
`42f78d19cd9711364fda53f2905866605056ce48d108855196641b0dd41735ce`.
That benchmark record lists CC BY 4.0; it is distinct from the segmented
Wikipedia corpus record.

The two corpus representations total 26.4 GB before conversion or indexing.
They are raw TSV/JSONL files, so there is no archive extraction stage; the
conversion itself creates another full-size working copy before Lucene index
storage and temporary segment files are considered.
At the feasibility check, this laptop had 43,777,794,048 free disk bytes and
8,259,321,856 bytes physical RAM, with only 794,972,160 bytes available.
The TSV alone plus a comparable converted JSONL would leave about 17 GB for
Lucene index, temporary segments, and the existing workspace. The exact
Lucene index size is not author-published here, so this is a conservative
capacity assessment, not a measured index requirement. The author's README
also reports 148 GB peak RAM for DPR inference, which is distinct from BM25
indexing. A full corpus download and checksum were **not** attempted, and no
official corpus index was built. The corpus is available upstream; the current
machine is the constraint. The Zenodo metadata labels the corpus record
`cc-zero`; Wikipedia-origin content retains attribution/license considerations
and that metadata alone should not be read as relicensing every article.

## Independent larger alternative actually acquired

The experiment uses the complete, pinned
[Wikimedia Simple English Wikipedia `20231101.simple` Parquet shard](https://huggingface.co/datasets/wikimedia/wikipedia/blob/3e1f92c331f318af862b87e2319ed5dc26d80f5d/20231101.simple/train-00000-of-00001.parquet).
Its published revision is `3e1f92c331f318af862b87e2319ed5dc26d80f5d`,
size 156,885,218 bytes and SHA-256
`31bded16768a47c286becd292079122f5d7d4397a17b87d4250a00ccd581e6f0`.
The downloaded file matched both size and hash. The
[dataset card](https://huggingface.co/datasets/wikimedia/wikipedia)
lists CC BY-SA 3.0 / GFDL; the source's article URLs and stable IDs are
retained in the pinned Parquet source for attribution. The index's
`simplewiki:<id>` keys map back to those source rows. All 241,787 rows were
included by source order,
subject only to nonempty title/text; none were skipped. No article was chosen
by test case, entity, topic, or counterfactual. The first 10,000 and 50,000
rows form deterministic corpus-size sensitivity prefixes.

`scripts/acquire_track_b2_corpus.py` verifies the published checksum.
`scripts/build_track_b2_index.py` streams batches of 128 Parquet rows to a
disk-backed SQLite FTS5 index. Stable document ID is
`simplewiki:<Parquet id>`. The index contains 241,787 documents, occupies
696,393,728 bytes, has SHA-256
`381ab36b35ad771af85399bac9cd341ab0a62ba549ae2c0acab9a76630939110`,
and passed FTS integrity checks and `PRAGMA integrity_check=ok`. Prefix counts
are exactly 10,000 and 50,000. The full acquisition and index reside in
ignored `work/track_b2/`; `results/track_b2/corpus_manifest.json` records
the validation, software versions, sample IDs, and 243.0-second build.

The index uses FTS5 `unicode61` and unweighted title/body columns. Per the
[SQLite FTS5 documentation](https://www.sqlite.org/fts5.html), FTS5 BM25
fixes `k1=1.2`, `b=0.75`; the search code reverses its negative score for
descending-positive reporting. This is **not** the paper's verified Lucene
configuration or Track B's in-memory BM25 (`k1=0.9`, `b=0.4`). Simple English
Wikipedia article pages are also not the segmented English Wikipedia
passages, so source coverage, passage granularity, ranking, and support
cannot be treated as equivalent to the original TopiOCQA corpus. No official
TopiOCQA reproduction claim is made.

For a post-registration analyzer sensitivity check, the same source rows were
also indexed with FTS5 `porter unicode61`. That separate local index has
241,787 documents, occupies 478,650,368 bytes, and has SHA-256
`4b28d8ca0ae3c545671dfce1533970b65e522f069a131ee683746a89afa803a3`.
Its manifest is `results/track_b2/porter_manifest.json`; the large index file
remains ignored. This changes tokenization/stemming within SQLite FTS5, not
the BM25 implementation or passage corpus.
