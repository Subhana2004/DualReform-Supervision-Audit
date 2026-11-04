# Dataset audit

Executed against real public archives on 2026-11-04. **This is a dataset-integrity
run, not a retrieval/model baseline.** Exact archive URLs, SHA-256, sizes, member
names and revisions are locked in configs/data_sources.json. The run completed
with Python 3.10.11 on Windows, no Torch or GPU model loading.

| Release/split | Raw turns | Raw conversations | Complete-history turns retained | Conversations excluded for turn gaps | Context differences* | Empty answers in raw release |
|---|---:|---:|---:|---:|---:|---:|
| topiocqa/train | 45,450 | 3,509 | 45,450 | 0 | 0 | 0 |
| topiocqa/dev | 2,514 | 205 | 2,514 | 0 | 0 | 0 |
| qrecc/train | 63,501 | 10,823 | 56,971 | 1,025 | 43,622 | 5,555 |
| qrecc/test | 16,451 | 2,775 | 14,872 | 248 | 11,442 | 1,427 |

*Context differences compare released `Context` to preceding raw Question/Answer
rows in retained complete conversations. **A difference is not automatically a
dataset defect.** In particular, QReCC may use rewrites or differently formatted
context and omit empty content. This audit has not recovered the final author's
QReCC preprocessing. QReCC reconstruction is diagnostic and is not used for model
or pseudo-reference training. The only optional pipeline adapter selects TopiOCQA.

Total released turns inspected: **127,916**. Retained complete-history turns total
119,807. Excluded conversation/turn IDs and raw empty-answer IDs are saved under
results/phase1. Empty answers are counted independently of the turn-gap policy;
retained counts are not counts of reference-free training eligibility. The
initial-pseudo adapter excludes empty responses explicitly.

## Acquisition, licensing, and version identity

| Archive | Bytes | SHA-256 |
|---|---:|---|
| topiocqa.zip | 7,801,758 | `42f78d19cd9711364fda53f2905866605056ce48d108855196641b0dd41735ce` |
| qrecc_data.zip | 7,971,464 | `6ed52a0b0e495f752424b15742119a5f8f33ca7a029c07122be1b849de19a308` |

**TopiOCQA.** Authoritative [project page](https://mcgill-nlp.github.io/topiocqa/)
links [Zenodo record 6193037](https://zenodo.org/records/6193037), DOI
10.5281/zenodo.6193037, dataset license **CC BY 4.0**. This archive contains
45,450 train and 2,514 dev turns. The upstream GitHub repository's code LICENSE
is CC BY-NC-SA 4.0; it is not substituted for the Zenodo data license. The updated
download script at author repo commit49b710e9746b32bad2296043e1e2fc4a1532bfdf
also references record7709644 (larger JSON files). That later release was
catalog-inspected but not silently mixed with the acquired original release.

The release train/dev numeric conversation IDs restart, so split names are part
of local IDs. The paper's approximate 51K total is not the acquired 47,964 total.
We cannot establish identical row eligibility to the paper from approximate
counts. The public dev set is a held-out evaluation target here; the paper's
exact validation selection remains unknown.

**QReCC.** Authoritative [Apple repository](https://github.com/apple/ml-qrecc),
revision1d174464290790c0198b474ad022952ecd83b76b, dataset archive at
dataset/qrecc_data.zip. Dataset license **CC BY-SA 3.0** per its README; code has
a separate LICENSE. Train/test boundaries are preserved. The raw archive has
63,501/16,451 turns. No full web corpus was acquired. Answer_URL is a URL, not
a stable corpus passage ID. Retrieval qrels/corpus mapping remains a blocker.

**SciConvQA.** The [KISTI catalog](https://aida.kisti.re.kr/data/e306c9c6-324e-47a5-9188-af72b898a22b?lang=en)
is accessible and lists version1.0, DOI10.23057/116, 900 conversations, 11,953
turns, a 1.25MB ZIP and **CC BY-NC** terms (no license version inferred).
The download is application-controlled. No application was submitted, researcher
contact made, or protected download attempted. The 120,916-article corpus has
separate acquisition requirements. Acquired/validated usable records: **0**.
Paper Table12 p.20 reports9,999 train/1,954 test turns and750/150 conversations;
those are author-reported counts, not local validation.

Additional final-paper UltraChat100K/10K experiments were identified on p.32;
the exact sector/split version was not recovered or downloaded. No unrelated
dataset was substituted for a missing original benchmark.

## Subsets, leakage, and gold boundary

Seed42 SHA-256 ordering selects whole conversations. Eight training conversations
are held out as validation *before* sampling. Eight conversations are sampled
independently from effective train, validation, and evaluation, for each public
dataset:48 conversations/**457 turns** total. TopiOCQA's
held-out validation contains119 turns; QReCC's contains60. The sample is for
engineering validation, not statistical performance claims or a paper-equivalent
training subset. Selection does not inspect relevance annotations or topics.

The boundary checks found zero conversation-ID overlaps under release namespaces
and zero duplicate full-session text fingerprints across effective partitions.
This is not proof of absence of partial topic overlap or near duplicates.
Histories use ordered turns and never include future rows. TopiOCQA matches all
released histories. QReCC context differences remain explicitly unresolved.

Training inputs allow only dataset/split/conversation/turn IDs, query, observed
response and prior query/response history. Gold passage columns, annotated
rewrites, rationale and topic are omitted. Full sample text is private in ignored
data/processed; committed per-example outputs contain input hashes and schema
status. No gold labels were used for preference construction or model training.

## Retrieval eligibility

No benchmark retrieval accuracy can be computed from these archives alone in
this workspace: full corpora, exact passage mapping, final split filtering and a
trained checkpoint are missing. TopiOCQA's corpus is the author-released segmented
Wikipedia collection (download_data.py references Zenodo6149599); the copy assumes
doc-prefixed IDs and strips three characters. That transformation must be
validated against the actual index, not assumed. UNANSWERABLE turns number
3,652 train/174 dev in this TopiOCQA release; exact paper handling is unverified.
Do not convert rationale or topic strings into invented gold IDs.
