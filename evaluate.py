#!/usr/bin/env python3
"""
evaluate.py — Autoresearch evaluation harness for DS analysis writing.

Calls two review subagents (substance + communication), collects their
per-dimension scores, computes a weighted composite, and outputs a
deterministic result the autoresearch loop can act on.

USAGE:
    python evaluate.py                    # evaluate analysis.md with defaults
    python evaluate.py --file report.md   # evaluate a different file
    python evaluate.py --runs 3           # average over 3 eval runs (reduces noise)

OUTPUT:
    Prints a structured result block that the writing agent parses.
    Also appends raw scores to eval_log.jsonl for debugging.
"""

import json
import re
import yaml
import argparse
import datetime
import subprocess
import statistics
import tempfile
from pathlib import Path


# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

def load_config(config_path: str = "review_config.yaml") -> dict:
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Validate weights sum to 1.0 (within floating-point tolerance)
    weights = config.get("weights", {})
    total = sum(weights.values())
    if abs(total - 1.0) > 0.01:
        raise ValueError(
            f"Config weights must sum to 1.0, got {total} "
            f"(substance={weights.get('substance')}, communication={weights.get('communication')})"
        )

    return config


# ─────────────────────────────────────────────
# Codex Judge Interface
# ─────────────────────────────────────────────
# Uses Codex CLI for cross-model evaluation (Claude writes, Codex judges).
# Each judge gets a prompt template + the analysis text, returns JSON scores.
# DRY helper: call_codex_judge() handles temp file, timeout, retry, parsing.

# Path to judge prompt templates (relative to project root)
JUDGE_TEMPLATES_DIR = Path(__file__).parent / "skills" / "ds-autoresearch" / "references"


def _parse_judge_json(raw_output: str) -> dict | None:
    """Extract JSON object from Codex output, ignoring surrounding text.

    Codex sometimes wraps JSON in markdown code fences or adds commentary.
    We find the first { and last } and attempt to parse the whole span.
    This handles nested braces (e.g., critique text containing { or }).
    """
    # Try to find JSON in code fences first
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw_output, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Fall back: find first { and last } — handles nested braces in critique text
    start = raw_output.find("{")
    end = raw_output.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(raw_output[start : end + 1])
        except json.JSONDecodeError:
            pass

    return None


def call_codex_judge(
    template_name: str,
    analysis_text: str,
    timeout_seconds: int = 120,
) -> tuple[dict | None, str | None]:
    """Call a Codex judge via CLI with a prompt template.

    Writes the full prompt (template + analysis) to a temp file, then
    runs `codex exec` in read-only mode with a timeout.

    Args:
        template_name: Filename in JUDGE_TEMPLATES_DIR (e.g., "substance-judge.md")
        analysis_text: The analysis text to evaluate
        timeout_seconds: Max seconds to wait for Codex (default 120)

    Returns:
        Tuple of (scores_dict, critique_text).
        scores_dict maps dimension names to float scores (0-10).
        critique_text is the judge's free-text explanation (for saving to critiques/).
        Returns (None, None) if the judge fails after retry.
    """
    template_path = JUDGE_TEMPLATES_DIR / template_name
    if not template_path.exists():
        print(f"  [WARN] Judge template not found: {template_path}")
        return None, None

    # Build the full prompt: template + analysis text
    template_text = template_path.read_text()
    full_prompt = template_text + analysis_text

    # Write to temp directory (cleaned up atomically even on SIGKILL/crash)
    # Codex prompts via temp file, not inline args (eng review #1)
    with tempfile.TemporaryDirectory(prefix="judge-") as tmpdir:
        prompt_file = str(Path(tmpdir) / "prompt.md")
        Path(prompt_file).write_text(full_prompt)
        return _run_codex_with_retry(prompt_file, timeout_seconds)


