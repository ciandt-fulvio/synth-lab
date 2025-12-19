"""Export PR-FAQ documents to PDF, Markdown, and HTML formats.

Supports multiple export formats for different use cases:
- PDF: Professional presentations and email distribution
- Markdown: Git-friendly version control and wikis
- HTML: Internal documentation and interactive consumption

Third-party documentation:
- reportlab: https://www.reportlab.com/docs/reportlab-userguide.pdf
- Jinja2: https://jinja.palletsprojects.com/

Sample usage:
    from synth_lab.research_prfaq.exporter import export_to_pdf, export_to_markdown
    from synth_lab.research_prfaq.models import PRFAQDocument

    prfaq = PRFAQDocument(...)
    export_to_pdf(prfaq, "output.pdf")
    export_to_markdown(prfaq, "output.md")

Expected output:
    PDF file with professional formatting
    Markdown file with Git-friendly structure
    HTML file with styling and interactive elements
"""

from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle
)
from reportlab.lib import colors
from loguru import logger

from synth_lab.research_prfaq.models import PRFAQDocument


class PRFAQExporter:
    """Export PR-FAQ documents to multiple formats."""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize exporter with optional template directory.

        Args:
            template_dir: Directory containing Jinja2 templates (default: built-in templates)
        """
        if template_dir is None:
            # Use templates directory relative to this file
            template_dir = Path(__file__).parent / "templates"

        self.template_dir = Path(template_dir)

        # Initialize Jinja2 environment for Markdown and HTML
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        logger.debug(f"PRFAQExporter initialized with template_dir={self.template_dir}")

    def export_to_pdf(self, prfaq: PRFAQDocument, output_path: str | Path) -> Path:
        """Export PR-FAQ to PDF format with professional formatting.

        Args:
            prfaq: PRFAQDocument to export
            output_path: Path for output PDF file

        Returns:
            Path to created PDF file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exporting PR-FAQ to PDF: {output_path}")

        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=36
        )

        # Container for PDF elements
        story = []

        # Get styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#4a4a4a'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c5282'),
            spaceAfter=10,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            leading=16,
            spaceAfter=12,
            alignment=TA_LEFT
        )

        # Title: Press Release Headline
        story.append(Paragraph(prfaq.press_release.headline, title_style))

        # Subtitle: One-liner
        story.append(Paragraph(prfaq.press_release.one_liner, subtitle_style))

        story.append(Spacer(1, 0.3 * inch))

        # Problem Statement
        story.append(Paragraph("Problem", heading_style))
        story.append(Paragraph(prfaq.press_release.problem_statement, body_style))

        # Solution Overview
        story.append(Paragraph("Solution", heading_style))
        story.append(Paragraph(prfaq.press_release.solution_overview, body_style))

        story.append(Spacer(1, 0.3 * inch))

        # FAQ Section
        story.append(Paragraph("Frequently Asked Questions", heading_style))
        story.append(Spacer(1, 0.1 * inch))

        for idx, faq_item in enumerate(prfaq.faq, 1):
            # Question (bold)
            question_style = ParagraphStyle(
                f'Question{idx}',
                parent=body_style,
                fontName='Helvetica-Bold',
                fontSize=11,
                spaceAfter=6
            )
            story.append(Paragraph(f"{idx}. {faq_item.question}", question_style))

            # Answer
            answer_style = ParagraphStyle(
                f'Answer{idx}',
                parent=body_style,
                leftIndent=20,
                spaceAfter=12
            )
            story.append(Paragraph(faq_item.answer, answer_style))

            # Customer segment (italics, small)
            segment_style = ParagraphStyle(
                f'Segment{idx}',
                parent=body_style,
                fontName='Helvetica-Oblique',
                fontSize=9,
                textColor=colors.HexColor('#666666'),
                leftIndent=20,
                spaceAfter=16
            )
            story.append(Paragraph(f"<i>Customer Segment: {faq_item.customer_segment}</i>", segment_style))

        # Metadata footer
        story.append(Spacer(1, 0.5 * inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#999999'),
            alignment=TA_CENTER
        )

        metadata_text = (
            f"Generated: {prfaq.generated_at.strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Batch ID: {prfaq.batch_id} | "
            f"Version: {prfaq.version} | "
            f"Confidence: {prfaq.confidence_score:.2f}"
        )
        story.append(Paragraph(metadata_text, footer_style))

        # Build PDF
        doc.build(story)

        logger.info(f"PDF export completed: {output_path} ({output_path.stat().st_size} bytes)")
        return output_path

    def export_to_markdown(self, prfaq: PRFAQDocument, output_path: str | Path) -> Path:
        """Export PR-FAQ to Markdown format (git-friendly).

        Args:
            prfaq: PRFAQDocument to export
            output_path: Path for output Markdown file

        Returns:
            Path to created Markdown file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exporting PR-FAQ to Markdown: {output_path}")

        # Load Jinja2 template
        template = self.jinja_env.get_template('prfaq.md.j2')

        # Render template with PR-FAQ data
        markdown_content = template.render(
            headline=prfaq.press_release.headline,
            one_liner=prfaq.press_release.one_liner,
            problem_statement=prfaq.press_release.problem_statement,
            solution_overview=prfaq.press_release.solution_overview,
            faq=prfaq.faq,
            batch_id=prfaq.batch_id,
            generated_at=prfaq.generated_at.strftime('%Y-%m-%d %H:%M:%S'),
            version=prfaq.version,
            confidence_score=prfaq.confidence_score
        )

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        logger.info(f"Markdown export completed: {output_path} ({output_path.stat().st_size} bytes)")
        return output_path

    def export_to_html(self, prfaq: PRFAQDocument, output_path: str | Path) -> Path:
        """Export PR-FAQ to HTML format with styling.

        Args:
            prfaq: PRFAQDocument to export
            output_path: Path for output HTML file

        Returns:
            Path to created HTML file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exporting PR-FAQ to HTML: {output_path}")

        # Load Jinja2 template
        template = self.jinja_env.get_template('prfaq.html.j2')

        # Render template with PR-FAQ data
        html_content = template.render(
            headline=prfaq.press_release.headline,
            one_liner=prfaq.press_release.one_liner,
            problem_statement=prfaq.press_release.problem_statement,
            solution_overview=prfaq.press_release.solution_overview,
            faq=prfaq.faq,
            batch_id=prfaq.batch_id,
            generated_at=prfaq.generated_at.strftime('%Y-%m-%d %H:%M:%S'),
            version=prfaq.version,
            confidence_score=prfaq.confidence_score
        )

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"HTML export completed: {output_path} ({output_path.stat().st_size} bytes)")
        return output_path


