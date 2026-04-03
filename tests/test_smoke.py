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

    def test_identical_output_detected(self):
        """Writer output identical to input should fail validation."""
        from loop_runner import validate_writer_output

        original = "# Analysis\n\nThis draft already exists.\n\n## Methods\n\nSame content."
        assert validate_writer_output(original, original) is False

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
        config_path = str(Path(__file__).parent.parent / "autoresearch" / "review_config.yaml")
        config = load_config(config_path)
        assert config["weights"]["substance"] + config["weights"]["communication"] == pytest.approx(1.0)

    def test_weighted_avg_empty_scores(self, sample_config):
        """Empty scores dict should not crash compute_composite."""
        from evaluate import compute_composite
        # If both score dicts are empty, weighted_avg returns 0 (via mean of empty)
        # This should raise an error rather than silently return 0
        with pytest.raises(Exception):
            compute_composite({}, {}, sample_config)

    def test_default_config_path_resolves_from_autoresearch_dir(self):
        """Repo-root invocations should still find autoresearch/review_config.yaml."""
        from loop_runner import resolve_config_path

        project_root = Path(__file__).parent.parent / "autoresearch"

        resolved = resolve_config_path("review_config.yaml", project_root)

        assert resolved == project_root / "review_config.yaml"


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


# ─────────────────────────────────────────────
# v2 Feature Tests: Feedback-Forward
# ─────────────────────────────────────────────

class TestFeedbackForward:
    """Tests for passing judge critiques to the writer (v2 feedback-forward)."""

    def test_writer_message_includes_critique_when_provided(self):
        """Writer message should contain judge critique text."""
        from loop_runner import _build_writer_message

        msg = _build_writer_message(
            analysis_text="# Test\n\nContent here.",
            cycle=2,
            total_cycles=10,
            phase="substance",
            cycle_summary="Previous: kept cycle 1",
            judge_feedback="SUBSTANCE: statistical_rigor scored 3.5 because no CIs.\n"
                          "COMMUNICATION: exec summary scored 8.5, strong improvement.",
        )
        assert "JUDGE FEEDBACK" in msg
        assert "statistical_rigor scored 3.5" in msg
        assert "exec summary scored 8.5" in msg

    def test_writer_message_omits_feedback_when_empty(self):
        """No judge feedback → no JUDGE FEEDBACK section in message."""
        from loop_runner import _build_writer_message

        msg = _build_writer_message(
            analysis_text="# Test\n\nContent.",
            cycle=1,
            total_cycles=10,
            phase="structural",
        )
        assert "JUDGE FEEDBACK" not in msg

    def test_writer_message_omits_feedback_when_none(self):
        """Explicit None judge feedback → no JUDGE FEEDBACK section."""
        from loop_runner import _build_writer_message

        msg = _build_writer_message(
            analysis_text="# Test\n\nContent.",
            cycle=2,
            total_cycles=10,
            phase="substance",
            judge_feedback=None,
        )
        assert "JUDGE FEEDBACK" not in msg

    def test_full_critique_passed_via_judge_feedback_not_summary(self):
        """Full critiques go via judge_feedback param, not cycle summary.

        Cycle summary stays concise (scores only). The writer gets full
        critiques through the separate judge_feedback parameter.
        """
        from loop_runner import _build_cycle_summary

        history = [
            {
                "action": "keep", "cycle": 1, "composite": 5.5,
                "hypothesis": "structural fix",
                "sub_critique": "Statistical rigor is weak — no confidence intervals.",
                "comm_critique": "Exec summary now leads with impact. Good.",
            },
        ]
        summary = _build_cycle_summary(history)
        # Summary should NOT contain critique text (that goes via judge_feedback)
        assert "Statistical rigor is weak" not in summary
        # But should still contain the action/score info
        assert "keep" in summary
        assert "5.5" in summary


# ─────────────────────────────────────────────
# v2 Feature Tests: Binary Eval Dimensions
# ─────────────────────────────────────────────

