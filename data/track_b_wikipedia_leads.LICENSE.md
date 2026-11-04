# Track B Wikipedia text attribution

`track_b_wikipedia_leads.jsonl` contains plain-text lead extracts from 58 English
Wikipedia articles, fetched via the public Action API on 2026-11-04. Each row
contains the article title, page ID, revision ID, and a revision URL, which links
to the page history and its contributors. Each text extract is hashed. Extraction
from the page lead and removal of markup are the changes made for this snapshot.

Wikipedia article text is available under the [Creative Commons Attribution–
ShareAlike 4.0 International license](https://creativecommons.org/licenses/by-sa/4.0/).
The article text in this file is redistributed under those same terms. See
[Wikipedia's reuse and attribution rules](https://en.wikipedia.org/wiki/Wikipedia:Copyrights).

This small 2026 article-level snapshot was curated from training-conversation
topics, observed answer entities, proposed substitutions, and generic distractors
before retrieval outcomes were inspected. No evaluation answers, gold reference
passages, or relevance labels were used. It is **not**
the TopiOCQA 2022 25.7-million-passage collection, is not a representative random
sample of Wikipedia, and is not licensed under the repository's software terms.
