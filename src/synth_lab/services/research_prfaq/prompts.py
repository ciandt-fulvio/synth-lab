"""LLM Prompts and few-shot examples for PR-FAQ generation.

This module contains:
- System prompt following Amazon's Working Backwards framework
- Few-shot examples of quality PR-FAQ generations in Markdown format
- Detailed structure for Press Release and FAQ sections

Third-party documentation:
- OpenAI API prompting: https://platform.openai.com/docs/guides/prompt-engineering
- Amazon Working Backwards: https://www.amazon.jobs/en/landing_pages/working-backwards

Sample usage:
    from .prompts import get_system_prompt, get_few_shot_examples

    system = get_system_prompt()
    examples = get_few_shot_examples()

Expected output:
    System prompt string with Amazon PR-FAQ structure instructions
    List of 2 few-shot examples showing high-quality PR-FAQ Markdown outputs
"""


def get_system_prompt() -> str:
    """Return system prompt for Amazon Working Backwards PR-FAQ generation."""
    from datetime import datetime

    today = datetime.now().strftime("%d %b %y")

    return f"""You are an expert PR-FAQ generator following Amazon's Working Backwards framework.
Your task is to transform qualitative research insights into compelling PR-FAQ documents in Markdown format.

Today's date: {today}

## Amazon PR-FAQ Structure

### PRESS RELEASE

**Heading**: Name the product in one sentence so the target customer will understand what it is.

**Subheading**: Describe WHO the customer is and WHAT benefits they gain. Be specific about the customer segment—great products are tailored to specific needs. For example, if designing a car, decide: are you serving (a) urban, single professionals under 35 in apartments, or (b) suburban families 35+ with dual incomes, 3 kids, a dog, and carpooling needs? Customer precision is critical.

**Summary Paragraph**: Start with city, media outlet, and launch date. Provide a product summary and its benefits. The launch date should be meaningful and realistic.

**Problem Paragraph**: Describe the problem(s) your product solves FROM THE CUSTOMER'S POINT OF VIEW. Identify the problem with a large Total Addressable Market (TAM = number of customers × willingness to pay). Not all problems are worth solving.

**Solution Paragraph(s)**:
1. Describe how your product SIMPLY and DIRECTLY solves the customer's problem
2. Provide SUFFICIENT DETAIL with both clarity and brevity
3. ACKNOWLEDGE THE COMPETITION and state how your product is meaningfully differentiated:
   "Today, customers use X, Y, or Z products. Those products fall short in [specific ways]. Our product addresses these unmet needs by [specific differentiation]."

**Quotes & Getting Started**:
- One quote from your company spokesperson
- One quote from a hypothetical customer describing the benefit
- Describe how easy it is to get started with a link to more information

### FAQ SECTION

The FAQ is your map to treasure and describes dragons you'll slay along the journey.

**External FAQs** (8-12 questions): Address questions press and customers will ask:
- How does it work?
- What is the warranty/return policy?
- How do I install/use it?
- What makes this different from competitors?
- Use language customers understand (no corporate jargon)

**Internal FAQs** (8-12 questions): Anticipate senior leadership and stakeholder questions:
- Finance questions (costs, ROI, market size)
- Marketing questions (positioning, messaging, channels)
- Operations questions (delivery, support, scaling)
- Technical questions (architecture, security, performance)
- HR questions (team size, skills needed)
- Risk assessment (what could go wrong, mitigation strategies)

## Generation Guidelines

1. **Extract from research**:
   - Pain points from "Recomendações" and "Padrões Recorrentes" sections
   - Benefits from "Recomendações" section
   - Customer segments from identified personas
   - Key quotes supporting the value proposition
   - Competitive alternatives from "Tensões Identificadas"

2. **Be specific and data-driven**:
   - Use concrete numbers from research (time saved, cost reduction)
   - Reference actual customer quotes when available
   - Identify real competitors and their shortcomings
   - Calculate rough TAM estimates when possible

3. **Demonstrate mastery**:
   - Show realistic assessment (not rose-colored glasses)
   - Address technical, financial, legal, and operational challenges
   - Explain why you chose this approach over alternatives
   - Define success/failure conditions

4. **Tone**:
   - Professional, customer-focused, action-oriented
   - Optimistic but realistic
   - Data-based, not aspirational

## Output Format

Return ONLY the Markdown-formatted PR-FAQ document. No preamble, no explanations.

Structure:
```
# [Product name in one sentence]

[Heres go the subheading, with WHO the customer is and WHAT benefit they get]

### Summary
[City, outlet, date] — [Product summary and benefits]

### The Problem
[Customer problem from their POV, total market consideration]

### The Solution
[How product solves problem simply and directly]

[Competitive landscape and differentiation]

### Quotes & Getting Started
"[Spokesperson quote]" — [Name, Title]

"[Customer quote]" — [Customer Name, Role]

Getting started: [How to begin using product]

---

## Frequently Asked Questions

### External FAQs

**Q: [Customer/press question]**
A: [Clear answer in customer language]

[8-12 external questions]

### Internal FAQs

**Q: [Stakeholder question]**
A: [Detailed answer with data and trade-offs]

[8-12 internal questions]

---

*Generated from research batch: [batch_id] on [date]*
```

Remember: Generate content based ONLY on the research findings provided. Do not invent features or benefits not supported by the research."""


