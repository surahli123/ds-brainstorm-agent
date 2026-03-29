#!/usr/bin/env python3
"""
calibrate_hybrid.py — Compare numeric vs hybrid judge formats.

Runs repeated evaluations on the same document, summarizes score drift,
and recommends whether the binary substance dimensions should be
downweighted in review_config.yaml.

Example:
    python3 calibrate_hybrid.py \
      --file ebay_marketing_analysis.md \
      --provider novita \
      --model minimax/minimax-m2.7 \
      --runs-per-format 5 \
      --output calibration-report.json
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import evaluate


def get_binary_substance_dimensions(config: dict) -> list[str]:
    """Return substance dimensions configured for binary scoring."""
    dimension_format = config.get("dimension_format", {})
    substance_weights = config.get("substance_dimensions", {})
    return [
        dim for dim in substance_weights
        if dimension_format.get(dim) == "binary"
    ]


def summarize_runs(runs: list[dict]) -> dict:
    """Aggregate repeated evaluation results into a compact summary."""
    if not runs:
        raise ValueError("Cannot summarize zero runs")

    composite_scores = [run["composite"] for run in runs]
    substance_scores = [run["substance_avg"] for run in runs]
    communication_scores = [run["communication_avg"] for run in runs]

    summary = {
        "num_runs": len(runs),
        "mean_composite": round(statistics.mean(composite_scores), 4),
        "stdev_composite": round(statistics.stdev(composite_scores), 4) if len(runs) > 1 else 0.0,
        "min_composite": round(min(composite_scores), 4),
        "max_composite": round(max(composite_scores), 4),
        "mean_substance_avg": round(statistics.mean(substance_scores), 4),
        "mean_communication_avg": round(statistics.mean(communication_scores), 4),
        "mean_substance_scores": {},
        "mean_communication_scores": {},
    }

    sub_dims = sorted(set.intersection(*(set(run["substance_scores"]) for run in runs)))
    comm_dims = sorted(set.intersection(*(set(run["communication_scores"]) for run in runs)))

    summary["mean_substance_scores"] = {
        dim: round(statistics.mean(run["substance_scores"][dim] for run in runs), 4)
        for dim in sub_dims
    }
    summary["mean_communication_scores"] = {
        dim: round(statistics.mean(run["communication_scores"][dim] for run in runs), 4)
        for dim in comm_dims
    }
    return summary


def compare_formats(numeric_summary: dict, hybrid_summary: dict, config: dict) -> dict:
    """Compare numeric and hybrid summaries on the same document."""
    binary_dims = get_binary_substance_dimensions(config)

    comparison = {
        "composite_delta": round(
            hybrid_summary["mean_composite"] - numeric_summary["mean_composite"], 4
        ),
        "substance_delta": round(
            hybrid_summary["mean_substance_avg"] - numeric_summary["mean_substance_avg"], 4
        ),
        "communication_delta": round(
            hybrid_summary["mean_communication_avg"] - numeric_summary["mean_communication_avg"], 4
        ),
        "binary_dimension_deltas": {},
        "non_binary_substance_deltas": {},
    }

    numeric_substance = numeric_summary.get("mean_substance_scores", {})
    hybrid_substance = hybrid_summary.get("mean_substance_scores", {})
    for dim, hybrid_score in hybrid_substance.items():
        if dim not in numeric_substance:
            continue
        delta = round(hybrid_score - numeric_substance[dim], 4)
        if dim in binary_dims:
            comparison["binary_dimension_deltas"][dim] = delta
        else:
            comparison["non_binary_substance_deltas"][dim] = delta

    return comparison


def recommend_binary_weight_adjustment(
    config: dict,
    numeric_summary: dict,
    hybrid_summary: dict,
    inflation_tolerance: float = 0.1,
    min_scale: float = 0.1,
) -> dict:
    """Recommend scaling binary substance weights to match numeric substance mean.

    We solve for a shared scale factor `s` applied to all binary substance
    dimensions such that:

        target_numeric_substance ~= weighted_avg(hybrid_scores, scaled_binary_weights)

    If the hybrid substance mean is not inflated beyond `inflation_tolerance`,
    or if the observed means imply the inflation is not driven by binary
    dimensions alone, the recommendation is to leave weights unchanged.
    """
    binary_dims = get_binary_substance_dimensions(config)
    current_weights = config.get("substance_dimensions", {})
    hybrid_scores = hybrid_summary.get("mean_substance_scores", {})
    target = numeric_summary["mean_substance_avg"]
    observed = hybrid_summary["mean_substance_avg"]

    recommendation = {
        "action": "leave",
        "reason": "Hybrid substance score is within tolerance of numeric baseline.",
        "scale_factor": 1.0,
        "current_weights": {
            dim: current_weights[dim]
            for dim in binary_dims
            if dim in current_weights
        },
        "suggested_weights": {
            dim: current_weights[dim]
            for dim in binary_dims
            if dim in current_weights
        },
    }

    if observed <= target + inflation_tolerance:
        return recommendation

    present_binary_dims = [dim for dim in binary_dims if dim in hybrid_scores]
    if not present_binary_dims:
        recommendation["reason"] = "No binary substance scores were present in the hybrid summary."
        return recommendation

    binary_weight_total = sum(current_weights[dim] for dim in present_binary_dims)
    non_binary_dims = [dim for dim in hybrid_scores if dim not in present_binary_dims]
    non_binary_weight_total = sum(current_weights.get(dim, 1.0) for dim in non_binary_dims)

    binary_weighted_sum = sum(
        current_weights[dim] * hybrid_scores[dim]
        for dim in present_binary_dims
    )
    non_binary_weighted_sum = sum(
        current_weights.get(dim, 1.0) * hybrid_scores[dim]
        for dim in non_binary_dims
    )

    numerator = (target * non_binary_weight_total) - non_binary_weighted_sum
    denominator = binary_weighted_sum - (target * binary_weight_total)

    if denominator <= 0:
        recommendation["reason"] = (
            "Observed hybrid scores do not support a stable shared scale factor for binary dimensions."
        )
        return recommendation

    if numerator <= 0:
        recommendation["reason"] = (
            "Non-binary substance dimensions already exceed the numeric target; binary downweighting alone will not calibrate the score."
        )
        return recommendation

    scale_factor = max(min_scale, min(1.0, numerator / denominator))
    if scale_factor >= 1.0:
        return recommendation

    recommendation["action"] = "downweight_binary_dimensions"
    recommendation["reason"] = (
        "Hybrid substance score is materially above numeric, and binary dimensions can be scaled down to align the means."
    )
    recommendation["scale_factor"] = round(scale_factor, 4)
    recommendation["suggested_weights"] = {
        dim: round(current_weights[dim] * scale_factor, 4)
        for dim in present_binary_dims
    }
    return recommendation


def run_calibration(
    analysis_file: str,
    config_path: str,
    provider: str,
    model: str,
    runs_per_format: int,
    eval_runs: int,
) -> dict:
    """Execute numeric and hybrid evaluations and build a calibration report."""
    config = evaluate.load_config(config_path)
    analysis_text = Path(analysis_file).read_text()

    report = {
        "analysis_file": analysis_file,
        "config_path": config_path,
        "provider": provider,
        "model": model,
        "runs_per_format": runs_per_format,
        "eval_runs": eval_runs,
        "formats": {},
    }

    for fmt in ("numeric", "hybrid"):
        evaluate.set_judge_provider(provider, model)
        evaluate.set_judge_format(fmt)
        runs = [
            evaluate.evaluate_with_averaging(analysis_text, config, num_runs=eval_runs)
            for _ in range(runs_per_format)
        ]
        report["formats"][fmt] = {
            "runs": runs,
            "summary": summarize_runs(runs),
        }

    numeric_summary = report["formats"]["numeric"]["summary"]
    hybrid_summary = report["formats"]["hybrid"]["summary"]
    report["comparison"] = compare_formats(numeric_summary, hybrid_summary, config)
    report["weight_recommendation"] = recommend_binary_weight_adjustment(
        config,
        numeric_summary,
        hybrid_summary,
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate hybrid judges against numeric judges")
    parser.add_argument("--file", required=True, help="Analysis markdown file to evaluate")
    parser.add_argument("--config", default="review_config.yaml", help="Path to review config")
    parser.add_argument("--provider", default="novita", help="Judge provider (default: novita)")
    parser.add_argument(
        "--model",
        default="minimax/minimax-m2.7",
        help="Judge model identifier (default: minimax/minimax-m2.7)",
    )
    parser.add_argument(
        "--runs-per-format",
        type=int,
        default=5,
        help="How many repeated evaluations to run for each format",
    )
    parser.add_argument(
        "--eval-runs",
        type=int,
        default=1,
        help="Inner averaging count passed to evaluate.evaluate_with_averaging()",
    )
    parser.add_argument(
        "--output",
        help="Optional path to save the full JSON calibration report",
    )
    args = parser.parse_args()

    report = run_calibration(
        analysis_file=args.file,
        config_path=args.config,
        provider=args.provider,
        model=args.model,
        runs_per_format=args.runs_per_format,
        eval_runs=args.eval_runs,
    )

    print(json.dumps(report, indent=2))
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
