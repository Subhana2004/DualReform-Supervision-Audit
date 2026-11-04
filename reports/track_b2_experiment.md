# Track B2 experiment: current-turn retrieval diagnostic

## Design and separation of inputs from evaluation

Track B2 freezes 30 independent TopiOCQA training conversations selected by
hash order after the Phase 1 eight-conversation validation holdout. The first
eligible `who` question and 2–4 title-case-word answer in each selected
conversation produced a same-current-intent response replacement (A) and
punctuation control (D). The sampled 60 pairs were committed in
`23fcfe6` **before** Track B2 retrieval. A fixed four-name replacement pool
and seed `20261105` make selection reproducible. The regex is syntactic: a
single-agent screening flagged five cases with organizations, a group,
or a fictional character/plural-answer mismatch
(`results/track_b2/semantic_screening.json`). All 30 are retained in the intention-to-treat
lexical diagnostic; they must not all be called verified factual errors.

Four supplemental B probes jointly edit the **current question and response**
to explicitly request another subject. Two C probes make the current question
ambiguous and retain multiple plausible interpretations. These six probes
reuse historical Track B conversations, so they are **not conversation
disjoint from each other or from the prior exploratory study** and do not
increase the independent sampled-conversation count. They are synthetic
diagnostics, not natural user behavior. No independently verified naturally
occurring factual error was available; category E has zero cases. Historical
A cases are re-run separately without selecting them by new outcome.

`results/track_b2/blind_review_worksheet.jsonl` was frozen with 36 empty
review items before rankings were inspected. A reviewer must use the current
question, observed response, prior context, and independently checked source
passages. Its `relevant_passage_ids`, claim support, validity, and reviewer
fields remain unfilled. There is no second reviewer or agreement statistic.
Benchmark gold fields, future turns, and manual labels never enter a query.
Current-question relevance and previous-response factual correctness are
different annotations; a next-question pronoun belongs only to an optional
continuity analysis.

## Execution

The corpus is the complete 241,787-article Simple English Wikipedia snapshot
documented in `reports/track_b2_corpus_provenance.md`. The same FTS5 index,
`unicode61` analyzer, BM25 scoring, source-order prefix, and sample are used
for each comparator. The independent methods are (1) response-only
paper-derived iteration-zero query, (2) prior and current question plus
response, and (3) prior and current question without response. They are
diagnostic query constructions, not trained DualReform or an official model.
The original official DualReform implementation remains unavailable and
unverified; no result here is labeled an official baseline.
The script stores the actual tokenized FTS query, top-100 ranking and scores,
top-three selected passage text, match count, and paired changes. It checks
determinism by repeating a query. Smaller 10,000/50,000-document prefixes
test corpus-size sensitivity on the 30-conversation sample; B/C use full
coverage. No GPU is used.

From the repository root, the reproducible command order is:

```powershell
python -m pip install -r requirements-track-b2.txt
$env:PYTHONPATH='src;.'
python scripts/acquire_track_b2_corpus.py
python scripts/build_track_b2_index.py
python scripts/preregister_track_b2.py
python scripts/prepare_track_b2_cases.py
python scripts/run_track_b2.py
python scripts/run_track_b2_legacy.py
python scripts/analyze_track_b2.py
python scripts/analyze_track_b2_legacy.py
python scripts/compare_track_b2_porter.py
```

The index builder intentionally refuses to overwrite an existing index. A
fresh reproduction should use a clean checkout or a versioned index path,
while retaining the committed pre-retrieval case checksums as an audit trail.

## Measured results

See `results/track_b2/metrics.json`, `rankings.jsonl`,
`comparisons.jsonl`, `legacy_rankings.jsonl`, and `run_manifest.json` for the
exact executed numbers and case-level traces. The counts of top-three changes
are **lexical ranking outcomes**, not harmful factual contamination. Current
question recall@k, passage support, and harmful-change rates are unscored
until blinded passage qrels and fact annotations exist. In particular,
missing target articles in this non-equivalent, unsegmented corpus must be
reported as coverage limitations rather than retriever failure.

The run produced **876 trace records** and **438 paired comparisons** in
1,517.95 seconds of CPU retrieval. All full-corpus records had at least three
positive-score matches; six records at the smaller prefixes were incomplete,
all involving the original response to `A_024`/its punctuation control.
At full size, match counts ranged from 7 to 177,865 (median 30,804). The
corpus index is 696,393,728 bytes; peak process memory was not measured.

| Complete 241,787-article corpus | A edit: changed top-three set | D punctuation: changed set | B true-current-question probes: changed set | C ambiguous probes: changed set |
|---|---:|---:|---:|---:|
| Response only | 30/30 | 0/30 | 4/4 | 0/2 |
| Question plus response | 24/30 | 0/30 | 4/4 | 1/2 |
| Question only | 0/30 | 0/30 | 4/4 | 1/2 |

For A, the question-plus-response change proportion was 0.80 with a
conversation-clustered 10,000-resample bootstrap interval of 0.667–0.933.
The paired difference from response-only change rate was 0.20, interval
0.067–0.333. These intervals quantify **retrieval-set sensitivity to the
synthetic edit**, not support quality or causal factual contamination. The
question-only A rate of 0/30 is deterministic because its query is unchanged.

At 10,000 / 50,000 / 241,787 articles, A response-only changed 30/30 at
each size; A question-plus-response changed 20/30, 26/30, and 24/30. That
nonmonotonic trend shows corpus composition affects the apparent robustness.
No B/C confidence interval is reported: four and two synthetic probes drawn
from historical conversations do not form a representative independent
sample. The semantic screening flags five of 30 A cases as type or answer
structure mismatches; all remain in the frozen lexical table.
The full corpus had no adjacent equal BM25 scores within any top-three set
and no exact-score tie across rank 3/4. Two hundred of 396 full-corpus
records had at least one adjacent exact score tie somewhere in top 100.
`doc_id` is the deterministic secondary sort key. The reported top-three
changes therefore are not exact-score tie flips at the selection boundary,
although lower-rank ties remain.

An exploratory same-corpus FTS5 `porter unicode61` index was also built after
the preregistered run. It has the same 241,787 article IDs and fixed FTS5
BM25 parameters, occupies 478,650,368 bytes, and was used for 136 records:
30 sampled A cases plus four historical A cases, response-only and
question-plus-response in both arms. Across those records, 56/136 top-three
sets differ between `unicode61` and Porter; the A question-plus-response
edit changes 20/30 sets under Porter versus 24/30 under `unicode61`.
Response-only changes 30/30 in both. The Scott and Space Invaders known-article
response-only top-three losses persist under Porter. This reduces concern
that those two observations depend solely on stemming, but does not test a
second BM25 implementation or the original Lucene analyzer. Full traces,
index hash, and runtime are in `porter_rankings.jsonl`,
`porter_comparison.json`, and `porter_manifest.json`.
