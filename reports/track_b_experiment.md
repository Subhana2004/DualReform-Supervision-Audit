# Track B: independent response-to-retrieval diagnostic

**Status:** executed on 2026-11-04. **Research decision: Outcome B — failure
inconclusive for DualReform.** Three same-referent interventions lost a manually
identified subject page in this independent small-corpus BM25 experiment. The
original segmented corpus, official implementation, checkpoint, and original
candidate artifacts remain unavailable. This is **not** an official DualReform
reproduction, a held-out benchmark score, or evidence that its trained model fails.

## Source and method boundary

The [final paper](https://proceedings.mlr.press/v306/kim26ak.html) states that
Algorithm 1 iteration zero retrieves with the observed response, without response
refinement. Our `paper_reimplementation.signals.pseudo_query(response, 0)` enforces
that rule. We reused the Phase 1 gold-blind `Turn` adapter, top-three selector,
trace capture, split checks, and result conventions. We did **not** port or run
unverified third-party DualReform training code. No supervision guard was added.

The [TopiOCQA author repository](https://github.com/McGill-NLP/topiocqa) points to
its segmented Wikipedia collection. [Zenodo record 6149599](https://zenodo.org/records/6149599)
lists a 13.6 GB JSONL and 12.8 GB TSV, together 26.4 GB. The author README says the
corpus has about 25.7 million passages. We did not download or index it. No
original passage-ID map is asserted. Our alternative is a **curated, article-level
58-page English Wikipedia lead snapshot** fetched on 2026-11-04 from the public
Action API. Titles were selected from training-conversation topics, observed
training answer entities, proposed substitutions, and generic distractors
before retrieval results. No evaluation answers, gold reference passages, or
relevance labels constructed this corpus. Each page has a stable `enwiki:<pageid>` ID,
revision URL, revision ID and text SHA-256 in
`data/track_b_wikipedia_leads.jsonl`. The 117,550 extracted characters occupy
132,443 bytes in JSONL. Article text is CC BY-SA 4.0 with attribution and extraction notice
in `data/track_b_wikipedia_leads.LICENSE.md`. The 2026 leads are neither the 2022
segments nor a representative Wikipedia sample.

The benchmark source is the [TopiOCQA Zenodo 6193037 archive](https://zenodo.org/records/6193037)
(SHA-256 `42f78d19cd9711364fda53f2905866605056ce48d108855196641b0dd41735ce`,
CC BY 4.0). Eleven predeclared pair edits cover six **training** conversations,
after the Phase 1 seed-42 eight-conversation validation holdout. This is a
diagnostic on natural benchmark conversation context with controlled edited
answers, not independent natural model errors. There are four factual-change /
same-referent cases (A), two referent-change cases (B), two deliberately ambiguous
cases (C), and three punctuation controls (D). The edit specifications,
pre-retrieval manual target annotations, and post-run single-reviewer judgments
are separate files. All eleven use the immediately following benchmark question
only for referent annotation; **the retrieval queries never contain that future
question**.

## Executed retrieval

One unchanged index and configuration served both arms of every pair. The
response-only arm uses the observed answer string, or its controlled edit. Our
independent BM25 uses Unicode `\w+` tokenization, case folding, no stemming or
stopwords, article title plus lead once, Lucene-style positive IDF, `k1=0.9`,
`b=0.4`, stable doc-ID tie breaks, and a maximum of 100 positive-score hits.
These are documented choices, **not** a verified Pyserini analyzer or published
passage index. A question-anchored diagnostic adds prior and current questions
to the response. A lightweight title filter keeps articles whose titles have at
least two content tokens and two-thirds coverage in the prior/current questions
from that anchored ranking. This comparator is not an Intent-Aware Supervision
Guard. Every retrieval call was immediately repeated and equality-checked; a
separate full rerun produced an identical `paired_rankings.jsonl` SHA-256.

| Measurement | Observed |
|---|---:|
| Corpus documents | 58 |
| Predeclared pairs / distinct conversations | 11 / 6 |
| Ranking traces / retrieval calls including repeats | 66 / 132 |
| Selections with fewer than three hits, all methods | 33 / 66 |
| Response-only selections with fewer than three hits | 11 / 22 |
| BM25 in-memory build / paired retrieval measured time | 0.014 s / 0.074 s |
| Peak traced Python allocation (not process RSS) | 1,886,675 bytes |
| GPU or model execution | None |

The exact run-specific times, environment, corpus hash and page revisions are in
`results/track_b/run_manifest.json`. The ranking file contains full scored lists,
paired response text, selected IDs, and Phase 1 format traces. Metrics and
case-level rank changes are in `results/track_b/metrics.json`. The final repeat
ranking hash is recorded in the verification artifact.

## Results and interpretation

The manually nominated subject page was in the response-only top three before
all four A edits. It remained after one edit and was absent after three. The
three losses coincide with the edited response yielding only one or two
positive-score articles, so these are **small-corpus target-loss observations**,
not a reliable estimate of the published system's factual-contamination rate.
The response-only pseudo-reference list changed in all four A pairs. The simple
question-anchored diagnostic recovered the nominated page in all four edited A
pairs, but lost one of the two B changed referents from its top three. The title
filter retained the nominated page for all A edits but never produced three hits
in any arm; it is unsuitable as a replacement pseudo-reference method here.

| Category | Response-only result | Interpretation |
|---|---|---|
| A: factual edit, same referent | Target loss 3/4; factual-contamination proxy 3/4; top-three list changed 4/4 | Three local target losses, one falsifying stable-target case |
| B: referent changed | New entity rank 1 in both edited arms; responsive 2/2 | Expected change, not contamination |
| C: ambiguous reference | One edit includes both plausible pages in top three; the other puts the second at rank 5 | No unique gold interpretation or justified error count |
| D: punctuation | Full rankings identical 3/3 | Stable negative controls |

No confidence interval is reported: the eleven cases are a deliberately curated,
small diagnostic set, not a probability sample. Category counts and page-identity
judgments are separated from automatic ranking arithmetic. Detailed causal
checks and counterexamples are in `track_b_failure_analysis.md`; limits and the
smallest resolving experiment are in `track_b_limitations.md`.

## Reproduce

With Python 3.10 and the Phase 1 audit requirements installed, acquire the
TopiOCQA archive using `python -m scripts.acquire_data`, then run:

```bash
PYTHONPATH=src:. python -m scripts.generate_track_b_pairs
PYTHONPATH=src:. python -m scripts.run_track_b
pytest -q
ruff check src scripts tests paper_reimplementation
python -m compileall -q src scripts tests paper_reimplementation
```

On PowerShell, set `$env:PYTHONPATH='src;.'` before the Python commands. The
committed Wikipedia snapshot is sufficient for exact reruns; the fetch script
refuses to overwrite it unless explicitly invoked with `--refresh`, which would
create a different corpus version and require a new audit. No paid API, GPU,
Kaggle notebook, model weight, or protected resource is required.
