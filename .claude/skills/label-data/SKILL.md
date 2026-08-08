---
name: label-data
description: Labels an image or video dataset — either a hybrid LLM-pre-label-plus-human-review flow, or human-only — and writes a local manifest. Use before /eda when the dataset has no labels yet, or when the user wants to label/relabel a batch of images or video.
---

# Label Data

Runs before `/eda`: raw, unlabeled image/video data in, a local **Manifest** (JSONL) out. See `CONTEXT.md` for the Labeling run / Pre-label / Hybrid mode / Human-only mode / Confidence / Manifest vocabulary this skill uses throughout.

## Steps

1. **Confirm the run's config up front**: data type (image or video — this skill doesn't support other types), task type (classification, multi-label tagging, captioning, or video-level tagging — whole-clip only, no segment/timestamp granularity), and mode (Hybrid or Human-only). If the user asks for bounding boxes or segmentation, say plainly that these are out of scope for this skill (no notebook-native way to draw on an image) rather than attempting a workaround.
2. **Locate the data.** Ask where the images/videos live (S3 prefix or local/notebook path) if not stated. Don't pull a large dataset into memory at once — list/sample first.

### Hybrid mode

3. **Generate the Pre-label batch script.** Per [ADR 0007](/docs/adr/0007-extend-scaffold-and-confirm-to-bedrock-calls.md), this skill never calls the vision model itself — it generates a script that loops over the items, calls a vision-capable Claude model (via Bedrock or the Anthropic API) once per item, and asks for a label plus a Confidence score for the chosen task type. The script writes one JSON record per item.
4. **Estimate cost before printing the script**: per-item token cost (image input + short output) × item count, using current published Claude pricing — reference the `claude-api` skill for up-to-date rates rather than guessing. State the estimate plainly, e.g. "≈ $X for N items at ~$Y/item." This is not a SageMaker cost, so the `cost-estimator` agent doesn't cover it — do this arithmetic directly.
5. **Stop and ask for confirmation** — print the script and the cost estimate, then ask "run this?" before doing anything further. `block_bedrock_submit.py` denies Claude from executing this script directly via Bash, so the human runs it themselves.
6. **Once the human reports the Pre-label output exists**, generate notebook viewer cells (`IPython.display` / `ipywidgets`) that show each item next to its Pre-label and Confidence, sorted lowest-confidence-first, with a control to accept or correct the label.

### Human-only mode

3. **Generate notebook viewer cells directly** — same viewer as Hybrid mode's review step, but with no Pre-label/Confidence shown; the human labels each item from scratch via the task-type-appropriate control (dropdown for classification, checkboxes for multi-label, text box for captioning/video-tagging).

### Both modes

7. **Write the Manifest**: local JSONL, one record per item — path, label, mode, and (Hybrid only) confidence and reviewer. Print the intended S3 destination path for the manifest as an editable suggestion; do not upload it yourself.
8. **Summarize**: item count labeled, mode used, task type, and the manifest's local path — so `/eda` can pick it up next.

## Notes

- This skill is local/notebook-only except for the Hybrid mode's Pre-label script, which is the one billable step — everything else has no AWS or API side effects and needs no confirmation gate.
- Single reviewer per item; there's no multi-annotator consensus logic in this skill.
- Reviewer identity: ask once at the start of a Human-only or review session and stamp it on every record written in that session, rather than asking per item.
