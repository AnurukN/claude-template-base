---
name: feature-engineering
description: Turns EDA findings into a SageMaker Processing Job, or a Local Anaconda script, that produces features and (optionally, SageMaker only) registers them to Feature Store. Use after /eda, or when the user wants to build/update a feature set for training.
---

# Feature Engineering

Generates a feature transform for whichever Platform target the user picks — a SageMaker Processing Job (scikit-learn or your own container, per the project's container strategy — see below), or a plain Local script. Per [ADR 0001](/docs/adr/0001-scaffold-and-confirm-execution-model.md), for SageMaker this skill generates code for the user to submit — it does not call `Processor.run()` itself.

## Steps

1. **Confirm the Platform target.** Ask "SageMaker or Local?" every time this skill is invoked — never assume a default (per [ADR 0010](/docs/adr/0010-local-anaconda-mlflow-platform-target.md)).
2. **Confirm the transform list.** Derive it from the most recent `/eda` output if available in the conversation; otherwise ask what transforms are needed (imputation, encoding, scaling, aggregation, joins). Don't guess silently at business-logic transforms (e.g. what counts as an "active user") — check `CONTEXT.md` for defined terms and ask if a term isn't defined there.
3. **Pick the container/runner.**
   - **SageMaker**: built-in `SKLearnProcessor`/`FrameworkProcessor` if the transforms are standard pandas/sklearn; a custom BYOC image (with a `Dockerfile` under e.g. `containers/feature-eng/`) only if the team's existing containers are already BYOC or the transform needs a dependency not in the built-in image. Don't introduce a BYOC container for what a built-in image already covers.
   - **Local**: no container — the script runs directly in the project's conda environment (see `environment.yml`).
4. **Generate the transform script** (`preprocessing.py` or similar): applies the confirmed transforms and writes train/validation/test splits.
   - **SageMaker**: reads from the input channel, writes to the output channels.
   - **Local**: reads from a local file path, writes to a local output folder (e.g. `./data/processed/`).
5. **Generate the submission code (SageMaker only)**: a `SKLearnProcessor`/`Processor` construction with instance type/count, input (S3 source or Feature Store query) and output S3 paths. Do not choose oversized instance types by default — start from the smallest instance that fits the data volume and say so. For Local, there is no submission step — step 6 covers running it directly.
6. **Feature Store registration (SageMaker only, optional).** If the user wants these features reusable across projects, generate a `FeatureGroup` definition and the `ingest()` call for the output — as code, not executed. Feature Store has no Local equivalent; say so if asked.
7. **Print a summary**: what the transform will read, what it will produce, where outputs land, and the generated code block(s) — then stop. Actually running it (`.run(...)` for SageMaker, or the script itself for Local) is the user's call.

## Notes

- Local: if the project has no `environment.yml` yet, generate one at the repo root (a single shared file per [ADR 0010](/docs/adr/0010-local-anaconda-mlflow-platform-target.md), not per-stage) covering this script's dependencies. If one already exists, add missing dependencies to it rather than replacing it.
- Keep feature derivation logic in the generated script itself (not inline in the chat), so it's reviewable and versionable in the repo.
- Flag any transform that fits a column only seen in training data (e.g. a `LabelEncoder` fit on train) — this must be persisted (joblib/pickle, to S3 for SageMaker or to a local path for Local) and reloaded at inference, not refit at serving time.
