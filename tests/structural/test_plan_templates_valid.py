"""
Structural test: ExecPlan templates in docs/plans/templates/ follow
the PLANS.md rubric and contain no placeholders.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = REPO_ROOT / "docs" / "plans" / "templates"

REQUIRED_SECTIONS = [
    "## Purpose",
    "## Big Picture",
    "## Milestones",
    "## Progress",
    "## Decision Log",
    "## Surprises & Discoveries",
    "## Awaiting Steering",
    "## Outcomes & Retrospective",
]

FORBIDDEN_PLACEHOLDERS = [
    "TBD", "TODO", "implement later", "fill in details",
]


def test_brownfield_template_exists():
    """The brownfield adoption template exists."""
    template = TEMPLATES_DIR / "0001-brownfield-adoption.md"
    assert template.exists(), (
        f"Missing {template.relative_to(REPO_ROOT)}. "
        f"Create a brownfield adoption ExecPlan template following "
        f"the PLANS.md rubric."
    )


def test_brownfield_template_follows_rubric():
    """The brownfield template has all 8 required sections."""
    template = TEMPLATES_DIR / "0001-brownfield-adoption.md"
    if not template.exists():
        return  # Test above catches missing file.

    text = template.read_text(encoding="utf-8")

    for section in REQUIRED_SECTIONS:
        assert section in text, (
            f"Template {template.relative_to(REPO_ROOT)} missing "
            f"required section '{section}'. Every ExecPlan must have "
            f"all 8 sections per docs/PLANS.md."
        )


def test_brownfield_template_has_acceptance_tests():
    """Every milestone in the template has an Acceptance Test line."""
    template = TEMPLATES_DIR / "0001-brownfield-adoption.md"
    if not template.exists():
        return

    text = template.read_text(encoding="utf-8")

    # Extract the Milestones section
    import re
    milestones_match = re.search(
        r"## Milestones\s*\n(.*?)(?=## |\Z)", text, re.DOTALL
    )
    assert milestones_match, "Template missing Milestones section."

    milestones_text = milestones_match.group(1)

    # Each milestone (### M... ) should have an Acceptance Test:
    milestone_headers = re.findall(r"### M\d+:.*", milestones_text)
    acceptance_lines = re.findall(r"Acceptance Test:", milestones_text)

    assert len(acceptance_lines) >= len(milestone_headers), (
        f"Template has {len(milestone_headers)} milestones but only "
        f"{len(acceptance_lines)} Acceptance Test lines. Each milestone "
        f"must have an Acceptance Test per docs/conventions/verification-floor.md."
    )


def test_brownfield_template_no_placeholders():
    """The template contains no TBD/TODO/placeholder phrases."""
    template = TEMPLATES_DIR / "0001-brownfield-adoption.md"
    if not template.exists():
        return

    text = template.read_text(encoding="utf-8")
    for phrase in FORBIDDEN_PLACEHOLDERS:
        assert phrase.lower() not in text.lower(), (
            f"Template contains placeholder '{phrase}'. "
            f"ExecPlan templates must be complete — no TBD/TODO items."
        )


def test_brownfield_template_no_forbidden_phrases():
    """The template's Decision Log contains no forbidden phrases."""
    template = TEMPLATES_DIR / "0001-brownfield-adoption.md"
    if not template.exists():
        return

    text = template.read_text(encoding="utf-8")
    forbidden = [
        "standard approach", "best practice", "industry standard",
        "commonly used", "widely accepted", "the go-to",
        "people generally", "everyone knows",
    ]
    for phrase in forbidden:
        assert phrase.lower() not in text.lower(), (
            f"Template contains forbidden phrase '{phrase}'."
        )
