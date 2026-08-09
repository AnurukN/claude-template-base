# Extend /label-data beyond image/video to text, audio, and tabular

`/label-data` (ADR 0006) was scoped to image/video labeling only, reviewed via a notebook viewer with an optional vision-model Hybrid Pre-label step. The reasoning behind that design — a single in-house reviewer, no new infrastructure, notebook execution matching `/eda`'s local model — has nothing to do with the data being visual specifically; it applies just as well to text, audio, and tabular datasets that the same DS/MLE personas need labeled before training. We chose to extend the skill's data-type option to cover all five rather than write a separate skill per modality, since the run's shape (data type → task type → mode → Manifest) is identical across modalities; only the item rendering in the notebook viewer and the Pre-label call's input modality change.

Tabular is included even though this template scopes out the Data Analyst persona (ADR 0002) — that exclusion is about SQL/BI/dashboard work, not tabular data in general. Assigning or correcting a target label per row for supervised training is squarely DS/MLE work, the same as image/video labeling already was.

Audio is the one case where we didn't extend the Hybrid Pre-label step at full parity with image/video. Claude models don't have a confirmed, standard native audio-input mode in the Messages/Bedrock API as of this writing, unlike vision input for image/video. Rather than assume a capability that may not exist, `/label-data` requires a transcript to already exist for audio Hybrid Pre-labeling (produced by some ASR step outside this skill), and Pre-labels the transcript text instead of the raw audio. If no transcript exists and no audio-capable model is confirmed, the skill falls back to Human-only mode and says so plainly — the same "say plainly out of scope" pattern already used for bounding boxes/segmentation on image/video.

This should be revisited once a Claude model with confirmed native audio input is available: check current capabilities via the `claude-api` skill rather than trusting this ADR's snapshot, and if confirmed, Hybrid Pre-labeling can call the model directly on raw audio the same way it already does on images.

## Considered Options

- **One skill, five data types** (chosen) — the run shape (data type → task type → mode → Manifest) is identical across modalities; only rendering and Pre-label input differ.
- **A separate skill per modality** — rejected: would duplicate the Manifest format, mode logic, and cost-estimate/confirmation flow five times over for no behavioral difference worth the split.
- **Full parity for audio Hybrid Pre-labeling (assume native audio input works)** — rejected: no confirmed capability to build on; would risk generating a script against an API that doesn't exist. Constrained to transcript-based Pre-labeling instead, with Human-only as the explicit fallback.
