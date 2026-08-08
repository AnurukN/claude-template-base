---
name: evaluate-model
description: Pulls metrics for a completed training run from SageMaker Experiments/Model Registry, compares against baseline, and dispatches the model-evaluator agent for a go/no-go recommendation. Use after /train-model completes, or when asked whether a model is good enough to deploy.
---

# Evaluate Model

Reads the evidence a training run produced and gets an independent go/no-go verdict. This skill does not itself judge model quality — that judgment is delegated to the `model-evaluator` agent so the recommendation comes from a focused read of the metrics, not from whatever else is in the conversation.

## Steps

1. **Identify the run.** The SageMaker Experiments run name / training job name from the most recent `/train-model` call in this conversation, or ask which run if not obvious.
2. **Identify the baseline.** The currently `Approved` model package in Model Registry for this model group, or the previous run in the same Experiment. If neither exists, say so explicitly — this is a first model, not a regression.
3. **Gather the metrics** for both the candidate run and the baseline: pull from SageMaker Experiments (`Run.list`/metrics) and/or the Model Registry model package's `ModelMetrics`.
4. **Dispatch the `model-evaluator` agent** with the candidate metrics, baseline metrics, and any project-specific quality bar the user has stated (e.g. "recall must stay above 0.85"). Do not pre-judge the result yourself — pass the raw metrics through.
5. **Report the agent's verdict** (go / no-go / inconclusive) to the user, with the reasoning and caveats it gave.
6. **On "go"**, offer to register the model package to SageMaker Model Registry (as `PendingManualApproval` — this skill does not auto-approve) so `/deploy-model` has something to deploy. On "no-go" or "inconclusive", stop here; don't proceed toward deployment.

## Notes

- If metrics can't be found for either run, say so and stop — don't let the agent guess at numbers that don't exist.
- Keep the Experiments run and Model Registry model package linked (tag the model package with the run name) so future evaluations can trace a deployed model back to the run that produced it.
