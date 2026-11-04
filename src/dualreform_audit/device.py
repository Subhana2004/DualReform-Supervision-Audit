"""Lazy hardware checks; never turn missing GPU into an implicit model substitution."""


def select_device(requested="auto", cuda_available=False):
    if requested not in ("auto", "cpu", "cuda"):
        raise ValueError("Unknown device")
    if requested == "cuda" and not cuda_available:
        raise RuntimeError("CUDA requested but unavailable")
    return "cuda" if cuda_available and requested != "cpu" else "cpu"
