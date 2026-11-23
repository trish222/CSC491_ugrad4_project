# CSC491_ugrad4_project
CSC491-005 Undergrad Group 4 Final Project

## Development pilot

The lecturer-approved [requirements](docs/requirements.md) describe 20 questions for a
software project manager. The input is MOOT's 93-row NASA project dataset. The
three goal columns are `Kloc+`, `Effort-`, and `Defects-`.

The `ai-pilot` branch is a Codex-authored development pilot. Its `ai-step1`
through `ai-step10` tags reserve `step1` through `step10` for the team's
hand-written treatment. The pilot is outside the six independent LLM treatments.

Run once from the repo root to fetch and checksum the pinned CSV:

```sh
python3 fetch_data.py
python3 -m unittest discover -s tests
python3 measure_pilot.py
```

Run each demo from the repo root:

```sh
python3 pilot.py remember
python3 pilot.py guess
python3 pilot.py certify
python3 pilot.py flow
python3 pilot.py blame
python3 pilot.py justify
python3 pilot.py choose
python3 pilot.py fix
python3 pilot.py spot
python3 pilot.py race
```

The pilot uses matched historical comparisons and a sign test in its domain
`certify` demo. The experiment's cross-treatment comparisons require the course
`same` implementation. The pilot's sample result and code counts are excluded
from those comparisons.

## Collecting trial outputs

Pin the course's Python ezr module and choose a one-shot API wrapper that takes
a prompt on stdin and emits only source code on stdout. Configure the wrapper
with one model version and empty conversation history for every call. Disable
memory and prior-session continuation. At ten repeats, the collector makes
600 calls across six treatment combinations.

```sh
python3 collect_trials.py --command "/absolute/path/to/one-shot-wrapper" \
  --model "exact-model-version" --ezr "/absolute/path/to/ezr.py" --repeats 10
```

The collector makes separate directories per treatment and trial and explicitly
passes prior skill source within that trial. Save the exact prompts, responses,
and recorded parse outcomes. Syntax parsing is a preliminary check. Review and
execute generated modules in isolation and record demo/test outcomes before
analyzing the treatments. Preserve each trial's history and apply the same code
counting convention across all seven treatments. Incomplete or failed responses
should be reported with their status.

## AI disclosure and status

Codex drafted the customer requirements, wrote the pilot and collector, and added
the pilot tests. The first pilot split shuffled and sliced by row. A test caught
two records sharing project ID 29 and identical predictor values on opposite
sides of the split. The follow-up groups records by ID when holding projects out.

The team-authored control, real LLM trials, course `same` comparisons, ezr oracle
and tuning, and final ACM PDF are pending. The pilot's checked-in tags record
development before the duplicate-ID fix. The current branch runs the corrected
evaluation split.

Dataset source: [MOOT](https://github.com/timm/moot) at
`ca6163861db7b231824ecabc11b15a492b75df34`.
Cite Menzies et al., *MOOT: a Repository of Many Multi-Objective Optimization
Tasks*, [arXiv:2511.16882](https://arxiv.org/abs/2511.16882).
