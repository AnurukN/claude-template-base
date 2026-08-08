---
name: train-model
description: Generates a SageMaker Training Job (or hyperparameter tuning job) for a model, prints the estimated cost and command, and waits for explicit confirmation before submitting. Use after /feature-engineering, or when the user wants to train/retrain a model.
---

# Train Model

Generates SageMaker Training Job code. Per [ADR 0001](/docs/adr/0001-scaffold-and-confirm-execution-model.md), this skill never calls `.fit()` itself — training jobs cost real money per instance-hour and are not trivially cancellable mid-run, so submission always requires the user's explicit go-ahead.

## Steps

1. **Confirm inputs.** Where the training data lives (S3 path from `/feature-engineering` output, or Feature Store), the algorithm/framework, and whether this is a single training run or a hyperparameter tuning job (`HyperparameterTuner`) across a range.
2. **Pick the estimator.** Built-in algorithm/framework container (`SKLearn`, `PyTorch`, `XGBoost`, etc.) unless the project already uses a BYOC training image — don't introduce a new container type without asking.
3. **Generate the training script** (`train.py`): reads the SageMaker channels (`SM_CHANNEL_TRAIN`, etc.), trains, writes the model artifact to `SM_MODEL_DIR`, and writes metrics somewhere `/evaluate-model` and the `model-evaluator` agent can find (a metrics JSON to the output path, and/or logged via SageMaker Experiments `Run.log_metric`).
4. **Generate the submission code**: `Estimator`/`HyperparameterTuner` construction with instance type/count, hyperparameters, and an Experiments `Run` context so this training run is tracked (per [ADR 0003](/docs/adr/0003-native-sagemaker-tracking.md)).
5. **Estimate cost before printing the final command**: instance type hourly rate × expected instance count × a rough duration estimate (based on data size / epochs if known, otherwise say the estimate is rough). State this plainly, e.g. "≈ $X for a Y-hour run on `ml.m5.xlarge`."
6. **Stop and ask for confirmation** — print the generated script, the submission code, and the cost estimate, then explicitly ask "submit this training job?" before running anything. If the user says no or doesn't respond, do not submit.
7. **After a confirmed run**, if the user asks you to actually execute it, run the submission code and report the resulting Experiments run name / job name so `/evaluate-model` can find it.

## Notes

- Never pick an instance type larger than what the user's data size plausibly needs without flagging it — oversized instances are the most common accidental cost blowup.
- If this is a retrain of an existing model, link the new run to the same Experiment as prior runs so `/evaluate-model` can compare against the last one automatically.
