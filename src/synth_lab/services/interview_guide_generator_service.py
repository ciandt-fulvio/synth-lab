"""
Interview Guide Generator Service.

Generates interview guides automatically when experiments are created.
Uses LLM to create questions, context definitions, and examples based on
the experiment's name, hypothesis, and description.

References:
- OpenAI Chat Completions: https://platform.openai.com/docs/api-reference/chat
- Phoenix Tracing: https://docs.arize.com/phoenix

Sample usage:
```python
from synth_lab.services.interview_guide_generator_service import (
    InterviewGuideGeneratorService)

service = InterviewGuideGeneratorService()
guide = await service.generate_for_experiment(
    experiment_id="exp_123",
    name="Checkout 1-clique",
    hypothesis="Usuários preferem checkout simplificado",
    description="Testar nova experiência de compra rápida")
```
"""

import asyncio
import json
from datetime import datetime, timezone

from loguru import logger
from pydantic import BaseModel

from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.interview_guide_repository import (
    InterviewGuide,
    InterviewGuideRepository)

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("interview-guide-generator")


class GeneratedGuideContent(BaseModel):
    """Generated content from LLM."""

    questions: str
    context_definition: str
    context_examples: str


class InterviewGuideGeneratorService:
    """
    Service for generating interview guides using LLM.

    Generates questions, context definitions, and examples based on
    experiment metadata (name, hypothesis, description).
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        interview_guide_repo: InterviewGuideRepository | None = None):
        """
        Initialize the service.

        Args:
            llm_client: LLM client for API calls (default: global singleton)
            interview_guide_repo: Repository for saving guides
        """
        self.llm = llm_client or get_llm_client()
        self.interview_guide_repo = interview_guide_repo or InterviewGuideRepository()
        self.logger = logger.bind(component="interview_guide_generator")

    def _build_prompt(
        self,
        name: str,
        hypothesis: str,
        description: str | None) -> str:
        """
        Build the prompt for interview guide generation.

        Args:
            name: Experiment name/title
            hypothesis: Research hypothesis
            description: Optional detailed description

        Returns:
            Formatted prompt string
        """
        description_text = description if description else "Não fornecida"

        # Build prompt in parts to avoid long lines
        intro = (
            "Você é um pesquisador UX especializado em criar roteiros de entrevistas qualitativas."
        )

        context_info = f"""## Informações do Experimento

**Título:** {name}

**Hipótese:** {hypothesis}

**Descrição:** {description_text}"""

        json_structure = """{
    "questions": "<tema_central>. <pergunta_especifica_1>? <pergunta_especifica_2>?",
    "context_definition": "<briefing_do_contexto_da_pesquisa>",
    "context_examples": "positives [<pos1>|<pos2>] ; nwutral=[<neu1>|<neu2>] ; negatives [<neg1>|<neg2>]"
}"""

        questions_example = (
            '"Experiências de compra online. Como você se sente ao fazer '
            'compras pela internet? O que te faz desistir de uma compra?"'
        )

        context_def_example = '"Entrevista sobre experiências e opiniões relacionadas a compras na Amazon.e/ou em outras lojas online."'

        context_examples_example = (
            '"negative: No natal passado fui comprar um presente para minha mãe na Amazon.com e o pedido atrasou duas semanas, chegou depois do natal. Fiquei muito frustrado porque era um presente especial. Outra vez, semana passada eu precisava de um carregador urgente, comprei com entrega rápida mas veio o modelo errado. Tive que devolver e esperar mais uma semana, me senti enganado.',
            "positive: No natal passado fui comprar um presente para minha mãe na Amazon.com e chegou super rápido, antes do prazo até. Fiquei impressionado com a eficiência. Semana passada eu precisava de um carregador urgente, usei o 1-clique e no dia seguinte já estava na minha casa. Me senti muito bem atendido, virei fã.",
            'neutral: Eu sempre ouço falar da Amazon.com e do tal botão de comprar com 1 clique, mas sinceramente nunca experimentei. Faço minhas compras mais em lojas físicas mesmo, não tenho muito costume de comprar online."')

        return f"""{intro}

Com base nas informações abaixo sobre um experimento de pesquisa, gere um guia
de entrevista estruturado.

