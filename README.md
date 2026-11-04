# DualReform Supervision Audit

**Phase 1 audit delivered; official baseline reproduction remains blocked.**
The official source named in the paper is unavailable; the accessible copy is
unverified. No GPU/model experiment, trained baseline, supervision guard, or
adversarial experiment is claimed.

Completed: source/methodology/dataset audits, real-data integrity checks across
127,916 released turns, deterministic457-turn sample, gold-blind adapters,
27 engineering tests, metric/output validation, read-only instrumentation,
and a Kaggle notebook with explicit blocked/optional stages.

| Artifact | Purpose |
|---|---|
| [Reproduction report](reports/phase1_reproduction.md) | Executive summary, actual results and level0–3 status |
| [Source provenance](reports/source_provenance.md) | Discovery attempts, revisions, licensing and authenticity gate |
| [Methodology audit](reports/methodology_audit.md) | Final paper specification and paper-to-copy traceability |
| [Dataset audit](reports/dataset_audit.md) | Real release counts, history discrepancies and eligibility |
| [Limitations](reports/phase1_limitations.md) | Exact blockers and unresolved deviations |
| [Phase2 readiness](reports/phase2_readiness.md) | What read-only instrumentation is ready |
| [Kaggle notebook](notebooks/phase1_kaggle_baseline.ipynb) | Default data audit; optional supplied-index/checkpoint stages |
| [Commands](docs/commands.md) / [Kaggle instructions](docs/kaggle.md) | Setup, checks, data, execution and export |

Quick start (PowerShell):

```powershell
python -m venv work\.venv
work\.venv\Scripts\python.exe -m pip install -r requirements-audit-lock.txt
$env:PYTHONPATH='src;.'
work\.venv\Scripts\python.exe -m scripts.acquire_data
work\.venv\Scripts\python.exe -m scripts.verify
work\.venv\Scripts\python.exe -m scripts.run_data_audit
```

Linux uses `export PYTHONPATH=src:.` and the corresponding environment Python.
Core adapters have no runtime dependencies. Audit/test dependencies are pinned;
optional ML dependencies have not been executed here. Python3.10 is tested.

`results/phase1/metrics.json` contains **data-integrity counts**, with retrieval
metrics null. `per_example.jsonl` contains hashes/status for actual validated
records; `run_manifest.json` records the real execution. No synthetic fixture
results are published as benchmark measurements. Full benchmark text, source
downloads, credentials, corpora and weights are excluded from Git.

Local partial reconstruction is isolated in `paper_reimplementation/`. It does
not assert official status and refuses to invent missing score hyperparameters.
See [external references](third_party/README.md) for source and dataset terms.

The next scientific prerequisite is an authenticated original source/checkpoint
and its experiment artifacts. A Kaggle GPU alone does not resolve provenance
or missing retrieval/candidate data. The notebook's default CPU-compatible audit
can run now; expensive stages are deliberately disabled until inputs exist.
