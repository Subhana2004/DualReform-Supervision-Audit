# Kaggle execution

Import `notebooks/phase1_kaggle_baseline.ipynb` into a new Kaggle Notebook,
enable Internet, and Run All. Select T4 only for GPU checks or the optional
checkpoint stage; the default audit needs no accelerator. Download
`/kaggle/working/phase1_exports.zip` from Output afterward. No Kaggle session was
started from this workspace. All delivered GPU cells have empty outputs.

The default notebook installs the pinned audit environment, checks hardware,
downloads the two small locked benchmark archives, runs tests and the real-data
audit, and exports logs and manifests. It does not execute a learned baseline.
The notebook checks out an immutable commit containing its runtime scripts.

To run paper-derived iteration-zero pseudo-reference retrieval, attach the full
TopiOCQA Lucene index as a Kaggle Dataset, set `RUN_INITIAL_PSEUDO=True`, and fill
`INDEX_DIR` and `CORPUS_MANIFEST`. Install/use Java 11 for the pinned Pyserini 0.25.0
profile. The index and its segment files must match that Lucene version. These
dependencies have not been tested on Kaggle. Provide a JSON corpus manifest:

```json
{
  "dataset": "topiocqa",
  "corpus_version": "document the authoritative segmented Wikipedia release",
  "index_sha256_manifest": "path or identifier for the checksummed index file inventory",
  "doc_id_prefix": "doc"
}
```

The corpus manifest is supplied evidence, not proof of equivalence. Review its
checksums, corpus cardinality, analyzer, title handling, and ID mapping before
comparing to the paper. Prefix removal is explicit; it is never inferred from
numeric-looking IDs. Retrieval uses k1=0.9, b=0.4, top-100, top-3 pseudo-reference
selection, and raw responses only at iteration 0. It preserves UNANSWERABLE
responses; empty responses are explicitly excluded. This is a partial paper-derived
reconstruction. No candidate generation, preference optimization, or later
refinement runs without their missing artifacts.

Optional trained-checkpoint inference needs a merged safetensors checkpoint,
`checkpoint_provenance.json`, and reviewed prompts JSONL containing only `id` and
`prompt`. Provenance must include `model_revision`, `dataset_version`,
`source_revision`, `license`, and a `files_sha256` mapping covering every weight
shard plus config and tokenizer files. Hash checks establish file identity, not
the checkpoint's official status. Base Llama is not a trained DualReform model.

The runner has a conservative 22 GiB aggregate GPU memory gate for an 8B fp16
checkpoint. One 16 GB T4 fails that gate. Two T4s may allow inference with
`device_map=auto`; no such run has been verified. The explicit fp16/eager and
greedy decoding profile differs from the copy's bf16/FlashAttention settings.
No automatic quantization, offload, or reduced-model substitution is performed.
The original training setup is not enabled; gradient accumulation alone does
not solve parameter/reference-model memory or T4 bf16 support.

For optional evaluation, attach a standard six-column TREC run and JSON qrels.
Only compare under matching corpus, split eligibility, checkpoint, decoding, and
retriever conditions. The notebook includes an optional pytrec_eval cross-check;
that dependency and stage are not locally executed. Generation LLMEval and GPT
candidate generation require paid APIs and remain disabled.
