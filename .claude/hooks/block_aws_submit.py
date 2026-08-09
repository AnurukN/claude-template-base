#!/usr/bin/env python
"""PreToolUse guardrail: Claude must never submit a billable SageMaker job/endpoint
directly. Per docs/adr/0001-scaffold-and-confirm-execution-model.md, skills generate
the command and a cost estimate, then the human runs it themselves after confirming.

Checks two things: the literal Bash command text, and — since a submit call just as
often lives in a generated .py/.ipynb file that the command merely executes (e.g.
`python train_submit.py`) — the contents of any script file the command runs.
"""
import json
import os
import re
import sys

SAGEMAKER_HINT = re.compile(r"sagemaker", re.IGNORECASE)

SUBMIT_PATTERNS = [
    r"create-training-job",
    r"create-processing-job",
    r"create-hyper-parameter-tuning-job",
    r"create-transform-job",
    r"create-auto-ml-job",
    r"create-endpoint(?!-config)",
    r"update-endpoint(?!-config)",
    r"create-notebook-instance",
    r"\.create_training_job\s*\(",
    r"\.create_processing_job\s*\(",
    r"\.create_hyper_parameter_tuning_job\s*\(",
    r"\.create_transform_job\s*\(",
    r"\.create_auto_ml_job",
    r"\.fit\s*\(",
    r"\.deploy\s*\(",
]
SUBMIT_RE = re.compile("|".join(SUBMIT_PATTERNS), re.IGNORECASE)

INTERPRETER_HINT = re.compile(r"\b(?:python3?|ipython|jupyter|papermill)\b", re.IGNORECASE)
SCRIPT_PATH_RE = re.compile(r"[^\s'\"]+\.(?:py|ipynb)\b")


def command_is_submit(command):
    return bool(SAGEMAKER_HINT.search(command) and SUBMIT_RE.search(command))


def resolve_path(path):
    candidates = [path]
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        candidates.append(os.path.join(project_dir, path))
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def is_template_infra(path):
    """Skip this template's own .claude/ tree: hooks/skills/agents legitimately mention
    these API call patterns as regex literals or instructions, not as a real submit call."""
    parts = os.path.normpath(os.path.abspath(path)).split(os.sep)
    return ".claude" in parts


def executed_script_with_submit(command):
    """If `command` runs a .py/.ipynb file that itself contains a submit call, return
    that file's path. Best-effort: only catches scripts resolvable from cwd or
    CLAUDE_PROJECT_DIR, and only a plain substring/regex match of the file's contents."""
    if not INTERPRETER_HINT.search(command):
        return None
    for path in SCRIPT_PATH_RE.findall(command):
        resolved = resolve_path(path)
        if not resolved or is_template_infra(resolved):
            continue
        try:
            with open(resolved, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError:
            continue
        if command_is_submit(content):
            return resolved
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return

    if payload.get("tool_name") != "Bash":
        return

    command = (payload.get("tool_input") or {}).get("command", "")
    if not command:
        return

    culprit_file = None
    if not command_is_submit(command):
        culprit_file = executed_script_with_submit(command)
        if not culprit_file:
            return

    if culprit_file:
        reason = (
            "This command runs %s, which itself looks like it submits or mutates a "
            "billable SageMaker resource (training/processing/tuning/transform job, or "
            "endpoint). Per this template's execution model "
            "(docs/adr/0001-scaffold-and-confirm-execution-model.md), Claude generates "
            "the command/script and an estimated cost and waits for the human to run it "
            "themselves after confirming — it does not execute it directly, including "
            "indirectly via a script. Print the command and cost estimate instead and "
            "wait for explicit go-ahead." % culprit_file
        )
    else:
        reason = (
            "This command looks like it submits or mutates a billable SageMaker resource "
            "(training/processing/tuning/transform job, or endpoint). Per this template's "
            "execution model (docs/adr/0001-scaffold-and-confirm-execution-model.md), Claude "
            "generates the command and an estimated cost and waits for the human to run it "
            "themselves after confirming — it does not execute it directly. Print the command "
            "and cost estimate instead and wait for explicit go-ahead."
        )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


if __name__ == "__main__":
    main()
