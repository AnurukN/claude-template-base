#!/usr/bin/env python
"""PreToolUse guardrail: Claude must never directly invoke a billable vision-model
call (Bedrock or the Anthropic API) itself. Per docs/adr/0007-extend-scaffold-and-
confirm-to-bedrock-calls.md, this extends the same rule block_aws_submit.py enforces
for SageMaker jobs to /label-data's Pre-label batch script: Claude generates the
script and a cost estimate, then the human runs it themselves after confirming.
"""
import json
import re
import sys

HINT = re.compile(r"bedrock|anthropic", re.IGNORECASE)

SUBMIT_PATTERNS = [
    r"invoke_model(_with_response_stream)?\s*\(",
    r"invoke-model",
    r"\.messages\.create\s*\(",
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
    if not command or not HINT.search(command) or not SUBMIT_RE.search(command):
        return

    reason = (
        "This command looks like it directly invokes a billable vision-model call "
        "(Bedrock or the Anthropic API) — e.g. a /label-data Pre-label batch script. "
        "Per this template's execution model (docs/adr/0007-extend-scaffold-and-"
        "confirm-to-bedrock-calls.md), Claude generates the script and a cost estimate "
        "and waits for the human to run it themselves after confirming — it does not "
        "execute it directly. Print the script and cost estimate instead and wait for "
        "explicit go-ahead."
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
