#!/usr/bin/env python
"""PreToolUse guardrail: Claude must never submit a billable SageMaker job/endpoint
directly. Per docs/adr/0001-scaffold-and-confirm-execution-model.md, skills generate
the command and a cost estimate, then the human runs it themselves after confirming.
"""
import json
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


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return

    if payload.get("tool_name") != "Bash":
        return

    command = (payload.get("tool_input") or {}).get("command", "")
    if not command or not SAGEMAKER_HINT.search(command) or not SUBMIT_RE.search(command):
        return

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
