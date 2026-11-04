# Reproduction commands

Windows PowerShell, from the repository root:

```powershell
python -m venv work\.venv
work\.venv\Scripts\python.exe -m pip install -r requirements-audit-lock.txt
$env:PYTHONPATH='src;.'
work\.venv\Scripts\python.exe -m scripts.acquire_data
work\.venv\Scripts\python.exe -m pytest -q
work\.venv\Scripts\ruff.exe check src scripts paper_reimplementation tests
work\.venv\Scripts\python.exe scripts\validate_notebook.py --execute-cpu
work\.venv\Scripts\python.exe -m scripts.run_data_audit
```

Linux/Kaggle, from the repository root:

```bash
python -m venv work/.venv
source work/.venv/bin/activate
python -m pip install -r requirements-audit-lock.txt
export PYTHONPATH=src:.
python -m scripts.acquire_data
python -m pytest -q
ruff check src scripts paper_reimplementation tests
python scripts/validate_notebook.py --execute-cpu
python -m scripts.run_data_audit
```

Optional stages, only after their external artifacts have been reviewed:

```bash
python -m scripts.run_initial_pseudo --inputs data/processed/topiocqa_train_only.jsonl --index /path/to/index --corpus-manifest /path/to/corpus.json --output results/private/initial_pseudo --limit 32
python -m scripts.run_checkpoint_inference --checkpoint /path/to/merged-checkpoint --provenance /path/to/checkpoint_provenance.json --prompts /path/to/reviewed_prompts.jsonl --output results/private/inference --limit 8
python -m scripts.evaluate_run --run /path/to/run.trec --qrels /path/to/qrels.json --output results/private/evaluation.json
```

The initial-pseudo command deliberately requires a train-only TopiOCQA projection;
the notebook creates it by filtering the audited sample. It cannot ingest gold
passage columns. Optional ML packages belong in a separate Linux GPU environment;
the pinned audit environment contains no Torch or Transformers. See docs/kaggle.md.

Source evidence discovery commands used (public reads; no researcher contact):

```bash
curl -L https://raw.githubusercontent.com/mlresearch/v306/main/assets/kim26ak/kim26ak.pdf
curl https://api.github.com/repos/ddoyoungkim/DualReform
curl https://api.github.com/repos/ddoyoungkim/DualReform/git/trees/main?recursive=1
curl https://anonymous.4open.science/api/repo/DualReform/files/
curl 'https://api.github.com/repos/dlwnsdn0285/kisti-rag/commits?path=DualReform-main&per_page=100'
curl 'https://api.github.com/repos/dlwnsdn0285/kisti-rag/git/trees/main?recursive=1'
curl https://raw.githubusercontent.com/dlwnsdn0285/kisti-rag/979ae1083105579298bd3682ce8a16eae0a7b566/DualReform-main/LICENSE
curl 'https://huggingface.co/api/models?search=DualReform'
```

The paper was downloaded to ignored work/evidence, parsed with pypdf 5.9.0 into
34 page-numbered text files, and read including all appendices. Source metadata,
all relevant Python/shell files, and four preference notebooks were fetched at
the pinned copy commit for static inspection only. Nothing from that research
code was imported or executed. Hashes are retained in reports/evidence.