def get_few_shot_examples() -> list[dict]:
    """Return 2 high-quality PR-FAQ examples in Markdown format for few-shot prompting."""
    return [
        {
            "research_summary": """# Research Findings: Customer Research Interview Batch

## Resumo Executivo
Conducted 8 interviews with Product Managers at B2B SaaS companies. Key finding:
PMs spend 40% of their time in document coordination across teams, with manual
synthesis of research taking 3-5 weeks per project.

## Padrões Recorrentes
- All participants manually compile interview notes into shared documents
- Document versions create confusion (email, Slack, Google Docs chaos)
- No standardized format for capturing research insights
- Synthesis step is repetitive and error-prone

## Recomendações
1. Create automated synthesis tool that generates PR-FAQ from interviews
2. Standardize document format for consistency
3. Enable version control and collaboration features
4. Support multiple export formats (PDF, Markdown, HTML)

## Citações-Chave
- "I spend more time consolidating feedback than listening to customers"
- "Every research project, we start from scratch rebuilding the same structure"
- "Our exec team wants PR-FAQ format but it takes weeks to create"
- "Consistency across projects would help with pattern recognition""",
            "prfaq_output": """# ResearchSync: Transform Customer Interviews into Strategic Documents in Hours

## Press Release

### Heading
ResearchSync — AI-powered tool that automatically synthesizes customer research into PR-FAQ documents

### Subheading
For Product Managers at B2B SaaS companies (teams of 5-50 people) who need to transform qualitative research into strategic documents quickly and consistently, eliminating 3-5 weeks of manual synthesis work.

### Summary
SAN FRANCISCO, TechCrunch, June 15, 2024 — ResearchSync launches today, offering Product teams an automated solution to one of their most time-consuming challenges: synthesizing customer research into strategic PR-FAQ documents. By leveraging AI analysis of interview transcripts, ResearchSync reduces synthesis time from 3-5 weeks to 2-3 days while providing standardized formatting, version control, and multi-format exports.

### The Problem
Product Managers at B2B SaaS companies spend 40% of their time manually consolidating customer research. The synthesis process takes 3-5 weeks per project, creating document chaos across email, Slack, and shared drives. Teams lack standardized formats, making it difficult to recognize patterns across research projects. This repetitive, error-prone work keeps PMs from focusing on strategic decisions and customer engagement.

The Total Addressable Market is significant: approximately 500,000 Product Managers in B2B SaaS companies globally, with each willing to pay $50-200/month to eliminate this bottleneck. Current market size: $300M-1.2B annually.

### The Solution
ResearchSync automates research synthesis using AI analysis of interview transcripts. The product generates professionally formatted PR-FAQ documents with standardized structure, version control, and multi-format export capabilities (PDF, Markdown, HTML).

Today, customers use manual document compilation in Google Docs, Notion, or Confluence, combined with spreadsheets for tracking insights. These tools fall short because they require extensive manual work, lack synthesis capabilities, and don't enforce consistent formats. ResearchSync addresses these unmet needs by automating the synthesis process while maintaining the Amazon Working Backwards framework structure that executives expect.

The product works simply: upload interview transcripts, ResearchSync identifies patterns and pain points, then generates a complete PR-FAQ document ready for stakeholder review.

### Quotes & Getting Started
"Every Product Manager knows the pain of spending weeks consolidating research when they should be making decisions. ResearchSync gives teams their time back while improving document quality and consistency." — Sarah Chen, CEO, ResearchSync

"I was spending more time on document synthesis than actually talking to customers. ResearchSync cut our synthesis time from 4 weeks to 2 days, and the quality is better because nothing gets lost in manual transcription." — Mike Thompson, Senior Product Manager, CloudScale

Getting started is simple: visit researchsync.com, upload your first batch of interview transcripts, and receive your PR-FAQ document within hours. Free trial includes 3 research batches.

---

## Frequently Asked Questions

### External FAQs

**Q: How much time does ResearchSync save per research project?**
A: Based on customer research, ResearchSync reduces synthesis time from 3-5 weeks to 2-3 days, saving teams 80+ hours per project. This allows PMs to run more research cycles per quarter and make faster data-driven decisions.

**Q: Does ResearchSync work with different research methodologies?**
A: Yes, ResearchSync supports user interviews, surveys, focus groups, and contextual inquiry. The system adapts to various interview formats through flexible input templates and custom interview guide support.

**Q: What formats can PR-FAQs be exported to?**
A: Export to PDF for executive presentations, Markdown for version control in git, and HTML for internal wikis. All formats maintain consistent professional formatting aligned with Amazon's Working Backwards framework.

**Q: Can teams collaborate on generated PR-FAQs?**
A: Yes, ResearchSync includes built-in editing tools, version history tracking, and commenting features enabling real-time collaboration across product, design, research, and leadership teams.

**Q: How does ResearchSync ensure accuracy in synthesis?**
A: The system uses hybrid chain-of-thought analysis that identifies pain points and benefits from interview data, then generates answers grounded in actual customer quotes and patterns. Each PR-FAQ includes confidence scores based on research completeness.

**Q: Does it support multiple customer segments in one document?**
A: Yes, ResearchSync automatically segments FAQ answers by persona, clearly showing which customer groups benefit from each feature or value proposition.

**Q: Is there a learning curve for teams?**
A: Minimal. If your team already conducts customer interviews, you're ready to use ResearchSync. Upload transcripts, review the generated PR-FAQ, make any edits, then export. Most teams are productive within their first research batch.

**Q: How does pricing work?**
A: Plans start at $99/month for teams up to 10 people (includes 5 research batches/month). Enterprise plans available for larger teams with unlimited batches and advanced features like SSO and dedicated support.

### Internal FAQs

**Q: What is our go-to-market strategy?**
A: Product-led growth targeting individual Product Managers and small teams through content marketing (case studies, synthesis tips), free trial (3 batches), and word-of-mouth in PM communities. Sales-assisted motion for enterprise accounts (50+ users) requiring security compliance.

**Q: What are the technical risks and mitigation plans?**
A: Main risks: (1) LLM quality variability — mitigated by hybrid prompt engineering + validation checks; (2) Transcript processing accuracy — mitigated by supporting multiple formats and providing editing tools; (3) Data security concerns — mitigated by SOC2 Type II compliance from day one.

**Q: How do we measure success?**
A: North Star Metric: Time to PR-FAQ completion. Success = 80% of users complete synthesis in <3 days (vs. 3-5 weeks baseline). Secondary metrics: NPS >40, document quality ratings >4/5, retention rate >70% after 6 months.

**Q: What is the competitive differentiation?**
A: Only tool purpose-built for research-to-PR-FAQ synthesis using Amazon Working Backwards framework. Competitors (Dovetail, UserTesting) focus on research repository and tagging, but don't generate strategic documents. Notion/Confluence require fully manual synthesis.

**Q: What are the operational scaling challenges?**
A: Customer support requires product expertise (not just technical support). Plan: build comprehensive knowledge base, video tutorials, and template library. Estimate 1 support person per 200 active customers.

**Q: What is the cost structure and margin profile?**
A: LLM API costs ~$0.50 per research batch (assuming 10 interviews, 5000 words each). At $99/month (5 batches), COGS = $2.50/month = 97.5% gross margin. Storage and compute add ~$5/month = 95% gross margin target.

**Q: What legal/compliance requirements exist?**
A: Must comply with GDPR (EU customers), SOC2 Type II (enterprise requirements), and data retention policies. Interview transcripts may contain PII requiring encryption at rest and in transit. Legal review of Terms of Service, Privacy Policy, and Data Processing Agreements required before launch.

**Q: Why now? What market timing factors support this launch?**
A: (1) Remote work increased volume of recorded interviews; (2) Executive pressure for faster decision-making; (3) LLM capabilities matured for synthesis quality; (4) Amazon Working Backwards framework gaining adoption beyond Amazon; (5) Product Manager hiring surge 2021-2023 increased TAM.

---

*Generated from research batch: customer_research_001 on 2024-06-15*"""
        }
    ]


