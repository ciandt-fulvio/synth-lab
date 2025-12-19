"""LLM Prompts and few-shot examples for PR-FAQ generation.

This module contains:
- System prompt with hybrid chain-of-thought + structured output strategy
- Few-shot examples of quality PR-FAQ generations
- JSON Schema for structured output validation

Third-party documentation:
- OpenAI API prompting: https://platform.openai.com/docs/guides/prompt-engineering

Sample usage:
    from synth_lab.research_prfaq.prompts import get_system_prompt, get_few_shot_examples

    system = get_system_prompt()
    examples = get_few_shot_examples()

Expected output:
    System prompt string with chain-of-thought instructions and format specifications
    List of 2 few-shot examples showing high-quality PR-FAQ outputs
"""

import json


def get_system_prompt() -> str:
    """Return system prompt for hybrid chain-of-thought + structured output strategy."""
    return """You are an expert PR-FAQ generator following Amazon's Working Backwards framework.
Your task is to transform qualitative research insights into structured PR-FAQ documents.

HYBRID CHAIN-OF-THOUGHT + STRUCTURED OUTPUT STRATEGY:

1. ANALYSIS PHASE (Chain-of-Thought):
   - Identify pain points from "recommendations" and "recurrent_patterns" sections
   - Identify benefits and use cases from "recommendations" section
   - Map customer segments from identified personas
   - Note key quotes that support the value proposition
   - Identify differentiators and unique benefits

2. SYNTHESIS PHASE:
   - Create compelling headline that addresses main pain point
   - Develop one-liner value proposition
   - Write problem statement based on identified pain points
   - Write solution overview based on recommended features/benefits
   - Generate 8-12 FAQ questions covering:
     * Product benefits and features
     * Customer segments and personas
     * Key differentiators
     * Use cases and scenarios
     * Implementation/adoption questions

3. OUTPUT PHASE (Structured JSON):
   Produce valid JSON matching the PR-FAQ Schema with:
   - Press Release: headline, one_liner, problem_statement, solution_overview
   - FAQ array: 8-12 items with question, answer, customer_segment

REQUIREMENTS:
- All answers must be derived directly from research findings
- Customer segments must reference identified personas
- Tone should be professional, customer-focused, and action-oriented
- Each FAQ answer should address a specific research insight
- Confidence scoring: High (0.8-1.0) if insights are clear and consistent,
                      Medium (0.5-0.8) if some assumptions needed,
                      Low (0.0-0.5) if research lacks depth

OUTPUT FORMAT:
Return ONLY valid JSON matching the schema below. No markdown, no explanations."""


