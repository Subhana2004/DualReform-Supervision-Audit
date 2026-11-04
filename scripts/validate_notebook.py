"""Validate notebook structure and compile every code cell; optional local CPU setup execution."""
import argparse
import nbformat


def validate(path="notebooks/phase1_kaggle_baseline.ipynb", execute_cpu=False):
    nb = nbformat.read(path, as_version=4)
    nbformat.validate(nb)
    scope = {"__name__": "__notebook_cpu_validation__"}
    cells = 0
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == "code":
            compile(cell.source, f"notebook-cell-{i}", "exec")
            cells += 1
            if execute_cpu and "cpu-validation" in cell.metadata.get("tags", []):
                exec(compile(cell.source, f"notebook-cell-{i}", "exec"), scope)
    assert cells >= 8
    assert all(not c.get("outputs") and c.get("execution_count") is None
               for c in nb.cells if c.cell_type == "code")
    print(f"Notebook valid: {cells} code cells; CPU setup execution={execute_cpu}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute-cpu", action="store_true")
    a = p.parse_args()
    validate(execute_cpu=a.execute_cpu)
