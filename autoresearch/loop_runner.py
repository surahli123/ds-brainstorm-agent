#!/usr/bin/env python3
"""
loop_runner.py — DS AutoResearch orchestrator.

Runs an edit→evaluate→keep/revert loop on a DS analysis document.
Claude Code (or Anthropic API) writes improvements, Codex judges score them.
Git-based state management in an isolated temp directory.

USAGE:
    python3 loop_runner.py --input analysis.md --cycles 10
    python3 loop_runner.py --input analysis.md --cycles 5 --provider anthropic
    python3 loop_runner.py --input analysis.md --cycles 10 --keep-workdir

See skills/ds-autoresearch/SKILL.md for full documentation.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# evaluate.py is imported as a module, not called as subprocess (eng review #2)
import evaluate


# ─────────────────────────────────────────────
# Phase Detection (percentage-based)
# ─────────────────────────────────────────────

def get_phase(cycle: int, total_cycles: int) -> str:
    """Map cycle number to writing phase.

    First 40% of cycles → structural improvements
    Middle 40% → substance refinement
    Final 20% → communication polish

    Uses 1-based cycle numbering (cycle 1 is the first cycle).
    """
    if total_cycles <= 0:
        return "structural"

    # Calculate progress as fraction (0.0 to ~1.0)
    # Use (cycle-1)/total so cycle 1 always starts at 0.0 (structural)
    progress = (cycle - 1) / total_cycles

    if progress < 0.4:
        return "structural"
    elif progress < 0.8:
        return "substance"
    else:
        return "polish"


# ─────────────────────────────────────────────
# Writer Output Validation
# ─────────────────────────────────────────────

def validate_writer_output(text: str, original: str) -> bool:
    """Check that writer output is valid (not a refusal or truncation).

    Checks:
    1. Contains at least one markdown header (#)
    2. Is at least 20% of original length
    3. Doesn't start with refusal patterns ("I can't", "I'm sorry", "As an AI")

    Returns True if output passes all checks.
    """
    if not text or not text.strip():
        return False

    stripped = text.strip()
    original_stripped = original.strip()

    if stripped == original_stripped:
        return False

    # Check for refusal patterns (case-insensitive)
    refusal_patterns = [
        r"^I can'?t",
        r"^I'?m sorry",
        r"^As an AI",
        r"^I apologize",
        r"^Unfortunately,? I",
        r"^I'?m unable",
    ]
    for pattern in refusal_patterns:
        if re.match(pattern, stripped, re.IGNORECASE):
            return False

    # Must contain at least one markdown header
    if not re.search(r"^#+\s", stripped, re.MULTILINE):
        return False

    # Must be at least 20% of original length
    if len(stripped) < len(original) * 0.2:
        return False

    return True


# ─────────────────────────────────────────────
# Top Dimension Detection (for regression blocking)
# ─────────────────────────────────────────────

def get_top_dimensions(config: dict) -> set:
    """Identify dimensions with weight >= 1.2 (high-priority).

    These dimensions trigger regression blocking: even if the composite
    improves, a drop > 0.5 on a top dimension causes a revert.
    """
    top = set()
    for section_key in ("substance_dimensions", "communication_dimensions"):
        dims = config.get(section_key, {})
        for dim_name, weight in dims.items():
            if weight >= 1.2:
                top.add(dim_name)
    return top


# ─────────────────────────────────────────────
# Decision Logic
# ─────────────────────────────────────────────

def _check_top_dimension_regression(
    prev_scores: dict, new_scores: dict, config: dict
) -> bool:
    """Check if any top-weight dimension dropped > 0.5.

    Returns True if there IS a regression (should revert).
    """
    top_dims = get_top_dimensions(config)

    # Merge substance + communication scores for both prev and new
    prev_all = {**prev_scores.get("substance_scores", {}),
                **prev_scores.get("communication_scores", {})}
    new_all = {**new_scores.get("substance_scores", {}),
               **new_scores.get("communication_scores", {})}

    for dim in top_dims:
        prev_val = prev_all.get(dim)
        new_val = new_all.get(dim)
        if prev_val is not None and new_val is not None:
            drop = prev_val - new_val
            if drop > 0.5:
                return True  # regression detected
    return False


def decide_action(prev_scores: dict, new_scores: dict, config: dict) -> str:
    """Decide whether to keep, revert, or ask human about this edit.

    Decision rules (from plan):
    - Composite improved >= 1.0 AND no top-dim regression → auto-KEEP
    - Composite improved 0.3-1.0 AND no top-dim regression → HUMAN_GATE
    - Composite improved >= 0.3 but top-dim regressed → REVERT
    - Composite improved < 0.3 → REVERT
    - Composite dropped → REVERT

    Returns: "keep", "revert", or "human_gate"
    """
    threshold = config.get("thresholds", {}).get("min_improvement", 0.3)
    improvement = new_scores["composite"] - prev_scores["composite"]

    # Check for top-dimension regression
    has_regression = _check_top_dimension_regression(prev_scores, new_scores, config)

    if improvement < threshold:
        # Below minimum threshold — revert (includes score drops)
        return "revert"

    if has_regression:
        # Composite improved but a top dimension regressed — revert
        return "revert"

    if improvement >= 1.0:
        # Large, clear improvement — auto-keep
        return "keep"

    # Marginal improvement (0.3 to 1.0) — ask human
    return "human_gate"



# ─────────────────────────────────────────────
# Stop Rules
# ─────────────────────────────────────────────

def should_halt(history: list[dict], config: dict) -> bool:
    """Check if N consecutive non-improving cycles have occurred.

    N is configured via thresholds.max_consecutive_reverts (default 3).
    Non-improving = action is "revert" or "skip".
    A "keep" or "human_gate" breaks the streak.
    """
    max_reverts = config.get("thresholds", {}).get("max_consecutive_reverts", 3)
    # Use 3 as the effective minimum to avoid halting too eagerly
    n = max(max_reverts, 3)

    if len(history) < n:
        return False

    # Check last N entries
    last_n = history[-n:]
    return all(
        entry.get("action") in ("revert", "skip")
        for entry in last_n
    )


def should_halt_judge_failures(history: list[dict]) -> bool:
    """Check if 3 consecutive cycles had judge failures.

    Per Codex Failure Policy: 3 consecutive cycles with at least one
    judge failure → HALT with status "judge_failure".
    """
    if len(history) < 3:
        return False

    last_three = history[-3:]
    return all(
        entry.get("judge_failure", False)
        for entry in last_three
    )


def budget_exceeded(current_cycle: int, max_total: int) -> bool:
    """Check if total cycle count (including skips) hit the hard cap."""
    return current_cycle >= max_total


def _average_results(
    first_result: dict,
    analysis_text: str,
    config: dict,
    num_runs: int,
) -> dict:
    """Run N-1 additional evaluations and average with first_result.

    Reuses first_result (already computed from call_judges_parallel)
    so we only make N-1 additional judge calls, not N.

    Returns the averaged result dict with score_stdev.
    Falls back to first_result if all additional runs fail.
    """
    if num_runs <= 1:
        return first_result

    additional_results = [first_result]
    for i in range(num_runs - 1):
        extra_sub, extra_comm, _, _ = evaluate.call_judges_parallel(
            analysis_text, config
        )
        if extra_sub is not None and extra_comm is not None:
            additional_results.append(
                evaluate.compute_composite(extra_sub, extra_comm, config)
            )
        else:
            print(f"  [WARN] Averaging run {i + 2}/{num_runs} failed — skipping")

    if len(additional_results) <= 1:
        return first_result

    avg_composite = statistics.mean(r["composite"] for r in additional_results)
    score_stdev = statistics.stdev(r["composite"] for r in additional_results)
    avg_sub_scores = {
        dim: round(statistics.mean(r["substance_scores"][dim] for r in additional_results), 2)
        for dim in first_result["substance_scores"]
    }
    avg_comm_scores = {
        dim: round(statistics.mean(r["communication_scores"][dim] for r in additional_results), 2)
        for dim in first_result["communication_scores"]
    }
    return {
        "composite": round(avg_composite, 4),
        "substance_avg": round(statistics.mean(r["substance_avg"] for r in additional_results), 4),
        "communication_avg": round(statistics.mean(r["communication_avg"] for r in additional_results), 4),
        "score_stdev": round(score_stdev, 4),
        "num_runs": len(additional_results),
        "substance_scores": avg_sub_scores,
        "communication_scores": avg_comm_scores,
    }


# ─────────────────────────────────────────────
# Writer Providers
# ─────────────────────────────────────────────

def _read_program_prompt(project_root: Path) -> str:
    """Read the single-cycle writer prompt from program.md."""
    prompt_path = project_root / "program.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Writer prompt not found: {prompt_path}")
    return prompt_path.read_text()


def _build_writer_message(
    analysis_text: str,
    cycle: int,
    total_cycles: int,
    phase: str,
    cycle_summary: str = "",
    judge_feedback: str | None = None,
) -> str:
    """Build the user message for the writer agent.

    Includes the analysis text, cycle info, phase, previous cycle summary,
    and judge feedback (v2 feedback-forward). The judge feedback tells the
    writer WHY scores are low so it can target specific weaknesses.
    """
    parts = [
        f"CYCLE: {cycle} of {total_cycles}",
        f"PHASE: {phase}",
    ]
    if cycle_summary:
        parts.append(f"\nPREVIOUS CYCLE SUMMARY:\n{cycle_summary}")
    if judge_feedback:
        parts.append(f"\nJUDGE FEEDBACK FROM PREVIOUS CYCLE:\n{judge_feedback}")
    parts.append(f"\nANALYSIS TO IMPROVE:\n\n{analysis_text}")
    return "\n".join(parts)


def call_writer_claude_code(
    analysis_text: str,
    system_prompt: str,
    cycle: int,
    total_cycles: int,
    phase: str,
    cycle_summary: str = "",
    judge_feedback: str | None = None,
    **kwargs,
) -> str | None:
    """Call Claude Code CLI as the writer agent.

    Uses `claude -p` (print mode) for non-interactive single-shot.
    Zero API keys needed — uses the user's existing Claude Code auth.

    Returns the improved analysis text, or None if the call fails.
    """
    user_msg = _build_writer_message(
        analysis_text, cycle, total_cycles, phase, cycle_summary,
        judge_feedback=judge_feedback,
    )

    try:
        # claude -p reads from stdin, --system-prompt sets system message
        result = subprocess.run(
            ["claude", "-p", "--system-prompt", system_prompt],
            input=user_msg,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min max for writer
        )
        if result.returncode != 0:
            print(f"  [WARN] Claude Code returned exit code {result.returncode}")
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print("  [WARN] Claude Code writer timed out after 300s")
        return None
    except FileNotFoundError:
        print("  [ERROR] 'claude' CLI not found. Install Claude Code first.")
        return None
    except Exception as e:
        print(f"  [ERROR] Writer call failed: {e}")
        return None


def call_writer_anthropic(
    analysis_text: str,
    system_prompt: str,
    cycle: int,
    total_cycles: int,
    phase: str,
    cycle_summary: str = "",
    judge_feedback: str | None = None,
    model: str = "claude-sonnet-4-20250514",
    **kwargs,
) -> str | None:
    """Call Anthropic API directly as the writer agent.

    Requires ANTHROPIC_API_KEY env var. Higher reliability for scripting
    but costs money per call.

    Returns the improved analysis text, or None if the call fails.
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        print("  [ERROR] 'anthropic' package not installed. Run: pip install anthropic")
        return None

    user_msg = _build_writer_message(
        analysis_text, cycle, total_cycles, phase, cycle_summary,
        judge_feedback=judge_feedback,
    )

    client = Anthropic()

    # Retry with backoff: 2 retries, 30s/60s (CEO review #15)
    backoff_seconds = [30, 60]
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=8192,
                system=system_prompt,
                messages=[{"role": "user", "content": user_msg}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            print(f"  [WARN] Anthropic API error (attempt {attempt + 1}): {e}")
            if attempt < 2:
                wait = backoff_seconds[attempt]
                print(f"  [INFO] Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print("  [ERROR] Anthropic API failed after 3 attempts")
                return None

    return None  # defensive: loop exhausted without return (should not reach here)


def call_writer_novita(
    analysis_text: str,
    system_prompt: str,
    cycle: int,
    total_cycles: int,
    phase: str,
    cycle_summary: str = "",
    judge_feedback: str | None = None,
    model: str = "deepseek/deepseek-v3.2",
    **kwargs,
) -> str | None:
    """Call Novita AI's OpenAI-compatible API as the writer agent.

    Requires NOVITA_API_KEY env var. Uses the openai Python package
    with a custom base_url pointing to Novita's endpoint.

    Supported models:
      - deepseek/deepseek-v3.2 (default, best price/performance)
      - minimax/minimax-m2.7 (larger output window)
      - zai-org/glm-4.7-flash (cheapest)

    Returns the improved analysis text, or None if the call fails.
    """
    try:
        from openai import OpenAI
    except ImportError:
        print("  [ERROR] 'openai' package not installed. Run: pip install openai")
        return None

    api_key = os.environ.get("NOVITA_API_KEY")
    if not api_key:
        print("  [ERROR] NOVITA_API_KEY not set. Export it first.")
        return None

    user_msg = _build_writer_message(
        analysis_text, cycle, total_cycles, phase, cycle_summary,
        judge_feedback=judge_feedback,
    )

    client = OpenAI(
        base_url="https://api.novita.ai/openai",
        api_key=api_key,
    )

    # Retry with backoff: 2 retries, 30s/60s (matching anthropic provider)
    backoff_seconds = [30, 60]
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=8192,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  [WARN] Novita API error (attempt {attempt + 1}): {e}")
            if attempt < 2:
                wait = backoff_seconds[attempt]
                print(f"  [INFO] Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print("  [ERROR] Novita API failed after 3 attempts")
                return None

    return None  # defensive: should not reach here


# ─────────────────────────────────────────────
# Git Operations (in isolated workdir)
# ─────────────────────────────────────────────

def _git(workdir: str, *args: str) -> subprocess.CompletedProcess:
    """Run a git command in the working directory.

    Timeout of 30s — git on a local file should complete in <1s.
    """
    return subprocess.run(
        ["git", "-C", workdir] + list(args),
        capture_output=True,
        text=True,
        timeout=30,
    )


def _git_init(workdir: str):
    """Initialize git repo and make initial commit.

    Raises RuntimeError if any git operation fails — this is the
    foundation of state management and must not fail silently.
    """
    r1 = _git(workdir, "init")
    if r1.returncode != 0:
        raise RuntimeError(f"git init failed: {r1.stderr}")
    # Create a non-main branch to avoid global pre-commit hook
    # that blocks direct commits to main/master
    rb = _git(workdir, "checkout", "-b", "autoresearch")
    if rb.returncode != 0:
        raise RuntimeError(f"git checkout -b failed: {rb.stderr}")
    r2 = _git(workdir, "add", ".")
    if r2.returncode != 0:
        raise RuntimeError(f"git add failed: {r2.stderr}")
    r3 = _git(workdir, "commit", "-m", "initial: baseline analysis")
    if r3.returncode != 0:
        raise RuntimeError(f"git initial commit failed: {r3.stderr}")


def _git_commit(workdir: str, message: str):
    """Stage analysis.md and commit with message.

    Raises RuntimeError on failure — a failed commit means
    the revert logic would operate on wrong state.
    """
    r1 = _git(workdir, "add", "analysis.md")
    if r1.returncode != 0:
        raise RuntimeError(f"git add failed: {r1.stderr}")
    r2 = _git(workdir, "commit", "-m", message)
    if r2.returncode != 0:
        raise RuntimeError(f"git commit failed: {r2.stderr}")


def _git_revert_file(workdir: str):
    """Revert analysis.md to previous commit (file-specific, not reset --hard).

    Raises RuntimeError if git operations fail — a failed revert means
    the workdir contains unreviewed content that shouldn't be written back.
    """
    r1 = _git(workdir, "checkout", "HEAD~1", "--", "analysis.md")
    if r1.returncode != 0:
        raise RuntimeError(f"git checkout revert failed: {r1.stderr}")
    r2 = _git(workdir, "commit", "-m", "revert: reverted analysis.md to previous version")
    if r2.returncode != 0:
        raise RuntimeError(f"git revert commit failed: {r2.stderr}")


def _git_diff(workdir: str) -> str:
    """Get diff of analysis.md from previous commit."""
    result = _git(workdir, "diff", "HEAD~1", "--", "analysis.md")
    return result.stdout


# ─────────────────────────────────────────────
# Cycle Summary Builder
# ─────────────────────────────────────────────

def _build_cycle_summary(history: list[dict]) -> str:
    """Build a brief summary of previous cycles for the writer.

    Tells the writer what was tried, what scores changed, and includes
    critique snippets so the writer knows WHY edits were kept/reverted.
    """
    if not history:
        return ""

    lines = [f"Previous cycles: {len(history)} completed"]
    kept = sum(1 for h in history if h.get("action") == "keep")
    reverted = sum(1 for h in history if h.get("action") == "revert")
    skipped = sum(1 for h in history if h.get("action") == "skip")

    lines.append(f"  Kept: {kept}, Reverted: {reverted}, Skipped: {skipped}")

    # Show last 3 cycles for context
    recent = history[-3:]
    for entry in recent:
        action = entry.get("action", "?")
        cycle_num = entry.get("cycle", "?")
        composite = entry.get("composite", "?")
        hypothesis = entry.get("hypothesis", "")
        lines.append(f"  Cycle {cycle_num}: {action} (composite={composite}) — {hypothesis}")
        # Note: full critiques are passed separately via judge_feedback param
        # (v2 feedback-forward). Cycle summary stays concise — scores only.

    return "\n".join(lines)


# ─────────────────────────────────────────────
# Startup Validation
# ─────────────────────────────────────────────

def _validate_dependencies(provider: str, judge_provider: str = "codex"):
    """Check that required CLI tools are installed (eng review #5).

    If judge_provider=codex: needs codex CLI
    If judge_provider=novita: needs NOVITA_API_KEY + openai package
    If provider=claude-code: needs claude CLI
    If provider=anthropic: needs ANTHROPIC_API_KEY
    """
    errors = []

    # Check judge provider
    if judge_provider == "codex":
        try:
            subprocess.run(
                ["codex", "--version"], capture_output=True, timeout=10
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            errors.append("'codex' CLI not found. Install: npm install -g @openai/codex")
    elif judge_provider == "novita":
        if not os.environ.get("NOVITA_API_KEY"):
            errors.append("NOVITA_API_KEY not set (needed for --judge-provider novita)")
        try:
            import openai  # noqa: F401
        except ImportError:
            errors.append("'openai' package not installed (needed for --judge-provider novita)")

    # Check writer provider
    if provider == "claude-code":
        try:
            subprocess.run(
                ["claude", "--version"], capture_output=True, timeout=10
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            errors.append("'claude' CLI not found. Install Claude Code first.")
    elif provider == "anthropic":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            errors.append("ANTHROPIC_API_KEY not set. Export it or use --provider claude-code")
    elif provider == "novita":
        if not os.environ.get("NOVITA_API_KEY"):
            errors.append("NOVITA_API_KEY not set. Export it or use --provider claude-code")
        try:
            import openai  # noqa: F401
        except ImportError:
            errors.append("'openai' package not installed. Run: pip install openai")

    if errors:
        print("STARTUP VALIDATION FAILED:")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)

    print("  ✓ All dependencies verified")


# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────

def _ensure_run_dir(project_root: Path) -> Path:
    """Create runs/<timestamp>/ directory for this run's output."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = project_root / "runs" / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "diffs").mkdir(exist_ok=True)
    (run_dir / "critiques").mkdir(exist_ok=True)  # CEO review #16
    return run_dir


def _log_scores(run_dir: Path, entry: dict):
    """Append a score entry to scores.jsonl."""
    with open(run_dir / "scores.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")


def _save_critique(run_dir: Path, cycle: int, judge_name: str, critique: str | None):
    """Save judge critique text to critiques/ directory (CEO review #16)."""
    if critique:
        path = run_dir / "critiques" / f"cycle-{cycle:03d}-{judge_name}.txt"
        path.write_text(critique)


def _save_diff(run_dir: Path, cycle: int, diff_text: str):
    """Save the diff for this cycle."""
    path = run_dir / "diffs" / f"cycle-{cycle:03d}.diff"
    path.write_text(diff_text)


def _write_summary(run_dir: Path, summary: dict):
    """Write final summary.json."""
    with open(run_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)


def resolve_config_path(config_path: str, project_root: Path) -> Path:
    """Resolve config paths relative to cwd first, then autoresearch/."""
    candidate = Path(config_path)
    if candidate.is_absolute():
        return candidate
    if candidate.exists():
        return candidate.resolve()
    return project_root / candidate


# ─────────────────────────────────────────────
# Human Gate
# ─────────────────────────────────────────────

def _human_gate_prompt(cycle: int, improvement: float, new_composite: float) -> bool:
    """Ask human whether to keep a marginal improvement.

    Auto-keep if improvement > 1.0 (already handled by decide_action).
    This is only called for 0.3-1.0 range (eng review #11).
    """
    print(f"\n  ┌─ HUMAN GATE (cycle {cycle}) ─────────────────")
    print(f"  │ Improvement: +{improvement:.2f} (composite: {new_composite:.2f})")
    print(f"  │ This is a marginal improvement (0.3-1.0 range).")
    print(f"  └─ Keep this edit? [y/N] ", end="")

    try:
        answer = input().strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        print("\n  [INFO] No input — reverting (safe default)")
        return False


# ─────────────────────────────────────────────
# Main Loop
# ─────────────────────────────────────────────

def run_loop(args):
    """Main autoresearch loop.

    1. Set up isolated workdir with git
    2. Baseline eval
    3. For each cycle: write → commit → eval → decide → keep/revert
    4. Stop on: 3 non-improving, budget exceeded, or target reached
    5. Copy final result back
    """
    project_root = Path(__file__).parent.resolve()

    # Validate dependencies
    print("Validating dependencies...")
    _validate_dependencies(args.provider, getattr(args, 'judge_provider', 'codex'))

    # Read writer prompt
    system_prompt = _read_program_prompt(project_root)

    # Load config
    config = evaluate.load_config(str(resolve_config_path(args.config, project_root)))

    # Set up isolated working directory
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    # Backup original before we touch anything (security: recovery path)
    backup_path = input_path.with_suffix(".md.bak")
    shutil.copy2(input_path, backup_path)
    print(f"Backup saved: {backup_path}")

    workdir = tempfile.mkdtemp(prefix="autoresearch-")
    print(f"Working directory: {workdir}")

    # Copy input file
    analysis_dest = Path(workdir) / "analysis.md"
    shutil.copy2(input_path, analysis_dest)

    # Save initial copy to run dir
    run_dir = _ensure_run_dir(project_root)
    shutil.copy2(input_path, run_dir / "analysis-initial.md")

    # Git init
    _git_init(workdir)

    # ── Configure judge provider + format ──
    judge_provider = getattr(args, 'judge_provider', 'codex')
    judge_model = getattr(args, 'judge_model', 'deepseek/deepseek-v3.2')
    judge_format = getattr(args, 'judge_format', 'hybrid')
    evaluate.set_judge_provider(judge_provider, judge_model)
    evaluate.set_judge_format(judge_format)
    if judge_provider != "codex" or judge_format != "numeric":
        print(f"  Judge: {judge_provider} ({judge_model}), format: {judge_format}")

    # ── Baseline eval ──
    num_runs = getattr(args, 'runs', 1)
    print(f"\nRunning baseline evaluation ({num_runs} run{'s' if num_runs > 1 else ''})...")
    analysis_text = analysis_dest.read_text()

    # First run: get critiques for feedback-forward
    sub_scores, comm_scores, sub_critique, comm_critique = evaluate.call_judges_parallel(
        analysis_text, config
    )

    if sub_scores is None or comm_scores is None:
        print("ERROR: Baseline evaluation failed — judges returned no scores.")
        print("Check that 'codex' is installed and working.")
        sys.exit(1)

    # Multi-run averaging: reuse first run, add N-1 more, average all.
    first_result = evaluate.compute_composite(sub_scores, comm_scores, config)
    baseline = _average_results(first_result, analysis_text, config, num_runs)
    if "score_stdev" in baseline:
        print(f"Baseline composite: {baseline['composite']} (averaged over {baseline['num_runs']} runs, stdev={baseline['score_stdev']:.3f})")
    else:
        print(f"Baseline composite: {baseline['composite']}")
    print(evaluate.format_output(baseline))

    # Save baseline critiques (from first run — used for feedback-forward)
    _save_critique(run_dir, 0, "substance", sub_critique)
    _save_critique(run_dir, 0, "communication", comm_critique)

    # Log baseline
    _log_scores(run_dir, {
        "cycle": 0, "action": "baseline",
        "timestamp": datetime.datetime.now().isoformat(),
        **baseline,
    })

    # ── Cycle loop ──
    current_best = baseline
    history = []
    consecutive_writer_failures = 0

    # Select writer function based on provider.
    # For Anthropic/Novita, bind the --model flag via functools.partial so
    # run_loop doesn't need to know about provider-specific kwargs.
    if args.provider == "claude-code":
        writer_fn = call_writer_claude_code
    elif args.provider == "novita":
        from functools import partial
        model = args.model or "deepseek/deepseek-v3.2"
        writer_fn = partial(call_writer_novita, model=model)
    else:
        from functools import partial
        model = args.model or "claude-sonnet-4-20250514"
        writer_fn = partial(call_writer_anthropic, model=model)

    for cycle in range(1, args.cycles + 1):
        # Budget check (eng review #12)
        if budget_exceeded(cycle, args.max_total_cycles):
            print(f"\n  HALT: Budget exceeded (max_total_cycles={args.max_total_cycles})")
            break

        # Stop rule: 3 consecutive non-improving — show actionable gaps
        if should_halt(history, config):
            print("\n  PLATEAU DETECTED — 3 consecutive non-improving cycles")
            # Find the most recent critique and surface actionable gaps
            last_with_critique = None
            for h in reversed(history):
                if h.get("sub_critique") or h.get("comm_critique"):
                    last_with_critique = h
                    break
            if last_with_critique:
                print("\n  Here's what the judges say is holding you back:\n")
                if last_with_critique.get("sub_critique"):
                    # Show first 500 chars of substance critique
                    crit = last_with_critique["sub_critique"][:500]
                    print(f"  SUBSTANCE GAPS:\n  {crit}\n")
                if last_with_critique.get("comm_critique"):
                    crit = last_with_critique["comm_critique"][:500]
                    print(f"  COMMUNICATION GAPS:\n  {crit}\n")
                print("  Add these to your draft, then re-run to continue improving.")
            break

        # Stop rule: 3 consecutive judge failures
        if should_halt_judge_failures(history):
            print("\n  HALT: 3 consecutive judge failures (systemic issue)")
            break

        # Target reached
        if current_best["composite"] >= config.get("thresholds", {}).get("target_score", 9.0):
            print(f"\n  HALT: Target score reached ({current_best['composite']})")
            break

        phase = get_phase(cycle, args.cycles)
        print(f"\n{'='*50}")
        print(f"CYCLE {cycle}/{args.cycles} — Phase: {phase}")
        print(f"{'='*50}")

        # ── 1. Write ──
        analysis_text = analysis_dest.read_text()
        cycle_summary = _build_cycle_summary(history)

        # Build judge feedback from previous cycle (v2 feedback-forward).
        # This tells the writer WHY scores are low so it targets weaknesses.
        judge_feedback = None
        if history:
            last = history[-1]
            sub_crit = last.get("sub_critique", "")
            comm_crit = last.get("comm_critique", "")
            if sub_crit or comm_crit:
                parts = []
                if sub_crit:
                    parts.append(f"SUBSTANCE JUDGE:\n{sub_crit}")
                if comm_crit:
                    parts.append(f"COMMUNICATION JUDGE:\n{comm_crit}")
                judge_feedback = "\n\n".join(parts)

        improved_text = writer_fn(
            analysis_text=analysis_text,
            system_prompt=system_prompt,
            cycle=cycle,
            total_cycles=args.cycles,
            phase=phase,
            cycle_summary=cycle_summary,
            judge_feedback=judge_feedback,
        )

        # Writer failure handling (CEO review #14, #15)
        if improved_text is None:
            print("  [WARN] Writer returned nothing — skipping cycle")
            consecutive_writer_failures += 1
            if consecutive_writer_failures >= 3:
                print("  HALT: 3 consecutive writer failures")
                history.append({
                    "cycle": cycle, "action": "skip", "judge_failure": False,
                    "reason": "writer_failure",
                })
                break
            history.append({
                "cycle": cycle, "action": "skip", "judge_failure": False,
                "reason": "writer_failure",
            })
            _log_scores(run_dir, {
                "cycle": cycle, "action": "skip", "reason": "writer_failure",
                "timestamp": datetime.datetime.now().isoformat(),
            })
            continue

        # Validate writer output (CEO review #14)
        if not validate_writer_output(improved_text, analysis_text):
            print("  [WARN] Writer output failed validation — skipping cycle")
            history.append({
                "cycle": cycle, "action": "skip", "judge_failure": False,
                "reason": "writer_validation_failed",
            })
            _log_scores(run_dir, {
                "cycle": cycle, "action": "skip", "reason": "writer_validation_failed",
                "timestamp": datetime.datetime.now().isoformat(),
            })
            continue

        consecutive_writer_failures = 0  # reset on success

        # ── 2. Commit ──
        analysis_dest.write_text(improved_text)
        _git_commit(workdir, f"cycle {cycle}: {phase} improvement")

        # Save diff
        diff_text = _git_diff(workdir)
        _save_diff(run_dir, cycle, diff_text)

        # ── 3. Evaluate ──
        print(f"  Evaluating ({num_runs} run{'s' if num_runs > 1 else ''})...")

        # First run: get critiques for feedback-forward
        sub_scores, comm_scores, sub_critique, comm_critique = evaluate.call_judges_parallel(
            improved_text, config
        )

        # Save critiques (CEO review #16)
        _save_critique(run_dir, cycle, "substance", sub_critique)
        _save_critique(run_dir, cycle, "communication", comm_critique)

        # ── 4. Decide ──
        if sub_scores is None or comm_scores is None:
            # Judge failure — skip cycle entirely (eng review #4)
            print("  [WARN] Judge failure — skipping cycle")
            _git_revert_file(workdir)
            history.append({
                "cycle": cycle, "action": "skip", "judge_failure": True,
            })
            _log_scores(run_dir, {
                "cycle": cycle, "action": "skip", "reason": "judge_failure",
                "timestamp": datetime.datetime.now().isoformat(),
            })
            continue

        # Multi-run averaging: reuse first run, add N-1 more, average all.
        first_result = evaluate.compute_composite(sub_scores, comm_scores, config)
        new_result = _average_results(first_result, improved_text, config, num_runs)
        if "score_stdev" in new_result:
            print(f"  Score stdev: {new_result['score_stdev']:.3f} (over {new_result['num_runs']} runs)")
        action = decide_action(current_best, new_result, config)
        improvement = new_result["composite"] - current_best["composite"]

        print(f"  Composite: {current_best['composite']} → {new_result['composite']} ({improvement:+.2f})")

        # Human gate for marginal improvements (eng review #11)
        if action == "human_gate":
            if args.auto_approve:
                print("  [AUTO-APPROVE] Marginal improvement auto-kept")
                action = "keep"
            elif _human_gate_prompt(cycle, improvement, new_result["composite"]):
                action = "keep"
            else:
                action = "revert"

        # ── 5. Execute decision ──
        if action == "keep":
            print(f"  ✓ KEEP (improvement: {improvement:+.2f})")
            current_best = new_result
        elif action == "revert":
            print(f"  ✗ REVERT (improvement: {improvement:+.2f})")
            _git_revert_file(workdir)

        # ── 6. Log ──
        history.append({
            "cycle": cycle,
            "action": action,
            "judge_failure": False,
            "composite": new_result["composite"],
            "improvement": round(improvement, 4),
            "phase": phase,
            "hypothesis": f"{phase} improvement",
            "sub_critique": sub_critique or "",
            "comm_critique": comm_critique or "",
        })
        _log_scores(run_dir, {
            "cycle": cycle,
            "action": action,
            "timestamp": datetime.datetime.now().isoformat(),
            **new_result,
        })

    # ── Finalize ──
    print(f"\n{'='*50}")
    print("LOOP COMPLETE")
    print(f"{'='*50}")

    # Copy final analysis to run dir for audit trail
    final_text = analysis_dest.read_text()
    shutil.copy2(analysis_dest, run_dir / "analysis-final.md")

    # Only write back if there was actual improvement (security: don't
    # overwrite original with unimproved or potentially broken content)
    if current_best["composite"] > baseline["composite"]:
        input_path.write_text(final_text)
        print(f"Final analysis written to: {input_path}")
        print(f"  (backup at: {backup_path})")
    else:
        print(f"No improvement over baseline — original file unchanged.")
        print(f"  Final version available at: {run_dir / 'analysis-final.md'}")

    # Write summary
    kept = sum(1 for h in history if h.get("action") == "keep")
    reverted = sum(1 for h in history if h.get("action") == "revert")
    skipped = sum(1 for h in history if h.get("action") == "skip")
    total = len(history)

    # Determine status
    status = "completed"
    if should_halt_judge_failures(history):
        status = "judge_failure"
    elif should_halt(history, config):
        status = "plateau"
    elif budget_exceeded(total, args.max_total_cycles):
        status = "budget_exceeded"
    elif current_best["composite"] >= config.get("thresholds", {}).get("target_score", 9.0):
        status = "target_reached"

    summary = {
        "status": status,
        "cycles": total,
        "kept": kept,
        "reverted": reverted,
        "skipped": skipped,
        "baseline_score": baseline["composite"],
        "final_score": current_best["composite"],
        "improvement": round(current_best["composite"] - baseline["composite"], 4),
        "input_file": str(input_path),
        "run_dir": str(run_dir),
        "timestamp": datetime.datetime.now().isoformat(),
    }
    _write_summary(run_dir, summary)

    print(f"\nBaseline: {baseline['composite']} → Final: {current_best['composite']}")
    print(f"Cycles: {total} (kept={kept}, reverted={reverted}, skipped={skipped})")
    print(f"Status: {status}")
    print(f"Run directory: {run_dir}")

    # Cleanup workdir unless --keep-workdir
    if not args.keep_workdir:
        shutil.rmtree(workdir, ignore_errors=True)
        print(f"Cleaned up workdir: {workdir}")
    else:
        print(f"Workdir preserved: {workdir}")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="DS AutoResearch — automated analysis improvement loop"
    )
    parser.add_argument(
        "--input", required=True,
        help="Path to the analysis markdown file to improve"
    )
    parser.add_argument(
        "--cycles", type=int, default=10,
        help="Number of improvement cycles (default: 10)"
    )
    parser.add_argument(
        "--config", default="review_config.yaml",
        help="Path to review config (default: review_config.yaml)"
    )
    parser.add_argument(
        "--provider", choices=["claude-code", "anthropic", "novita"],
        default="claude-code",
        help="Writer provider (default: claude-code, zero API keys needed)"
    )
    parser.add_argument(
        "--max-total-cycles", type=int, default=20,
        help="Hard budget cap including skipped cycles (default: 20)"
    )
    parser.add_argument(
        "--keep-workdir", action="store_true",
        help="Don't delete the temp working directory (for debugging)"
    )
    parser.add_argument(
        "--auto-approve", action="store_true",
        help="Skip human gate — auto-keep any improvement >= min_improvement threshold"
    )
    parser.add_argument(
        "--runs", type=int, default=1,
        help="Number of judge runs to average per evaluation (default: 1, recommended: 3 for stability)"
    )
    parser.add_argument(
        "--judge-provider", choices=["codex", "novita"],
        default="codex",
        help="Judge provider (default: codex). Use novita to avoid Codex rate limits."
    )
    parser.add_argument(
        "--judge-model", default="deepseek/deepseek-v3.2",
        help="Model for Novita judge (default: deepseek/deepseek-v3.2)"
    )
    parser.add_argument(
        "--judge-format", choices=["numeric", "binary", "hybrid"],
        default="hybrid",
        help="Judge scoring format (default: hybrid — binary for objective dims, numeric for subjective)"
    )
    parser.add_argument(
        "--model", default=None,
        help="Writer model (default: deepseek/deepseek-v3.2 for novita, claude-sonnet-4-20250514 for anthropic)"
    )

    args = parser.parse_args()
    run_loop(args)


if __name__ == "__main__":
    main()
