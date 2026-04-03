#!/usr/bin/env python3
"""
test_brainstorm_skill.py — Structural tests for brainstorm skill files.

Tests that skill markdown files contain required sections, fields, and
cross-file consistency. No LLM calls needed — these verify the skill
"contract" that persona prompts and orchestrator instructions define.

Run: python -m pytest tests/test_brainstorm_skill.py -v
"""

import json
from pathlib import Path

import pytest

# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

BRAINSTORM_DIR = Path(__file__).parent.parent / "brainstorm" / "skill"


@pytest.fixture
def dispatch_template():
    """Load the dispatch prompt template."""
    return (BRAINSTORM_DIR / "prompts" / "build_debate_query.md").read_text()


@pytest.fixture
def skill_md():
    """Load the main SKILL.md orchestrator."""
    return (BRAINSTORM_DIR / "SKILL.md").read_text()


@pytest.fixture
def methodology_critic():
    """Load methodology critic persona."""
    return (BRAINSTORM_DIR / "references" / "methodology-critic.md").read_text()


@pytest.fixture
def stakeholder_advocate():
    """Load stakeholder advocate persona."""
    return (BRAINSTORM_DIR / "references" / "stakeholder-advocate.md").read_text()


@pytest.fixture
def pragmatist():
    """Load pragmatist persona."""
    return (BRAINSTORM_DIR / "references" / "pragmatist.md").read_text()


@pytest.fixture
def search_grounding():
    """Load search grounding reference."""
    return (BRAINSTORM_DIR / "references" / "search-grounding.md").read_text()


@pytest.fixture
def evals_json():
    """Load eval definitions."""
    return json.loads((BRAINSTORM_DIR / "evals" / "evals.json").read_text())


@pytest.fixture(params=["methodology-critic.md", "stakeholder-advocate.md", "pragmatist.md"])
def persona_file(request):
    """Parameterized fixture: each persona file."""
    path = BRAINSTORM_DIR / "references" / request.param
    return request.param, path.read_text()


# ─────────────────────────────────────────────
# Fix A: Grounding Step (Step 2.5)
# ─────────────────────────────────────────────

class TestGroundingStep:
    """Verify the 'state understanding before hypothesizing' step exists."""

    def test_dispatch_template_has_grounding_step(self, dispatch_template):
        """Dispatch template must include Step 2.5 grounding."""
        assert "Ground Your Understanding" in dispatch_template
        assert "system_understanding" in dispatch_template

    def test_dispatch_template_has_never_hypothesize_rule(self, dispatch_template):
        """Must prohibit hypothesizing about unnamed components."""
        assert "NEVER hypothesize" in dispatch_template

    def test_dispatch_template_has_ground_before_challenging_rule(self, dispatch_template):
        """Critical rule 8: ground before challenging."""
        assert "Ground before challenging" in dispatch_template

    def test_system_understanding_in_base_output_schema(self, dispatch_template):
        """system_understanding must appear in the base output JSON schema."""
        assert '"system_understanding"' in dispatch_template
        assert '"components"' in dispatch_template
        assert '"boundaries"' in dispatch_template
        assert '"unknowns"' in dispatch_template

    def test_system_understanding_in_persona_output(self, persona_file):
        """Each persona's Output Format must include system_understanding."""
        name, content = persona_file
        assert "system_understanding" in content, (
            f"{name} Output Format section is missing system_understanding field"
        )


# ─────────────────────────────────────────────
# Improvement #1: Divergence Anchors
# ─────────────────────────────────────────────

