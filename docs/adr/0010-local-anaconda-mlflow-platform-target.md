Status: accepted — supersedes ADR-0003

# Add Local (Anaconda + MLflow) as a second platform target

`/feature-engineering`, `/train-model`, `/evaluate-model`, `/deploy-model`, and `/build-pipeline` currently only generate SageMaker code, and ADR 0003 rejected MLflow because "the team is already fully on AWS." That premise no longer holds — small-dataset work needs a zero-cost local option. We're adding **Local** as a second Platform target alongside **SageMaker**, chosen by the user each time a skill is invoked (per ADR 0001's scaffold-and-confirm style, not a hidden config default). MLflow provides tracking only — a local file-based Tracking Store at `file:./mlruns`, no Model Registry and no standing serving process. `/deploy-model`'s Local target instead offers three user-selected Local deploy modes (MLflow Serve, a generated local API wrapper, or export-only) rather than a SageMaker Endpoint equivalent, and `/build-pipeline`'s Local target generates a plain sequential script instead of a `sagemaker.workflow.pipeline.Pipeline`.

## Considered options for MLflow's role

- **Tracking + Model Registry + Serving** (full swap for SageMaker Experiments/Model Registry/Endpoint) — rejected: adds serving infrastructure to stand up and maintain, which doesn't match the cost-driven, small-dataset use case this is meant to serve.
- **Tracking only, with `/deploy-model` handling serving separately per user-selected mode** — chosen: keeps MLflow's footprint minimal and reuses `/deploy-model`'s existing pattern of offering multiple deploy targets.
