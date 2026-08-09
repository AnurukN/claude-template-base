# Claude Template — Data/ML Engineering

A reusable `.claude/` configuration for Data Scientist and ML Engineer work on Python + AWS SageMaker. Copy the `.claude/`, `CONTEXT.md`, and `docs/adr/` directories into a new project repo to bring this whole setup with you.

See `CONTEXT.md` for the glossary this template's own docs use (Hook / Skill / Agent / Persona), and `docs/adr/` for the reasoning behind each design decision below.

## Layout

```
.claude/
  skills/     ML-specific skills, one per pipeline stage, plus a general engineering bundle
  agents/     Specialists dispatched for one delegated judgment call
  hooks/      Deterministic guardrails that run on their own
  settings.json
docs/adr/     Architecture decisions, one per file, numbered in order
CONTEXT.md    Glossary for this template's own vocabulary
```

## ML pipeline skills

Each stage of the EDA → training → evaluation → deployment pipeline is its own skill, invoked independently rather than chained — chain them yourself with `/build-pipeline` once the individual stages work:

| Skill | Does |
|---|---|
| `/label-data` | Labels an image/video dataset (LLM pre-label + human review, or human-only), writes a local manifest — run before `/eda` when the data has no labels yet |
| `/eda` | Exploratory analysis on a new dataset, local to the notebook |
| `/feature-engineering` | Turns EDA findings into a SageMaker Processing Job for features |
| `/train-model` | Generates a training/tuning job, prints cost, waits for confirmation |
| `/evaluate-model` | Pulls run metrics, dispatches `model-evaluator` for a go/no-go |
| `/deploy-model` | Generates an endpoint deployment, prints cost, waits for confirmation |
| `/build-pipeline` | Wires the above into one SageMaker Pipeline |

## Agents

| Agent | Does |
|---|---|
| `model-evaluator` | Reads run metrics vs. baseline, renders a go/no-go/inconclusive verdict |
| `cost-estimator` | Computes an estimated USD cost for a job/endpoint config before submission |
| `data-scientist` | Interprets a distribution/correlation/missingness pattern and recommends what to do about it |
| `ml-engineer` | Reviews a job/endpoint config for production-readiness, or triages a failed job/endpoint from its logs |
| `frontend-developer` | Implements/reviews UI code for web app work unrelated to the ML pipeline — see `docs/adr/0005-frontend-developer-agent-outside-persona-scope.md` |
| `backend-developer` | Implements/reviews server-side/API code (validation, auth, data access, security) for the same non-ML web app work |
| `tester` | Writes/reviews automated tests and runs the suite for the same non-ML web app work — not model quality |
| `teamlead` | Read-only coordinator over frontend/backend/tester — task breakdown, cross-cutting consistency, merge-readiness verdicts |
| `git-manager` | Commits, PR descriptions, and conflict resolution with hard safety rules — shared by both the ML and web app codebases |

## Hooks

| Hook | Event | Does |
|---|---|---|
| `block_aws_submit.py` | PreToolUse (Bash) | Denies any Bash call that would submit/mutate a billable SageMaker job or endpoint directly — that's the human's job, not Claude's |
| `block_bedrock_submit.py` | PreToolUse (Bash) | Denies any Bash call that would directly invoke a billable Bedrock/Anthropic vision-model call (e.g. `/label-data`'s Pre-label script) — same reasoning, extended per `docs/adr/0007-extend-scaffold-and-confirm-to-bedrock-calls.md` |
| `session_cost.py` | Stop | Prints an estimated USD cost for the Claude Code session itself, from token usage |
| `announce.py` | Stop, Notification | Speaks a short status ("finish job" / "need approve") aloud via the OS's TTS engine and always emits a visible systemMessage, so the alert shows even without audio |

## Execution model

Skills that touch AWS, or that call a billable LLM API directly (Bedrock/Anthropic), never submit anything themselves. They generate the code/config, print the exact command plus an estimated cost, and wait for explicit confirmation before the human runs it. `block_aws_submit.py` and `block_bedrock_submit.py` enforce the "Claude doesn't run it" half of that deterministically — see `docs/adr/0001-scaffold-and-confirm-execution-model.md` and `docs/adr/0007-extend-scaffold-and-confirm-to-bedrock-calls.md`. Both hooks check the literal Bash command *and* the contents of any `.py`/`.ipynb` file that command executes, so wrapping a submit/invoke call inside a generated script doesn't bypass the guardrail.

All hooks in `.claude/settings.json` run as `"shell": "bash"` — on Windows this means Claude Code's bundled Git Bash (or WSL) must be available for them to fire at all.

## General engineering skills bundle

Alongside the ML-specific skills, `.claude/skills/` also carries a general-purpose engineering bundle (`tdd`, `code-review`, `diagnosing-bugs`, `triage`, `domain-modeling`, and others) for the ordinary software engineering that DS/MLE work still involves. Run `/setup-matt-pocock-skills` once per new repo to configure its issue tracker and triage-label conventions — see `docs/adr/0004-keep-general-engineering-skills-bundle.md`.

### Workflow skills (manual-invoke only)

The bundle also includes a set of `/command`-only skills for planning and handoff work — each sets `disable-model-invocation: true`, so Claude never reaches for them on its own; you invoke them by name. If you're not sure which one fits, run `/ask-matt` — it's a router over all of them.

| Skill | Does |
|---|---|
| `/ask-matt` | Router — asks which skill/flow fits your situation |
| `/wayfinder` | Plans work too big for one session as a map of decision tickets on the issue tracker |
| `/to-spec` | Turns the current conversation into a spec, published to the issue tracker |
| `/to-tickets` | Breaks a plan/spec/conversation into tracer-bullet tickets with blocking edges |
| `/to-questionnaire` | Turns a decision you can't answer alone into a questionnaire for someone who can |
| `/implement` | Implements a spec/ticket, using `/tdd` at agreed seams, then `/code-review` |
| `/handoff` | Compacts the current conversation into a handoff doc for another agent |
| `/teach` | Stateful, multi-session teaching workspace for learning a topic |
| `/grill-me` / `/grill-with-docs` | Relentless interview to sharpen a plan or design (the latter also writes ADRs/glossary as it goes) |
| `/improve-codebase-architecture` | Scans for deepening opportunities, presents an HTML report, then grills through whichever one you pick |
| `/wait-what` | Re-pitch the last message in plain terms, using this repo's `CONTEXT.md` vocabulary |

## Scope

Phase 1 targets Data Scientist and ML Engineer personas only; Data Analyst (SQL/BI/dashboard) work is explicitly out of scope for now — see `docs/adr/0002-phase-1-persona-scope.md`. Model/experiment tracking uses native SageMaker Model Registry + Experiments rather than MLflow — see `docs/adr/0003-native-sagemaker-tracking.md`.

`.claude/settings.json` also enables Claude Code's experimental Agent Teams feature (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, `teammateMode: "auto"`) by default for every repo that copies this template. This is a provisional experiment, not a settled decision tied to a specific workflow here — see `docs/adr/0008-experimental-agent-teams-default.md`.

## Using this in a new project

1. Copy `.claude/`, `CONTEXT.md`, and `docs/adr/` into the new repo.
2. Run `/setup-matt-pocock-skills` once to configure the general engineering bundle for that repo.
3. Start with `/eda` on the new dataset.