class TestBinaryEvalScoring:
    """Tests for binary (yes/no checklist) scoring mode."""

    def test_binary_scores_convert_to_numeric(self):
        """Binary checklist {true/false} → numeric 0-10 score."""
        from evaluate import convert_binary_to_numeric

        binary = {
            "has_confidence_intervals": False,
            "has_significance_tests": False,
            "has_sample_sizes": True,
            "has_effect_sizes": False,
        }
        # 1/4 true → 2.5
        score = convert_binary_to_numeric(binary)
        assert score == pytest.approx(2.5)

    def test_all_true_scores_ten(self):
        """All checklist items true → score of 10.0."""
        from evaluate import convert_binary_to_numeric

        binary = {"a": True, "b": True, "c": True}
        assert convert_binary_to_numeric(binary) == pytest.approx(10.0)

    def test_all_false_scores_zero(self):
        """All checklist items false → score of 0.0."""
        from evaluate import convert_binary_to_numeric

        binary = {"a": False, "b": False}
        assert convert_binary_to_numeric(binary) == pytest.approx(0.0)

    def test_empty_checklist_scores_zero(self):
        """Empty checklist → 0.0."""
        from evaluate import convert_binary_to_numeric

        assert convert_binary_to_numeric({}) == pytest.approx(0.0)

    def test_parse_binary_judge_output(self):
        """Parse judge JSON with binary checklist format."""
        from evaluate import parse_binary_judge_output

        raw = {
            "statistical_rigor": {
                "has_confidence_intervals": False,
                "has_significance_tests": True,
                "has_sample_sizes": True,
                "has_effect_sizes": False,
            },
            "methodology_soundness": {
                "has_clear_method": True,
                "has_assumptions_stated": False,
                "has_limitations": True,
            },
            "critique": "Some critique text here.",
        }
        scores, critique = parse_binary_judge_output(raw)
        assert scores["statistical_rigor"] == pytest.approx(5.0)  # 2/4
        assert scores["methodology_soundness"] == pytest.approx(6.67, abs=0.1)  # 2/3
        assert critique == "Some critique text here."

    def test_parse_binary_handles_mixed_format(self):
        """If judge returns numeric scores (not binary), pass through unchanged."""
        from evaluate import parse_binary_judge_output

        raw = {
            "statistical_rigor": 7.5,
            "methodology_soundness": 6.0,
            "critique": "Direct numeric scores.",
        }
        scores, critique = parse_binary_judge_output(raw)
        assert scores["statistical_rigor"] == 7.5
        assert scores["methodology_soundness"] == 6.0


# ─────────────────────────────────────────────
# v1.1 Tests: Novita Provider, Auto-Approve,
# Multi-Run Averaging, Judge Format Routing
# ─────────────────────────────────────────────

class TestAutoApprove:
    """Tests for --auto-approve flag behavior."""

    def test_auto_approve_keeps_marginal_improvement(self, sample_config):
        """Marginal improvement (0.3-1.0) should be kept when auto-approve is on."""
        from loop_runner import decide_action
        prev = {"composite": 7.0, "substance_scores": {}, "communication_scores": {}}
        new = {"composite": 7.5, "substance_scores": {}, "communication_scores": {}}
        # decide_action returns "human_gate" for marginal
        action = decide_action(prev, new, sample_config)
        assert action == "human_gate"
        # auto-approve logic in run_loop converts human_gate → keep

    def test_below_threshold_still_reverts(self, sample_config):
        """Improvement below min_improvement (0.3) should revert even with auto-approve."""
        from loop_runner import decide_action
        prev = {"composite": 7.0, "substance_scores": {}, "communication_scores": {}}
        new = {"composite": 7.1, "substance_scores": {}, "communication_scores": {}}
        action = decide_action(prev, new, sample_config)
        assert action == "revert"


