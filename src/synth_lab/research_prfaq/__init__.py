"""Research Report to PR/FAQ Generator.

This module transforms qualitative research insights from batch research reports
into customer-focused PR-FAQ documents in Markdown format following Amazon's
Working Backwards framework.

Third-party documentation:
- OpenAI API: https://platform.openai.com/docs/
- Amazon Working Backwards: https://www.amazon.jobs/en/landing_pages/working-backwards

Sample input (batch_report.md):
    # Research Findings

    ## Resumo Executivo
    ...

    ## Recomendações
    ...

    ## Padrões Recorrentes
    ...

Expected output (prfaq.md):
    # Product Name: One-line description

    ## Press Release

    ### Heading
    ...

    ### The Problem
    ...

    ## Frequently Asked Questions

    ### External FAQs
    ...

    ### Internal FAQs
    ...
"""

from synth_lab.research_prfaq.models import (
    setup_logging,
    parse_batch_summary,
)
from synth_lab.research_prfaq.generator import (
    generate_prfaq_markdown,
    save_prfaq_markdown,
    load_prfaq_markdown,
)

__all__ = [
    "setup_logging",
    "parse_batch_summary",
    "generate_prfaq_markdown",
    "save_prfaq_markdown",
    "load_prfaq_markdown",
]