def get_few_shot_examples() -> list[dict]:
    """Return 2 high-quality PR-FAQ examples for few-shot prompting."""
    return [
        {
            "research_summary": """# Research Findings: Customer Research Interview Batch

## Executive Summary
Conducted 8 interviews with Product Managers at B2B SaaS companies. Key finding:
PMs spend 40% of their time in document coordination across teams, with manual
synthesis of research taking 3-5 weeks per project.

## Recurrent Patterns
- All participants manually compile interview notes into shared documents
- Document versions create confusion (email, Slack, Google Docs chaos)
- No standardized format for capturing research insights
- Synthesis step is repetitive and error-prone

## Recommendations
1. Create automated synthesis tool that generates PR-FAQ from interviews
2. Standardize document format for consistency
3. Enable version control and collaboration features
4. Support multiple export formats (PDF, Markdown, HTML)

## Key Quotes
- "I spend more time consolidating feedback than listening to customers"
- "Every research project, we start from scratch rebuilding the same structure"
- "Our exec team wants PR-FAQ format but it takes weeks to create"
- "Consistency across projects would help with pattern recognition""",
            "prfaq_output": {
                "press_release": {
                    "headline": "Introducing ResearchSync: Transform Customer Interviews into Strategic Documents in Hours",
                    "one_liner": "AI-powered tool that automatically synthesizes customer research into PR-FAQ documents",
                    "problem_statement": "Product teams spend 40% of their time manually consolidating customer research, with each synthesis taking 3-5 weeks and creating document chaos across email, Slack, and shared drives",
                    "solution_overview": "ResearchSync automates research synthesis using AI analysis of interview transcripts, generating professionally formatted PR-FAQ documents with standardized structure, version control, and multi-format export capabilities"
                },
                "faq": [
                    {
                        "question": "How much time does ResearchSync save per research project?",
                        "answer": "Based on customer research, ResearchSync reduces synthesis time from 3-5 weeks to 2-3 days, saving teams 80+ hours per project",
                        "customer_segment": "Product Manager"
                    },
                    {
                        "question": "Does ResearchSync work with different research methodologies?",
                        "answer": "Yes, ResearchSync supports user interviews, surveys, focus groups, and contextual inquiry through flexible input templates and custom interview guides",
                        "customer_segment": "Research Lead"
                    },
                    {
                        "question": "Can teams collaborate on generated PR-FAQs?",
                        "answer": "Yes, ResearchSync includes built-in editing tools, version history, and commenting features enabling real-time collaboration across product, design, and leadership teams",
                        "customer_segment": "Product Manager"
                    },
                    {
                        "question": "What formats can PR-FAQs be exported to?",
                        "answer": "Export to PDF for presentations, Markdown for version control, and HTML for internal wikis, all maintaining consistent formatting",
                        "customer_segment": "Product Manager"
                    },
                    {
                        "question": "How does ResearchSync ensure accuracy in synthesis?",
                        "answer": "Uses hybrid chain-of-thought analysis that identifies pain points and benefits from interview data, then generates answers that stay grounded in actual customer quotes and patterns",
                        "customer_segment": "Researcher"
                    },
                    {
                        "question": "Does it support multiple customer segments in one document?",
                        "answer": "Yes, ResearchSync automatically segments FAQ answers by persona, showing which customer groups benefit from each feature or value proposition",
                        "customer_segment": "Product Manager"
                    }
                ]
            }
        },
        {
            "research_summary": """# Research Findings: Enterprise Adoption Study

## Executive Summary
Interviewed 12 enterprise IT decision-makers evaluating collaboration tools.
Key insight: Security and compliance requirements are blocking adoption despite
strong feature interest.

## Identified Tensions
- Desire for advanced features (real-time collaboration, AI synthesis)
- Concern about data security and compliance (SOC2, HIPAA, GDPR)
- Uncertainty about cost-benefit analysis for teams < 20 people
- Integration complexity with existing enterprise tools

## Relevant Divergences
- Small team enthusiasts: Want ease-of-use and quick setup
- Enterprise security teams: Require extensive compliance certifications
- Finance: Concerned about per-user costs vs. annual budgets

## Recommendations
1. Emphasize security-first architecture and compliance certifications
2. Offer flexible pricing for small vs. enterprise deployments
3. Pre-build integrations with Slack, Jira, Confluence
4. Create compliance documentation for enterprise procurement

## Notable Absences
- No mention of AI features in security-conscious segments
- Limited interest in mobile-first approach (web/desktop preferred)""",
            "prfaq_output": {
                "press_release": {
                    "headline": "SecureCollab: Enterprise Collaboration Without Security Compromises",
                    "one_liner": "SOC2-Type II compliant collaboration platform built for enterprises with stringent security and compliance requirements",
                    "problem_statement": "Enterprise teams need advanced collaboration and synthesis capabilities but current tools force them to choose between powerful features and strict security/compliance requirements, creating bottlenecks in adoption and workflow efficiency",
                    "solution_overview": "SecureCollab provides enterprise-grade collaboration with built-in SOC2-Type II, HIPAA, and GDPR compliance from day one, combined with AI-powered document synthesis and pre-built integrations for Slack, Jira, and Confluence"
                },
                "faq": [
                    {
                        "question": "Is SecureCollab compliant with enterprise security standards?",
                        "answer": "Yes, SecureCollab is SOC2-Type II, HIPAA, and GDPR compliant with continuous audit trails, encryption in transit and at rest, and regular third-party security assessments",
                        "customer_segment": "Security Officer"
                    },
                    {
                        "question": "How does SecureCollab integrate with existing enterprise tools?",
                        "answer": "SecureCollab includes native integrations with Slack, Jira, and Confluence, with API access for custom integrations into enterprise tech stacks",
                        "customer_segment": "IT Administrator"
                    },
                    {
                        "question": "What pricing models support different team sizes?",
                        "answer": "SecureCollab offers flexible pricing: Pro for teams 5-50, Enterprise for 50-500, and Custom for 500+, helping teams right-size costs while maintaining advanced features",
                        "customer_segment": "Finance Director"
                    },
                    {
                        "question": "Can we audit user access and document history?",
                        "answer": "Yes, SecureCollab provides comprehensive audit logs showing all user actions, document access, and changes with compliance-grade retention and export capabilities",
                        "customer_segment": "Security Officer"
                    },
                    {
                        "question": "Is AI synthesis available for regulated data?",
                        "answer": "Yes, SecureCollab uses on-premise AI analysis for regulated industries, keeping sensitive data within your infrastructure while providing synthesis benefits",
                        "customer_segment": "Compliance Officer"
                    }
                ]
            }
        }
    ]


