# Source provenance — Phase 1

Audit date: 2026-11-04. **Classification: official implementation unavailable;
accessible third-party copy unverified; local algorithm components are explicitly
paper-derived partial reconstructions. The source authenticity gate has not passed.**

The requested publication exists in [PMLR 306](https://proceedings.mlr.press/v306/kim26ak.html),
pp. 58156–58189. The publisher-linked PDF is 34 pages and was downloaded and read
including appendices. Its reproducibility statement, PDF p. 10, names
[`ddoyoungkim/DualReform`](https://github.com/ddoyoungkim/DualReform). The publication
landing page links a PDF and OpenReview, not a separate code supplement. PDF and
source hashes are recorded in [evidence/source_inventory.json](evidence/source_inventory.json).

| Discovery target | Observed evidence | Consequence |
|---|---|---|
| Publisher paper and PDF | Available; PDF p. 10 supplies official URL | Authoritative methodology source |
| Official repository metadata, main tree, commits | GitHub API bodies return `Not Found` | No official revision, license, checkpoint or executable baseline verified |
| Public repositories of `ddoyoungkim` | Public repository listing fetched; no DualReform match | Bounded discovery evidence, not proof that no release exists anywhere |
| Anonymous lead | Initial curl request HTTP 401; later HTML shell HTTP 200; public `/api/repo/DualReform/files/` returns `{"error":"repository_expired"}` | A reachable HTML shell does not recover source |
| OpenReview paper forum | Browser verification challenge; API v2 note request HTTP 403 | Separate attachments/supplement could not be enumerated |
| KAIST DM Lab publications URL | Connection timeout | Lab page did not independently authenticate a code release |
| GitHub/web exact-name searches | Accessible kisti-rag copy found | Candidate copy only |
| Hugging Face model search `DualReform` | API returned `[]` | No matching trained checkpoint discovered by that search |
| Authoritative dataset pages | QReCC/TopiOCQA public; SciConvQA catalog accessible with application link | Dataset availability is separate from model/source availability |

Search engines also surface older arXiv/OpenReview titles. The final publisher PDF
is the specification used here; earlier submissions are not silently substituted.
No researchers were contacted and no authentication barrier was bypassed.

## Accessible copy

* URL/owner: [`dlwnsdn0285/kisti-rag`](https://github.com/dlwnsdn0285/kisti-rag),
  nested `DualReform-main/`. The parent describes a KAIST/KISTI Korean literature
  RAG project, a different repository-level deliverable.
* Pinned source commit: [`979ae1083105579298bd3682ce8a16eae0a7b566`](https://github.com/dlwnsdn0285/kisti-rag/commit/979ae1083105579298bd3682ce8a16eae0a7b566),
  dated 2025-11-27, message `add dualreform and fixed relative path`.
  The path-filtered history request returned this single commit. The original
  DualReform Git history was not preserved in that directory.
* Parent main-tree SHA observed: `b3ea79423e1892ee5ba42832fb260681efa61d48`;
  recursive tree metadata reported `truncated=false`. Inspection uses the pinned
  addition commit, not mutable main.
* README title is an earlier formulation, “LEARNING CONVERSATIONAL QUERY
  REWRITING WITHOUT SUPERVISED REFERENCE PASSAGES.” It describes the same broad
  mechanisms and credits ConvGQR, InfoCQR and LongLoRA. This supports relevance,
  not author endorsement, completeness, or byte-equivalence to final code.
* Its 2025 addition predates the final 2026 paper and expanded final experiments.
  No signed release, author-linked mirror statement, original commit mapping, or
  trained artifact validates its relationship to the final publication.

## Licensing and redistribution

The nested [LICENSE](https://github.com/dlwnsdn0285/kisti-rag/blob/979ae1083105579298bd3682ce8a16eae0a7b566/DualReform-main/LICENSE)
contains Apache 2.0 and its README asserts that license. Parent repository API
metadata reports `license: null`; do not extend the nested license to parent
datasets/code. `PreferenceOptimization/DATA_LICENSE` contains CC BY-NC 4.0;
model and dataset terms remain independent. Apache redistribution requires the
license, applicable notices, and modification notices. No research source is
vendored here; only URLs, revision identifiers, static findings and hashes are
published. Downloaded source stays in ignored work/evidence.

Llama 3.1 base metadata indicates its separate Llama license and gated access.
Access to base Llama would not provide trained DualReform weights. GTR-T5-large
has a separate model card/license. Exact metadata revisions are pinned in config;
neither model was downloaded or loaded locally. Dataset licenses are recorded in
reports/dataset_audit.md; do not assume source licenses cover passages or weights.

## Completeness and installation

The copy contains response refinement/query inference scripts, sparse/dense index
and retrieval code, four stateful preference/SFT notebooks, training scripts,
generation-evaluation and adapter-merge notebooks. It references external data,
indexes, candidate outputs, SFT models and adapters through local `/data/...`
paths. It does not provide an immediately runnable, pinned end-to-end environment
or an orchestration script establishing the final three-iteration experiment.

README environment: Ubuntu 20.04.4, Python 3.10.4, Torch 2.1.2, Transformers
4.43.0, Faiss GPU, Pyserini, sentence-transformers, and RTX A6000 Ada (wording as
published). Source additionally imports TRL, PEFT, Accelerate, bitsandbytes,
FlashAttention, datasets, pytrec_eval and others without a complete lock.
The copied training scripts use bf16, FlashAttention 2 and NF4 4-bit loading;
the SFT effective batch is 64, differing from paper batch 32. See methodology audit.

No copied research script was installed, imported, or executed. Its contents were
statically indexed with codebase-memory and checked against exact source. The
index reported no parse failures, but notebook code was untracked by its graph;
notebook cells and all relevant source sections were read directly. LICENSE was
excluded by the index and read directly. Graph results were navigation, not proof.

## Gate decision

Exact official reproduction is blocked. A *partial* paper-derived implementation
is feasible for equations, trace formats, supplied-run evaluation and iteration-0
retrieval with an independently acquired full index. Exact training is not
reconstructable without resolving score weights/cutoffs, candidate artifacts,
split details, optimizer orchestration and checkpoint provenance. We implemented
only bounded, labeled components, with unknown parameters left unset. This does
not satisfy the acceptance criterion of a verified original baseline.
