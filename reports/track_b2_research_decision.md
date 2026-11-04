# Track B2 research decision

## Outcome B — Evidence remains inconclusive

The historical case rerun demonstrates a reproducible **known-article rank
loss** for two of four previously selected false-response interventions in a
larger, independently acquired corpus. It does not establish a representative
failure rate or a supervision-quality loss. The article corpus is not the
original segmented TopiOCQA corpus; selected pseudo-reference passages have
not received independent blinded relevance and factual-support judgments;
synthetic replacement names are often implausible; and naturally occurring
response errors have not been verified. The systematic 30-conversation
experiment measures lexical retrieval movement, with uncertainty estimates
for that movement only. Its relevance recall and support-quality fields are
intentionally unscored.

In the 30-conversation synthetic sample, response-only changed its top-three
set in 30/30 A edits, question-plus-response in 24/30, and question-only in
0/30 because its query did not change. Punctuation controls changed 0/30.
Those are lexical measurements, not the unscored harmful-support rate. The
five flagged type or answer-structure mismatches further limit factual-error
interpretation.
The two historical response-only known-article losses persist with a Porter
tokenizer on the same corpus, although anchored rankings and the sample's
anchored change count shift. This sensitivity check remains within SQLite
FTS5 and does not establish an official Lucene result.

The evidence is consistent with response terms competing with current-question
terms, but does not isolate unsupported factual claims as the cause. The
response-only method loses a known current-question article in Scott and Space
Invaders cases. Question-only retains all four known historical articles in
top three across the edits by construction. Question anchoring retains the
Scott article, yet loses the Space Invaders and Blade Runner articles from
top three in their false arms. Thus a simple comparator may help some cases,
and adding the response to the question is not uniformly protective. Neither
observation proves support quality. The Simple Wikipedia Space Invaders name
spelling is an explicit lexical confound.

**A reproducible supervision problem may exist, but the current evidence does
not justify implementing the Intent-Aware Supervision Guard.** The smallest
next experiment is to have two independent reviewers, blind to retrieval
rankings and method, annotate current-question evidence and claim support for
all 30 sampled conversations and edited arms, adjudicate disagreements, and
then score the frozen rankings. If harmful support changes persist, repeat on
the original segmented corpus using hardware with verified disk and indexing
capacity and the author-documented passage mapping. Include naturally
observed, independently checked errors and true current-question intent
changes in a larger conversation-disjoint sample.

The hypothesis would be weakened or falsified if blinded passage judgments
show no increase in unsupported pseudo-references under factual edits, if the
effect vanishes on the original corpus, or if question-only retrieval achieves
equal or better support without material losses on genuine intent changes.
Until those measurements exist, no guard component has a demonstrated
incremental value. If they eventually do, the smallest candidate would be a
question-conditioned check on response-only candidates, compared directly
with question-only retrieval; that component has **not** been implemented.