def _run_codex_with_retry(
    prompt_file: str, timeout_seconds: int
) -> tuple[dict | None, str | None]:
    """Run Codex exec with one retry on malformed output.

    Reads the prompt from the temp file and passes it via stdin to
    `codex exec -s read-only -`. The `-` tells codex to read from stdin.

    Per Codex Failure Policy: retry once on malformed JSON,
    then return None if second attempt also fails.
    """
    prompt_text = Path(prompt_file).read_text()

    for attempt in range(2):
        try:
            result = subprocess.run(
                ["codex", "exec", "-s", "read-only", "-"],
                input=prompt_text,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )

            if result.returncode != 0:
                print(f"  [WARN] Codex returned exit code {result.returncode}")
                if attempt == 0:
                    continue  # retry once
                return None, None

            raw = result.stdout.strip()
            parsed = _parse_judge_json(raw)

            if parsed is None:
                print(f"  [WARN] Failed to parse JSON from Codex (attempt {attempt + 1})")
                if attempt == 0:
                    continue  # retry once
                return None, None

            # Extract critique (free-text) and scores (numeric values)
            critique = parsed.pop("critique", None)
            scores = {k: float(v) for k, v in parsed.items() if isinstance(v, (int, float))}

            if not scores:
                print(f"  [WARN] No numeric scores in Codex output (attempt {attempt + 1})")
                if attempt == 0:
                    continue
                return None, None

            return scores, critique

        except subprocess.TimeoutExpired:
            print(f"  [WARN] Codex timed out after {timeout_seconds}s (attempt {attempt + 1})")
            if attempt == 0:
                continue  # retry once
            return None, None

        except Exception as e:
            print(f"  [WARN] Codex error: {e} (attempt {attempt + 1})")
            if attempt == 0:
                continue
            return None, None

    return None, None



def call_judges_parallel(
    analysis_text: str, config: dict
) -> tuple[dict | None, dict | None, str | None, str | None]:
    """Run both judges in parallel via ThreadPoolExecutor.

    Returns (substance_scores, communication_scores,
             substance_critique, communication_critique).
    Any of these can be None if the corresponding judge failed.
    """
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=2) as executor:
        sub_future = executor.submit(
            call_codex_judge, "substance-judge.md", analysis_text
        )
        comm_future = executor.submit(
            call_codex_judge, "communication-judge.md", analysis_text
        )

        sub_scores, sub_critique = sub_future.result()
        comm_scores, comm_critique = comm_future.result()

    return sub_scores, comm_scores, sub_critique, comm_critique


# ─────────────────────────────────────────────
# Score Aggregation
# ─────────────────────────────────────────────

def compute_composite(
    substance_scores: dict,
    communication_scores: dict,
    config: dict
) -> dict:
    """
    Computes the weighted composite score from both subagents.

    The composite is:
        composite = w_substance * avg(substance_dims) + w_comm * avg(comm_dims)

    Individual dimensions can also have per-dimension weights defined
    in review_config.yaml for fine-grained control.
    """
    weights = config["weights"]
    w_sub = weights["substance"]
    w_comm = weights["communication"]

    # Per-dimension weighting (if configured)
    sub_dim_weights = config.get("substance_dimensions", {})
    comm_dim_weights = config.get("communication_dimensions", {})

    def weighted_avg(scores: dict, dim_weights: dict) -> float:
        if not dim_weights:
            return statistics.mean(scores.values())
        total_weight = sum(dim_weights.get(k, 1.0) for k in scores)
        return sum(
            scores[k] * dim_weights.get(k, 1.0) for k in scores
        ) / total_weight

    sub_avg = weighted_avg(substance_scores, sub_dim_weights)
    comm_avg = weighted_avg(communication_scores, comm_dim_weights)
    composite = w_sub * sub_avg + w_comm * comm_avg

    return {
        "substance_avg": round(sub_avg, 4),
        "communication_avg": round(comm_avg, 4),
        "composite": round(composite, 4),
        "substance_scores": {k: round(v, 2) for k, v in substance_scores.items()},
        "communication_scores": {k: round(v, 2) for k, v in communication_scores.items()},
    }


# ─────────────────────────────────────────────
# Multi-Run Noise Reduction
# ─────────────────────────────────────────────