class TestDivergenceAnchors:
    """Verify mandatory first actions and convergence prevention."""

    def test_persona_has_mandatory_first_actions(self, persona_file):
        """Each persona must have MANDATORY FIRST ACTIONS section."""
        name, content = persona_file
        assert "MANDATORY FIRST ACTIONS" in content, (
            f"{name} is missing MANDATORY FIRST ACTIONS section"
        )

    def test_persona_has_prohibited_convergence(self, persona_file):
        """Each persona must have PROHIBITED CONVERGENCE section."""
        name, content = persona_file
        assert "PROHIBITED CONVERGENCE" in content, (
            f"{name} is missing PROHIBITED CONVERGENCE section"
        )

    def test_persona_declares_uncertainty_type(self, persona_file):
        """Each persona must declare its owned uncertainty type."""
        name, content = persona_file
        assert "uncertainty" in content.lower(), (
            f"{name} doesn't declare its uncertainty type"
        )

    def test_uncertainty_types_are_distinct(self, methodology_critic, stakeholder_advocate, pragmatist):
        """Each persona must own a DIFFERENT type of uncertainty."""
        assert "statistical uncertainty" in methodology_critic
        assert "value uncertainty" in stakeholder_advocate
        assert "feasibility uncertainty" in pragmatist

    def test_dispatch_template_references_mandatory_actions(self, dispatch_template):
        """Dispatch template Step 3 must reference MANDATORY FIRST ACTIONS."""
        assert "MANDATORY FIRST ACTIONS" in dispatch_template

    def test_dispatch_template_has_stay_in_lane_rule(self, dispatch_template):
        """Critical rule 9: stay in your lane."""
        assert "Stay in your lane" in dispatch_template

    def test_convergence_rules_use_binary_test(self, persona_file):
        """Convergence rules should use a clear test, not vague percentages."""
        name, content = persona_file
        # Should reference drifting into specific other personas' lanes
        assert "drifting into" in content or "STOP and refocus" in content, (
            f"{name} PROHIBITED CONVERGENCE lacks actionable lane test"
        )


# ─────────────────────────────────────────────
# Fix B1: --knowledge-dir
# ─────────────────────────────────────────────

class TestKnowledgeDir:
    """Verify --knowledge-dir flag and loading logic."""

    def test_skill_md_has_knowledge_dir_flag(self, skill_md):
        """SKILL.md parameter table must include --knowledge-dir."""
        assert "--knowledge-dir" in skill_md

    def test_skill_md_has_step_0_2b(self, skill_md):
        """SKILL.md must have Step 0.2b for external knowledge loading."""
        assert "Step 0.2b" in skill_md
        assert "External Knowledge Directory" in skill_md

    def test_evidence_block_has_external_knowledge_section(self, skill_md):
        """Evidence block template must include External Domain Knowledge section."""
        assert "External Domain Knowledge" in skill_md

    def test_knowledge_dir_handles_missing_dir(self, skill_md):
        """Step 0.2b must handle missing directory gracefully."""
        assert "No knowledge files found" in skill_md or "not found" in skill_md.lower()

    def test_knowledge_dir_handles_md_files(self, skill_md):
        """Step 0.2b must describe handling for .md files, not just .yaml."""
        # Both file types should be mentioned in the glob
        assert "*.yaml" in skill_md
        assert "*.md" in skill_md


# ─────────────────────────────────────────────
# Fix B2: Confluence Placeholder
# ─────────────────────────────────────────────

class TestConfluencePlaceholder:
    """Verify Confluence search integration placeholder."""

    def test_skill_md_has_confluence_step(self, skill_md):
        """SKILL.md must have Step 0.3b for Confluence search."""
        assert "Step 0.3b" in skill_md
        assert "Confluence" in skill_md

    def test_confluence_skips_silently_when_unavailable(self, skill_md):
        """Must skip silently when MCP not available, not warn user."""
        assert "skip silently" in skill_md.lower()

    def test_confluence_above_web_search_in_evidence_block(self, skill_md):
        """Confluence results must appear BEFORE web search results in evidence block."""
        confluence_pos = skill_md.find("Confluence Context")
        domain_context_pos = skill_md.find("### Domain Context")
        # Find the evidence block section's Domain Context (web search results)
        # Confluence should come before it in the evidence block template
        assert confluence_pos > 0, "Confluence Context section missing from evidence block"

    def test_search_grounding_has_confluence_section(self, search_grounding):
        """search-grounding.md must have Confluence search strategy."""
        assert "Confluence" in search_grounding
        assert "ABOVE web search" in search_grounding

    def test_confluence_detects_mcp_tool(self, skill_md):
        """Must check for mcp__atlassian__search_confluence tool."""
        assert "mcp__atlassian" in skill_md or "Atlassian MCP" in skill_md


# ─────────────────────────────────────────────
# Improvement #3: Context Trimming
# ─────────────────────────────────────────────

class TestContextTrimming:
    """Verify context trimming between Phase 2 and Phase 3."""

    def test_skill_md_has_context_trimming_step(self, skill_md):
        """SKILL.md must have Step 2.6 for context trimming."""
        assert "Step 2.6" in skill_md
        assert "Context Trimming" in skill_md or "context trim" in skill_md.lower()

    def test_context_trimming_specifies_what_to_keep(self, skill_md):
        """Trimming step must specify what to reference in Phase 3."""
        assert "persona" in skill_md.lower() and "JSON" in skill_md


# ─────────────────────────────────────────────
# HIGH #2: Inline Prompt Sync
# ─────────────────────────────────────────────