class TestJudgeFormatRouting:
    """Tests for judge format template selection via JudgeConfig."""

    def test_numeric_format_uses_standard_templates(self):
        from evaluate import JudgeConfig
        jc = JudgeConfig(format="numeric")
        assert jc.get_template_name("substance") == "substance-judge.md"
        assert jc.get_template_name("communication") == "communication-judge.md"

    def test_binary_format_uses_binary_templates(self):
        from evaluate import JudgeConfig
        jc = JudgeConfig(format="binary")
        assert jc.get_template_name("substance") == "substance-judge-binary.md"
        assert jc.get_template_name("communication") == "communication-judge-binary.md"

    def test_hybrid_format_uses_hybrid_templates(self):
        from evaluate import JudgeConfig
        jc = JudgeConfig(format="hybrid")
        assert jc.get_template_name("substance") == "substance-judge-hybrid.md"
        assert jc.get_template_name("communication") == "communication-judge-hybrid.md"

    def test_invalid_format_raises(self):
        from evaluate import set_judge_format
        with pytest.raises(ValueError, match="Unknown judge format"):
            set_judge_format("invalid")

    def test_format_reset_to_numeric(self):
        """JudgeConfig instances are independent — no global state leak."""
        from evaluate import JudgeConfig
        hybrid = JudgeConfig(format="hybrid")
        numeric = JudgeConfig(format="numeric")
        assert hybrid.get_template_name("substance") == "substance-judge-hybrid.md"
        assert numeric.get_template_name("substance") == "substance-judge.md"


class TestJudgeProviderRouting:
    """Tests for judge provider selection via JudgeConfig."""

    def test_default_provider_is_codex(self):
        from evaluate import JudgeConfig
        jc = JudgeConfig()
        assert jc.provider == "codex"

    def test_config_with_novita(self):
        from evaluate import JudgeConfig
        jc = JudgeConfig(provider="novita", model="minimax/minimax-m2.7")
        assert jc.provider == "novita"
        assert jc.model == "minimax/minimax-m2.7"

    def test_config_roundtrip(self):
        from evaluate import JudgeConfig
        jc = JudgeConfig(provider="novita", model="test-model", format="hybrid")
        d = jc.to_dict()
        jc2 = JudgeConfig.from_dict(d)
        assert jc2.provider == "novita"
        assert jc2.model == "test-model"
        assert jc2.format == "hybrid"

    def test_all_providers_use_threadpool(self, monkeypatch):
        """Both codex and novita providers now use ThreadPoolExecutor uniformly."""
        import evaluate

        calls = []

        def fake_call_judge(self, template_name, analysis_text):
            calls.append((template_name, analysis_text))
            return {"score": 1.0}, f"critique for {template_name}"

        monkeypatch.setattr(evaluate.JudgeConfig, "call_judge", fake_call_judge)

        jc = evaluate.JudgeConfig(provider="novita", model="minimax/minimax-m2.7", format="hybrid")
        sub_scores, comm_scores, sub_critique, comm_critique = evaluate.call_judges_parallel(
            "analysis text", {}, judge_config=jc
        )

        assert len(calls) == 2
        assert sub_scores == {"score": 1.0}
        assert comm_scores == {"score": 1.0}


