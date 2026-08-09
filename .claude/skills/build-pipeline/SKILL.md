---
name: build-pipeline
description: Wires feature-engineering, training, evaluation, and deployment stages into a single SageMaker Pipeline definition, or a Local sequential script. Use once the individual stages (via /feature-engineering, /train-model, /evaluate-model, /deploy-model) are working standalone and the user wants to automate the sequence end-to-end.
---

# Build Pipeline

Composes the already-validated per-stage code from `/feature-engineering`, `/train-model`, `/evaluate-model`, and `/deploy-model` into one automated sequence for whichever Platform target the user picks — a `sagemaker.workflow.pipeline.Pipeline` for SageMaker, or a Local pipeline (a single sequential script/Makefile, per [ADR 0010](/docs/adr/0010-local-anaconda-mlflow-platform-target.md)) for Local. This skill does not re-derive the stage logic — it wires together the scripts those skills already generated.

Only run this once the individual skills have produced working code in this project. Don't use this skill to skip straight to a pipeline before a single manual run of each stage has been confirmed to work — a pipeline automates a known-good sequence, it isn't how you first discover one.

## Steps

1. **Confirm the Platform target.** Ask "SageMaker or Local?" every time this skill is invoked — never assume a default. Both tracks must be composed of stage code already generated under the same target; don't mix a SageMaker training script into a Local pipeline or vice versa.
2. **Confirm the stage code exists.** Locate the processing script, training script, and (if applicable) evaluation/condition logic already generated for this Platform target in this project. If a stage hasn't been built yet, direct the user to that skill first rather than inventing the step from scratch.
3. **Wire the stages together.**
   - **SageMaker**: map each stage to a Pipeline step type — `ProcessingStep` (feature engineering), `TrainingStep` (training), a `ProcessingStep` or `Callback`/Lambda step for evaluation that writes a metrics report, `ConditionStep` gating deployment on the evaluation result (e.g. only register/deploy `if` the primary metric clears a threshold), and a registration/deploy step. Wire `PipelineSession` and step dependencies (`.add_depends_on` or data dependencies via step properties) so steps run in the right order with the right inputs/outputs threaded between them.
   - **Local**: generate a single script (or Makefile target) that runs each stage's script in sequence — feature engineering, then training, then evaluation — checking the evaluation script's exit code/output before proceeding to deploy, as the Local substitute for a `ConditionStep`. If the evaluation result is no-go, the script stops before deploy.
4. **Parameterize what should vary per run**: instance types, input path, metric threshold. SageMaker — as `ParameterString`/`ParameterFloat` pipeline parameters, not hardcoded, so the same pipeline definition serves multiple runs. Local — as command-line args/env vars to the sequential script, same reasoning.
5. **Generate the pipeline/script and its run code**: SageMaker — the pipeline definition and `pipeline.upsert(role_arn=...)`, printed per [ADR 0001](/docs/adr/0001-scaffold-and-confirm-execution-model.md); creating/starting the pipeline execution is the user's call, not automatic. Local — the sequential script itself; running it is likewise the user's call, though there's no cost gate to justify withholding it beyond review.
6. **Do not silently drop the confirmation gates** the individual skills established (e.g. deploy still only happens conditionally on the evaluation threshold) — the pipeline/script should encode the same guardrails those skills apply manually, since there's no human in the loop once it starts.

## Notes

- A `ConditionStep` (SageMaker) or exit-code check (Local) before deployment is the pipeline's substitute for the manual "go/no-go" the `model-evaluator` agent gives interactively — make sure the threshold it checks matches what the team actually uses in `/evaluate-model`.
