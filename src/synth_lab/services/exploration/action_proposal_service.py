"""
ActionProposalService for LLM-assisted scenario exploration.

Generates improvement proposals via LLM for scenario nodes.
The LLM receives context about the current scenario and proposes
concrete actions with estimated impacts.

References:
    - Spec: specs/024-llm-scenario-exploration/spec.md
    - Data model: specs/024-llm-scenario-exploration/data-model.md

Sample usage:
    from synth_lab.services.exploration.action_proposal_service import ActionProposalService

    service = ActionProposalService()
    proposals = service.generate_proposals(node, experiment)

Expected output:
    List of ActionProposal with action, category, rationale, impacts
"""

import json
from typing import Any

from loguru import logger

from synth_lab.domain.entities.action_proposal import (
    VALID_CATEGORIES,
    ActionProposal)
from synth_lab.domain.entities.experiment import Experiment
from synth_lab.domain.entities.scenario_node import ScenarioNode
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.exploration_repository import ExplorationRepository
from synth_lab.services.exploration.action_catalog import (
    ActionCatalogService,
    get_action_catalog_service)

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("action-proposal-service")

# LLM configuration
LLM_MODEL = "gpt-4.1-mini"
LLM_TIMEOUT = 30.0  # 30 seconds per spec


class ProposalGenerationError(Exception):
    """Raised when proposal generation fails."""

    pass


class ActionProposalService:
    """
    Service for generating action proposals via LLM.

    Generates 1-2 concrete improvement proposals for scenario nodes,
    each with an action description, category, rationale, and
    estimated impacts on scorecard parameters.
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        catalog_service: ActionCatalogService | None = None,
        repository: ExplorationRepository | None = None):
        """
        Initialize the action proposal service.

        Args:
            llm_client: LLM client instance. If None, uses global client.
            catalog_service: Action catalog service. If None, uses global service.
            repository: Exploration repository. If None, creates new instance.
        """
        self.llm = llm_client or get_llm_client()
        self.catalog = catalog_service or get_action_catalog_service()
        self.repository = repository or ExplorationRepository()
        self.logger = logger.bind(component="action_proposal_service")

    def generate_proposals(
        self,
        node: ScenarioNode,
        experiment: Experiment,
        max_proposals: int = 4) -> list[ActionProposal]:
        """
        Generate improvement proposals for a scenario node.

        Uses LLM to analyze the current scenario and propose concrete
        actions that could improve the success rate.

        Args:
            node: The scenario node to generate proposals for.
            experiment: The experiment context (name, hypothesis, scorecard).
            max_proposals: Maximum number of proposals to generate (1-4).

        Returns:
            List of ActionProposal objects (0-4 items).

        Raises:
            ProposalGenerationError: If LLM call fails repeatedly.
        """
        # Build path context for span name with parent info
        path = self.repository.get_path_to_node(node.id)
        if len(path) > 1:
            # Get current and parent actions
            current_action = node.short_action or node.action_applied or "?"
            parent_node = path[-2]  # Second to last is parent
            parent_action = parent_node.short_action or parent_node.action_applied or "ROOT"

            # Truncate if too long
            if len(parent_action) > 20:
                parent_action = parent_action[:17] + "..."
            if len(current_action) > 20:
                current_action = current_action[:17] + "..."

            span_name = f"ActionProposal d{node.depth} | {parent_action} → {current_action}"
        else:
            # Root node
            span_name = f"ActionProposal d{node.depth} | ROOT"

        with _tracer.start_as_current_span(
            span_name,
            attributes={
                "node_id": node.id,
                "experiment_id": experiment.id,
                "node_depth": node.depth,
                "path_length": len(path),
                "current_action": node.action_applied or "root",
                "parent_action": path[-2].action_applied if len(path) > 1 else None,
            }):
            prompt = self._build_prompt(node, experiment, max_proposals)

            self.logger.info(
                f"Generating proposals for node {node.id} "
                f"(depth={node.depth}, success_rate={node.get_success_rate():.2%})"
            )

            try:
                response = self.llm.complete_json(
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt},
                    ],
                    model=LLM_MODEL,
                    temperature=0.7,  # Some creativity for diverse proposals
                    operation_name="Generate Action Proposals")

                proposals = self._parse_response(response)
                valid_proposals = self._validate_proposals(proposals)

                self.logger.info(
                    f"Generated {len(valid_proposals)} valid proposals for node {node.id}"
                )
                return valid_proposals

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM response: {e}")
                return []  # Return empty list, don't interrupt exploration
            except Exception as e:
                self.logger.error(f"Proposal generation failed: {e}")
                return []  # Return empty list, don't interrupt exploration

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        return """Voce e um especialista em otimizacao de produtos digitais.
Sua tarefa e propor acoes concretas e incrementais para melhorar os resultados de um experimento.

