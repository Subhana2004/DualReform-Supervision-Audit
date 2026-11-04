# Paper-to-code methodology audit

Specification: final [publisher PDF](https://raw.githubusercontent.com/mlresearch/v306/main/assets/kim26ak/kim26ak.pdf),
34 PDF pages, not an earlier OpenReview submission. All source references below
are to the **unverified copy** at commit
`979ae1083105579298bd3682ce8a16eae0a7b566`, under `DualReform-main/`.
“Verified in source” means the local code behavior was inspected; it does not
authenticate the copy or mean execution passed.

## Exact conceptual ordering

1. Generate a fixed diverse candidate pool: 12 GPT-3.5-turbo-0125 rewrites and
   three Llama-3.1-8B-Instruct expansions (Appendix E.2, p. 21; Figures 10–11,
   p. 25). GPT decoding: temperature/top-p 0.8/0.8, max tokens 2560.
2. Algorithm 1, p. 5: at iteration **i=0**, refined response is empty. Retrieve
   from the raw observed response; do not call a generic LLM refiner at startup.
3. At i>0, freeze the CQR model learned in the previous iteration. Convert the
   current observed response into the question-form template in Prompt 1,
   together with conversation history/current query, and refine with that CQR.
4. Equation 8 retrieves with raw response concatenated with refined response.
   Select the top three passages as pseudo-references (§5.1, p. 6).
5. Retrieve for each candidate and rank candidates by retrieval quality against
   **pseudo** references (Appendix C, Eq. 18–21, p. 17). Gold references are for
   evaluation only (p. 5 footnote).
6. Train SFT on the highest-ranked candidate, then DPO on preferences (§3.2,
   pp. 3, 6). Repeat the pseudo-reference/training cycle three times, with
   pseudo-reference updates once per epoch (§5.1 p. 6, Appendix E.2 p. 20).
7. At test time, reformulate queries with the trained CQR and retrieve against
   the benchmark corpus. Response refinement is an offline training role.

## Experimental specification

| Component | Published specification | Unresolved detail / fidelity limit |
|---|---|---|
| Main benchmarks | SciConvQA and TopiOCQA; QReCC additionally Table 13, p. 21 | Final exact train/validation row lists and eligibility not released here |
| Additional benchmark | UltraChat Questions about the World: 100K train, 10K held-out, Table 17 p. 32 | Sector revision, row IDs, generation inputs not recovered |
| QReCC | ~14K conversations, ~80K QA, 54M passages; Appendix D.1 p. 17 | Raw archive contains 79,952 turns; complete corpus/mapping absent |
| TopiOCQA | ~3.9K conversations, ~51K QA, ~20M Wikipedia passages; p. 17 | Acquired release contains 47,964 turns; corpus code comments suggest a larger passage count; do not equate versions |
| SciConvQA | 750 train/150 test conversations; 9,999/1,954 turns; Table 12 p. 20 | Application-controlled download and corpus not acquired |
| SciConvQA corpus | 120,916 English articles from 481,578 articles; 749 fields; 1,909,524 passages; pp. 18–19 | LangChain RecursiveCharacterTextSplitter size 500, overlap 100; dependency version unspecified |
| SciConvQA annotation | GPT-4o-2024-08-06 generation, manual sample checking, rationale-to-passage longest common substring mapping; pp. 18–19 | No regeneration: paid API and unavailable source corpus |
| Response transformation | Prompt 1, Eq. 9, p. 5; previous trained CQR, raw+refined concat Eq. 8 | Copy truncates responses to 100 characters in one prompt path, undocumented by paper |
| Sparse retrieval | BM25 via Pyserini; QReCC k1=.82,b=.68; TopiOCQA/SciConvQA .9,.4; top-100; p. 21 | Analyzer/version, corpus title handling and index checksum unspecified |
| Dense retrieval | GTR-T5-large via Faiss, query/passage max length 384, top-100; p. 21 footnote 4 | Model repo named; original model commit, Faiss version/index exact settings not specified |
| Alternate dense retrieval | ANCE Table 16 pp. 31–32 | Not mapped to a runnable final-paper experiment in inspected files |
| Backbone | Llama-3.1-8B-Instruct; Qwen-2.5-7B-Instruct additional comparison, Table 8 p. 9 | No trained DualReform checkpoint discovered; base weights are not replacements |
| Candidate preference score | Weighted coverage mean Recall@k, MRR, nDCG; nonnegative weights summing to 1; Eq. 18–21 p. 17 | Concrete K and omega weights not supplied; no defaults invented |
| SFT | One epoch, LR 2e-5, batch 32; Appendix E.2 p. 20 | Copy uses microbatch 2 x accumulation 32 = 64 |
| DPO | DualReform beta .5; paper ties LR/batch to the reported optimization settings | Copy defaults LR2e-4,beta .1; supplied CLI values needed; exact multi-round SFT/DPO orchestration ambiguous |
| Iterations | Three pseudo-reference updates / epochs; pp. 6,20 | Copy has separate manual commands, no verified loop |
| Repetitions/seeds | Three random initializations, mean and standard error; p. 6 | Exact seed triplet unspecified; copy SFT42,DPO0,pair sampler1 |
| Hardware | PyTorch2.1.2; NVIDIA RTX A6000 Ada as written; p. 20 | Exact GPU SKU/memory/count ambiguous; no T4 validation implied |
| Cost | Table7 p.9: refinement3.58h; sparse1.15min/dense2.42min; training2.79h; cumulative overhead6.41h on one A6000 | These are author measurements; not our runtimes or T4 estimates |
| Retrieval metrics | MRR, nDCG@3, Recall@k, main R@5/R@20; pytrec_eval; pp.6,20–21 | Missing-query denominator and no-answer filtering require original qrels; our evaluator makes these explicit |
| Generation | Llama3.1-8B, BM25 top4; LLMEval using GPT-4o-2024-08-06, ROUGE1/L, BERTScore; pp.20–21 | No API calls or generation results here |

## Traceability table

Source links use immutable revisions. Notebook references use zero-based code-cell
indices from the saved `.ipynb`; flattened inspection line ranges are also given.

| Paper component | Source file / symbol / location | Classification | Audit finding |
|---|---|---|---|
| Refinement template and conversation context, §4.4 p.5 | [CQR/refine_response.py](https://github.com/dlwnsdn0285/kisti-rag/blob/979ae1083105579298bd3682ce8a16eae0a7b566/DualReform-main/CQR/refine_response.py#L38), `set_prompt`, lines38–248 | Verified in source / Inconsistent | Parameterized self-ask text; lines212–222 truncate raw answer at100chars and special-case UNANSWERABLE; final template not fixed in script |
| Refinement generation | same file, `generate_rewrite`259–264, `build_generator_llama3_1`433–457 | Unverified | Model path external; sampling parameters passed without explicit do_sample; output splits on a tokenizer special token. No loaded model test |
| Iteration0 no refinement, Algorithm1 p.5 | No executable loop in inspected scripts; local `paper_reimplementation/signals.py::pseudo_query` | Reconstructed from paper / Missing | Local function enforces empty refinement at i=0, requires previous refinement later |
| Raw response retrieval, Eq8 p.5 | [bm25_on_topiocqa.py](https://github.com/dlwnsdn0285/kisti-rag/blob/979ae1083105579298bd3682ce8a16eae0a7b566/DualReform-main/CQR/sparse_retrieve/bm25/bm25_on_topiocqa.py#L20), `main`20–267; args336–367 | Verified in source | `this_answer_only` path, explicit k1/b/top_k; selfask path concatenates selected input fields; exact final command unknown |
| Pseudo top3 | `CQR/preference_generation/create_pref_data_TopiOCQA.ipynb`, cell20; flattened lines667–690 | Verified in source | First three distinct retrieved IDs, binary qrels |
| Candidate rewrites | `CQR/gpt_rewrite_candidate_queries.py::generate_rewrite` | Verified in source / Unverified | GPT3.5 temp.8/top_p.8/max2560 matches paper; twelve runs require external invocation/artifacts |
| Candidate expansion | `CQR/query_expansion_llama3.py::set_prompt`, generation builders | Unverified | Llama expansion implemented; final three candidate file identities not provided |
| Preference scoring Eq21 | `create_pref_data_TopiOCQA.ipynb` cells21–22; flattened lines703–769 | Inconsistent | Mean of returned metric dictionary values, including MAP/multiple recalls, with 1/cut factor; different from explicit three-weight paper definition |
| Preference construction Eq4 | same notebook cells23–29; flattened lines807–955 | Inconsistent | Score buckets, duplicate-text filtering, extrema-only pairs, category-specific thresholds and caps; not fully specified by paper |
| SFT target selection Eq3 | `create_sft_TopiOCQA.ipynb`, pseudo_best_reQ and best_data cells | Unverified / Inconsistent | Stateful cutoff dictionaries/bug block clean execution; final best-query artifacts unavailable |
| SFT optimization | [supervised-fine-tune-qlora_llama3.py](https://github.com/dlwnsdn0285/kisti-rag/blob/979ae1083105579298bd3682ce8a16eae0a7b566/DualReform-main/PreferenceOptimization/supervised-fine-tune-qlora_llama3.py#L147), `train`, lines147–201 | Verified in source / Inconsistent | Batch64 vs paper32; bf16, LoRA r8/alpha16/qkv/o; NF4 loading earlier in function |
| DPO optimization | [dpo_llama3_accelerate.py](https://github.com/dlwnsdn0285/kisti-rag/blob/979ae1083105579298bd3682ce8a16eae0a7b566/DualReform-main/PreferenceOptimization/dpo_llama3_accelerate.py#L70), `main`70–312 | Verified in source / Unverified | NF4/bf16/FlashAttention2 lines125–147; beta/lr CLI defaults differ; seed0; steps=per_epoch_steps*1 |
| Split boundaries | same DPO script lines205–207 | Inconsistent / Unverified | DataFrame 5% row sampling random_state1; related preference pairs can share a conversation. No proof of benchmark test leakage, but a conversation-disjoint validation guarantee is absent |
| Sparse evaluation | `bm25_on_topiocqa.py::print_res`270–332 | Verified in source | pytrec_eval; separate binary qrels and nDCG relevance; copy writes seven-column run and strips first3 doc-ID characters |
| Dense retrieval | `CQR/dense_retrieve/run_dense_search_topiocqa.py::main`, model/index utilities; `CQR/db_build/data_preprocessing_topiocqa.py::main` | Verified in source / Unverified | GTR model named, max length384; full index/corpus mapping not recovered |
| Preprocessing IDs and gold boundary | `CQR/sparse_retrieve/data/preprocess_topiocqa.py::convert_collection`, `combine_data_train` | Inconsistent / Unverified | Converter breaks in first loop with writes commented; preprocessing materializes gold fields. A safe training allowlist is required; existence of gold fields alone does not establish training leakage |
| Final expanded experiments | Qwen, ANCE, UltraChat, dynamic beta, self-generated candidates pp.9,31–34 | Unverified | Final-paper settings are not established by this older copy |
| Trained model/checkpoint | README paths, SFT/DPO and merge notebooks | Missing | No public trained release recovered |

## Concrete blockers in the copy

The preference notebook retains only `temp_all_res_pseudo_dict[3]` and then indexes
`pseudo_res_lists_dict[1]` in cell22 (flattened lines733,762). This fails in a clean
execution of those displayed cells. Later `allpairs_dict` values are lists, but
cell28 calls `.items()` on a value (flattened lines862–900 and941). Sampling
10,000 preferences without checking availability also prevents small runs.
These findings are static; we did not claim to have executed failing research
training. Fixing them would require a labeled port with an explicit decision on
the intended algorithm, not a silent “official baseline” patch.

## Local reconstruction boundaries

`paper_reimplementation/signals.py` implements the query-form template, iteration0
query rule, top3 selection, Eq21 with **mandatory supplied weights/K**, and strict
score-order pairs. These functions are tested only with engineering fixtures.
They do not reproduce the copy's contradictory scoring/sampling policy and are
not used to manufacture benchmark preferences. `scripts.run_initial_pseudo`
is a reconstructed sparse iteration0 adapter requiring an external full index.
`scripts.run_checkpoint_inference` is an inference engine for an externally
provenanced checkpoint and pre-rendered prompts; its fp16/eager/greedy profile
is an explicit deviation, not an exact baseline configuration.
