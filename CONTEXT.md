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