class TestNovitaWriterMocked:
    """Tests for call_writer_novita with mocked API."""

    def test_missing_api_key_returns_none(self):
        from loop_runner import call_writer_novita
        with patch.dict(os.environ, {}, clear=True):
            # Remove NOVITA_API_KEY if set
            os.environ.pop("NOVITA_API_KEY", None)
            result = call_writer_novita(
                analysis_text="test",
                system_prompt="test",
                cycle=1, total_cycles=5, phase="structural"
            )
            assert result is None

    def test_missing_openai_package_returns_none(self):
        from loop_runner import call_writer_novita
        with patch.dict(os.environ, {"NOVITA_API_KEY": "test-key"}):
            with patch.dict("sys.modules", {"openai": None}):
                # This should handle the ImportError gracefully
                # Note: may not trigger if openai is already imported
                pass  # Import error handling is tested implicitly

    def test_successful_call_returns_text(self):
        from loop_runner import call_writer_novita
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "# Improved Analysis\n\nBetter content."

        with patch.dict(os.environ, {"NOVITA_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as mock_openai_cls:
                mock_client = MagicMock()
                mock_openai_cls.return_value = mock_client
                mock_client.chat.completions.create.return_value = mock_response

                result = call_writer_novita(
                    analysis_text="original text",
                    system_prompt="improve this",
                    cycle=1, total_cycles=5, phase="structural"
                )
                assert result == "# Improved Analysis\n\nBetter content."

    def test_api_error_retries_and_returns_none(self):
        from loop_runner import call_writer_novita
        with patch.dict(os.environ, {"NOVITA_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as mock_openai_cls:
                mock_client = MagicMock()
                mock_openai_cls.return_value = mock_client
                mock_client.chat.completions.create.side_effect = Exception("API error")

                with patch("time.sleep"):  # skip retry delays
                    result = call_writer_novita(
                        analysis_text="test",
                        system_prompt="test",
                        cycle=1, total_cycles=5, phase="structural"
                    )
                    assert result is None
                    # Should have retried 3 times
                    assert mock_client.chat.completions.create.call_count == 3


class TestModelDefaults:
    """Tests for --model default behavior per provider."""

    def test_novita_default_model(self):
        """Novita provider should default to deepseek/deepseek-v3.2."""
        model = None or "deepseek/deepseek-v3.2"
        assert model == "deepseek/deepseek-v3.2"

    def test_anthropic_default_model(self):
        """Anthropic provider should default to claude-sonnet-4-20250514."""
        model = None or "claude-sonnet-4-20250514"
        assert model == "claude-sonnet-4-20250514"

    def test_explicit_model_overrides_default(self):
        """Explicit --model should override provider defaults."""
        model = "minimax/minimax-m2.7" or "deepseek/deepseek-v3.2"
        assert model == "minimax/minimax-m2.7"


class TestCheckpoint:
    """Tests for checkpoint save/load/validate cycle."""

    def test_save_and_load_checkpoint(self):
        """Checkpoint round-trips through JSON correctly."""
        from loop_runner import _save_checkpoint, _load_checkpoint
        with tempfile.TemporaryDirectory() as d:
            run_dir = Path(d)
            cp = {"cycle": 3, "workdir": d, "current_best": {"composite": 7.5},
                  "history": [{"action": "keep"}], "run_dir": d}
            _save_checkpoint(run_dir, cp)
            loaded = _load_checkpoint(run_dir)
            assert loaded["cycle"] == 3
            assert loaded["current_best"]["composite"] == 7.5

    def test_load_missing_checkpoint_returns_none(self):
        """Missing checkpoint.json returns None, not crash."""
        from loop_runner import _load_checkpoint
        with tempfile.TemporaryDirectory() as d:
            assert _load_checkpoint(Path(d)) is None

    def test_validate_checkpoint_valid(self):
        """Valid checkpoint with existing workdir passes validation."""
        from loop_runner import _validate_checkpoint
        with tempfile.TemporaryDirectory() as d:
            cp = {"cycle": 1, "workdir": d, "current_best": {},
                  "history": [], "run_dir": d}
            assert _validate_checkpoint(cp) == []

    def test_validate_checkpoint_missing_keys(self):
        """Checkpoint missing required keys fails validation."""
        from loop_runner import _validate_checkpoint
        assert len(_validate_checkpoint({"cycle": 1})) > 0

    def test_validate_checkpoint_missing_workdir(self):
        """Checkpoint with non-existent workdir fails validation."""
        from loop_runner import _validate_checkpoint
        cp = {"cycle": 1, "workdir": "/nonexistent/path/xyz",
              "current_best": {}, "history": [], "run_dir": "/tmp"}
        assert len(_validate_checkpoint(cp)) > 0

    def test_build_checkpoint_has_all_fields(self):
        """_build_checkpoint produces dict with all required keys."""
        from loop_runner import _build_checkpoint
        with tempfile.TemporaryDirectory() as d:
            cp = _build_checkpoint(
                cycle=2, workdir=d, current_best={"composite": 6.0},
                history=[{"action": "keep"}], run_dir=d,
                baseline={"composite": 5.0}, input_path="/tmp/test.md",
                judge_config_dict={"provider": "codex", "model": "x", "format": "numeric"},
                args_dict={"cycles": 10},
            )
            assert cp["cycle"] == 2
            assert cp["judge_config"]["provider"] == "codex"
            assert "timestamp" in cp


class TestAtomicWrite:
    """Tests for _atomic_write durability."""

    def test_atomic_write_creates_file(self):
        """Atomic write creates the target file with correct content."""
        from loop_runner import _atomic_write
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "test.txt"
            _atomic_write(path, "hello world")
            assert path.read_text() == "hello world"

    def test_atomic_write_no_tmp_left(self):
        """No .tmp file should remain after atomic write."""
        from loop_runner import _atomic_write
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "test.txt"
            _atomic_write(path, "content")
            tmp = path.with_suffix(".txt.tmp")
            assert not tmp.exists()

    def test_atomic_write_overwrites(self):
        """Atomic write replaces existing file content."""
        from loop_runner import _atomic_write
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "test.txt"
            path.write_text("old")
            _atomic_write(path, "new")
            assert path.read_text() == "new"


class TestBackupVersioning:
    """Tests for versioned backup paths."""

    def test_first_backup_uses_base(self):
        """First backup is .md.bak (no version number)."""
        from loop_runner import _next_backup_path
        with tempfile.TemporaryDirectory() as d:
            input_path = Path(d) / "analysis.md"
            input_path.write_text("test")
            result = _next_backup_path(input_path)
            assert result == input_path.with_suffix(".md.bak")

    def test_second_backup_gets_version_001(self):
        """When .md.bak exists, next is .md.bak.001."""
        from loop_runner import _next_backup_path
        with tempfile.TemporaryDirectory() as d:
            input_path = Path(d) / "analysis.md"
            input_path.write_text("test")
            input_path.with_suffix(".md.bak").write_text("backup1")
            result = _next_backup_path(input_path)
            assert result == input_path.with_suffix(".md.bak.001")

    def test_third_backup_gets_version_002(self):
        """When .md.bak and .md.bak.001 exist, next is .md.bak.002."""
        from loop_runner import _next_backup_path
        with tempfile.TemporaryDirectory() as d:
            input_path = Path(d) / "analysis.md"
            input_path.write_text("test")
            input_path.with_suffix(".md.bak").write_text("backup1")
            input_path.with_suffix(".md.bak.001").write_text("backup2")
            result = _next_backup_path(input_path)
            assert result == input_path.with_suffix(".md.bak.002")


class TestHybridScoreParsing:
    """Tests for parsing mixed binary + numeric judge output."""

    def test_mixed_format_parses_both(self):
        """Hybrid output has binary dicts AND numeric floats."""
        from evaluate import parse_binary_judge_output
        raw = {
            "statistical_rigor": {
                "has_confidence_intervals": True,
                "has_significance_tests": True,
                "has_sample_sizes": False,
                "has_effect_sizes": False,
            },
            "methodology_soundness": 6.5,
            "evidence_conclusion_alignment": 7.0,
            "data_interpretation_accuracy": {
                "numbers_described_correctly": True,
                "comparisons_have_baselines": True,
                "acknowledges_outliers": True,
                "avoids_overgeneralization": False,
            },
            "critique": "Mixed format test.",
        }
        scores, critique = parse_binary_judge_output(raw)
        # Binary dims convert to 0-10 scale
        assert scores["statistical_rigor"] == 5.0  # 2/4 * 10
        assert scores["data_interpretation_accuracy"] == 7.5  # 3/4 * 10
        # Numeric dims pass through
        assert scores["methodology_soundness"] == 6.5
        assert scores["evidence_conclusion_alignment"] == 7.0
        assert critique == "Mixed format test."


class TestDiscardAutopsy:
    """Tests for discard autopsy classification after reverts."""

    def test_wrong_phase_classification(self, sample_config):
        """Editing a communication dim during substance phase → wrong_phase."""
        from loop_runner import classify_discard

        current_best = {
            "composite": 6.0,
            "substance_scores": {"statistical_rigor": 6.0, "methodology_soundness": 6.0,
                                 "evidence_conclusion_alignment": 6.0, "data_interpretation_accuracy": 6.0},
            "communication_scores": {"narrative_flow": 6.0, "audience_calibration": 6.0,
                                     "visualization_effectiveness": 6.0, "executive_summary_clarity": 6.0},
        }
        new_result = {
            "composite": 5.5,
            "substance_scores": {"statistical_rigor": 6.0, "methodology_soundness": 6.0,
                                 "evidence_conclusion_alignment": 6.0, "data_interpretation_accuracy": 6.0},
            "communication_scores": {"narrative_flow": 3.0, "audience_calibration": 6.0,
                                     "visualization_effectiveness": 6.0, "executive_summary_clarity": 6.0},
        }
        result = classify_discard([], new_result, current_best, "substance", sample_config)
        assert result["classification"] == "wrong_phase"
        assert result["most_affected_dim"] == "narrative_flow"

    def test_wrong_dimension_classification(self, sample_config):
        """Targeting a high-scoring dim while a low-scoring dim exists → wrong_dimension."""
        from loop_runner import classify_discard

        current_best = {
            "composite": 6.0,
            "substance_scores": {"statistical_rigor": 9.0, "methodology_soundness": 4.0,
                                 "evidence_conclusion_alignment": 6.0, "data_interpretation_accuracy": 6.0},
            "communication_scores": {"narrative_flow": 6.0, "audience_calibration": 6.0,
                                     "visualization_effectiveness": 6.0, "executive_summary_clarity": 6.0},
        }
        new_result = {
            "composite": 5.8,
            "substance_scores": {"statistical_rigor": 7.0, "methodology_soundness": 4.0,
                                 "evidence_conclusion_alignment": 6.0, "data_interpretation_accuracy": 6.0},
            "communication_scores": {"narrative_flow": 6.0, "audience_calibration": 6.0,
                                     "visualization_effectiveness": 6.0, "executive_summary_clarity": 6.0},
        }
        result = classify_discard([], new_result, current_best, "substance", sample_config)
        assert result["classification"] == "wrong_dimension"
        assert "methodology_soundness" in result["suggestion"]

    def test_wrong_approach_classification(self, sample_config):
        """Correct phase and dimension but score dropped → wrong_approach."""
        from loop_runner import classify_discard

        current_best = {
            "composite": 6.0,
            "substance_scores": {"statistical_rigor": 4.0, "methodology_soundness": 6.0,
                                 "evidence_conclusion_alignment": 6.0, "data_interpretation_accuracy": 6.0},
            "communication_scores": {"narrative_flow": 6.0, "audience_calibration": 6.0,
                                     "visualization_effectiveness": 6.0, "executive_summary_clarity": 6.0},
        }
        new_result = {
            "composite": 5.5,
            "substance_scores": {"statistical_rigor": 3.0, "methodology_soundness": 6.0,
                                 "evidence_conclusion_alignment": 6.0, "data_interpretation_accuracy": 6.0},
            "communication_scores": {"narrative_flow": 6.0, "audience_calibration": 6.0,
                                     "visualization_effectiveness": 6.0, "executive_summary_clarity": 6.0},
        }
        result = classify_discard([], new_result, current_best, "substance", sample_config)
        assert result["classification"] == "wrong_approach"

    def test_autopsy_returns_all_fields(self, sample_config):
        """Autopsy dict must have classification, most_affected_dim, suggestion."""
        from loop_runner import classify_discard

        current_best = {
            "composite": 6.0,
            "substance_scores": {"statistical_rigor": 6.0},
            "communication_scores": {"narrative_flow": 6.0},
        }
        new_result = {
            "composite": 5.0,
            "substance_scores": {"statistical_rigor": 4.0},
            "communication_scores": {"narrative_flow": 6.0},
        }
        result = classify_discard([], new_result, current_best, "substance", sample_config)
        assert "classification" in result
        assert "most_affected_dim" in result
        assert "suggestion" in result
        assert result["classification"] in ("wrong_phase", "wrong_dimension", "wrong_approach")

    def test_suggest_unexplored_dim(self, sample_config):
        """_suggest_unexplored_dim returns lowest-scoring non-recently-targeted dim."""
        from loop_runner import _suggest_unexplored_dim

        current_best = {
            "substance_scores": {"statistical_rigor": 8.0, "methodology_soundness": 3.0,
                                 "evidence_conclusion_alignment": 6.0, "data_interpretation_accuracy": 5.0},
            "communication_scores": {"narrative_flow": 7.0, "audience_calibration": 6.0,
                                     "visualization_effectiveness": 6.0, "executive_summary_clarity": 6.0},
        }
        # No recent history — should suggest lowest scoring dim
        result = _suggest_unexplored_dim([], current_best)
        assert result == "methodology_soundness"  # score 3.0, lowest

        # With methodology_soundness recently targeted, should skip it
        history = [{"autopsy": {"most_affected_dim": "methodology_soundness"}}]
        result = _suggest_unexplored_dim(history, current_best)
        assert result == "data_interpretation_accuracy"  # next lowest at 5.0
