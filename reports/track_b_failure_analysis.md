# Track B competing explanations and case review

The pre-retrieval annotations in `configs/track_b_manual_labels.json` nominate
the **article about the referent of the next benchmark question**, not every
potentially relevant passage. The review in `results/track_b/manual_review.json`
was done by one assistant after retrieval. It uses the benchmark question context
and the linked article leads, without benchmark gold IDs. This single-reviewer
page-identity standard is narrower than a full relevance assessment.

## Concrete same-referent observations

| Case | Changed observed answer | Nominated page rank, original → edit | Manual evidence and qualification |
|---|---|---:|---|
| `A_scott_actor` | Mary Elizabeth Winstead → Scarlett Johansson | Scott Pilgrim film 2 → absent | [Film revision](https://en.wikipedia.org/w/index.php?oldid=1383320551) names Winstead as Ramona; the next question asks what kind of work “this” is. The edited answer matches only one article here. |
| `A_space_developer` | Tomohiro Nishikado → Shigeru Miyamoto | Space Invaders 2 → absent | [Game revision](https://en.wikipedia.org/w/index.php?oldid=1383438025) identifies Nishikado; the next question asks about game sequels. The edited answer matches only one article. |
| `A_carol_author` | Charles Dickens → Jane Austen | A Christmas Carol 2 → absent | [Novella revision](https://en.wikipedia.org/w/index.php?oldid=1383244047) identifies Dickens; the next question asks for publication date. The edited answer matches only two articles. |
| `A_blade_director` | Denis Villeneuve → Ridley Scott | Blade Runner 2049 2 → 2 | [Film revision](https://en.wikipedia.org/w/index.php?oldid=1381652668) names Villeneuve as director and Scott as executive producer. The inaccurate director answer **did not** remove the film from top three. |

For the first three, the changed entity's biography page ranks first. The
unnominated entity is unsupported as the role in the cited target article. The
target page is therefore a relevant page under the independently annotated
conversational subject, and its loss is more than a generic rank shuffle in
**this corpus**. The untouched case shows that an inaccurate answer need not
produce such a loss: the film lead also discusses Scott, preserving the film in
the candidate set. That is a direct falsifier of any claim that all factual
changes corrupt pseudo-references.

## Alternative explanations

1. **Changed vocabulary.** BM25 responds to lexical substitution. All A edits
   replaced a name, so the wrong entity page naturally gained term matches.
   The observed mechanism is lexical response sensitivity, not evidence of a
   learned model believing the false claim. Identical rankings for all three
   punctuation controls support this account.
2. **Genuine referent change.** In B, replacing the sole man or company makes
   “he” or “this” in the following question point to a different entity. Both
   changed entities rank first under response-only BM25. Counting this as a
   failure would be a false positive.
3. **Incomplete corpus.** The 58 article leads cover only a handpicked sliver
   of Wikipedia. In every A target-loss case the edited response had fewer
   than three positive-score hits. No original TopiOCQA passage ID mapping or
   full 2022 index was available. An original-passage result could differ in
   either direction; the observed 3/4 is not a population rate.
4. **Synthetic-only effect.** The conversation questions and original answers
   came from six real TopiOCQA training conversations. All counterfactual
   answers are controlled synthetic edits, not observed model hallucinations.
   We therefore have no natural error-frequency estimate.
5. **Retriever dependence.** Question anchoring retains the nominated page in
   all A edits, but in B it pushes Ubisoft out of the top three in one case.
   A title-overlap filter selects the A subject pages but returns fewer than
   three documents in every arm, and cannot resolve ambiguous pronouns. Its
   coverage failure rules it out as an evaluated replacement for BM25 pseudo
   selection. Different retrieval choices can produce different tradeoffs.

The C cases deliberately introduce two plausible antecedents. One modified
response retrieves both biography pages in the top three; the two-company case
puts Ubisoft at rank five. Neither justifies calling a unique referent, and
rank five alone is not a measured ambiguity-handling error. We did not turn
ambiguity into an invented gold label.

## Decision

**Outcome B — failure inconclusive for DualReform.** The independent diagnostic
shows a plausible response-vocabulary failure mechanism and three reviewed
target losses in a tiny alternative corpus. The missing full original corpus,
curated cases, and absence of naturally occurring errors prevent a claim about
the published method or a statistically defensible rate. The proposed
Intent-Aware Supervision Guard is a hypothesis worth testing once the full
corpus and independent labels are available; this run does not justify its
implementation or effectiveness claim.
