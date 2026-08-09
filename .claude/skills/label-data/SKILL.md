---
name: label-data
description: Labels an image, video, text, audio, or tabular dataset — either a hybrid LLM-pre-label-plus-human-review flow, or human-only — and writes a local manifest. Use before /eda when the dataset has no labels yet, or when the user wants to label/relabel a batch of items of any of these types.
---

# Label Data

Runs before `/eda`: raw, unlabeled data in, a local **Manifest** (JSONL) out. Supports five data types — image, video, text, audio, tabular. See `CONTEXT.md` for the Labeling run / Pre-label / Hybrid mode / Human-only mode / Confidence / Manifest vocabulary this skill uses throughout.

## Steps

1. **Confirm the run's config up front**: data type, task type, and mode (Hybrid or Human-only). Task type depends on data type:
   - **image / video**: classification, multi-label tagging, captioning, or video-level tagging (whole-clip only, no segment/timestamp granularity). If the user asks for bounding boxes or segmentation, say plainly that these are out of scope for this skill (no notebook-native way to draw on an image) rather than attempting a workaround.
   - **text**: classification, multi-label tagging, or free-text annotation (e.g. summarization/correction). There's no inline span/entity highlighter — say so plainly if asked; a human can still type offsets into a text box, but nothing draws on the text.
   - **audio**: classification, multi-label tagging, or transcription-correction — audio-level only, same whole-clip restriction as video (no timestamp segment granularity).
   - **tabular**: classification or multi-label tagging of a row against the existing column set. There's no free-text/captioning task for tabular (no natural "caption" for a row) — say so plainly if asked.
2. **Locate the data.**
   - image/video/audio: Ask where the files live (S3 prefix or local/notebook path) if not stated. Don't pull a large dataset into memory at once — list/sample first.
   - text: Ask whether items are one file each, or rows in a single file (CSV/JSONL/Parquet) — most text datasets are the latter.
   - tabular: Always rows in a single tabular file/table — load it (or a sample, if large) as a dataframe up front, not per item.

### Hybrid mode

3. **Generate the Pre-label batch script.** Per [ADR 0007](/docs/adr/0007-extend-scaffold-and-confirm-to-bedrock-calls.md), this skill never calls the model itself — it generates a script that loops over the items, calls a Claude model capable of the item's modality (via Bedrock or the Anthropic API) once per item, and asks for a label plus a Confidence score for the chosen task type.
   - image/video: vision-capable model call, one item (image, or a sampled frame/clip reference) per call.
   - text/tabular: plain text-capable model call — send the text, or the row serialized as JSON, as the prompt.
   - audio: **check current model capabilities before assuming this works** — Claude models don't have a confirmed, standard native audio-input mode as of this template's writing (reference the `claude-api` skill rather than trusting this doc). Unless you've confirmed the model/provider in use accepts raw audio, Hybrid Pre-labeling requires a transcript to already exist (from an ASR step outside this skill) so the Pre-label call runs as a text-capable call over the transcript. If no transcript exists and no audio-capable model is confirmed, say so plainly and fall back to Human-only mode for that run rather than guessing at an API that may not exist. See [ADR 0009](/docs/adr/0009-extend-label-data-to-text-audio-tabular.md).
   The script writes one JSON record per item either way.
4. **Estimate cost before printing the script**: per-item token cost (input + short output — image/transcript input costs more than plain short text) × item count, using current published Claude pricing — reference the `claude-api` skill for up-to-date rates rather than guessing. State the estimate plainly, e.g. "≈ $X for N items at ~$Y/item." This is not a SageMaker cost, so the `cost-estimator` agent doesn't cover it — do this arithmetic directly.
5. **Stop and ask for confirmation** — print the script and the cost estimate, then ask "run this?" before doing anything further. `block_bedrock_submit.py` denies Claude from executing this script directly via Bash, so the human runs it themselves.
6. **Once the human reports the Pre-label output exists**, generate notebook viewer cells (`IPython.display` / `ipywidgets`) that show each item next to its Pre-label and Confidence, sorted lowest-confidence-first, with a control to accept or correct the label. Item rendering is data-type-specific: inline image, inline video player, printed text (truncate/expand long text rather than dumping it all), inline `IPython.display.Audio` player, or the row rendered as a small table (`display(df.loc[[i]])`) for tabular.

### Human-only mode

3. **Generate notebook viewer cells directly** — same data-type-specific rendering as Hybrid mode's review step, but with no Pre-label/Confidence shown; the human labels each item from scratch via the task-type-appropriate control (dropdown for classification, checkboxes for multi-label, text box for captioning/transcription/free-text annotation).

### Both modes

7. **Write the Manifest**: local JSONL, one record per item — an item reference, label, mode, and (Hybrid only) confidence and reviewer. Keep the reference field named `path` for consistency across data types, but treat it as "however this item is addressed" rather than literally a filesystem path — a file path for image/video/audio, a row index/ID (plus source file) for text-as-rows or tabular. Print the intended S3 destination path for the manifest as an editable suggestion; do not upload it yourself.
8. **Summarize**: item count labeled, data type, mode used, task type, and the manifest's local path — so `/eda` can pick it up next.

## Notes

- This skill is local/notebook-only except for the Hybrid mode's Pre-label script, which is the one billable step — everything else has no AWS or API side effects and needs no confirmation gate.
- Single reviewer per item; there's no multi-annotator consensus logic in this skill.
- Reviewer identity: ask once at the start of a Human-only or review session and stamp it on every record written in that session, rather than asking per item.
- Tabular labeling here means assigning/correcting a target label per row for supervised ML — it's DS/MLE work feeding `/eda`/`/feature-engineering`, not the BI/dashboard-style analysis this template's Data Analyst persona scope excludes (see [ADR 0002](/docs/adr/0002-phase-1-persona-scope.md)).
- Audio Hybrid Pre-labeling depends on a transcript today, not a confirmed native audio-input model call — see [ADR 0009](/docs/adr/0009-extend-label-data-to-text-audio-tabular.md) and re-check current capabilities via the `claude-api` skill before assuming otherwise.
