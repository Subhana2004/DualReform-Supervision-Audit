# Track B2 case-level failure analysis

The four historical A interventions were re-run on the complete 241,787-page
alternative corpus, with the same FTS5 settings and queries as the systematic
study. Their page identities were fixed by the **current question**, before
interpreting the new rankings: `simplewiki:259081` (*Scott Pilgrim vs. the
World*), `simplewiki:99204` (*Space Invaders*), `simplewiki:20261` (*A
Christmas Carol*), and `simplewiki:600373` (*Blade Runner 2049*). Each page
contains the current-question relation, though they are article pages rather
than benchmark passages. Full scored top-100 traces and selected article text
are in `results/track_b2/legacy_rankings.jsonl`.
All four known articles are present in the complete alternative index
(known-article index coverage 4/4, missing 0). This is not an exhaustive
relevance-coverage measure for the 30-conversation sample.

| Historical case | Response-only relevant page, original → false response | Question plus response | Question only | Interpretation |
|---|---:|---:|---:|---|
| Scott/Ramona actor | 3 → absent from top 100 | 1 → 1 | 1 → 1 | The page loss persists on a larger corpus. Question anchoring and question-only keep the named-film article, but the full selected top-three sets still change. |
| Space Invaders developer | 1 → absent from top 100 | 1 → 7 | 1 → 1 | Relevant game page loss persists for response-only. Adding the false answer to a question-anchored query also moves it outside top three. Question-only keeps it. |
| A Christmas Carol author | 45 → absent from top 100 | 4 → 8 | 2 → 2 | This cannot be counted as a top-three page loss: the page was already outside response-only top three. Question anchoring is weaker than question-only for this page. |
| Blade Runner 2049 director | 6 → absent from top 100 | 2 → 6 | 2 → 2 | Again no response-only top-three page loss because baseline rank was 6. Question anchoring loses the page from top three on the edit. |

These are exact rank observations, not four independent, representative
estimates. The old examples were selected for the earlier 58-article study.
The larger corpus overturns the blanket 3/4 top-three loss description:
**two of four** historical current-question pages begin in response-only top
three and then leave it. In two other cases, the page was already absent from
that selected set. A rank loss can reflect lexical competition and corpus
composition without proving that a pseudo-reference is factually unsupported.
The known-article top-three counts by method are response-only 2/4 → 0/4,
question-plus-response 3/4 → 1/4, and question-only 4/4 → 4/4. These are
checks for **one identified relevant article per historically selected case**,
not comprehensive relevant-passage recall@3.

The Simple Wikipedia *Space Invaders* article spells the developer's given
name “Toshihiro” in its body, while the benchmark response says “Tomohiro.”
It still contains the Nishikado/game relation, but this spelling variation is
a specific lexical and source-quality confound. The Scott article explicitly
lists Mary Elizabeth Winstead as Ramona; the *A Christmas Carol* article
credits Dickens; the *Blade Runner 2049* article credits Villeneuve. The
response-only false arms retrieve pages about the replacement names or their
works. Whether each selected article supports or contradicts the current
question requires passage-level review; title identity alone does not settle
it.

Question anchoring itself has counterexamples: the correct page drops from
rank 1 to 7 for Space Invaders and from rank 2 to 6 for Blade Runner 2049
after the false response is appended. The question-only comparator is stable
for all four historical cases because the question text is unchanged. That
stability is expected by construction and does not establish factual support.

The systematic sample's paired changes and corpus-size sensitivity are in
`results/track_b2/comparisons.jsonl`. The supplementary B cases change the
current question itself and thus justify a different retrieval target in
principle, but they are joint question/response edits and cannot isolate
response factuality. The C cases retain multiple plausible interpretations;
no unique target success is scored. No naturally occurring erroneous response
has been independently established. The blank blinded worksheet is a visible
record of that missing annotation work, not a claim of reviewer agreement.

The systematic sample also supplies counterexamples to simple rank logic:

- `A_001`: replacing Michael Jackson with Isaac Newton moves response-only
  results from Jackson-related articles to Newton-related articles. The
  question-plus-response query keeps *The Way You Make Me Feel* in its top
  three in both arms, yet its **top-three set still changes**. Calling that
  change a harmful loss would be a false positive without support judgments.
- `A_018`: response-only moves from Fred Hoyle-related articles to
  Curie-related articles, while question-plus-response remains on *Alloy*,
  *Solid*, and *Chemical element*. The long earlier history dominates the
  anchor query; stable ranking is not proof that it answers the current
  triple-alpha discovery question.
- `A_024`: the original name has zero matching documents in each 10,000 and
  50,000 prefix, versus seven matches in the full corpus. Six incomplete
  top-three traces at the smaller prefixes are explicit coverage failures,
  not retriever failures. The full-corpus matches still require relevance
  review.
- `A_029`: the original response is a group, *Native Americans*, whereas
  the edit names Isaac Newton. The question-only result is stable but its
  first three articles are not obviously Atlanta evidence. This case is one
  of five semantic screening flags and illustrates why lexical stability
  cannot be scored as correctness.

All 30 A response-only top-three sets change; 24/30 anchored sets change.
All 30 D controls stay fixed, and all four B explicit-question edits change
top-three sets under every method. These counts describe query sensitivity.
They do not identify a harmful pseudo-reference or show that anchoring
improves factual support. No reviewer has exhaustively judged those top-three
passages.

The exploratory Porter-tokenizer check preserves the Scott and Space
Invaders response-only known-article losses with identical top-three lists.
It moves the question-plus-response known article to rank 13 rather than 7
for Space Invaders, and changes the systematic A anchored set-change count
from 24/30 to 20/30. Thus the response-only historical losses survive this
tokenizer choice, while the anchor metric is analyzer-sensitive. This is not
an independent Lucene replication.
