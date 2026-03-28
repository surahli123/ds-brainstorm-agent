# Novita AI Writer Provider for DS AutoResearch Loop

**Date:** 2026-03-27
**Status:** Approved
**Scope:** `loop_runner.py` only — ~40-50 lines of new code

## Problem

The autoresearch loop's writer fails because `claude -p` returns "Credit balance is too low." Feedback-forward is already implemented (lines 706-719) but has never been tested because the writer never runs. We need a working writer provider.

## Solution

Add a `novita` writer provider that uses Novita AI's OpenAI-compatible API. Supports three models via `--model` flag:

| Model | ID | Default? |
|-------|----|----------|
| DeepSeek V3.2 | `deepseek/deepseek-v3.2` | Yes |
| MiniMax M2.7 | `minimax/minimax-m2.7` | No |
| GLM-4.7-Flash | `zai-org/glm-4.7-flash` | No |

## Changes

### 1. New function: `call_writer_novita()` (in `loop_runner.py`, after `call_writer_anthropic`)

- Uses `openai` Python package with `base_url="https://api.novita.ai/openai"`
- Reads `NOVITA_API_KEY` from environment
- Calls `chat.completions.create()` with system prompt + user message
- Returns `response.choices[0].message.content` or `None` on failure
- Matches existing writer function signature

### 2. CLI changes (in `loop_runner.py` argparse)

- Add `"novita"` to `--provider` choices
- In `run_loop()`, wire up: `args.provider == "novita"` → `call_writer_novita` with `partial(model=...)`
- Default model when provider is novita: `deepseek/deepseek-v3.2`

### 3. Dependency validation

- If `--provider novita`: check `NOVITA_API_KEY` is set, check `openai` package importable
- Add `openai` to error message if missing

## What's NOT changing

- `program.md` — writer prompt already handles judge feedback (rule #6)
- `evaluate.py` — judges use Codex CLI, independent of writer
- `review_config.yaml` — scoring unchanged
- Feedback-forward wiring (lines 706-719) — already built, untouched

## Usage

```bash
# Default (DeepSeek V3.2)
python3 loop_runner.py --input analysis.md --cycles 5 --provider novita

# MiniMax M2.7
python3 loop_runner.py --input analysis.md --cycles 5 --provider novita --model minimax/minimax-m2.7

# GLM-4.7-Flash (cheapest)
python3 loop_runner.py --input analysis.md --cycles 5 --provider novita --model zai-org/glm-4.7-flash
```

## Success Criteria

1. `python3 loop_runner.py --input ebay_marketing_analysis.md --cycles 5 --provider novita` completes without writer failures
2. Judge feedback appears in writer prompts (feedback-forward verified)
3. At least 1 cycle produces a "keep" action (score improvement)
