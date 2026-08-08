---
name: build-pipeline
description: Wires feature-engineering, training, evaluation, and deployment stages into a single SageMaker Pipeline definition. Use once the individual stages (via /feature-engineering, /train-model, /evaluate-model, /deploy-model) are working standalone and the user wants to automate the sequence end-to-end.
---

# Build Pipeline

Composes the already-validated per-stage code from `/feature-engineering`, `/train-model`, `/evaluate-model`, and `/deploy-model` into one `sagemaker.workflow.pipeline.Pipeline`. This skill does not re-derive the stage logic — it wraps the scripts/estimators those skills already generated as pipeline `Steps`.

Only run this once the individual skills have produced working code in this project. Don't use this skill to skip straight to a pipeline before a single manual run of each stage has been confirmed to work — a pipeline automates a known-good sequence, it isn't how you first discover one.

## Steps

1. **Confirm the stage code exists.** Locate the processing script, training script, and (if applicable) evaluation/condition logic already generated in this project. If a stage hasn't been built yet, direct the user to that skill first rather than inventing the step from scratch.
2. **Map each stage to a Pipeline step type**: `ProcessingStep` (feature engineering), `TrainingStep` (training), a `ProcessingStep` or `Callback`/Lambda step for evaluation that writes a metrics report, `ConditionStep` gating deployment on the evaluation result (e.g. only register/deploy `if` the primary metric clears a threshold), and a registration/deploy step.
3. **Wire `PipelineSession` and step dependencies** (`.add_depends_on` or data dependencies via step properties) so steps run in the right order with the right inputs/outputs threaded between them.
4. **Parameterize what should vary per run**: instance types, input S3 path, metric threshold — as `ParameterString`/`ParameterFloat` pipeline parameters, not hardcoded, so the same pipeline definition serves multiple runs.
5. **Generate the pipeline definition and upsert code** (`pipeline.upsert(role_arn=...)`), and print it — per [ADR 0001](/docs/adr/0001-scaffold-and-confirm-execution-model.md), creating/starting the pipeline execution is the user's call, not automatic.
6. **Do not silently drop the confirmation gates** the individual skills established (e.g. deploy still only happens conditionally on the evaluation threshold) — the pipeline should encode the same guardrails those skills apply manually, via the `ConditionStep`, since there's no human in the loop once a pipeline execution starts.

## Notes

- A `ConditionStep` before deployment is the pipeline's substitute for the manual "go/no-go" the `model-evaluator` agent gives interactively — make sure the threshold it checks matches what the team actually uses in `/evaluate-model`.
