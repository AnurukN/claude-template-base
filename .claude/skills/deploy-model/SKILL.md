---
name: deploy-model
description: Generates a SageMaker Endpoint deployment for an approved model, prints the estimated cost and command, waits for confirmation before deploying, and includes a smoke test. Use after /evaluate-model returns "go", or when asked to deploy/serve a model.
---

# Deploy Model

Generates SageMaker Endpoint deployment code. Per [ADR 0001](/docs/adr/0001-scaffold-and-confirm-execution-model.md), this skill never calls `.deploy()` itself — a live endpoint bills per instance-hour until explicitly deleted, so creation always requires the user's explicit go-ahead.

## Steps

1. **Confirm the model to deploy.** The Model Registry model package from a `/evaluate-model` "go" verdict — refuse to proceed if the model package's approval status isn't `Approved`, or ask the user to approve it first.
2. **Pick the deployment shape.** Real-time endpoint (`ModelPackage.deploy()`) for low-latency synchronous inference, Serverless Inference for spiky/low-traffic workloads, or Batch Transform for offline bulk scoring — ask if it's not obvious from how the model will be used, don't default silently to the most expensive option (real-time).
3. **Generate the deployment code**: instance type/count (or serverless memory/concurrency config), endpoint name, and a data capture config if the project wants request/response logging for drift monitoring later.
4. **Estimate cost**: instance hourly rate × instance count, stated as an ongoing monthly run-rate (a real-time endpoint keeps billing until deleted) — call this out explicitly, since it's a different cost shape than a training job's one-off charge.
5. **Generate a smoke test**: a small script that invokes the endpoint with 1-2 known sample inputs and checks the response shape/sanity, to run right after deployment succeeds.
6. **Stop and ask for confirmation** — print the code, cost estimate, and smoke test, then explicitly ask "deploy this endpoint?" before running anything. If the user says no or doesn't respond, do not deploy.
7. **After a confirmed deploy**, remind the user how to tear it down (`predictor.delete_endpoint()`) — an endpoint left running is the most common source of surprise AWS bills in this workflow.

## Notes

- Never reuse an existing endpoint name for a new model version without asking — prefer a new endpoint + traffic shifting, or an explicit "replace" confirmation, over silently overwriting what's live.
