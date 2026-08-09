---
name: deploy-model
description: Generates a SageMaker Endpoint deployment for an approved model, or a Local deploy (MLflow Serve, a Local API wrapper, or export-only), prints the estimated cost and command, waits for confirmation, and includes a smoke test. Use after /evaluate-model returns "go", or when asked to deploy/serve a model.
---

# Deploy Model

Generates deployment code for whichever Platform target the user picks. Per [ADR 0001](/docs/adr/0001-scaffold-and-confirm-execution-model.md), this skill never runs the deploy itself — creation always requires the user's explicit go-ahead.

## Steps

1. **Confirm the Platform target.** Ask "SageMaker or Local?" every time this skill is invoked — never assume a default (per [ADR 0010](/docs/adr/0010-local-anaconda-mlflow-platform-target.md)).
2. **Confirm the model to deploy.**
   - **SageMaker**: the Model Registry model package from a `/evaluate-model` "go" verdict — refuse to proceed if its approval status isn't `Approved`, or ask the user to approve it first.
   - **Local**: the MLflow run from a `/evaluate-model` "go" verdict — refuse to proceed if the run isn't tagged `approved: true`, or ask the user to tag it first. Load the model artifact from that run's artifact URI.
3. **Pick the deployment shape.**
   - **SageMaker**: real-time endpoint (`ModelPackage.deploy()`) for low-latency synchronous inference, Serverless Inference for spiky/low-traffic workloads, or Batch Transform for offline bulk scoring — ask if it's not obvious from how the model will be used, don't default silently to the most expensive option (real-time).
   - **Local**: ask which of the three Local deploy modes — **MLflow Serve** (`mlflow models serve -m <artifact_uri>`, a live local REST endpoint), **Local API** (a generated FastAPI/Flask wrapper around the loaded model, for when the user wants custom request/response handling MLflow Serve doesn't give), or **Export Only** (copy the model artifact plus a standalone inference script, no live server — for batch/offline use). None of these is a SageMaker Endpoint equivalent; say so if the user expects parity.
4. **Generate the deployment code**:
   - **SageMaker**: instance type/count (or serverless memory/concurrency config), endpoint name, and a data capture config if the project wants request/response logging for drift monitoring later.
   - **Local — MLflow Serve**: the `mlflow models serve` command with a chosen local port.
   - **Local — Local API**: the FastAPI/Flask app (a `/predict` route loading the artifact once at startup) and the command to run it.
   - **Local — Export Only**: the export/copy code and the standalone inference script; no server code.
5. **Estimate cost** — dispatch the `cost-estimator` agent regardless of platform (it returns "$0 — runs on your local machine" instantly for Local, no computation needed). For SageMaker, state instance hourly rate × instance count as an ongoing monthly run-rate (a real-time endpoint keeps billing until deleted) — call this out explicitly, since it's a different cost shape than a training job's one-off charge.
6. **Generate a smoke test**: SageMaker — invoke the endpoint with 1-2 known sample inputs and check the response shape/sanity. Local MLflow Serve/Local API — a small script that POSTs the same sample inputs to the local port. Local Export Only — a script that runs the exported inference script directly against the sample inputs (no network call).
7. **Stop and ask for confirmation** — print the code, cost estimate, and smoke test, then explicitly ask "deploy this endpoint?" (SageMaker), or "start this locally?" / "export this now?" (Local, depending on mode) before running anything. If the user says no or doesn't respond, do not run it.
8. **After a confirmed deploy**, remind the user how to tear it down: SageMaker — `predictor.delete_endpoint()`, an endpoint left running is the most common source of surprise AWS bills. Local MLflow Serve/Local API — how to stop the local server process (the port it's bound to). Local Export Only — nothing to tear down.

## Notes

- Local: if the chosen deploy mode needs a dependency not already in the project's `environment.yml` (e.g. `fastapi`/`uvicorn` for a Local API), add it to that single root file rather than creating a separate one.
- SageMaker: never reuse an existing endpoint name for a new model version without asking — prefer a new endpoint + traffic shifting, or an explicit "replace" confirmation, over silently overwriting what's live.
- Local: never bind MLflow Serve/Local API to a port already in use without checking — ask for a different port instead of silently failing or killing whatever's on it.
