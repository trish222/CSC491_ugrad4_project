"""Print the pilot's stepwise added code lines from its tags."""
import csv
import subprocess
import sys


previous = "ai-base"
counts = []
for step in range(1, 11):
    tag = f"ai-step{step}"
    diff = subprocess.check_output(
        ["git", "diff", "--unified=0", previous, tag, "--", "pilot.py"], text=True
    )
    counts.append(sum(line.startswith("+") and not line.startswith("+++")
                      and bool(line[1:].strip()) and not line[1:].lstrip().startswith("#")
                      for line in diff.splitlines()))
    previous = tag
out = csv.writer(sys.stdout)
out.writerow(("step", "new_loc", "percent_of_total_new_loc"))
for step, count in enumerate(counts, 1):
    out.writerow((step, count, f"{100 * count / sum(counts):.2f}"))