{context_info}

## Instruções

Gere um JSON com a seguinte estrutura:

{json_structure}

### Detalhamento:

1. **questions**: Uma string contendo:
   - Um tema central que resume o foco da pesquisa
   - Uma ou duas perguntas específicas relacionadas à hipótese
   - Exemplo: {questions_example}

2. **context_definition**: Um briefing curto (2-3 frases) que contextualiza:
   - O cenário da pesquisa
   - O que queremos entender do usuário
   - Exemplo: {context_def_example}

3. **context_examples**: Seis exemplos separados por "|" (pipe):
   - 2 exemplos POSITIVOS: experiências anteriores boas
   - 2 exemplos NEUTROS: experiências comuns/cotidianas
   - 2 exemplos NEGATIVOS: experiências frustrantes ou problemáticas
   - Cada exemplo deve ser uma frase curta descrevendo uma situação real
   - Exemplo: {context_examples_example}

## Regras Importantes

- Os exemplos devem ser realistas e relacionados ao contexto do experimento
- As perguntas devem ser abertas (não sim/não)
- O context_definition deve ser neutro e não induzir respostas
- Mantenha tudo em português brasileiro

Responda APENAS com o JSON, sem explicações adicionais."""

    async def generate_content(
        self,
        name: str,
        hypothesis: str,
        description: str | None = None) -> GeneratedGuideContent:
        """
        Generate interview guide content using LLM.

        Args:
            name: Experiment name
            hypothesis: Research hypothesis
            description: Optional description

        Returns:
            GeneratedGuideContent with questions, context, and examples

        Raises:
            ValueError: If LLM response is invalid
            RuntimeError: If LLM call fails
        """
        with _tracer.start_as_current_span(
            "InterviewGuideGenerator: generate_content",
            attributes={
                "experiment_name": name,
                "has_description": description is not None,
            }) as span:
            prompt = self._build_prompt(name, hypothesis, description)
            self.logger.info(f"Generating interview guide for: {name}")

            try:
                # Use complete_json for structured response
                response = self.llm.complete_json(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    operation_name="Interview Guide Generation")

                # Parse JSON response
                data = json.loads(response)

                # Validate required fields
                required_fields = ["questions", "context_definition", "context_examples"]
                for field in required_fields:
                    if field not in data:
                        raise ValueError(f"Missing required field: {field}")

                content = GeneratedGuideContent(
                    questions=data["questions"],
                    context_definition=data["context_definition"],
                    context_examples=data["context_examples"])

                self.logger.info(f"Interview guide generated successfully for: {name}")
                if span:
                    span.set_attribute("questions_length", len(content.questions))
                    span.set_attribute("context_length", len(content.context_definition))

                return content

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM response as JSON: {e}")
                if span:
                    span.set_attribute("error", f"JSON parse error: {e}")
                raise ValueError(f"Invalid JSON response from LLM: {e}") from e

            except Exception as e:
                self.logger.error(f"Interview guide generation failed: {e}")
                if span:
                    span.set_attribute("error", str(e))
                raise RuntimeError(f"Failed to generate interview guide: {e}") from e

    async def generate_for_experiment(
        self,
        experiment_id: str,
        name: str,
        hypothesis: str,
        description: str | None = None) -> InterviewGuide:
        """
        Generate and save interview guide for an experiment.

        Args:
            experiment_id: ID of the experiment
            name: Experiment name
            hypothesis: Research hypothesis
            description: Optional description

        Returns:
            Created InterviewGuide entity

        Raises:
            ValueError: If guide already exists or generation fails
            RuntimeError: If LLM call fails
        """
        with _tracer.start_as_current_span(
            "InterviewGuideGenerator: generate_for_experiment",
            attributes={
                "experiment_id": experiment_id,
                "experiment_name": name,
            }):
            # Check if guide already exists
            existing = self.interview_guide_repo.get_by_experiment_id(experiment_id)
            if existing is not None:
                self.logger.warning(
                    f"Interview guide already exists for experiment: {experiment_id}"
                )
                return existing

            # Generate content via LLM
            content = await self.generate_content(name, hypothesis, description)

            # Create and save guide
            now = datetime.now(timezone.utc)
            guide = InterviewGuide(
                experiment_id=experiment_id,
                context_definition=content.context_definition,
                questions=content.questions,
                context_examples=content.context_examples,
                created_at=now,
                updated_at=None)

            created_guide = self.interview_guide_repo.create(guide)
            self.logger.info(f"Interview guide created for experiment: {experiment_id}")

            return created_guide

    def generate_for_experiment_sync(
        self,
        experiment_id: str,
        name: str,
        hypothesis: str,
        description: str | None = None) -> InterviewGuide:
        """
        Synchronous wrapper for generate_for_experiment.

        For use in non-async contexts. Creates event loop if needed.

        Args:
            experiment_id: ID of the experiment
            name: Experiment name
            hypothesis: Research hypothesis
            description: Optional description

        Returns:
            Created InterviewGuide entity
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is None:
            # No event loop running, create one
            return asyncio.run(
                self.generate_for_experiment(experiment_id, name, hypothesis, description)
            )
        else:
            # Event loop already running, schedule as task
            # This should not happen in typical usage, but handle gracefully
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.generate_for_experiment(experiment_id, name, hypothesis, description))
                return future.result()


