# Enable experimental Agent Teams by default (provisional)

`.claude/settings.json` sets `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` and `teammateMode: "auto"`, turning on Claude Code's experimental Agent Teams feature for every repo that copies this template, rather than leaving it opt-in per project.

This is unlike every other decision in this ADR log: it isn't driven by a concrete workflow need in the DS/MLE pipeline or the web app agent track. It's here because the maintainer wants to try the feature out, full stop — there is no specific skill or agent in this template that currently depends on it, and no evidence yet on whether always-on teammate mode helps or gets in the way of the scaffold-and-confirm flows the rest of this template relies on (`0001`, `0007`).

We chose to enable it at the template level anyway, instead of only in this one repo's local settings, so the experiment plays out wherever the template is copied and surfaces feedback sooner. The trade-off: it rides on an explicitly experimental Claude Code flag, which can change behavior or disappear across Claude Code versions with no deprecation guarantee, and every new repo copying this template inherits that instability by default with no specific justification tied to its own workflow.

This entry should be revisited once there's an actual verdict: either promote it to a real decision (name the workflow it helps, the way `0005`–`0007` name theirs) once one exists, or revert to opt-in — e.g. move it to `.claude/settings.local.json` — if the experiment doesn't pan out.
