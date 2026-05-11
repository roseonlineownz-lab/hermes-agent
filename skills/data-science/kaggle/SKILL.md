---
name: kaggle
description: "Kaggle CLI: download datasets, submit to competitions, push notebook kernels. Free GPU/TPU runtime is available via Kernels."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [KAGGLE_USERNAME, KAGGLE_KEY]
  commands: [kaggle, python3]
metadata:
  hermes:
    tags: [Kaggle, Datasets, Competitions, Free GPU, Data Science]
    homepage: https://www.kaggle.com/docs/api
---

# Kaggle — Datasets, Competitions, Kernels

Kaggle exposes a Python CLI (`pip install kaggle`) that wraps everything you can do in the UI: download datasets, list/enter competitions, push notebook kernels, manage submissions. Free GPU/TPU runtime is available via Kernels — 30 hours/week of GPU, no credit card.

## Prerequisites

1. Create an API token: https://www.kaggle.com/settings → "Create New Token". This downloads `kaggle.json` with two fields.
2. Either drop the JSON in `~/.kaggle/kaggle.json` (chmod 600) **or** export the credentials as env vars:
   ```bash
   export KAGGLE_USERNAME=yourname
   export KAGGLE_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
3. Install the CLI: `pip install --user kaggle` (or `uv pip install kaggle`).

## Common tasks

### Search & list datasets
```bash
kaggle datasets list -s "weather" --sort-by votes --max-size 1000
```

### Download a dataset (zipped)
```bash
mkdir -p ~/data/weather && cd ~/data/weather
kaggle datasets download -d zaraavagyan/weathercsv
unzip weathercsv.zip
```

### Pull a competition's files
```bash
kaggle competitions list -s titanic
kaggle competitions download -c titanic -p ./titanic
unzip ./titanic/titanic.zip -d ./titanic
```

### Submit predictions
```bash
kaggle competitions submit -c titanic -f submission.csv -m "stacked random forest v3"
kaggle competitions submissions -c titanic   # last 10 submissions + scores
```

### Push a notebook kernel (free GPU)
```bash
# 1. Init: creates kernel-metadata.json in cwd
kaggle kernels init -p .

# 2. Edit kernel-metadata.json:
#    "id": "yourname/my-experiment",
#    "code_file": "experiment.ipynb",
#    "language": "python",
#    "kernel_type": "notebook",
#    "is_private": "true",
#    "enable_gpu": "true",
#    "enable_internet": "false",
#    "dataset_sources": ["zaraavagyan/weathercsv"]

# 3. Push:
kaggle kernels push -p .
```

The kernel runs server-side on Kaggle's GPU/TPU cluster. Poll status:

```bash
kaggle kernels status yourname/my-experiment
kaggle kernels output yourname/my-experiment -p ./out   # download outputs once "complete"
```

## Workflow patterns

- **Free-GPU pipeline:** push an `.ipynb` that loads model weights from a Kaggle dataset (no internet needed), runs evaluation/finetune, writes results to `/kaggle/working`, and download those artifacts with `kernels output`.
- **Dataset-as-cache:** turn a one-off scrape into a Kaggle dataset (`kaggle datasets create`); future runs read it with no rate limits.
- **Competition wash-up:** combine `competitions leaderboard` + `competitions submissions` into a digest your agent posts to Linear/ClickUp.

## Gotchas

- **CPU-only kernels are unlimited; GPU kernels are 30h/week** and TPU is 20h/week (subject to change). Check `https://www.kaggle.com/account` → "Compute usage".
- `enable_internet: true` requires a phone-verified account. Without it, kernels can't reach pypi/huggingface — pre-bundle dependencies as Kaggle datasets.
- The CLI looks for credentials in this order: `KAGGLE_USERNAME/KAGGLE_KEY` env vars > `KAGGLE_CONFIG_DIR/kaggle.json` > `~/.kaggle/kaggle.json`. Set whichever fits your sandbox.
- Datasets >20GB time out from the CLI — use `kaggle datasets download --unzip` only for the smaller chunks.

## See also

- Mark-XXX integration: `core/integrations/kaggle.py` (subprocess wrapper around the CLI)
- `skills/data-science/colab/SKILL.md` (sibling free-GPU runtime)
- `skills/data-science/jupyter-live-kernel/SKILL.md` (local kernels)
