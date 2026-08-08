# Notebook-based labeling tool over SageMaker Ground Truth or a custom app

`/label-data` needed a way to get image/video labels from a small internal team, with an LLM pre-labeling pass reviewed by a human. The natural AWS-native option was SageMaker Ground Truth, which already provides a managed labeling workforce and UI — consistent with this template's existing preference for native SageMaker tooling (see [ADR 0003](/docs/adr/0003-native-sagemaker-tracking.md)). We chose not to use it, and also chose not to build a standalone labeling web app, in favor of a notebook-based viewer (`IPython.display`/`ipywidgets`) that runs the same way `/eda` does: local, no AWS side effects, no confirmation gate.

Ground Truth's workforce/job infrastructure is built for external or large internal workforces and adds setup overhead (private work teams, UI templates, job management) this use case doesn't need — the actual reviewer is one person on the team, not a managed workforce. A custom web app was rejected for the same reason building it would be disproportionate: it would pull in the frontend/backend-developer agent track that this template currently reserves for work *unrelated* to the ML pipeline (see [ADR 0005](/docs/adr/0005-frontend-developer-agent-outside-persona-scope.md)), whereas labeling directly feeds it. A plain notebook viewer gets a human review loop working with no new infrastructure, at the cost of not scaling past a solo/small-team reviewer — if that changes, Ground Truth is the natural next step, not a rewrite of `/label-data`'s Manifest format.

## Considered Options

- **SageMaker Ground Truth** — rejected: workforce/job setup overhead not justified for a single in-house reviewer.
- **Custom labeling web app** — rejected: pulls in frontend/backend app-building work this template deliberately keeps out of the DS/MLE pipeline's scope.
- **Notebook-based viewer** (chosen) — matches `/eda`'s existing local execution model; revisit if/when an external or larger workforce is needed.