# Convenience functions for direct usage
def export_to_pdf(prfaq: PRFAQDocument, output_path: str | Path) -> Path:
    """Export PR-FAQ to PDF format.

    Args:
        prfaq: PRFAQDocument to export
        output_path: Path for output PDF file

    Returns:
        Path to created PDF file
    """
    exporter = PRFAQExporter()
    return exporter.export_to_pdf(prfaq, output_path)


def export_to_markdown(prfaq: PRFAQDocument, output_path: str | Path) -> Path:
    """Export PR-FAQ to Markdown format.

    Args:
        prfaq: PRFAQDocument to export
        output_path: Path for output Markdown file

    Returns:
        Path to created Markdown file
    """
    exporter = PRFAQExporter()
    return exporter.export_to_markdown(prfaq, output_path)


def export_to_html(prfaq: PRFAQDocument, output_path: str | Path) -> Path:
    """Export PR-FAQ to HTML format.

    Args:
        prfaq: PRFAQDocument to export
        output_path: Path for output HTML file

    Returns:
        Path to created HTML file
    """
    exporter = PRFAQExporter()
    return exporter.export_to_html(prfaq, output_path)


if __name__ == "__main__":
    """Validation with real data from existing PR-FAQ generation."""
    import sys
    from synth_lab.research_prfaq.models import PressRelease, FAQItem

    # Track all validation failures
    validation_failures = []
    total_tests = 0

    # Create a realistic test PR-FAQ document
    test_prfaq = PRFAQDocument(
        batch_id="test_batch_001",
        press_release=PressRelease(
            headline="Introducing ResearchSync: Transform Customer Interviews into Strategic Documents",
            one_liner="AI-powered synthesis of customer research into actionable PR-FAQ documents",
            problem_statement="Product teams spend 40% of their time manually consolidating customer research, with synthesis taking 3-5 weeks per project. This delay impacts go-to-market decisions and product strategy alignment.",
            solution_overview="ResearchSync automates research synthesis, generating PR-FAQ documents in hours with standardized format, version control, and AI-powered insights extraction from customer interviews."
        ),
        faq=[
            FAQItem(
                question="How much time does ResearchSync save compared to manual synthesis?",
                answer="ResearchSync reduces synthesis time from 3-5 weeks to 2-3 days, saving 80+ hours per project. Teams can iterate faster and make data-driven decisions with confidence.",
                customer_segment="Product Manager"
            ),
            FAQItem(
                question="Can teams collaborate on generated PR-FAQ documents?",
                answer="Yes, with built-in editing tools, version history tracking, and commenting capabilities for real-time collaboration across product, design, and research teams.",
                customer_segment="Product Manager"
            ),
            FAQItem(
                question="What format does ResearchSync output?",
                answer="PR-FAQ documents are generated in JSON format with validation against JSON Schema, and can be exported to PDF, Markdown, and HTML for different use cases.",
                customer_segment="Technical Lead"
            ),
            FAQItem(
                question="How accurate are the AI-generated insights?",
                answer="Each PR-FAQ includes a confidence score (0-1) based on research completeness. Documents undergo JSON Schema validation to ensure structural correctness.",
                customer_segment="UX Researcher"
            ),
            FAQItem(
                question="Can I customize the PR-FAQ template?",
                answer="Yes, the minimal PR-FAQ format (Headline, One-liner, Problem, Solution, FAQ) can be customized via Jinja2 templates for Markdown and HTML exports.",
                customer_segment="Technical Lead"
            ),
            FAQItem(
                question="What customer segments are identified?",
                answer="Each FAQ item is linked to synth persona archetypes (e.g., Product Manager, UX Researcher, Technical Lead) based on research findings.",
                customer_segment="UX Researcher"
            ),
            FAQItem(
                question="How is version control handled?",
                answer="All PR-FAQ edits are tracked with timestamps, field changes, and version numbers. Historical versions are stored in .versions/ directory.",
                customer_segment="Product Manager"
            ),
            FAQItem(
                question="What happens if the research batch has incomplete data?",
                answer="The generator extracts insights from available sections (recommendations, recurrent_patterns) and flags missing data with lower confidence scores.",
                customer_segment="UX Researcher"
            )
        ],
        confidence_score=0.87
    )

    # Create test output directory
    output_dir = Path("data/outputs/prfaq/test_exports")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Test 1: Export to PDF
    total_tests += 1
    try:
        pdf_path = export_to_pdf(test_prfaq, output_dir / "test_prfaq.pdf")
        if not pdf_path.exists():
            validation_failures.append(f"PDF export: File not created at {pdf_path}")
        elif pdf_path.stat().st_size == 0:
            validation_failures.append(f"PDF export: File is empty")
        else:
            logger.info(f"✓ PDF export successful: {pdf_path.stat().st_size} bytes")
    except Exception as e:
        validation_failures.append(f"PDF export: {str(e)}")

    # Test 2: Export to Markdown
    total_tests += 1
    try:
        md_path = export_to_markdown(test_prfaq, output_dir / "test_prfaq.md")
        if not md_path.exists():
            validation_failures.append(f"Markdown export: File not created at {md_path}")
        elif md_path.stat().st_size == 0:
            validation_failures.append(f"Markdown export: File is empty")
        else:
            # Verify content has expected sections
            with open(md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            if "ResearchSync" not in md_content:
                validation_failures.append(f"Markdown export: Missing headline in content")
            elif "## Problem" not in md_content:
                validation_failures.append(f"Markdown export: Missing Problem section")
            elif "## FAQ" not in md_content:
                validation_failures.append(f"Markdown export: Missing FAQ section")
            else:
                logger.info(f"✓ Markdown export successful: {md_path.stat().st_size} bytes")
    except Exception as e:
        validation_failures.append(f"Markdown export: {str(e)}")

    # Test 3: Export to HTML
    total_tests += 1
    try:
        html_path = export_to_html(test_prfaq, output_dir / "test_prfaq.html")
        if not html_path.exists():
            validation_failures.append(f"HTML export: File not created at {html_path}")
        elif html_path.stat().st_size == 0:
            validation_failures.append(f"HTML export: File is empty")
        else:
            # Verify content has HTML structure
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            if "<html" not in html_content.lower():
                validation_failures.append(f"HTML export: Missing HTML structure")
            elif "<h1>" not in html_content.lower():
                validation_failures.append(f"HTML export: Missing H1 heading")
            elif "ResearchSync" not in html_content:
                validation_failures.append(f"HTML export: Missing headline in content")
            else:
                logger.info(f"✓ HTML export successful: {html_path.stat().st_size} bytes")
    except Exception as e:
        validation_failures.append(f"HTML export: {str(e)}")

    # Test 4: Verify PRFAQExporter class initialization
    total_tests += 1
    try:
        exporter = PRFAQExporter()
        if not exporter.template_dir.exists():
            validation_failures.append(f"PRFAQExporter: Template directory not found: {exporter.template_dir}")
        else:
            logger.info(f"✓ PRFAQExporter initialized with template_dir={exporter.template_dir}")
    except Exception as e:
        validation_failures.append(f"PRFAQExporter initialization: {str(e)}")

    # Final validation result
    if validation_failures:
        print(f"\n❌ VALIDATION FAILED - {len(validation_failures)} of {total_tests} tests failed:")
        for failure in validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"\n✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print(f"   PDF: {output_dir / 'test_prfaq.pdf'}")
        print(f"   Markdown: {output_dir / 'test_prfaq.md'}")
        print(f"   HTML: {output_dir / 'test_prfaq.html'}")
        print("Exporter is validated and ready for CLI integration")
        sys.exit(0)
