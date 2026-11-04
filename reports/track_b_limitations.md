# Track B limits and resolving experiment

The official DualReform implementation and trained checkpoint remain
unavailable/unverified. The observed run is an independent paper-derived
iteration-zero *retrieval* diagnostic. It has no candidate rewrite generation,
SFT, DPO, response refinement, or GPU model execution. No Kaggle notebook was
needed for its CPU BM25 implementation.

The 58 English Wikipedia article leads differ from TopiOCQA's author-segmented
~25.7-million-passage corpus in vintage, passage granularity, text coverage,
document IDs, title indexing, and analyzer. `k1=.9` and `b=.4` match the
published sparse parameters, but our Unicode tokenizer and Python BM25 are
not established as Pyserini/Lucene-equivalent. Results must not be compared
numerically to DualReform's TopiOCQA benchmark table.

Eleven predeclared edits on six training conversations cannot estimate a
population frequency. Cases were chosen for an interpretable subject and an
available Wikipedia article, which creates coverage and selection bias. The
original answers are benchmark responses; the changed answers are controlled
synthetic statements. One assistant manually annotated referents and reviewed
page identity; there is no blinded second reviewer or exhaustive passage
relevance adjudication. The future benchmark question was used for interpretation,
never inserted into a retrieval query. Automatic page-ID membership is a
narrow proxy for evidence support. Fifty percent of response-only arms had
fewer than three positive-score articles; all three A target losses are among
them. This is a decisive generalization limit.

The smallest resolving study is: obtain and checksum the original TopiOCQA
segmented collection and author-documented ID map; build a Pyserini index at
`k1=.9,b=.4` with recorded analyzer/version; pre-register a larger random,
conversation-disjoint sample and controlled A/B/C/D edits; have at least two
annotators, blind to rankings, judge intended referents and candidate passage
support; then run the same paired raw-response retrieval and question-anchored
controls. Report disagreements, complete top-three coverage, rates with
conversation-clustered uncertainty, and failures under a naturally observed
error set if one can be obtained without paid model calls. The official
checkpoint is not required to test iteration-zero retrieval, but would be
required for any later trained DualReform claim.
