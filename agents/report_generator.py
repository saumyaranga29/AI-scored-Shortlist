"""
Report Generator
Produces a styled HTML shortlist report from the scored candidates list.
Uses Jinja2 for templating.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader, select_autoescape
from models.schemas import CandidateScore, JDRequirements, ShortlistReport

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def _score_color(score: float) -> str:
    """Return a CSS color class based on score value."""
    if score >= 8.0:
        return "excellent"
    elif score >= 6.5:
        return "good"
    elif score >= 5.0:
        return "average"
    else:
        return "poor"


def _rec_color(recommendation: str) -> str:
    mapping = {
        "Strong Hire": "strong-hire",
        "Hire": "hire",
        "Maybe": "maybe",
        "No Hire": "no-hire",
    }
    return mapping.get(recommendation, "no-hire")


def generate_html_report(
    jd: JDRequirements,
    candidates: List[CandidateScore],
) -> str:
    """
    Generate a complete HTML shortlist report.

    Args:
        jd: Parsed JD requirements
        candidates: List of scored candidates (already sorted by total_score desc)

    Returns:
        HTML string of the full report
    """
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["score_color"] = _score_color
    env.filters["rec_color"] = _rec_color

    recommended = [c for c in candidates if c.recommendation in ("Strong Hire", "Hire")]
    report = ShortlistReport(
        job_title=jd.job_title,
        jd_summary=jd,
        candidates=candidates,
        generated_at=datetime.now().strftime("%d %b %Y, %I:%M %p"),
        total_analyzed=len(candidates),
        recommended_count=len(recommended),
    )

    template = env.get_template("report.html")
    return template.render(report=report, score_color=_score_color, rec_color=_rec_color)


def generate_json_report(
    jd: JDRequirements,
    candidates: List[CandidateScore],
) -> str:
    """Generate a JSON export of the shortlist report."""
    recommended = [c for c in candidates if c.recommendation in ("Strong Hire", "Hire")]
    report = ShortlistReport(
        job_title=jd.job_title,
        jd_summary=jd,
        candidates=candidates,
        generated_at=datetime.now().strftime("%d %b %Y, %I:%M %p"),
        total_analyzed=len(candidates),
        recommended_count=len(recommended),
    )
    return report.model_dump_json(indent=2)
