# Dataset acquisition and isolation

Run `python -m scripts.acquire_data` from the repository root. Downloads are
restricted to the two public archives in `configs/data_sources.json`, with exact
byte sizes and SHA-256 checks. No authentication is required for those archives.

* TopiOCQA: [author project](https://mcgill-nlp.github.io/topiocqa/),
  [Zenodo release 6193037](https://zenodo.org/records/6193037), CC BY 4.0.
  Cite Adlakha et al., *TopiOCQA: Open-domain Conversational Question Answering
  with Topic Switching*, TACL 2022.
* QReCC: [Apple repository](https://github.com/apple/ml-qrecc) at the revision in
  the lock, dataset CC BY-SA 3.0. Cite Anantha et al., *Open-Domain Question
  Answering Goes Conversational via Question Rewriting*, NAACL 2021.
* SciConvQA: [KISTI release, DOI 10.23057/116](https://aida.kisti.re.kr/data/e306c9c6-324e-47a5-9188-af72b898a22b?lang=en),
  CC BY-NC, application-controlled download. Not downloaded. Its journal corpus
  has separate access/terms and is not included here.

`raw/`, `processed/`, and `corpus/` are ignored. The project does not redistribute
benchmark text, passage collections, or human annotations. The full projected
457-turn engineering sample is only written locally to
`data/processed/sample_inputs.jsonl`. Public per-example artifacts contain IDs,
hashes, and validation status, not benchmark answers.

`scripts.run_data_audit` retains release train/dev/test boundaries. Eight complete
training conversations, chosen by seed 42 SHA-256 ordering, form a new validation
set. Sampling happens *after* this holdout. Numeric conversation IDs restart in
official splits, so release split is part of the namespace. Full-session text
fingerprints are also checked across partitions.

The schema loader rejects malformed fields/duplicate turn IDs. In the executed
audit, conversations with missing turn numbers are explicitly excluded and
listed in results/phase1/*_excluded.json. This is an **audit eligibility policy**,
not the paper's preprocessing. QReCC contexts often differ from reconstructed
raw Q/A histories; no QReCC model/pseudo-reference experiment is authorized by
these adapters. TopiOCQA has zero such discrepancies in this release.

Gold passages, annotated rewrites, rationale, topics, and additional answers are
excluded by an explicit training-input field allowlist. The pseudo-reference
runner accepts no qrels path. Evaluation is a separate command. Do not construct
an index or select training records using evaluation gold passages.

No full retrieval corpus or qrels-to-passage-ID mapping was acquired. Topic,
rationale text, and Answer_URL are not passage IDs. See reports/dataset_audit.md
and docs/kaggle.md for the remaining external artifacts.
