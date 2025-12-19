"""Research Report to PR/FAQ Generator.

This module transforms qualitative research insights from batch research reports
into structured customer-focused PR-FAQ documents following Amazon's Working
Backwards framework.

Third-party documentation:
- OpenAI API: https://platform.openai.com/docs/
- Pydantic: https://docs.pydantic.dev/
- Typer: https://typer.tiangolo.com/

Sample input (batch_summary.json):
    {
        "batch_id": "batch_001",
        "summary_content": "Research findings in markdown...",
        "sections": {
            "executive_summary": "...",
            "recommendations": "...",
            "recurrent_patterns": "..."
        }
    }

Expected output (prfaq.json):
    {
        "batch_id": "batch_001",
        "press_release": {
            "headline": "...",
            "one_liner": "...",
            "problem_statement": "...",
            "solution_overview": "..."
        },
        "faq": [
            {
                "question": "...",
                "answer": "...",
                "customer_segment": "..."
            }
        ]
    }
"""

from synth_lab.research_prfaq.models import (
    PressRelease,
    FAQItem,
    PRFAQDocument,
    ResearchReport,
    setup_logging,
    parse_batch_summary,
)
from synth_lab.research_prfaq.generator import generate_prfaq, save_prfaq_json, load_prfaq_json
from synth_lab.research_prfaq.exporter import export_to_pdf, export_to_markdown, export_to_html
from synth_lab.research_prfaq.validator import validate_prfaq, validate_research_report

__all__ = [
    "PressRelease",
    "FAQItem",
    "PRFAQDocument",
    "ResearchReport",
    "setup_logging",
    "parse_batch_summary",
    "generate_prfaq",
    "save_prfaq_json",
    "load_prfaq_json",
    "export_to_pdf",
    "export_to_markdown",
    "export_to_html",
    "validate_prfaq",
    "validate_research_report",
]
