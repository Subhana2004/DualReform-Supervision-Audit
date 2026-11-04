# Track B2 correction: current-turn supervision target

Track B's case specifications, annotations, rankings, metrics, and reports remain
unchanged in their original paths. This correction was made before running any
Track B2 retrieval. The paper-derived iteration-zero query is the **current
observed response**. Its supervision quality must be judged against the
information need of the **current question and preceding context**. The next
question can test continuity separately; it cannot define current-turn qrels.

## Recheck of every earlier category

| Track B case | Current question / correct relation | Earlier label | Corrected interpretation |
|---|---|---|---|
| `A_scott_actor` | Who played Ramona in *Scott Pilgrim vs. the World*? Mary Elizabeth Winstead did. | The film as the next question's referent | The film lead **is** relevant to the current question because it states the Ramona cast relation. Its loss under the false Scarlett Johansson answer is a relevant-page loss, but the old reason for selecting it was misaligned. Winstead's biography also supports the relation. |
| `A_space_developer` | Who developed *Space Invaders*? The benchmark answer names Tomohiro Nishikado. | The game for its later sequel question | The game lead explicitly credits Nishikado and is current-question evidence. Its loss under Shigeru Miyamoto remains a local relevant-page loss. |
| `A_carol_author` | Who wrote *A Christmas Carol*? Charles Dickens did. | The novella for its later publication question | The novella lead states the author relation and is current-question evidence. Its loss under Jane Austen remains a local relevant-page loss. |
| `A_blade_director` | Who directed *Blade Runner 2049*? Denis Villeneuve did. | The film for the later producer question | The film page stays at rank 2 after the false Ridley Scott answer. Stability of this page does **not** make the selected pseudo-reference set correct: Scott's biography can still be irrelevant to the director relation. |
| `B_yttrium_person` | Who discovered the element under discussion, yttrium? | The next “he” changes from Arrhenius to Davy | The **current question's intent does not change**. Davy is a false answer to the same question; movement to Davy's page is not correct intent-change responsiveness. This prior positive control was misclassified. |
| `B_lastofus_company` | Who developed *The Last of Us*? Naughty Dog did. | The next “this” changes from Naughty Dog to Ubisoft | The **current question's intent does not change**. Ubisoft is a false answer to the same question; movement to its page is not a justified current-turn target change. This prior positive control was misclassified. |
| `C_yttrium_two_people` | Who discovered the same element? | Two possible referents for next “he” | The edited response adds a second possible *answer*, but the current question remains about yttrium. Ambiguity belongs to the separate next-turn continuity analysis. |
| `C_lastofus_two_companies` | Who developed the same game? | Two possible referents for next “this” | The edited response adds a second possible developer, while the current information need remains fixed. It does not establish current-question ambiguity. |
| Three `D_*_punctuation` cases | Same question, same answer words | Stable rankings | The token-level negative controls remain valid. Identical rankings establish retrieval stability under punctuation, **not** factual support. |

The TopiOCQA release contains `Rationale` and `Topic`, but the gold-blind
training adapter excludes them. They are permitted only for offline evaluation
or annotation verification. Track B's film/game/novella pages contain the
original correct relation in the committed Wikipedia snapshot; those three
local page-loss observations therefore survive a corrected *page-relevance*
check. The old claim of **3/4 factual-contamination rate** does not survive:
the cases were handpicked, the false-response arms often had fewer than three
hits, and the selected sets were never exhaustively judged for support. The
earlier **2/2 B responsiveness** is invalid as a current-turn measure. Its
next-turn pronoun behavior may be described separately, without treating it as
supervision ground truth.

No second independent reviewer has assessed these corrected labels. All
current-turn judgments in Track B2 are marked provisional until blinded
review. No future turn or gold field is used to construct retrieval queries.