def evaluate_with_averaging(
    analysis_text: str,
    config: dict,
    num_runs: int = 1
) -> dict:
    """
    Runs evaluation num_runs times and averages to reduce scoring noise.

    This is critical for autoresearch: if the same draft scores 7.2 one
    time and 8.1 the next, the loop makes unreliable keep/revert decisions.
    Averaging over 3 runs significantly reduces this variance.
    """
    all_results = []

    for i in range(num_runs):
        sub_scores, _ = call_codex_judge("substance-judge.md", analysis_text)
        comm_scores, _ = call_codex_judge("communication-judge.md", analysis_text)
        # Skip this run if either judge failed (returned None)
        if sub_scores is None or comm_scores is None:
            print(f"  [WARN] Judge failure on run {i + 1}/{num_runs} — skipping")
            continue
        result = compute_composite(sub_scores, comm_scores, config)
        all_results.append(result)

    if not all_results:
        raise RuntimeError("All evaluation runs failed — no valid scores collected")

    if num_runs == 1:
        return all_results[0]

    # Average across runs
    avg_composite = statistics.mean(r["composite"] for r in all_results)
    avg_sub = statistics.mean(r["substance_avg"] for r in all_results)
    avg_comm = statistics.mean(r["communication_avg"] for r in all_results)
    # Guard on actual successful run count, not requested count —
    # partial judge failures can reduce len(all_results) below num_runs
    score_variance = statistics.stdev(r["composite"] for r in all_results) if len(all_results) > 1 else 0

    # Average per-dimension scores — use keys common to ALL runs
    # (LLM judges can return slightly different keys across runs)
    sub_dims = set.intersection(
        *(set(r["substance_scores"].keys()) for r in all_results)
    )
    comm_dims = set.intersection(
        *(set(r["communication_scores"].keys()) for r in all_results)
    )

    avg_sub_scores = {
        dim: round(statistics.mean(r["substance_scores"][dim] for r in all_results), 2)
        for dim in sorted(sub_dims)
    }
    avg_comm_scores = {
        dim: round(statistics.mean(r["communication_scores"][dim] for r in all_results), 2)
        for dim in sorted(comm_dims)
    }

    return {
        "substance_avg": round(avg_sub, 4),
        "communication_avg": round(avg_comm, 4),
        "composite": round(avg_composite, 4),
        "score_stdev": round(score_variance, 4),
        "num_runs": num_runs,
        "substance_scores": avg_sub_scores,
        "communication_scores": avg_comm_scores,
    }


# ─────────────────────────────────────────────
# Output Formatting
# ─────────────────────────────────────────────

def format_output(result: dict) -> str:
    """
    Formats evaluation output for the writing agent to parse.
    The agent reads the COMPOSITE line to make keep/revert decisions.
    Per-dimension scores guide its next improvement hypothesis.
    """
    lines = []
    lines.append("=" * 50)
    lines.append("EVALUATION RESULT")
    lines.append("=" * 50)
    lines.append(f"COMPOSITE: {result['composite']}")
    lines.append(f"  substance_avg: {result['substance_avg']}")
    lines.append(f"  communication_avg: {result['communication_avg']}")

    if "score_stdev" in result:
        lines.append(f"  score_stdev: {result['score_stdev']} (over {result['num_runs']} runs)")

    lines.append("")
    lines.append("SUBSTANCE DIMENSIONS:")
    for dim, score in result["substance_scores"].items():
        flag = " ← LOWEST" if score == min(result["substance_scores"].values()) else ""
        lines.append(f"  {dim}: {score}{flag}")

    lines.append("")
    lines.append("COMMUNICATION DIMENSIONS:")
    for dim, score in result["communication_scores"].items():
        flag = " ← LOWEST" if score == min(result["communication_scores"].values()) else ""
        lines.append(f"  {dim}: {score}{flag}")

    lines.append("=" * 50)
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Evaluate DS analysis writing")
    parser.add_argument("--file", default="analysis.md", help="Path to analysis file")
    parser.add_argument("--config", default="review_config.yaml", help="Config file")
    parser.add_argument("--runs", type=int, default=1,
                        help="Number of eval runs to average (reduces noise)")
    args = parser.parse_args()

    # Load inputs
    analysis_text = Path(args.file).read_text()
    config = load_config(args.config)

    # Run evaluation
    result = evaluate_with_averaging(analysis_text, config, num_runs=args.runs)

    # Print for the writing agent to read
    print(format_output(result))

    # Append to eval log for debugging
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "file": args.file,
        **result,
    }
    with open("eval_log.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")


if __name__ == "__main__":
    main()
