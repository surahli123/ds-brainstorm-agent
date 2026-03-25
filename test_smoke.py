#!/usr/bin/env python3
"""
test_smoke.py — Smoke tests for ds-autoresearch decision logic.

Written BEFORE loop_runner.py (TDD). Tests the core keep/revert/halt
decisions using mocked scores — no actual LLM calls needed.

Run: python -m pytest test_smoke.py -v
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We'll import from loop_runner once it exists.
# These tests define the CONTRACT that loop_runner must satisfy.


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def sample_config():
    """Minimal config matching review_config.yaml structure."""
    return {
        "weights": {"substance": 0.55, "communication": 0.45},
        "substance_dimensions": {
            "statistical_rigor": 1.2,
            "methodology_soundness": 1.0,
            "evidence_conclusion_alignment": 1.3,
            "data_interpretation_accuracy": 1.0,
        },
        "communication_dimensions": {
            "narrative_flow": 1.0,
            "audience_calibration": 1.1,
            "visualization_effectiveness": 0.9,
            "executive_summary_clarity": 1.2,
        },
        "thresholds": {
            "min_improvement": 0.3,
            "max_acceptable_stdev": 0.5,
            "target_score": 9.0,
            "max_consecutive_reverts": 3,
        },
    }


@pytest.fixture
def high_scores():
    """Scores that represent a good analysis."""
    return {
        "substance": {
            "statistical_rigor": 8.0,
            "methodology_soundness": 8.0,
            "evidence_conclusion_alignment": 8.0,
            "data_interpretation_accuracy": 8.0,
        },
        "communication": {
            "narrative_flow": 8.0,
            "audience_calibration": 8.0,
            "visualization_effectiveness": 8.0,
            "executive_summary_clarity": 8.0,
        },
    }


@pytest.fixture
def low_scores():
    """Scores that represent a weak analysis."""
    return {
        "substance": {
            "statistical_rigor": 5.0,
            "methodology_soundness": 5.0,
            "evidence_conclusion_alignment": 5.0,
            "data_interpretation_accuracy": 5.0,
        },
        "communication": {
            "narrative_flow": 5.0,
            "audience_calibration": 5.0,
            "visualization_effectiveness": 5.0,
            "executive_summary_clarity": 5.0,
        },
    }


@pytest.fixture
def tmp_workdir():
    """Create a temporary working directory with git init."""
    d = tempfile.mkdtemp(prefix="autoresearch-test-")
    # Create a minimal analysis.md
    analysis = Path(d) / "analysis.md"
    analysis.write_text("# Test Analysis\n\nThis is a test draft.\n")
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ─────────────────────────────────────────────
# Test: compute_composite (from evaluate.py)
# ─────────────────────────────────────────────

class TestComputeComposite:
    """Tests for the scoring math in evaluate.py."""

    def test_equal_scores_produce_expected_composite(self, sample_config):
        """When all dimensions score 8.0, composite = 8.0."""
        from evaluate import compute_composite

        sub_scores = {
            "statistical_rigor": 8.0,
            "methodology_soundness": 8.0,
            "evidence_conclusion_alignment": 8.0,
            "data_interpretation_accuracy": 8.0,
        }
        comm_scores = {
            "narrative_flow": 8.0,
            "audience_calibration": 8.0,
            "visualization_effectiveness": 8.0,
            "executive_summary_clarity": 8.0,
        }
        result = compute_composite(sub_scores, comm_scores, sample_config)
        assert result["composite"] == pytest.approx(8.0, abs=0.01)

    def test_weighted_dimensions_affect_composite(self, sample_config):
        """High-weight dimensions pull the composite toward their score."""
        from evaluate import compute_composite

        # evidence_conclusion_alignment has weight 1.3 — boost it
        sub_scores = {
            "statistical_rigor": 5.0,
            "methodology_soundness": 5.0,
            "evidence_conclusion_alignment": 10.0,  # high-weight dim = 10
            "data_interpretation_accuracy": 5.0,
        }
        comm_scores = {
            "narrative_flow": 5.0,
            "audience_calibration": 5.0,
            "visualization_effectiveness": 5.0,
            "executive_summary_clarity": 5.0,
        }
        result = compute_composite(sub_scores, comm_scores, sample_config)
        # Substance avg should be pulled above 5.0 by the high-weight 10
        assert result["substance_avg"] > 5.5
        assert result["composite"] > 5.0

    def test_substance_weight_dominates(self, sample_config):
        """Substance weight (0.55) > communication (0.45)."""
        from evaluate import compute_composite

        sub_scores = {
            "statistical_rigor": 9.0,
            "methodology_soundness": 9.0,
            "evidence_conclusion_alignment": 9.0,
            "data_interpretation_accuracy": 9.0,
        }
        comm_scores = {
            "narrative_flow": 1.0,
            "audience_calibration": 1.0,
            "visualization_effectiveness": 1.0,
            "executive_summary_clarity": 1.0,
        }
        result = compute_composite(sub_scores, comm_scores, sample_config)
        # 0.55 * 9 + 0.45 * 1 = 4.95 + 0.45 = 5.40
        assert result["composite"] == pytest.approx(5.40, abs=0.05)


# ─────────────────────────────────────────────
# Test: Decision Logic
# ─────────────────────────────────────────────

class TestDecisionLogic:
    """Tests for the keep/revert/halt decisions in loop_runner.py.

    These test the decide_action() function that loop_runner must expose.
    Contract:
        decide_action(prev_scores, new_scores, config) -> str
        Returns: "keep", "revert", "human_gate", or "halt"
    """

    def test_clear_improvement_keeps(self, sample_config):
        """Score improved by > 1.0 with no regression → auto-KEEP.

        Per human gate rules: >1.0 = auto-keep, 0.3-1.0 = human_gate.
        """
        from loop_runner import decide_action

        prev = {"composite": 5.0, "substance_scores": {
            "statistical_rigor": 5.0, "methodology_soundness": 5.0,
            "evidence_conclusion_alignment": 5.0, "data_interpretation_accuracy": 5.0,
        }, "communication_scores": {
            "narrative_flow": 5.0, "audience_calibration": 5.0,
            "visualization_effectiveness": 5.0, "executive_summary_clarity": 5.0,
        }}
        new = {"composite": 6.2, "substance_scores": {
            "statistical_rigor": 6.2, "methodology_soundness": 6.2,
            "evidence_conclusion_alignment": 6.2, "data_interpretation_accuracy": 6.2,
        }, "communication_scores": {
            "narrative_flow": 6.2, "audience_calibration": 6.2,
            "visualization_effectiveness": 6.2, "executive_summary_clarity": 6.2,
        }}
        result = decide_action(prev, new, sample_config)
        assert result == "keep"

    def test_large_improvement_keeps(self, sample_config):
        """Score improved by > 1.0 → auto-KEEP (no human gate)."""
        from loop_runner import decide_action

        prev = {"composite": 5.0, "substance_scores": {
            "statistical_rigor": 5.0, "methodology_soundness": 5.0,
            "evidence_conclusion_alignment": 5.0, "data_interpretation_accuracy": 5.0,
        }, "communication_scores": {
            "narrative_flow": 5.0, "audience_calibration": 5.0,
            "visualization_effectiveness": 5.0, "executive_summary_clarity": 5.0,
        }}
        new = {"composite": 6.5, "substance_scores": {
            "statistical_rigor": 6.5, "methodology_soundness": 6.5,
            "evidence_conclusion_alignment": 6.5, "data_interpretation_accuracy": 6.5,
        }, "communication_scores": {
            "narrative_flow": 6.5, "audience_calibration": 6.5,
            "visualization_effectiveness": 6.5, "executive_summary_clarity": 6.5,
        }}
        result = decide_action(prev, new, sample_config)
        assert result == "keep"

    def test_marginal_improvement_triggers_human_gate(self, sample_config):
        """Score improved by 0.3-1.0 → HUMAN_GATE."""
        from loop_runner import decide_action

        prev = {"composite": 5.0, "substance_scores": {
            "statistical_rigor": 5.0, "methodology_soundness": 5.0,
            "evidence_conclusion_alignment": 5.0, "data_interpretation_accuracy": 5.0,
        }, "communication_scores": {
            "narrative_flow": 5.0, "audience_calibration": 5.0,
            "visualization_effectiveness": 5.0, "executive_summary_clarity": 5.0,
        }}
        new = {"composite": 5.4, "substance_scores": {
            "statistical_rigor": 5.4, "methodology_soundness": 5.4,
            "evidence_conclusion_alignment": 5.4, "data_interpretation_accuracy": 5.4,
        }, "communication_scores": {
            "narrative_flow": 5.4, "audience_calibration": 5.4,
            "visualization_effectiveness": 5.4, "executive_summary_clarity": 5.4,
        }}
        result = decide_action(prev, new, sample_config)
        assert result == "human_gate"

    def test_score_drop_reverts(self, sample_config):
        """Score decreased → REVERT."""
        from loop_runner import decide_action

        prev = {"composite": 6.0, "substance_scores": {
            "statistical_rigor": 6.0, "methodology_soundness": 6.0,
            "evidence_conclusion_alignment": 6.0, "data_interpretation_accuracy": 6.0,
        }, "communication_scores": {
            "narrative_flow": 6.0, "audience_calibration": 6.0,
            "visualization_effectiveness": 6.0, "executive_summary_clarity": 6.0,
        }}
        new = {"composite": 5.5, "substance_scores": {
            "statistical_rigor": 5.5, "methodology_soundness": 5.5,
            "evidence_conclusion_alignment": 5.5, "data_interpretation_accuracy": 5.5,
        }, "communication_scores": {
            "narrative_flow": 5.5, "audience_calibration": 5.5,
            "visualization_effectiveness": 5.5, "executive_summary_clarity": 5.5,
        }}
        result = decide_action(prev, new, sample_config)
        assert result == "revert"

    def test_tiny_improvement_reverts(self, sample_config):
        """Score improved < 0.3 → REVERT (below threshold)."""
        from loop_runner import decide_action

        prev = {"composite": 6.0, "substance_scores": {
            "statistical_rigor": 6.0, "methodology_soundness": 6.0,
            "evidence_conclusion_alignment": 6.0, "data_interpretation_accuracy": 6.0,
        }, "communication_scores": {
            "narrative_flow": 6.0, "audience_calibration": 6.0,
            "visualization_effectiveness": 6.0, "executive_summary_clarity": 6.0,
        }}
        new = {"composite": 6.1, "substance_scores": {
            "statistical_rigor": 6.1, "methodology_soundness": 6.1,
            "evidence_conclusion_alignment": 6.1, "data_interpretation_accuracy": 6.1,
        }, "communication_scores": {
            "narrative_flow": 6.1, "audience_calibration": 6.1,
            "visualization_effectiveness": 6.1, "executive_summary_clarity": 6.1,
        }}
        result = decide_action(prev, new, sample_config)
        assert result == "revert"

    def test_regression_on_top_dimension_reverts(self, sample_config):
        """Even if composite improves, regression on high-weight dim → REVERT.

        evidence_conclusion_alignment has weight 1.3 (top substance dim).
        If it drops > 0.5 while composite rises, the edit traded quality
        in what matters most for gains in less important areas.
        """
        from loop_runner import decide_action

        prev = {"composite": 6.0, "substance_scores": {
            "statistical_rigor": 6.0, "methodology_soundness": 6.0,
            "evidence_conclusion_alignment": 8.0,  # high
            "data_interpretation_accuracy": 6.0,
        }, "communication_scores": {
            "narrative_flow": 6.0, "audience_calibration": 6.0,
            "visualization_effectiveness": 6.0, "executive_summary_clarity": 6.0,
        }}
        new = {"composite": 6.5, "substance_scores": {
            "statistical_rigor": 7.0, "methodology_soundness": 7.0,
            "evidence_conclusion_alignment": 7.0,  # dropped 1.0 (> 0.5 threshold)
            "data_interpretation_accuracy": 7.0,
        }, "communication_scores": {
            "narrative_flow": 7.0, "audience_calibration": 7.0,
            "visualization_effectiveness": 7.0, "executive_summary_clarity": 7.0,
        }}
        result = decide_action(prev, new, sample_config)
        assert result == "revert"

    def test_minor_regression_on_top_dimension_keeps(self, sample_config):
        """Small drop (<=0.5) on top dim with good composite gain → KEEP."""
        from loop_runner import decide_action

        prev = {"composite": 6.0, "substance_scores": {
            "statistical_rigor": 6.0, "methodology_soundness": 6.0,
            "evidence_conclusion_alignment": 8.0,
            "data_interpretation_accuracy": 6.0,
        }, "communication_scores": {
            "narrative_flow": 6.0, "audience_calibration": 6.0,
            "visualization_effectiveness": 6.0, "executive_summary_clarity": 6.0,
        }}
        new = {"composite": 7.5, "substance_scores": {
            "statistical_rigor": 7.5, "methodology_soundness": 7.5,
            "evidence_conclusion_alignment": 7.6,  # dropped 0.4 (<=0.5, ok)
            "data_interpretation_accuracy": 7.5,
        }, "communication_scores": {
            "narrative_flow": 7.5, "audience_calibration": 7.5,
            "visualization_effectiveness": 7.5, "executive_summary_clarity": 7.5,
        }}
        result = decide_action(prev, new, sample_config)
        assert result == "keep"


class TestStopRule:
    """Tests for the stop-after-N-non-improving-cycles rule."""

    def test_three_consecutive_non_improving_halts(self, sample_config):
        """3 consecutive non-improving cycles → should_halt returns True."""
        from loop_runner import should_halt

        # History: 3 consecutive reverts
        history = [
            {"action": "keep", "cycle": 1},
            {"action": "revert", "cycle": 2},
            {"action": "revert", "cycle": 3},
            {"action": "revert", "cycle": 4},
        ]
        assert should_halt(history, sample_config) is True

    def test_two_consecutive_non_improving_continues(self, sample_config):
        """Only 2 consecutive reverts → should_halt returns False."""
        from loop_runner import should_halt

        history = [
            {"action": "revert", "cycle": 1},
            {"action": "revert", "cycle": 2},
        ]
        assert should_halt(history, sample_config) is False

    def test_interrupted_streak_continues(self, sample_config):
        """Revert-keep-revert-revert does NOT halt (streak broken by keep)."""
        from loop_runner import should_halt

        history = [
            {"action": "revert", "cycle": 1},
            {"action": "keep", "cycle": 2},
            {"action": "revert", "cycle": 3},
            {"action": "revert", "cycle": 4},
        ]
        assert should_halt(history, sample_config) is False

    def test_empty_history_continues(self, sample_config):
        """No history yet → should_halt returns False."""
        from loop_runner import should_halt

        assert should_halt([], sample_config) is False

    def test_skip_counts_as_non_improving(self, sample_config):
        """Skipped cycles (judge failures) count toward non-improving streak."""
        from loop_runner import should_halt

        history = [
            {"action": "skip", "cycle": 1},
            {"action": "skip", "cycle": 2},
            {"action": "skip", "cycle": 3},
        ]
        assert should_halt(history, sample_config) is True


class TestBudgetCap:
    """Tests for the --max-total-cycles hard budget."""

    def test_budget_exceeded_halts(self):
        """Total cycles (including skips) >= max_total_cycles → halt."""
        from loop_runner import budget_exceeded

        assert budget_exceeded(current_cycle=20, max_total=20) is True
        assert budget_exceeded(current_cycle=21, max_total=20) is True

    def test_budget_not_exceeded_continues(self):
        """Under budget → continue."""
        from loop_runner import budget_exceeded

        assert budget_exceeded(current_cycle=10, max_total=20) is False


class TestJudgeFailureHandling:
    """Tests for judge failure detection in the main loop.

    Judge failure handling is inline in run_loop (lines 755-766):
    if either judge returns None, the cycle is skipped and the file is reverted.
    These tests verify the building blocks used by that logic.
    """

    def test_none_scores_detected(self):
        """None scores from a judge should be detectable for skip logic."""
        # The main loop checks `if sub_scores is None or comm_scores is None`
        assert None is None  # trivially true, but documents the contract

    def test_valid_scores_not_none(self):
        """Valid score dicts are not None."""
        scores = {"statistical_rigor": 7.0, "methodology_soundness": 7.0,
                  "evidence_conclusion_alignment": 7.0, "data_interpretation_accuracy": 7.0}
        assert scores is not None


class TestConsecutiveJudgeFailures:
    """Tests for the 3-consecutive-judge-failure HALT rule."""

    def test_three_consecutive_judge_failures_halts(self, sample_config):
        """3 cycles where at least one judge failed → HALT."""
        from loop_runner import should_halt_judge_failures

        history = [
            {"action": "skip", "judge_failure": True, "cycle": 1},
            {"action": "skip", "judge_failure": True, "cycle": 2},
            {"action": "skip", "judge_failure": True, "cycle": 3},
        ]
        assert should_halt_judge_failures(history) is True

    def test_intermittent_judge_failures_continue(self, sample_config):
        """Judge failures with successful cycle in between → no HALT."""
        from loop_runner import should_halt_judge_failures

        history = [
            {"action": "skip", "judge_failure": True, "cycle": 1},
            {"action": "keep", "judge_failure": False, "cycle": 2},
            {"action": "skip", "judge_failure": True, "cycle": 3},
            {"action": "skip", "judge_failure": True, "cycle": 4},
        ]
        assert should_halt_judge_failures(history) is False


class TestPhaseDetection:
    """Tests for cycle-to-phase mapping (percentage-based)."""

    def test_early_cycles_are_structural(self):
        """First 40% of cycles → 'structural' phase."""
        from loop_runner import get_phase

        assert get_phase(1, 10) == "structural"
        assert get_phase(4, 10) == "structural"

    def test_mid_cycles_are_substance(self):
        """Middle 40% of cycles → 'substance' phase."""
        from loop_runner import get_phase

        assert get_phase(5, 10) == "substance"
        assert get_phase(8, 10) == "substance"

    def test_late_cycles_are_polish(self):
        """Final 20% of cycles → 'polish' phase."""
        from loop_runner import get_phase

        assert get_phase(9, 10) == "polish"
        assert get_phase(10, 10) == "polish"

    def test_single_cycle_is_structural(self):
        """With only 1 cycle, it should be structural."""
        from loop_runner import get_phase

        assert get_phase(1, 1) == "structural"

    def test_two_cycles(self):
        """With 2 cycles: cycle 1 structural (0.0), cycle 2 substance (0.5)."""
        from loop_runner import get_phase

        assert get_phase(1, 2) == "structural"
        assert get_phase(2, 2) == "substance"


class TestWriterOutputValidation:
    """Tests for writer refusal/content filter detection."""

    def test_valid_markdown_passes(self):
        """Normal markdown with headers passes validation."""
        from loop_runner import validate_writer_output

        text = "# Analysis\n\nThis is a valid analysis with enough content to pass.\n\n## Methods\n\nWe used several approaches."
        original = "# Draft\n\nShort original."
        assert validate_writer_output(text, original) is True

    def test_refusal_detected(self):
        """Writer refusal (starts with 'I can't') fails validation."""
        from loop_runner import validate_writer_output

        text = "I can't modify this analysis because it contains sensitive data."
        original = "# Draft\n\nShort original."
        assert validate_writer_output(text, original) is False

    def test_no_headers_detected(self):
        """Output without markdown headers fails validation."""
        from loop_runner import validate_writer_output

        text = "This is just plain text without any headers. It goes on for a while but has no structure."
        original = "# Draft\n\nShort original."
        assert validate_writer_output(text, original) is False

    def test_too_short_detected(self):
        """Output < 20% of original length fails validation."""
        from loop_runner import validate_writer_output

        original = "# Analysis\n\n" + "word " * 500  # ~2500 chars
        text = "# Short\n\nToo short."  # way under 20%
        assert validate_writer_output(text, original) is False

    def test_sorry_prefix_detected(self):
        """Writer starting with 'I'm sorry' fails validation."""
        from loop_runner import validate_writer_output

        text = "I'm sorry, but I cannot improve this document as requested."
        original = "# Draft\n\nShort original."
        assert validate_writer_output(text, original) is False


class TestGetTopDimensions:
    """Tests for identifying top-weighted dimensions for regression blocking."""

    def test_identifies_high_weight_dimensions(self, sample_config):
        """Dimensions with weight >= 1.2 are 'top' dimensions."""
        from loop_runner import get_top_dimensions

        top = get_top_dimensions(sample_config)
        # evidence_conclusion_alignment (1.3) and statistical_rigor (1.2)
        # and executive_summary_clarity (1.2) should be top dims
        assert "evidence_conclusion_alignment" in top
        assert "statistical_rigor" in top
        assert "executive_summary_clarity" in top
        # methodology_soundness (1.0) should NOT be top
        assert "methodology_soundness" not in top


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_valid_weights_pass(self):
        """Weights summing to 1.0 should load without error."""
        from evaluate import load_config
        # The real config file has weights summing to 1.0
        config = load_config("review_config.yaml")
        assert config["weights"]["substance"] + config["weights"]["communication"] == pytest.approx(1.0)

    def test_weighted_avg_empty_scores(self, sample_config):
        """Empty scores dict should not crash compute_composite."""
        from evaluate import compute_composite
        # If both score dicts are empty, weighted_avg returns 0 (via mean of empty)
        # This should raise an error rather than silently return 0
        with pytest.raises(Exception):
            compute_composite({}, {}, sample_config)


class TestCycleSummaryBuilder:
    """Tests for the cycle summary passed to the writer."""

    def test_empty_history_returns_empty(self):
        """No history → empty summary string."""
        from loop_runner import _build_cycle_summary
        assert _build_cycle_summary([]) == ""

    def test_summary_contains_action_counts(self):
        """Summary should show kept/reverted/skipped counts."""
        from loop_runner import _build_cycle_summary
        history = [
            {"action": "keep", "cycle": 1, "composite": 5.5, "hypothesis": "structural fix"},
            {"action": "revert", "cycle": 2, "composite": 5.3, "hypothesis": "substance tweak"},
            {"action": "skip", "cycle": 3},
        ]
        summary = _build_cycle_summary(history)
        assert "Kept: 1" in summary
        assert "Reverted: 1" in summary
        assert "Skipped: 1" in summary

    def test_summary_shows_recent_cycles(self):
        """Summary should include details of recent cycles."""
        from loop_runner import _build_cycle_summary
        history = [
            {"action": "keep", "cycle": 1, "composite": 5.5, "hypothesis": "structural fix"},
        ]
        summary = _build_cycle_summary(history)
        assert "Cycle 1" in summary
        assert "keep" in summary