class TestInlinePromptSync:
    """Verify SKILL.md inline dispatch prompts reference new instructions."""

    def test_inline_prompts_reference_grounding(self, skill_md):
        """Inline dispatch prompts must mention grounding / system understanding."""
        # Find the inline prompt section (Step 1.1)
        step_1_1_start = skill_md.find("Step 1.1")
        assert step_1_1_start > 0
        # The inline prompts section should reference grounding
        inline_section = skill_md[step_1_1_start:step_1_1_start + 3000]
        assert "Ground" in inline_section or "system_understanding" in inline_section or "Step 2.5" in inline_section, (
            "SKILL.md inline dispatch prompts don't reference grounding step"
        )

    def test_inline_prompts_reference_mandatory_actions(self, skill_md):
        """Inline dispatch prompts must mention MANDATORY FIRST ACTIONS."""
        step_1_1_start = skill_md.find("Step 1.1")
        inline_section = skill_md[step_1_1_start:step_1_1_start + 3000]
        assert "MANDATORY FIRST ACTIONS" in inline_section or "mandatory" in inline_section.lower(), (
            "SKILL.md inline dispatch prompts don't reference MANDATORY FIRST ACTIONS"
        )

    def test_inline_prompts_reference_convergence(self, skill_md):
        """Inline dispatch prompts must mention PROHIBITED CONVERGENCE."""
        step_1_1_start = skill_md.find("Step 1.1")
        inline_section = skill_md[step_1_1_start:step_1_1_start + 3000]
        assert "CONVERGENCE" in inline_section or "convergence" in inline_section or "stay in your lane" in inline_section.lower(), (
            "SKILL.md inline dispatch prompts don't reference PROHIBITED CONVERGENCE"
        )


# ─────────────────────────────────────────────
# HIGH #3: Eval Coverage
# ─────────────────────────────────────────────

class TestEvalCoverage:
    """Verify evals test new functionality."""

    def test_eval_001_checks_system_understanding(self, evals_json):
        """eval-001 structural checks must require system_understanding."""
        eval_001 = evals_json["test_cases"][0]
        required = eval_001["structural_checks"]["perspective_fields"]["required_per_perspective"]
        assert "system_understanding" in required, (
            "eval-001 required_per_perspective missing system_understanding"
        )

    def test_eval_002_checks_system_understanding(self, evals_json):
        """eval-002 structural checks must require system_understanding."""
        eval_002 = evals_json["test_cases"][1]
        required = eval_002["structural_checks"]["perspective_fields"]["required_per_perspective"]
        assert "system_understanding" in required, (
            "eval-002 required_per_perspective missing system_understanding"
        )


# ─────────────────────────────────────────────
# Improvement #4: Targeted Adversarial Pushback
# ─────────────────────────────────────────────

class TestTargetedAdversarialPushback:
    """Verify Step 3.2 uses verbatim quotes from persona findings."""

    def test_step_3_2_has_targeted_label(self, skill_md):
        """Step 3.2 must be labeled 'Targeted Adversarial' not generic."""
        assert "Step 3.2: Push Back (Targeted Adversarial)" in skill_md, (
            "Step 3.2 missing '(Targeted Adversarial)' label"
        )

    def test_verbatim_quote_requirement(self, skill_md):
        """Step 3.2 must require verbatim quotes from findings[].description."""
        step_3_2_start = skill_md.find("Step 3.2: Push Back")
        assert step_3_2_start > 0
        # Check the section between Step 3.2 and Step 3.2.1
        step_3_2_1_start = skill_md.find("Step 3.2.1", step_3_2_start)
        section = skill_md[step_3_2_start:step_3_2_1_start]
        assert "VERBATIM" in section, "Step 3.2 must require VERBATIM quotes"
        assert "findings[].description" in section, (
            "Step 3.2 must reference findings[].description as the quote source"
        )

    def test_verbatim_quoting_rules_section(self, skill_md):
        """Step 3.2 must have explicit verbatim quoting rules."""
        step_3_2_start = skill_md.find("Step 3.2: Push Back")
        step_3_2_1_start = skill_md.find("Step 3.2.1", step_3_2_start)
        section = skill_md[step_3_2_start:step_3_2_1_start]
        assert "Verbatim quoting rules" in section, (
            "Step 3.2 must have a 'Verbatim quoting rules' subsection"
        )
        assert "Never fabricate" in section, (
            "Verbatim quoting rules must prohibit fabricated quotes"
        )

    def test_adversarial_has_three_scenarios(self, skill_md):
        """Step 3.2 must handle: addressed-some, addressed-all, deflected."""
        step_3_2_start = skill_md.find("Step 3.2: Push Back")
        step_3_2_1_start = skill_md.find("Step 3.2.1", step_3_2_start)
        section = skill_md[step_3_2_start:step_3_2_1_start]
        assert "addressed some concerns but not others" in section
        assert "addressed all raised concerns" in section
        assert "deflected or gave a vague answer" in section

    def test_domain_reference_handling(self, skill_md):
        """Verbatim quoting rules must handle domain_reference fields."""
        step_3_2_start = skill_md.find("Step 3.2: Push Back")
        step_3_2_1_start = skill_md.find("Step 3.2.1", step_3_2_start)
        section = skill_md[step_3_2_start:step_3_2_1_start]
        assert "domain_reference" in section, (
            "Step 3.2 must mention domain_reference field for quote attribution"
        )


