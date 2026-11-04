# Phase 2 readiness

**Read-only instrumentation is ready; controlled failure testing is not yet ready
to run against a trustworthy DualReform baseline.** No suspected weakness has
been established, no adversarial response has been generated, and no Intent-Aware
Supervision Guard exists in this repository.

`dualreform_audit.trace.trace_record` preserves a deep copy of original inputs and
outputs, including dataset/split/conversation/turn IDs, ordered prior Q/A history,
current query, observed response, refined response, pseudo-reference IDs/ranks/
scores, candidate payloads, preference payloads and configuration. Required
configuration fields include experiment ID, source revision, dataset version,
model and retriever. It does not edit, sanitize, judge or correct an answer.

The optional initial-pseudo runner captures full top-100 rankings and top-three
IDs. The checkpoint engine captures supplied prompts and raw generated token
IDs/text, file hashes, generation settings and hardware details. Reference metrics
are computed separately; the training signal module accepts only pseudo IDs and
candidate rankings, with unknown score parameters explicitly required.

Validated now:

* Serialization/deep-copy preservation, strict passage ID/rank validation, finite
  scores and output provenance requirements on synthetic engineering fixtures.
* Whole-conversation seed42 sampling, separate validation from training, ordered
  histories, no future turns and split/session-fingerprint overlap checks on
  public data.
* Correct initialization behavior: no refined response at iteration0; a previous
  CQR refinement must be supplied later. A real TopiOCQA raw-response construction
  smoke assertion passed, without retrieval/model execution.
* Metric mathematics and explicit missing-query/no-positive-qrel treatment.

Still missing before any valid counterfactual comparison:

* Author-authenticated original implementation or a reviewed, explicitly labeled
  reconstruction protocol resolving score weights, cutoffs and pair sampling.
* Trained baseline checkpoint, original full corpus/index and stable mapping.
* Genuine cached candidate queries and per-candidate rankings with provenance.
* Real unmodified pipeline traces and matching evaluation eligibility.
* Executed baseline repeatability checks under an agreed hardware/decoding profile.

Once those artifacts exist, these schemas can record unmodified baseline decisions
and support future paired comparisons. No automatic response perturbation,
counterfactual labeling, unsupported-claim detector, guard, or intervention is
included. Synthetic test success makes no scientific statement about DualReform.
