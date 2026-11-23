"""Collect one-shot Python source responses for the six LLM treatments."""
import argparse
import ast
import itertools
import json
from pathlib import Path
import shlex
import subprocess

from pilot import DATA


ROOT = Path(__file__).resolve().parent


def requirements():
    skills = {}
    for line in (ROOT / "docs/requirements.md").read_text().splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) == 5 and cells[1].isdigit():
            skills.setdefault(cells[2], []).append(cells[3])
    if len(skills) != 10 or any(len(asks) != 2 for asks in skills.values()):
        raise ValueError("Expected ten skills with two requests each.")
    return skills


def source_code(response):
    code = response.strip()
    if code.startswith(("```python\n", "```\n")) and code.endswith("\n```"):
        code = code.split("\n", 1)[1].rsplit("\n", 1)[0]
    tree = ast.parse(code)
    if not any(isinstance(node, ast.FunctionDef) and node.name == "demo"
               for node in tree.body):
        raise ValueError("Expected a top-level demo function.")
    return code + "\n"


def collect(folder, command, model, background, reuse, header, ezr, trial):
    folder.mkdir(parents=True)
    prior = {}
    measurements = []
    instruction = ("Reuse earlier modules when useful." if reuse else
                   "Implement independently without importing or copying earlier modules.")
    library = {"python": "Python standard library only",
               "sklearn": "Python standard library and scikit-learn",
               "ezr": "Python standard library and the supplied ezr.py"}[background]
    if background == "ezr":
        (folder / "ezr.py").write_text(ezr)
    for step, (skill, asks) in enumerate(requirements().items(), 1):
        prompt = f"""Write the {skill} skill as a Python module. {instruction}
Allowed background: {library}.
Customer asks: {' '.join(asks)}
CSV header: {header}
Use a top-level demo(csv_path, seed) returning a nonempty JSON-compatible dict.
Shuffle rows with random.Random(seed). Hold out the first 20 rows and any rows
sharing their idX. Ignore X columns as predictive features. Never use held-out
goals (Kloc+, Effort-, Defects-) as predictors or to tune the model. Use them
only for evaluation and completed-project analyses. Import prior modules by
name when applicable. Output only the new module's source.
Earlier modules from this trial: {json.dumps(prior)}
"""
        if background == "ezr":
            prompt += f"\nCourse ezr.py source:\n{ezr}\n"
        (folder / f"{skill}.prompt.txt").write_text(prompt)
        entry = {"trial": trial, "step": step, "skill": skill, "model": model,
                 "background": background, "reuse": reuse, "new_loc": None}
        try:
            response = subprocess.run(command, input=prompt, cwd=folder, text=True,
                                      capture_output=True, check=True, timeout=240).stdout
            (folder / f"{skill}.response.txt").write_text(response)
            code = source_code(response)
            (folder / f"{skill}.py").write_text(code)
            prior[skill] = code
            entry.update(status="parsed", new_loc=sum(
                bool(line.strip()) and not line.lstrip().startswith("#")
                for line in code.splitlines()))
        except (OSError, subprocess.SubprocessError, ValueError, SyntaxError) as error:
            entry.update(status=type(error).__name__)
        measurements.append(entry)
        (folder / "measurements.json").write_text(json.dumps(measurements, indent=2) + "\n")
        if entry["status"] in {"FileNotFoundError", "CalledProcessError"}:
            raise SystemExit(f"Model command failed at {folder.name}/{skill}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", required=True, help="One-shot runner reading stdin")
    parser.add_argument("--model", required=True, help="Exact model version for the log")
    parser.add_argument("--ezr", required=True, type=Path, help="Pinned course Python source")
    parser.add_argument("--repeats", type=int, choices=range(1, 21), default=10)
    parser.add_argument("--out", type=Path, default=ROOT / "runs")
    args = parser.parse_args()
    if not DATA.exists() or args.out.exists():
        parser.error("Fetch the dataset first and choose a fresh output directory.")
    command = shlex.split(args.command)
    if not command:
        parser.error("Provide the one-shot runner command.")
    with DATA.open() as stream:
        header = stream.readline().strip()
    ezr = args.ezr.read_text()
    for trial, background, reuse in itertools.product(
            range(1, args.repeats + 1), ("python", "sklearn", "ezr"), (False, True)):
        folder = args.out.resolve() / f"{background}-{int(reuse)}-trial{trial:02}"
        collect(folder, command, args.model, background, reuse, header, ezr, trial)


if __name__ == "__main__":
    main()
