# Claude Template — Data/ML Engineering Config

A reusable `.claude/` template (hooks, agents, skills) tailored for data scientist and ML engineer workflows on Python + AWS SageMaker, meant to be copied into new project repos.

## Language

**Hook**:
Deterministic automation that Claude Code runs on its own at a lifecycle event (e.g. Stop, PreToolUse), without the user invoking it. Used for guardrails — things that must always happen, no judgment call involved.
_Avoid_: Automation, check, validator (when referring to the mechanism itself, not its purpose)

**Skill**:
A user-invoked procedure (`/command`) that carries out one stage of work end to end. Each stage of the ML workflow (EDA, training, evaluation, deployment) is its own skill, invoked independently rather than chained.
_Avoid_: Workflow, command, script

**Agent**:
A specialist sub-process dispatched to perform one delegated subtask and report back — used when a task needs focused judgment (e.g. interpreting metrics) separate from the main conversation.
_Avoid_: Subagent task, bot, assistant (when referring to the mechanism itself)

**Persona**:
The target role a skill/agent/hook is designed for in this template. Scope for this template is **Data Scientist** and **ML Engineer**; Data Analyst (SQL/BI/dashboard-focused) is explicitly out of scope for now.
_Avoid_: Role, user type

### Data labeling

**Labeling run**:
One invocation of the labeling skill over a dataset, configured upfront with a data type (image, video, text, audio, or tabular), a task type (classification, multi-label tagging, captioning/free-text annotation, or video/audio-level tagging), and a mode (Hybrid or Human-only).
_Avoid_: Labeling job (reserve "job" for actual SageMaker jobs elsewhere in this template)

**Pre-label**:
A label suggestion for one item, produced by a generated batch script that calls a Claude model capable of the item's modality — vision-capable for image/video, text-capable for text/tabular, and for audio a text-capable call over an existing transcript (see [ADR 0009](/docs/adr/0009-extend-label-data-to-text-audio-tabular.md)). Never final — always subject to human review in Hybrid mode. This is a generated script/job, not this template's **Agent** — no Claude Code sub-process is dispatched to produce it.
_Avoid_: Auto-label, AI label, labeling agent

**Hybrid mode**:
A labeling run mode where every item receives a Pre-label first, which a human then reviews and corrects via the notebook viewer.

**Human-only mode**:
A labeling run mode where every item is labeled directly by a human via the notebook viewer, with no Pre-label step.

**Confidence**:
A per-item score attached by the Pre-label step in Hybrid mode, used to prioritize which items a human reviews first.

**Manifest**:
The local JSONL file a labeling run produces — one record per item, holding an item reference (file path for image/video/audio, row index/ID for text-as-rows/tabular), label, mode, and (in Hybrid mode) confidence and reviewer.
_Avoid_: Output file, labels file
