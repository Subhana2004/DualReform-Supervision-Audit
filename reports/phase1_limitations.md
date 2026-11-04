# Phase 1 limits and blockers

**No official DualReform inference, retrieval accuracy, intermediate pseudo-reference
pipeline, or training result has been reproduced.** GPU execution is NOT EXECUTED.
The completed run measures real-data integrity only. These are independent blockers:

| Blocker | Evidence | What resolves it |
|---|---|---|
| Source authenticity | Paper's official repository API returns404; anonymous API says repository_expired; copy lacks official linkage/history | Recover an author-authenticated source archive/revision or obtain a separately approved paper-derived protocol |
| Executable copy completeness | Stateful notebook cutoff/list errors; converter break; external local paths; no final loop/lock | Audit a recoverable original release; any port/fix must be separately labeled and reviewed |
| Preference score and sampling | Paper omits concrete weights/K; copy uses a different metric mean and thresholds | Recover exact experimental configuration/artifacts, without guessing values |
| Candidate queries | Paper requires12 GPT3.5 rewrites +3 Llama expansions; cached outputs not located | Acquire provenance-checked cached candidates, or authorize a separate paid candidate-generation run |
| Trained checkpoint | No matching public trained release recovered by bounded searches | Acquire a provenance/license/hash-verified trained DualReform checkpoint, not base Llama |
| Corpora and qrels | No full54M QReCC/Wikipedia/SciConvQA corpus or final mapping acquired | Acquire official corpus/index and validate version, titles/analyzer, stable IDs and evaluation eligibility |
| SciConvQA access | Catalog lists CC BY-NC/application-controlled ZIP; corpus separate | User applies through KISTI and supplies legitimately obtained data/corpus; no researcher contact is required by this workflow |
| GPU execution | No CUDA/PyTorch installed locally; no Kaggle tool/session configured; CLI/hardware commands unavailable in PATH | User imports notebook in Kaggle; attach reviewed artifacts and enable available hardware |
| Single-T4 feasibility | Copy expects bf16/FlashAttention2/NF4, original setup on A6000; optional8B fp16 requires22GiB aggregate gate | Review exact hardware/memory profile; twoT4 inference is untested, full training is not promised |
| Dataset version/eligibility | Acquired TopiOCQA47,964 turns differs from approximate paper51K; QReCC histories differ; exact validation seeds unknown | Recover author's actual row lists, preprocessing and qrels protocol |

The audit environment is dependency-locked and locally installed. The optional
Kaggle Pyserini/Java and Torch/Transformers profiles are proposed, **not executed
compatibility validations**. Original pytrec_eval cross-checks and ML tokenization
were not executed locally; analytical metric tests passed. Pinned current base
model revisions are new audit pins, not verified training-time author revisions.

The dataset loader's complete-history exclusion and conversation-level validation
split are explicit engineering policies, not paper-equivalent preprocessing.
QReCC reconstruction is only diagnostic. Its many context differences are not
declared corruptions or evidence of a research defect. TopiOCQA has no context
differences under the implemented comparison.

The457-turn sample supports engineering validation only. No performance
comparison, significance test, intervention result, or evidence of factual
contamination follows from it. Zero session overlap does not rule out near
duplicates, topic overlap or pretrained model contamination.

The publication itself has varying numerical values across tables for some
extended iterative results (compare Tables2/4 with14); do not normalize these
away. Original exact experiment configurations are required for a fair comparison.

All expensive stages are disabled by default, no paid resources consumed, no
researcher messages sent, and no restricted access bypassed. The supervision
guard, factual edits and adversarial tests have not been implemented.

Tooling note: Agent Reach1.5.0 was available; its check-update reported1.6.1.
No tool update was performed during research. This is unrelated to baseline results.
