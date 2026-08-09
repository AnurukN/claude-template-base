---
name: train-model
description: Generates a SageMaker Training Job (or hyperparameter tuning job), or a Local Anaconda+MLflow training run, prints the estimated cost and command, and waits for explicit confirmation before running. Use after /feature-engineering, or when the user wants to train/retrain a model.
---

# Train Model

Generates training code for whichever Platform target the user picks. Per [ADR 0001](/docs/adr/0001-scaffold-and-confirm-execution-model.md), this skill never calls `.fit()`/runs the script itself — submission always requires the user's explicit go-ahead.

## Steps

1. **Confirm the Platform target.** Ask "SageMaker or Local?" every time this skill is invoked — never assume a default (per [ADR 0010](/docs/adr/0010-local-anaconda-mlflow-platform-target.md)).
2. **Confirm inputs.** Where the training data lives (S3 path from `/feature-engineering` output or Feature Store for SageMaker; a local file path for Local), the algorithm/framework, and whether this is a single training run or a hyperparameter tuning job (`HyperparameterTuner`, SageMaker only) across a range.
3. **Pick the estimator/library.** SageMaker: built-in algorithm/framework container (`SKLearn`, `PyTorch`, `XGBoost`, etc.) unless the project already uses a BYOC training image. Local: the equivalent plain library call (`sklearn`, `xgboost`, etc.) run in-process — no container involved.
4. **Generate the training script** (`train.py`):
   - **SageMaker**: reads the SageMaker channels (`SM_CHANNEL_TRAIN`, etc.), trains, writes the model artifact to `SM_MODEL_DIR`, and writes metrics somewhere `/evaluate-model` and the `model-evaluator` agent can find (a metrics JSON to the output path, and/or logged via SageMaker Experiments `Run.log_metric`).
   - **Local**: reads the local file path directly, trains, and wraps the run in `mlflow.start_run()` — logging hyperparameters (`mlflow.log_param`), metrics (`mlflow.log_metric`), and the model artifact (`mlflow.<flavor>.log_model`) to the Tracking Store (`file:./mlruns`).
5. **Generate the submission/run code**:
   - **SageMaker**: `Estimator`/`HyperparameterTuner` construction with instance type/count, hyperparameters, and an Experiments `Run` context so this training run is tracked (per [ADR 0003](/docs/adr/0003-native-sagemaker-tracking.md), superseded by ADR 0010 for the Local target).
   - **Local**: a plain invocation of `train.py` (or a call to its entrypoint) with hyperparameters passed as arguments — this is a Local run, no job submission API involved.
6. **Estimate cost before printing the final command** — dispatch the `cost-estimator` agent regardless of platform (it returns "$0 — runs on your local machine" instantly for Local, no computation needed). For SageMaker state it plainly, e.g. "≈ $X for a Y-hour run on `ml.m5.xlarge`."
7. **Stop and ask for confirmation** — print the generated script, the run code, and the cost estimate, then explicitly ask "submit this training job?" (SageMaker) or "run this training locally now?" (Local) before running anything. If the user says no or doesn't respond, do not run it.
8. **After a confirmed run**, if the user asks you to actually execute it, run the submission/run code and report the resulting Experiments run name / job name (SageMaker) or Local run ID from the Tracking Store (Local) so `/evaluate-model` can find it.

## Notes

- Local: if the project has no `environment.yml` yet, generate one at the repo root (a single shared file per [ADR 0010](/docs/adr/0010-local-anaconda-mlflow-platform-target.md), not per-stage) covering `mlflow` plus whatever training library this script needs. If one already exists, add missing dependencies to it rather than replacing it.
- SageMaker: never pick an instance type larger than what the user's data size plausibly needs without flagging it — oversized instances are the most common accidental cost blowup.
- If this is a retrain of an existing model, link the new run to the same Experiment (SageMaker) or the same MLflow Experiment (Local) as prior runs so `/evaluate-model` can compare against the last one automatically.