async def generate_interview_guide_async(
    experiment_id: str,
    name: str,
    hypothesis: str,
    description: str | None = None) -> InterviewGuide | None:
    """
    Standalone async function to generate interview guide.

    Convenience function for background task usage.

    Args:
        experiment_id: ID of the experiment
        name: Experiment name
        hypothesis: Research hypothesis
        description: Optional description

    Returns:
        Created InterviewGuide or None if failed
    """
    service = InterviewGuideGeneratorService()
    try:
        return await service.generate_for_experiment(experiment_id, name, hypothesis, description)
    except Exception as e:
        logger.error(f"Background interview guide generation failed for {experiment_id}: {e}")
        return None


if __name__ == "__main__":
    """Validation block for interview guide generator."""
    import sys

    print("=== Interview Guide Generator Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Import works
    total_tests += 1
    try:
        from synth_lab.services.interview_guide_generator_service import (
            GeneratedGuideContent,
            InterviewGuideGeneratorService)

        print("✓ All imports successful")
    except Exception as e:
        all_validation_failures.append(f"Import: {e}")

    # Test 2: Service initialization
    total_tests += 1
    try:
        service = InterviewGuideGeneratorService()
        assert service.llm is not None
        assert service.interview_guide_repo is not None
        print("✓ Service initializes correctly")
    except Exception as e:
        all_validation_failures.append(f"Service init: {e}")

    # Test 3: Prompt building
    total_tests += 1
    try:
        service = InterviewGuideGeneratorService()
        prompt = service._build_prompt(
            name="Checkout 1-clique",
            hypothesis="Usuários preferem checkout simplificado",
            description="Testar nova experiência de compra")
        assert "Checkout 1-clique" in prompt
        assert "Usuários preferem checkout simplificado" in prompt
        assert "questions" in prompt
        assert "context_definition" in prompt
        assert "context_examples" in prompt
        print("✓ Prompt building includes all required elements")
    except Exception as e:
        all_validation_failures.append(f"Prompt building: {e}")

    # Test 4: Prompt handles None description
    total_tests += 1
    try:
        service = InterviewGuideGeneratorService()
        prompt = service._build_prompt(
            name="Test",
            hypothesis="Test hypothesis",
            description=None)
        assert "Não fornecida" in prompt
        print("✓ Prompt handles None description correctly")
    except Exception as e:
        all_validation_failures.append(f"Prompt None description: {e}")

    # Test 5: GeneratedGuideContent model works
    total_tests += 1
    try:
        content = GeneratedGuideContent(
            questions="Tema central. Pergunta 1? Pergunta 2?",
            context_definition="Contexto da pesquisa.",
            context_examples="pos1|pos2|neu1|neu2|neg1|neg2")
        assert content.questions is not None
        assert content.context_definition is not None
        assert content.context_examples is not None
        print("✓ GeneratedGuideContent model works correctly")
    except Exception as e:
        all_validation_failures.append(f"GeneratedGuideContent: {e}")

    # Final validation result
    print()
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Interview guide generator service is validated and ready for use")
        sys.exit(0)