REGRAS IMPORTANTES:
1. Proponha entre 1 e 4 acoes por resposta
2. Cada acao deve ser CONCRETA e ESPECIFICA (nao generica)
3. Cada acao deve ter uma CATEGORIA do catalogo fornecido
4. Os IMPACTOS devem ser pequenos e realistas (entre -0.10 e +0.10)
5. Foque em reduzir complexity, perceived_risk e time_to_value para aumentar success_rate
6. O rationale deve explicar POR QUE essa acao ajudaria
7. O short_action deve ser um RESUMO em 3 palavras (maximo 30 caracteres)
8. NUNCA repita acoes que ja foram aplicadas no caminho atual (veja secao "Historico")

FORMATO DE RESPOSTA (JSON):
{
    "proposals": [
        {
            "action": "Descricao concreta da acao",
            "short_action": "Resumo 3 palavras",
            "category": "categoria_do_catalogo",
            "rationale": "Por que isso ajudaria",
            "impacts": {
                "complexity": -0.02,
                "time_to_value": -0.01
            }
        }
    ]
}

EXEMPLOS de short_action:
- "Simplificar formulario" (para acao de reduzir campos)
- "Tutorial interativo" (para acao de onboarding)
- "Indicador progresso" (para acao de feedback visual)"""

    def _build_prompt(
        self,
        node: ScenarioNode,
        experiment: Experiment,
        max_proposals: int) -> str:
        """Build the user prompt for the LLM."""
        # Get catalog context
        catalog_context = self.catalog.get_prompt_context()

        # Get scorecard data
        scorecard = experiment.scorecard_data
        feature_name = scorecard.feature_name if scorecard else experiment.name
        description = scorecard.description_text if scorecard else ""

        # Get current parameters
        params = node.scorecard_params
        results = node.simulation_results

        # Get path from root to current node (for action history)
        path = self.repository.get_path_to_node(node.id)

        # Build prompt
        prompt_parts = [
            "## Contexto do Experimento",
            "",
            f"**Nome do Experimento**: {experiment.name}",
            f"**Hipotese**: {experiment.hypothesis}",
            f"**Feature**: {feature_name}",
        ]

        if description:
            prompt_parts.append(f"**Descricao**: {description}")

        # Add action history (if not root node)
        if len(path) > 1:
            prompt_parts.extend([
                "",
                "## Historico de Acoes Aplicadas",
                "",
                "**IMPORTANTE**: NAO repita acoes que ja foram aplicadas abaixo.",
                "",
            ])
            for i, path_node in enumerate(path[1:], 1):  # Skip root node
                action_text = path_node.action_applied or "N/A"
                category_text = path_node.action_category or "N/A"
                prompt_parts.append(
                    f"{i}. [{category_text}] {action_text}"
                )

        prompt_parts.extend([
            "",
            "## Parametros Atuais do Scorecard",
            "",
            f"- Complexity: {params.complexity:.2f}",
            f"- Initial Effort: {params.initial_effort:.2f}",
            f"- Perceived Risk: {params.perceived_risk:.2f}",
            f"- Time to Value: {params.time_to_value:.2f}",
            "",
            "## Resultados Observados",
            "",
        ])

        if results:
            prompt_parts.extend([
                f"- Success Rate: {results.success_rate:.2%}",
                f"- Fail Rate: {results.fail_rate:.2%}",
                f"- Did Not Try Rate: {results.did_not_try_rate:.2%}",
            ])
        else:
            prompt_parts.append("(simulacao pendente)")

        prompt_parts.extend([
            "",
            catalog_context,
            "",
            "## Instrucoes",
            "",
            f"Proponha ate {max_proposals} acoes concretas para melhorar o success_rate.",
            "Cada acao deve ter categoria valida do catalogo e impactos estimados.",
            "EVITE repeticoes das acoes ja aplicadas no historico acima.",
            "Retorne APENAS o JSON, sem explicacoes adicionais.",
        ])

        return "\n".join(prompt_parts)

    def _parse_response(self, response: str) -> list[dict[str, Any]]:
        """Parse the LLM response into raw proposal dicts."""
        data = json.loads(response)
        proposals = data.get("proposals", [])

        if not isinstance(proposals, list):
            self.logger.warning("LLM response 'proposals' is not a list")
            return []

        return proposals

    def _validate_proposals(
        self,
        proposals: list[dict[str, Any]]) -> list[ActionProposal]:
        """Validate and convert raw proposals to ActionProposal objects."""
        valid = []

        for i, raw in enumerate(proposals):
            try:
                # Validate required fields
                required = ["action", "category", "rationale", "impacts", "short_action"]
                if not all(k in raw for k in required):
                    self.logger.warning(f"Proposal {i} missing required fields")
                    continue

                # Validate category
                category = raw["category"]
                if not self.catalog.validate_category(category):
                    self.logger.warning(
                        f"Proposal {i} has invalid category: {category}. "
                        f"Valid: {VALID_CATEGORIES}"
                    )
                    continue

                # Validate impacts
                impacts = raw["impacts"]
                if not isinstance(impacts, dict):
                    self.logger.warning(f"Proposal {i} impacts is not a dict")
                    continue

                # Check impact values are in range
                valid_impacts = {}
                for param, delta in impacts.items():
                    if not isinstance(delta, (int, float)):
                        self.logger.warning(f"Proposal {i} impact {param} is not numeric")
                        continue
                    if abs(delta) > 0.10:
                        self.logger.warning(
                            f"Proposal {i} impact {param}={delta} exceeds [-0.10, +0.10]"
                        )
                        # Clamp to valid range
                        delta = max(-0.10, min(0.10, delta))
                    valid_impacts[param] = delta

                if not valid_impacts:
                    self.logger.warning(f"Proposal {i} has no valid impacts")
                    continue

                # Create ActionProposal
                proposal = ActionProposal(
                    action=str(raw["action"]),
                    category=category,
                    rationale=str(raw["rationale"]),
                    short_action=str(raw["short_action"])[:30],
                    impacts=valid_impacts)
                valid.append(proposal)

            except Exception as e:
                self.logger.warning(f"Failed to validate proposal {i}: {e}")
                continue

        return valid[:4]  # Limit to 4 proposals max


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Service instantiation
    total_tests += 1
    try:
        service = ActionProposalService()
        if service.llm is None:
            all_validation_failures.append("LLM client should not be None")
        if service.catalog is None:
            all_validation_failures.append("Catalog service should not be None")
    except Exception as e:
        all_validation_failures.append(f"Service instantiation failed: {e}")

    # Test 2: Validate proposals with valid data
    total_tests += 1
    try:
        service = ActionProposalService()
        raw_proposals = [
            {
                "action": "Add tooltip on hover",
                "short_action": "Tooltip hover",
                "category": "ux_interface",
                "rationale": "Reduces cognitive load",
                "impacts": {"complexity": -0.02, "time_to_value": -0.01},
            },
            {
                "action": "Add progress indicator",
                "short_action": "Indicador progresso",
                "category": "flow",
                "rationale": "Shows progress",
                "impacts": {"perceived_risk": -0.03},
            },
        ]
        valid = service._validate_proposals(raw_proposals)
        if len(valid) != 2:
            all_validation_failures.append(f"Should validate 2 proposals: {len(valid)}")
    except Exception as e:
        all_validation_failures.append(f"Validate proposals failed: {e}")

    # Test 3: Validate proposals with invalid category
    total_tests += 1
    try:
        service = ActionProposalService()
        raw_proposals = [
            {
                "action": "Some action",
                "short_action": "Some short",
                "category": "invalid_category",
                "rationale": "Some reason",
                "impacts": {"complexity": -0.02},
            },
        ]
        valid = service._validate_proposals(raw_proposals)
        if len(valid) != 0:
            all_validation_failures.append(f"Invalid category should be rejected: {len(valid)}")
    except Exception as e:
        all_validation_failures.append(f"Invalid category test failed: {e}")

    # Test 4: Validate proposals with out-of-range impact (should clamp)
    total_tests += 1
    try:
        service = ActionProposalService()
        raw_proposals = [
            {
                "action": "Big change",
                "short_action": "Grande mudanca",
                "category": "ux_interface",
                "rationale": "Reason",
                "impacts": {"complexity": -0.20},  # Out of range
            },
        ]
        valid = service._validate_proposals(raw_proposals)
        if len(valid) != 1:
            all_validation_failures.append(f"Should clamp and accept: {len(valid)}")
        elif valid[0].impacts["complexity"] != -0.10:
            all_validation_failures.append(
                f"Impact should be clamped to -0.10: {valid[0].impacts['complexity']}"
            )
    except Exception as e:
        all_validation_failures.append(f"Clamp test failed: {e}")

    # Test 5: Parse response JSON
    total_tests += 1
    try:
        service = ActionProposalService()
        response = json.dumps({
            "proposals": [
                {
                    "action": "Test action",
                    "short_action": "Test short",
                    "category": "onboarding",
                    "rationale": "Test rationale",
                    "impacts": {"initial_effort": -0.05},
                }
            ]
        })
        proposals = service._parse_response(response)
        if len(proposals) != 1:
            all_validation_failures.append(f"Should parse 1 proposal: {len(proposals)}")
    except Exception as e:
        all_validation_failures.append(f"Parse response failed: {e}")

    # Test 6: Missing required fields (including short_action)
    total_tests += 1
    try:
        service = ActionProposalService()
        raw_proposals = [
            {
                "action": "Incomplete proposal",
                # Missing category, rationale, impacts, short_action
            },
        ]
        valid = service._validate_proposals(raw_proposals)
        if len(valid) != 0:
            all_validation_failures.append(f"Incomplete proposal should be rejected: {len(valid)}")
    except Exception as e:
        all_validation_failures.append(f"Missing fields test failed: {e}")

    # Test 7: Build prompt generates valid content
    total_tests += 1
    try:
        from unittest.mock import MagicMock

        from synth_lab.domain.entities.experiment import (
            Experiment,
            ScorecardData,
            ScorecardDimension)
        from synth_lab.domain.entities.scenario_node import (
            ScenarioNode,
            ScorecardParams,
            SimulationResults)

        experiment = Experiment(
            name="Test Experiment",
            hypothesis="Test hypothesis",
            scorecard_data=ScorecardData(
                feature_name="Test Feature",
                description_text="Test description",
                complexity=ScorecardDimension(score=0.45),
                initial_effort=ScorecardDimension(score=0.30),
                perceived_risk=ScorecardDimension(score=0.25),
                time_to_value=ScorecardDimension(score=0.40)))

        node = ScenarioNode(
            exploration_id="expl_12345678",
            depth=0,
            scorecard_params=ScorecardParams(
                complexity=0.45,
                initial_effort=0.30,
                perceived_risk=0.25,
                time_to_value=0.40),
            simulation_results=SimulationResults(
                success_rate=0.25,
                fail_rate=0.45,
                did_not_try_rate=0.30))

        # Mock repository to avoid database dependency
        mock_repo = MagicMock()
        mock_repo.get_path_to_node.return_value = [node]  # Return just root node

        service = ActionProposalService(repository=mock_repo)
        prompt = service._build_prompt(node, experiment, 4)

        if "Test Experiment" not in prompt:
            all_validation_failures.append("Prompt should contain experiment name")
        if "Complexity: 0.45" not in prompt:
            all_validation_failures.append("Prompt should contain complexity")
        if "Success Rate: 25.00%" not in prompt:
            all_validation_failures.append("Prompt should contain success rate")
        if "Catalogo de Acoes" not in prompt:
            all_validation_failures.append("Prompt should contain catalog context")
        # Root node (path length = 1) should NOT have action history
        if "Historico de Acoes" in prompt:
            all_validation_failures.append("Root node should not have action history")
    except Exception as e:
        all_validation_failures.append(f"Build prompt test failed: {e}")

    # Test 8: System prompt is valid
    total_tests += 1
    try:
        service = ActionProposalService()
        system_prompt = service._get_system_prompt()
        if "JSON" not in system_prompt:
            all_validation_failures.append("System prompt should mention JSON")
        if "proposals" not in system_prompt:
            all_validation_failures.append("System prompt should mention proposals")
        if "-0.10" not in system_prompt and "+0.10" not in system_prompt:
            all_validation_failures.append("System prompt should mention impact limits")
        if "short_action" not in system_prompt:
            all_validation_failures.append("System prompt should mention short_action")
        if "1 e 4 acoes" not in system_prompt:
            all_validation_failures.append("System prompt should mention 1-4 actions")
        if "Historico" not in system_prompt:
            all_validation_failures.append("System prompt should mention history warning")
    except Exception as e:
        all_validation_failures.append(f"System prompt test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
