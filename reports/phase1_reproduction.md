# Phase 1 reproduction report

## Executive summary

The source audit and reproducibility infrastructure are ready for review, but
**an official DualReform baseline has not been reproduced**. The final paper names
an official repository that returns404; the accessible Apache-licensed copy has
unverified provenance and material implementation inconsistencies. These prevent
claiming an unchanged original run. No hypothesis about factual contamination has
been tested, and no guard or adversarial intervention was implemented.

Executed work: locked acquisition and integrity validation of127,916 real
TopiOCQA/QReCC turns, deterministic sampling of457 turns,
gold-blind adapters, analytical metric checks, immutable trace capture,27 passing
engineering tests, lint/compile checks, and notebook schema/CPU-setup validation.
GPU models, full-corpus retrieval, candidate generation and training did not run.

## Reproduction status

| Level | Status | Evidence / blocker |
|---|---|---|
|0 environment/smoke | **PARTIAL** | Pinned audit environment installed; real loaders, history/split checks, metric and output tests run. Original ML packages/model/tokenizer/checkpoint/retriever not loaded |
|1 original pseudo-reference pipeline | **BLOCKED / NOT REPRODUCED** | No authenticated source, original corpus/index or candidate artifacts; no response refinement/retrieval/preferences executed |
|2 original checkpoint inference/evaluation | **BLOCKED / NOT REPRODUCED** | No trained DualReform checkpoint or mapped full-corpus evaluation artifacts |
|3 original training | **BLOCKED / NOT REPRODUCED** | Unresolved methodology parameters, paid candidate generation, source/data artifacts and unavailable approved GPU execution setup |

Paper-derived components exist separately and pass fixture tests. Iteration0
query construction also passed a real TopiOCQA input smoke assertion. This does
not constitute end-to-end pseudo-reference reproduction. Optional runners are
prepared for supplied artifacts but their expensive paths remain unexecuted.

## Actual numerical outputs

* Released records inspected:127,916; retained complete-history records119,807.
* Public engineering sample:457 turns from48 conversations,
  seed42; no performance uncertainty or significance claim.
* TopiOCQA train/dev:45,450/2,514; released histories all match preceding Q/A.
* QReCC train/test:63,501/16,451 raw;56,971/14,872 retained after the explicitly
  labeled turn-gap policy;43,622/11,442 retained context differences unresolved.
* Zero conversation/session-fingerprint overlap in effective train/val/eval.
* Data audit runtime:11.488s for the recorded run;
  Windows/Python3.10.11. This is not model/retrieval throughput.
* Retrieval MRR/nDCG/Recall, pseudo-reference accuracy and generation metrics:
  **not measured**. The result JSON uses null rather than fabricated zeros.

Actual results are in `results/phase1/metrics.json`, `per_example.jsonl`,
`run_manifest.json`, with per-dataset exclusion artifacts. Full sampled text is
in ignored `data/processed/sample_inputs.jsonl`. Commands and outputs of quality
checks are in `results/verification/`. The manifest records source-copy revision,
archive/model availability, parameters, environment, timestamp, Git SHA and dirty
state. A dirty state is explicitly recorded if only evidence/notebook/report
files were pending at run time; it is not presented as a clean committed run.

## Paper comparison — conditions not equivalent

| Item | Paper | This executed experiment |
|---|---|---|
|Dataset/split | TopiOCQA/SciConvQA final evaluation; additional QReCC | Public TopiOCQA original train/dev and QReCC archive integrity only |
|Model/checkpoint | Trained DualReform Llama3.1-8B | None loaded |
|Retriever/corpus | BM25 and GTR, full benchmark corpora | None executed |
|Training | Iterative pseudo-ref + SFT/DPO | None |
|Examples | Final eligibility not fully recovered |127,916 raw checked;457 sampled |
|Hardware | RTX A6000 Ada as stated | Windows laptop CPU; no Torch/CUDA model execution |
|Metric | MRR,nDCG@3,R@5,R@20 | Schema/split integrity counts |
|Result | See author-reported table below | No compatible retrieval result |

Selected **author-reported**, not reproduced, results (percent scale):

| Dataset/retriever | Method | MRR | nDCG@3 | R@5 | R@20 | Paper location |
|---|---|---:|---:|---:|---:|---|
|TopiOCQA/BM25 | Original query |2.09|1.77|2.90|5.21|Table2,p.7|
|TopiOCQA/BM25 | DualReform |28.39±.39|26.08±.46|39.57±1.05|56.62±1.24|Table2,p.7|
|TopiOCQA/GTR | DualReform |40.14±.21|38.33±.28|53.78±.58|71.99±.30|Table2,p.7|
|SciConvQA/BM25 | DualReform |20.06±.19|18.42±.27|28.64±.28|43.14±.20|Table2,p.7|
|SciConvQA/GTR | DualReform |23.53±.09|22.04±.23|31.19±.18|45.21±.22|Table2,p.7|
|QReCC/BM25 | DualReform |48.40|45.30|58.91|77.90|Table13,p.21|

Main-table errors are the paper's standard errors over three random
initializations, not local confidence intervals. Do not subtract local
engineering counts from these metrics or interpret the sample as performance.

## GPU/notebook handoff

`notebooks/phase1_kaggle_baseline.ipynb` has empty execution outputs. Structure and
all9 code cells compile; CPU setup cells were executed locally. The complete
Kaggle notebook has not run in a Kaggle session. It records hardware, runtime,
package versions and peak GPU memory when an optional model run actually occurs.

Default Run All performs data audit/tests and exports logs. Optional index and
checkpoint stages stop with explicit prerequisites. One T4 does not satisfy the
conservative22GiB fp16 8B memory gate. No architecture change or quantization is
silently enabled; fp16/eager/greedy optional inference is explicitly a deviation.
Source authenticity, candidate artifacts, exact score parameters and checkpoint
availability remain blockers even if a GPU becomes available.

## Deliverable assessment

Source/dataset audits, paper-to-source traceability, engineering adapters/tests,
run records, read-only trace schema, CI and notebook are delivered. The source
authenticity and trustworthy real-data **learned baseline** acceptance criteria
remain unsatisfied. This is a documented blocker outcome, not Phase1 baseline
success. See phase1_limitations.md and phase2_readiness.md for exact boundaries.
