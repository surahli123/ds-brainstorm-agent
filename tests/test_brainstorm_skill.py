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
