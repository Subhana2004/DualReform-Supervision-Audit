"""Inference engine for a separately acquired checkpoint and reviewed, pre-rendered prompts.

Does not assert checkpoint authenticity, synthesize prompts, or substitute a base model.
Hardware precision is explicitly fp16/eager, a deviation from the copied bf16/FlashAttention path.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import time

from dualreform_audit.io import digest, git_sha, write_json, write_jsonl


def execute(checkpoint, prompts, provenance, output, limit=8):
    info = json.loads(Path(provenance).read_text(encoding="utf-8"))
    required = {"model_revision", "dataset_version", "source_revision", "license", "files_sha256"}
    if not required <= info.keys() or not info["files_sha256"]:
        raise ValueError("Checkpoint provenance is incomplete")
    root = Path(checkpoint).resolve()
    for name, sha in info["files_sha256"].items():
        target = (root / name).resolve()
        if not target.is_relative_to(root) or digest(target) != sha:
            raise ValueError("Checkpoint hash verification failed")
    for target in root.rglob("*.safetensors"):
        if target.relative_to(root).as_posix() not in info["files_sha256"]:
            raise ValueError("Every weight shard must be covered by checkpoint provenance")
    if not any(root.rglob("*.safetensors")):
        raise ValueError("Expected a merged safetensors checkpoint; adapters require audited merge")
    rows = [json.loads(s) for s in Path(prompts).read_text(encoding="utf-8").splitlines()]
    if limit < 1 or not rows or any(set(r) != {"id", "prompt"} for r in rows):
        raise ValueError("Expected nonempty reviewed prompts containing only id and prompt")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    if not torch.cuda.is_available():
        raise RuntimeError("GPU inference requested but CUDA is unavailable")
    memory = sum(torch.cuda.get_device_properties(i).total_memory
                 for i in range(torch.cuda.device_count()))
    if memory < 22 * 1024**3:
        raise RuntimeError("8B fp16 checkpoint needs a reviewed memory budget: this runner requires "
                           "22 GiB aggregate GPU memory; one T4 is insufficient. No automatic quantization.")
    random.seed(42)
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.use_deterministic_algorithms(True)
    tokenizer = AutoTokenizer.from_pretrained(root, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        root, local_files_only=True, torch_dtype=torch.float16, device_map="auto",
        attn_implementation="eager", trust_remote_code=False)
    model.eval()
    for i in range(torch.cuda.device_count()):
        torch.cuda.reset_peak_memory_stats(i)
    clock, records = time.perf_counter(), []
    for row in rows[:limit]:
        inputs = tokenizer(row["prompt"], return_tensors="pt").to(model.get_input_embeddings().weight.device)
        if inputs.input_ids.shape[1] + 512 > 4096:
            raise ValueError("Prompt exceeds 4096-token budget; refusing silent truncation")
        with torch.inference_mode():
            sequence = model.generate(**inputs, max_new_tokens=512, do_sample=False,
                                      pad_token_id=tokenizer.eos_token_id)
        records.append({**row, "generated_text": tokenizer.decode(
            sequence[0, inputs.input_ids.shape[1]:], skip_special_tokens=False),
            "generated_token_ids": sequence[0, inputs.input_ids.shape[1]:].tolist()})
    torch.cuda.synchronize()
    out = Path(output)
    write_jsonl(out / "per_example.jsonl", records)
    write_json(out / "run_manifest.json", {
        "execution_status": "completed_checkpoint_inference_authenticity_as_supplied",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(), "git_sha": git_sha(),
        "checkpoint_provenance": info, "prompts_sha256": digest(prompts),
        "runtime_seconds": time.perf_counter() - clock, "seed": 42,
        "gpu_execution": "EXECUTED", "python": __import__("platform").python_version(),
        "torch": torch.__version__, "cuda": torch.version.cuda,
        "gpus": [{"name": torch.cuda.get_device_name(i),
                  "peak_allocated_bytes": torch.cuda.max_memory_allocated(i)}
                 for i in range(torch.cuda.device_count())],
        "hardware_adaptation": "fp16/eager; no quantization or architecture change",
        "generation": {"max_new_tokens": 512, "do_sample": False,
                       "note": "greedy engine setting; exact published decoding is unverified"},
        "result_paths": [str(out / "per_example.jsonl")],
        "accuracy": None, "note": "Retrieval/evaluation is a separate explicit stage"})


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ("checkpoint", "prompts", "provenance", "output"):
        p.add_argument("--" + arg, required=True)
    p.add_argument("--limit", type=int, default=8)
    a = p.parse_args()
    execute(a.checkpoint, a.prompts, a.provenance, a.output, a.limit)