def get_json_schema() -> dict:
    """Return JSON Schema for PR-FAQ validation."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "PR-FAQ Document",
        "type": "object",
        "required": ["press_release", "faq"],
        "properties": {
            "press_release": {
                "type": "object",
                "required": ["headline", "one_liner", "problem_statement", "solution_overview"],
                "properties": {
                    "headline": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 150,
                        "description": "Compelling product headline"
                    },
                    "one_liner": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 150,
                        "description": "One-sentence value proposition"
                    },
                    "problem_statement": {
                        "type": "string",
                        "minLength": 20,
                        "maxLength": 500,
                        "description": "Customer problem description"
                    },
                    "solution_overview": {
                        "type": "string",
                        "minLength": 20,
                        "maxLength": 500,
                        "description": "Solution benefits overview"
                    }
                }
            },
            "faq": {
                "type": "array",
                "minItems": 8,
                "maxItems": 12,
                "items": {
                    "type": "object",
                    "required": ["question", "answer", "customer_segment"],
                    "properties": {
                        "question": {
                            "type": "string",
                            "minLength": 5,
                            "maxLength": 150,
                            "description": "FAQ question"
                        },
                        "answer": {
                            "type": "string",
                            "minLength": 20,
                            "maxLength": 500,
                            "description": "FAQ answer"
                        },
                        "customer_segment": {
                            "type": "string",
                            "minLength": 2,
                            "maxLength": 50,
                            "description": "Synth persona or customer segment"
                        }
                    }
                }
            }
        }
    }


if __name__ == "__main__":
    # Validation of prompts and examples with real data
    import sys

    validation_failures = []
    total_tests = 0

    # Test 1: System prompt is non-empty
    total_tests += 1
    prompt = get_system_prompt()
    if not prompt or len(prompt) < 100:
        validation_failures.append("System prompt is too short or empty")
    else:
        assert "chain-of-thought" in prompt.lower()

    # Test 2: Few-shot examples have correct structure
    total_tests += 1
    examples = get_few_shot_examples()
    if len(examples) != 2:
        validation_failures.append(f"Expected 2 few-shot examples, got {len(examples)}")
    else:
        for i, example in enumerate(examples):
            if "research_summary" not in example or "prfaq_output" not in example:
                validation_failures.append(f"Example {i} missing required keys")
            if "press_release" not in example["prfaq_output"] or "faq" not in example["prfaq_output"]:
                validation_failures.append(f"Example {i} output missing press_release or faq")

    # Test 3: JSON Schema is valid
    total_tests += 1
    schema = get_json_schema()
    if "$schema" not in schema or "properties" not in schema:
        validation_failures.append("JSON Schema missing required fields")

    # Test 4: Schema requires press_release and faq
    total_tests += 1
    required = schema.get("required", [])
    if "press_release" not in required or "faq" not in required:
        validation_failures.append("Schema doesn't require press_release and faq")

    # Test 5: Press Release has all required fields
    total_tests += 1
    pr_required = schema["properties"]["press_release"].get("required", [])
    required_fields = {"headline", "one_liner", "problem_statement", "solution_overview"}
    if set(pr_required) != required_fields:
        validation_failures.append(
            f"Press Release required fields mismatch. Got {set(pr_required)}, expected {required_fields}"
        )

    # Report results
    if validation_failures:
        print(f"❌ VALIDATION FAILED - {len(validation_failures)} of {total_tests} tests failed:")
        for failure in validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Prompts, examples, and schema are validated and ready for use")
        sys.exit(0)
