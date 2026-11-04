# Track B2 execution and verification log

Local environment: Windows, CPU only. Raw corpus and SQLite index are ignored
under `work/track_b2/`; their source and index hashes are recorded in
`corpus_manifest.json`.

| Stage | Command / check | Observed result |
|---|---|---|
| Corpus acquisition | `python scripts/acquire_track_b2_corpus.py` | Pinned 156,885,218-byte Parquet file acquired; SHA-256 matched `31bded16768a47c286becd292079122f5d7d4397a17b87d4250a00ccd581e6f0`. |
| Index build | `python scripts/build_track_b2_index.py` | 241,787/241,787 rows indexed, 0 skipped; 696,393,728-byte index; SQLite integrity `ok`; 243.015 seconds. |
| Case freeze | `python scripts/preregister_track_b2.py` | 30 independent conversations, 60 A/D cases; pair SHA-256 `09386853e0b217ce75fda58aad2fa27c93c982830d84c739631c3bb2423165ef`; committed as `23fcfe6` before new retrieval. |
| Supplementary probes | `python scripts/prepare_track_b2_cases.py` | 4 true-current-question B edits, 2 current-question C ambiguity probes, 36 blank reviewer worksheet items. |
| Historical rerun | `python scripts/run_track_b2_legacy.py` | 24 scored retrieval records on the complete index. |
| Focused tests | `python -m pytest tests/test_track_b2.py -q` | 5 passed in 61.70 seconds before the systematic run completed. |
| Full tests | `python -m pytest -q` | 40 passed in 67.20 seconds before final trace completeness test was enabled. |
| Lint | `python -m ruff check scripts tests/test_track_b2.py` | All checks passed. |
| Compilation | `python -m compileall -q scripts src tests` | Exit code 0. |
| Systematic retrieval | `python scripts/run_track_b2.py` | 876 scored records, 438 paired comparisons, six incomplete top-three records in small prefixes, 1,517.955 seconds. No GPU. |
| Systematic analysis | `python scripts/analyze_track_b2.py` | 30/30 response-only A sets changed, 24/30 question-plus-response A sets changed, 0/30 question-only A sets changed; 0/30 D controls changed. |
| Historical analysis | `python scripts/analyze_track_b2_legacy.py` | Known current-question article in response-only top three: 2/4 original arms, 0/4 false-response arms. |
| Post-output full tests | `python -m pytest -q` | 41 passed in 79.20 seconds. |
| Repository lint | `python -m ruff check src scripts paper_reimplementation tests` | All checks passed. |
| Notebook validation | `python scripts/validate_notebook.py` | `Notebook valid: 9 code cells; CPU setup execution=False`. No notebook execution claimed. |
| Porter sensitivity | `python scripts/compare_track_b2_porter.py` | 241,787 documents, 136 scored records, 56/136 top-three sets differ by analyzer; 478,650,368-byte local index; 288.768 seconds. |
| Final repository gates | `python -m pytest -q`; `python -m ruff check src scripts paper_reimplementation tests`; `python -m compileall -q src scripts paper_reimplementation tests`; `python scripts/validate_notebook.py` | 42 passed in 84.10 seconds; Ruff passed; compilation exit 0; notebook valid with CPU setup execution disabled. |

CI status is reported after the stacked PR workflow completes. No GPU or
independent second-reviewer run occurred.
