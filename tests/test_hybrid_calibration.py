#!/usr/bin/env python3

import pytest

from calibrate_hybrid import (
    compare_formats,
    get_binary_substance_dimensions,
    recommend_binary_weight_adjustment,
    summarize_runs,
)


@pytest.fixture
def calibration_config():
    return {
        "substance_dimensions": {
            "statistical_rigor": 1.2,
            "methodology_soundness": 1.0,
            "evidence_conclusion_alignment": 1.3,
            "data_interpretation_accuracy": 1.0,
        },
        "dimension_format": {
            "statistical_rigor": "binary",
            "methodology_soundness": "numeric",
            "evidence_conclusion_alignment": "numeric",
            "data_interpretation_accuracy": "binary",
        },
    }


def test_get_binary_substance_dimensions(calibration_config):
    assert get_binary_substance_dimensions(calibration_config) == [
        "statistical_rigor",
        "data_interpretation_accuracy",
    ]


def test_summarize_runs_averages_scores():
    runs = [
        {
            "composite": 7.2,
            "substance_avg": 6.8,
            "communication_avg": 7.7,
            "substance_scores": {
                "statistical_rigor": 6.0,
                "methodology_soundness": 7.0,
            },
            "communication_scores": {
                "narrative_flow": 7.5,
                "executive_summary_clarity": 8.0,
            },
        },
        {
            "composite": 7.8,
            "substance_avg": 7.4,
            "communication_avg": 8.1,
            "substance_scores": {
                "statistical_rigor": 8.0,
                "methodology_soundness": 7.5,
            },
            "communication_scores": {
                "narrative_flow": 7.0,
                "executive_summary_clarity": 8.5,
            },
        },
    ]

    summary = summarize_runs(runs)

    assert summary["mean_composite"] == pytest.approx(7.5)
    assert summary["stdev_composite"] == pytest.approx(0.4243, abs=1e-4)
    assert summary["mean_substance_scores"]["statistical_rigor"] == pytest.approx(7.0)
    assert summary["mean_communication_scores"]["executive_summary_clarity"] == pytest.approx(8.25)


def test_compare_formats_reports_binary_dimension_deltas(calibration_config):
    numeric_summary = {
        "mean_composite": 7.3,
        "mean_substance_avg": 6.9,
        "mean_communication_avg": 7.8,
        "mean_substance_scores": {
            "statistical_rigor": 6.5,
            "methodology_soundness": 7.0,
            "evidence_conclusion_alignment": 6.8,
            "data_interpretation_accuracy": 7.2,
        },
    }
    hybrid_summary = {
        "mean_composite": 7.7,
        "mean_substance_avg": 7.4,
        "mean_communication_avg": 7.8,
        "mean_substance_scores": {
            "statistical_rigor": 8.5,
            "methodology_soundness": 7.1,
            "evidence_conclusion_alignment": 6.9,
            "data_interpretation_accuracy": 7.7,
        },
    }

    comparison = compare_formats(numeric_summary, hybrid_summary, calibration_config)

    assert comparison["composite_delta"] == pytest.approx(0.4)
    assert comparison["binary_dimension_deltas"]["statistical_rigor"] == pytest.approx(2.0)
    assert comparison["non_binary_substance_deltas"]["methodology_soundness"] == pytest.approx(0.1)


def test_recommend_binary_weight_adjustment_downweights_binary_dims(calibration_config):
    numeric_summary = {
        "mean_substance_avg": 6.8,
    }
    hybrid_summary = {
        "mean_substance_avg": 7.3,
        "mean_substance_scores": {
            "statistical_rigor": 9.0,
            "methodology_soundness": 7.0,
            "evidence_conclusion_alignment": 6.5,
            "data_interpretation_accuracy": 8.0,
        },
    }

    recommendation = recommend_binary_weight_adjustment(
        calibration_config,
        numeric_summary,
        hybrid_summary,
    )

    assert recommendation["action"] == "downweight_binary_dimensions"
    assert recommendation["scale_factor"] < 1.0
    assert recommendation["suggested_weights"]["statistical_rigor"] < 1.2
    assert recommendation["suggested_weights"]["data_interpretation_accuracy"] < 1.0


def test_recommend_binary_weight_adjustment_leaves_weights_when_not_inflated(calibration_config):
    numeric_summary = {
        "mean_substance_avg": 7.0,
    }
    hybrid_summary = {
        "mean_substance_avg": 7.05,
        "mean_substance_scores": {
            "statistical_rigor": 7.5,
            "methodology_soundness": 7.0,
            "evidence_conclusion_alignment": 6.8,
            "data_interpretation_accuracy": 7.2,
        },
    }

    recommendation = recommend_binary_weight_adjustment(
        calibration_config,
        numeric_summary,
        hybrid_summary,
    )

    assert recommendation["action"] == "leave"
    assert recommendation["scale_factor"] == 1.0