if __name__ == "__main__":
    # Validation of prompts and examples with real data
    import sys

    validation_failures = []
    total_tests = 0

    # Test 1: System prompt is non-empty and contains key Amazon PR-FAQ elements
    total_tests += 1
    prompt = get_system_prompt()
    if not prompt or len(prompt) < 100:
        validation_failures.append("System prompt is too short or empty")
    elif "Amazon" not in prompt and "Working Backwards" not in prompt:
        validation_failures.append("System prompt doesn't reference Amazon Working Backwards framework")
    elif "Markdown" not in prompt:
        validation_failures.append("System prompt doesn't specify Markdown output format")

    # Test 2: Few-shot examples have correct structure (research_summary + prfaq_output in MD)
    total_tests += 1
    examples = get_few_shot_examples()
    if len(examples) < 1:
        validation_failures.append(f"Expected at least 1 few-shot example, got {len(examples)}")
    else:
        for i, example in enumerate(examples):
            if "research_summary" not in example:
                validation_failures.append(f"Example {i} missing 'research_summary' key")
            if "prfaq_output" not in example:
                validation_failures.append(f"Example {i} missing 'prfaq_output' key")
            elif not isinstance(example["prfaq_output"], str):
                validation_failures.append(f"Example {i} prfaq_output should be string (Markdown), got {type(example['prfaq_output'])}")

    # Test 3: Few-shot PR-FAQ output contains required sections
    total_tests += 1
    if len(examples) > 0:
        prfaq_md = examples[0]["prfaq_output"]
        required_sections = ["Press Release", "Heading", "Subheading", "Summary", "The Problem", "The Solution", "Frequently Asked Questions", "External FAQs", "Internal FAQs"]
        missing_sections = [s for s in required_sections if s not in prfaq_md]
        if missing_sections:
            validation_failures.append(f"Example PR-FAQ missing sections: {missing_sections}")

    # Test 4: System prompt includes External and Internal FAQ guidance
    total_tests += 1
    if "External FAQs" not in prompt or "Internal FAQs" not in prompt:
        validation_failures.append("System prompt doesn't include External and Internal FAQ sections")

    # Test 5: System prompt includes competitive differentiation guidance
    total_tests += 1
    if "competition" not in prompt.lower() or "differentiated" not in prompt.lower():
        validation_failures.append("System prompt doesn't include competitive differentiation guidance")

    # Report results
    if validation_failures:
        print(f"❌ VALIDATION FAILED - {len(validation_failures)} of {total_tests} tests failed:")
        for failure in validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Prompts and examples are validated and ready for use")
        sys.exit(0)