# ─────────────────────────────────────────────
# Improvement #5: Verdict Assessment Banner
# ─────────────────────────────────────────────

class TestVerdictAssessment:
    """Verify Step 2.5.1 verdict banner with unanimous MAJOR_ISSUES trigger."""

    def test_verdict_step_exists(self, skill_md):
        """SKILL.md must have Step 2.5.1 Verdict Assessment."""
        assert "Step 2.5.1" in skill_md
        assert "Verdict Assessment" in skill_md

    def test_verdict_after_synthesis_before_trimming(self, skill_md):
        """Verdict must appear after Step 2.5 (synthesis) and before Step 2.6 (trimming)."""
        step_2_5_pos = skill_md.find("Step 2.5: Present")
        verdict_pos = skill_md.find("Step 2.5.1")
        step_2_6_pos = skill_md.find("Step 2.6")
        assert step_2_5_pos < verdict_pos < step_2_6_pos, (
            "Step 2.5.1 must be between Step 2.5 (synthesis) and Step 2.6 (trimming)"
        )

    def test_unanimous_major_issues_trigger(self, skill_md):
        """Trigger must require ALL non-error personas to return MAJOR_ISSUES."""
        verdict_start = skill_md.find("Step 2.5.1")
        step_2_6_start = skill_md.find("Step 2.6", verdict_start)
        section = skill_md[verdict_start:step_2_6_start]
        assert "MAJOR_ISSUES" in section
        assert "unanimous" in section.lower() or "ALL non-error" in section, (
            "Verdict trigger must require unanimous MAJOR_ISSUES"
        )

    def test_error_stub_exclusion(self, skill_md):
        """Error stubs must be excluded from unanimity check."""
        verdict_start = skill_md.find("Step 2.5.1")
        step_2_6_start = skill_md.find("Step 2.6", verdict_start)
        section = skill_md[verdict_start:step_2_6_start]
        assert "error" in section.lower() and "exclude" in section.lower(), (
            "Verdict must exclude error-status personas from unanimity"
        )

    def test_minimum_quorum(self, skill_md):
        """Must require minimum 2 successful personas for verdict."""
        verdict_start = skill_md.find("Step 2.5.1")
        step_2_6_start = skill_md.find("Step 2.6", verdict_start)
        section = skill_md[verdict_start:step_2_6_start]
        assert "minimum 2" in section or "minimum 2 of 3" in section, (
            "Verdict must require minimum 2 non-error personas"
        )

    def test_verdict_offers_concrete_options(self, skill_md):
        """Banner must offer concrete options: continue, narrow, add context."""
        verdict_start = skill_md.find("Step 2.5.1")
        step_2_6_start = skill_md.find("Step 2.6", verdict_start)
        section = skill_md[verdict_start:step_2_6_start]
        assert "Continue" in section or "continue" in section
        assert "Narrow" in section or "narrow" in section
        assert "knowledge-dir" in section or "domain" in section, (
            "Verdict must suggest --knowledge-dir or --domain as context options"
        )

    def test_no_banner_when_not_unanimous(self, skill_md):
        """Must explicitly state no banner when at least one persona returns SOUND/CONCERNS."""
        verdict_start = skill_md.find("Step 2.5.1")
        step_2_6_start = skill_md.find("Step 2.6", verdict_start)
        section = skill_md[verdict_start:step_2_6_start]
        assert "SOUND" in section or "CONCERNS" in section, (
            "Verdict must describe the non-triggered case (SOUND/CONCERNS)"
        )
        assert "Do not display" in section or "Proceed normally" in section, (
            "Verdict must say to proceed normally when not triggered"
        )
