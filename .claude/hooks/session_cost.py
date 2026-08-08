#!/usr/bin/env python
import json
import os
import sys
import tempfile
from datetime import date

# USD per 1M tokens. intro_until: use intro_input/intro_output while date.today() <= that date.
PRICING = {
    "claude-fable-5":   {"input": 10.00, "output": 50.00},
    "claude-opus-5":    {"input": 5.00,  "output": 25.00},
    "claude-sonnet-5":  {"input": 3.00,  "output": 15.00,
                         "intro_input": 2.00, "intro_output": 10.00, "intro_until": "2026-08-31"},
    "claude-haiku-4-5": {"input": 1.00,  "output": 5.00},
    "claude-opus-4-8":  {"input": 5.00,  "output": 25.00},
    "claude-opus-4-7":  {"input": 5.00,  "output": 25.00},
    "claude-opus-4-6":  {"input": 5.00,  "output": 25.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
}
CACHE_WRITE_5M_MULT = 1.25
CACHE_WRITE_1H_MULT = 2.0
CACHE_READ_MULT = 0.1

MODEL_NAMES = {
    "claude-fable-5":    "Fable 5",
    "claude-opus-5":     "Opus 5",
    "claude-sonnet-5":   "Sonnet 5",
    "claude-haiku-4-5":  "Haiku 4.5",
    "claude-opus-4-8":   "Opus 4.8",
    "claude-opus-4-7":   "Opus 4.7",
    "claude-opus-4-6":   "Opus 4.6",
    "claude-sonnet-4-6": "Sonnet 4.6",
}


def display_name(model):
    if not model:
        return None
    match = None
    for prefix, name in MODEL_NAMES.items():
        if model.startswith(prefix):
            if match is None or len(prefix) > len(match[0]):
                match = (prefix, name)
    return match[1] if match else model


def rates_for(model):
    if not model:
        return None
    match = None
    for prefix, rates in PRICING.items():
        if model.startswith(prefix):
            if match is None or len(prefix) > len(match[0]):
                match = (prefix, rates)
    if not match:
        return None
    rates = match[1]
    input_rate, output_rate = rates["input"], rates["output"]
    until = rates.get("intro_until")
    if until and date.today().isoformat() <= until:
        input_rate = rates.get("intro_input", input_rate)
        output_rate = rates.get("intro_output", output_rate)
    return input_rate, output_rate


def session_cost(transcript_path):
    by_id = {}
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if entry.get("type") != "assistant":
                    continue
                msg = entry.get("message") or {}
                usage = msg.get("usage")
                mid = msg.get("id")
                if not usage or not mid:
                    continue
                by_id[mid] = (msg.get("model"), usage)
    except OSError:
        return 0.0, 0.0, {}, None

    total = 0.0
    priced_tokens = 0
    unpriced_models = set()
    last_model = None

    for model, usage in by_id.values():
        last_model = model or last_model
        rates = rates_for(model)
        if rates is None:
            unpriced_models.add(model or "unknown")
            continue
        input_rate, output_rate = rates

        input_tokens = usage.get("input_tokens", 0) or 0
        output_tokens = usage.get("output_tokens", 0) or 0
        cache_read = usage.get("cache_read_input_tokens", 0) or 0

        creation = usage.get("cache_creation") or {}
        write_5m = creation.get("ephemeral_5m_input_tokens")
        write_1h = creation.get("ephemeral_1h_input_tokens")
        if write_5m is None and write_1h is None:
            write_5m = usage.get("cache_creation_input_tokens", 0) or 0
            write_1h = 0
        write_5m = write_5m or 0
        write_1h = write_1h or 0

        total += input_tokens / 1_000_000 * input_rate
        total += output_tokens / 1_000_000 * output_rate
        total += write_5m / 1_000_000 * input_rate * CACHE_WRITE_5M_MULT
        total += write_1h / 1_000_000 * input_rate * CACHE_WRITE_1H_MULT
        total += cache_read / 1_000_000 * input_rate * CACHE_READ_MULT

        priced_tokens += input_tokens + output_tokens + write_5m + write_1h + cache_read

    return total, priced_tokens, unpriced_models, last_model


def state_path(session_id):
    return os.path.join(tempfile.gettempdir(), "claude_cost_state_%s.json" % session_id)


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return

    transcript_path = payload.get("transcript_path")
    session_id = payload.get("session_id") or "unknown"
    if not transcript_path or not os.path.isfile(transcript_path):
        return

    total, _tokens, unpriced, last_model = session_cost(transcript_path)

    sp = state_path(session_id)
    previous = 0.0
    try:
        with open(sp, encoding="utf-8") as f:
            previous = json.load(f).get("total", 0.0)
    except (OSError, ValueError):
        pass

    delta = max(total - previous, 0.0)

    try:
        with open(sp, "w", encoding="utf-8") as f:
            json.dump({"total": total}, f)
    except OSError:
        pass

    model_label = display_name(last_model)
    msg = "\U0001F4B0 Task: $%.4f | Session total: $%.4f" % (delta, total)
    if model_label:
        msg += "  | Model: %s" % model_label
    if unpriced:
        msg += "  (unpriced model(s): %s)" % ", ".join(sorted(unpriced))

    print(json.dumps({"systemMessage": msg}))


if __name__ == "__main__":
    main()
