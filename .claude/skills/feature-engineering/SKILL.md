---
name: feature-engineering
description: Turns EDA findings into a SageMaker Processing Job that produces features and (optionally) registers them to Feature Store. Use after /eda, or when the user wants to build/update a feature set for training.
---

# Feature Engineering

Generates a SageMaker Processing Job (scikit-learn or your own container, per the project's container strategy — see below) that transforms raw data into a training-ready feature set. Per [ADR 0001](/docs/adr/0001-scaffold-and-confirm-execution-model.md), this skill generates code for the user to submit — it does not call `Processor.run()` itself.

## Steps

1. **Confirm the transform list.** Derive it from the most recent `/eda` output if available in the conversation; otherwise ask what transforms are needed (imputation, encoding, scaling, aggregation, joins). Don't guess silently at business-logic transforms (e.g. what counts as an "active user") — check `CONTEXT.md` for defined terms and ask if a term isn't defined there.
2. **Pick the container.** Built-in `SKLearnProcessor`/`FrameworkProcessor` if the transforms are standard pandas/sklearn; a custom BYOC image (with a `Dockerfile` under e.g. `containers/feature-eng/`) only if the team's existing containers are already BYOC or the transform needs a dependency not in the built-in image. Don't introduce a BYOC container for what a built-in image already covers.
3. **Generate the Processing Job script** (`preprocessing.py` or similar): reads from the input channel, applies the confirmed transforms, writes train/validation/test splits to the output channels.
4. **Generate the submission code**: a `SKLearnProcessor`/`Processor` construction with instance type/count, input (S3 source or Feature Store query) and output S3 paths. Do not choose oversized instance types by default — start from the smallest instance that fits the data volume and say so.
5. **Feature Store registration (optional).** If the user wants these features reusable across projects, generate a `FeatureGroup` definition and the `ingest()` call for the output — as code, not executed.
6. **Print a summary**: what the job will read, what it will produce, where outputs land, and the generated code block(s) — then stop. Actually running the job (`.run(...)`) is the user's call.

## Notes

- Keep feature derivation logic in the generated script itself (not inline in the chat), so it's reviewable and versionable in the repo.
- Flag any transform that fits a column only seen in training data (e.g. a `LabelEncoder` fit on train) — this must be persisted (joblib/pickle to S3) and reloaded at inference, not refit at serving time.
