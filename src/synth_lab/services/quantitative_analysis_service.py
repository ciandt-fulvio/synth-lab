"""
Quantitative analysis service for synth-lab.

Orchestrates causal model generation, edge selection management,
Monte Carlo simulation, and AI interpretations.

References:
    - Spec: specs/042-quantitative-analysis/spec.md
    - Prompts: Apêndice A (DAG_SYSTEM), Apêndice B (INTERP_SYSTEM)
    - OpenAI Chat Completions: https://platform.openai.com/docs/api-reference/chat
    - Phoenix Tracing: https://docs.arize.com/phoenix

Sample usage:
    service = QuantitativeAnalysisService()
    model = service.generate_causal_model("exp_12345678")
"""

import json
import secrets

from loguru import logger

from synth_lab.domain.entities.causal_model import generate_causal_model_id
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.causal_model_repository import CausalModelRepository
from synth_lab.repositories.experiment_repository import ExperimentRepository
from synth_lab.repositories.simulation_run_repository import SimulationRunRepository
from synth_lab.repositories.synth_repository import SynthRepository
from synth_lab.services.interview_guide_generator_service import (
    InterviewGuideGeneratorService,
)
from synth_lab.services.simulation_engine import (
    compute_raw_interpretations,
    compute_segments,
    extract_user_vars,
    run_monte_carlo,
    run_sensitivity,
)

_tracer = get_tracer("quantitative-analysis-service")

# ============================================================================
# DAG_SYSTEM prompt (Apêndice A from spec)
# ============================================================================

DAG_SYSTEM_PROMPT = """You are an expert in causal inference, product experimentation, and behavioral modeling for a Brazilian financial institution.

Given an experiment description, generate a causal DAG where each edge is an ASSERTION about how a variable affects another.

RULES:
- 7-10 nodes, 7-10 edges. Last node = outcome (adoption/conversion/engagement).
- CRITICAL DAG STRUCTURE — 3 layers:
  1. DEMOGRAPHIC ROOTS (left): "Idade", "Renda", "Escolaridade" as root nodes (no incoming edges).
  2. MEDIATING VARIABLES (middle): Behavioral/psychological constructs (e.g., "Confiança", "Percepção de Valor").
  3. OUTCOME (right): Final adoption node.
  Every demographic root must have at least 1 outgoing edge.
- Available userVar values (ONLY): ageNorm, incomeNorm, eduNorm, digitalCapability, familySizeNorm, hasVisualDisab, hasMotorDisab, riskAversion, institutionalTrust, frictionTolerance
  ALL are normalized [0,1].
- Demographic→Mediator: ageNorm (for Idade), incomeNorm (for Renda), eduNorm (for Escolaridade).

CRITICAL — EDGE FORMAT:
Each edge is an ASSERTION (statement), NOT a question. The PM responds with agreement level.

CRITICAL — EDGE HEADER:
Instead of "statement", each edge has a "header" field. This is a SHORT contextual intro:
  Format: "Quanto [target] é influenciado(a) por [source concept]"
  Example: "Quanto a Familiaridade Digital é influenciada pela idade"

CRITICAL — OPTIONS (5 self-contained sentences):
Each option has: text, mu, sigma.
- "text" is a COMPLETE, self-contained sentence that the PM reads and agrees/disagrees with.
- mu is [0,1] coupling strength. sigma is uncertainty fraction. BOTH ARE HIDDEN from PM.
- The PM sees ONLY the text.

The 5 options MUST follow this exact pattern (strongest agreement first, weakest last):
  Option 0: text = strong effect claim.                      mu=0.80, sigma=0.15
  Option 1: text = significant effect claim.                 mu=0.65, sigma=0.25
  Option 2: text = "Não sei dizer se [X] impacta [Y]"       mu=0.50, sigma=0.50
  Option 3: text = weak/uncertain effect claim.              mu=0.30, sigma=0.25
  Option 4: text = no effect claim.                          mu=0.15, sigma=0.15

THESE mu/sigma VALUES ARE FIXED. Do NOT change them.

RULES FOR OPTION TEXT:
- Option 0 must be the STRONGEST claim, with specificity
- Option 1 is strong but less absolute
- Option 2 ALWAYS starts with "Não sei dizer se..." — this is the uncertainty option
- Option 3 acknowledges some weak relationship but with hedging language
- Option 4 flatly denies the relationship
- ALL options are complete Portuguese sentences.

CRITICAL — "direction" field:
Each edge MUST include a "direction" field: 1 (direct/positive) or -1 (inverse/negative).

CRITICAL — VARIED DEFAULTS:
- "default" is NOT always 2. Be OPINIONATED based on common sense about the experiment.
- At least 2 edges should have default != 2. At least 1 should be 0,1 or 3,4.

Node names SHORT (max 25 chars). Portuguese BR.
interceptMu: -0.3 to 0.5. interceptSigma: 0.3 to 0.5.

Respond with ONLY valid JSON:
{
  "label": "string",
  "interceptMu": number,
  "interceptSigma": number,
  "nodes": ["string"...],
  "edges": [{
    "id": "string",
    "from": "string",
    "to": "string",
    "userVar": "string",
    "direction": 1 or -1,
    "header": "string",
    "options": [{"text":"string","mu":number,"sigma":number}...5 items],
    "default": number
  }...]
}"""


# ============================================================================
# INTERP_SYSTEM prompt (Apêndice B from spec)
# ============================================================================

INTERP_SYSTEM_PROMPT = """Você é um consultor sênior de estratégia de produto. Você ajuda product managers a decidir próximos passos com base nos resultados de simulação.

Você receberá a descrição do experimento, o tipo de seção, estatísticas brutas E os dados completos de análise de sensibilidade.

REGRAS:
- Escreva em Português BR. 2-4 frases no máximo.
- Seja ESPECÍFICO para este experimento — referencie o produto/funcionalidade real.
- Responda APENAS com o texto, sem aspas, sem markdown.

INSTRUÇÕES POR SEÇÃO:

SE section = "Distribuição":
- SEMPRE comece com: "Com 80% de confiança, a taxa de adoção fica entre X% e Y%."
- Depois analise a incerteza: se alta, explique QUAIS premissas (dos dados de sensibilidade) estão gerando mais incerteza e o que o PM pode fazer SEM rodar uma entrevista completa (ex: desk research, benchmarks de concorrentes, análise de dados internos).
- Se a incerteza for baixa, diga que é um bom sinal e sugira próximos passos.

SE section = "Segmentos":
- Foque na implicação prática: qual segmento abordar primeiro, se as diferenças justificam um rollout em fases.
- Referencie segmentos específicos pelo nome.

SE section = "Sensibilidade":
- Foque nas 1-2 premissas de maior impacto e que pesquisa ou dado específico poderia resolver a incerteza.
- Seja concreto: "Para validar se [premissa], analise dados de uso do app atual filtrado por faixa etária" — não dê conselhos genéricos."""


class QuantitativeAnalysisService:
    """Service for causal model generation, simulation, and interpretation.

    Handles DAG generation via LLM, edge selection persistence,
    Monte Carlo simulation, and AI interpretations.
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        causal_model_repo: CausalModelRepository | None = None,
        experiment_repo: ExperimentRepository | None = None,
        simulation_run_repo: SimulationRunRepository | None = None,
        synth_repo: SynthRepository | None = None,
        interview_guide_service: InterviewGuideGeneratorService | None = None,
    ):
        self.llm = llm_client or get_llm_client()
        self.causal_model_repo = causal_model_repo or CausalModelRepository()
        self.experiment_repo = experiment_repo or ExperimentRepository()
        self.simulation_run_repo = simulation_run_repo or SimulationRunRepository()
        self.synth_repo = synth_repo or SynthRepository()
        self.interview_guide_service = (
            interview_guide_service or InterviewGuideGeneratorService(llm_client=self.llm)
        )
        self.logger = logger.bind(component="quantitative_analysis")

    def generate_causal_model(self, experiment_id: str) -> dict:
        """
        Generate a causal DAG for an experiment via LLM.

        Deletes any existing model for this experiment (CASCADE on edges),
        then generates a new one via gpt-5.1.

        Args:
            experiment_id: Parent experiment ID.

        Returns:
            Dict with model data (id, label, nodes, edges, etc.).

        Raises:
            ValueError: If experiment not found or missing required fields.
            RuntimeError: If LLM returns invalid JSON after retries.
        """
        with _tracer.start_as_current_span(
            "QuantitativeAnalysis: generate_causal_model",
            attributes={
                "experiment_id": experiment_id,
                "operation.type": "dag_generation",
            },
        ) as span:
            # Load experiment context
            experiment = self.experiment_repo.get_by_id(experiment_id)
            if experiment is None:
                raise ValueError(f"Experiment not found: {experiment_id}")

            name = experiment.name
            hypothesis = experiment.hypothesis
            description = getattr(experiment, "description", None) or ""

            if not name or not hypothesis:
                raise ValueError(
                    f"Experiment {experiment_id} missing name or hypothesis"
                )

            # Delete existing model if any
            self.causal_model_repo.delete_by_experiment(experiment_id)

            # Build user message with experiment context
            user_message = (
                f"Experimento: {name}\n"
                f"Hipótese: {hypothesis}\n"
            )
            if description:
                user_message += f"Descrição: {description}\n"

            # Call LLM
            self.logger.info(f"Generating causal model for experiment: {experiment_id}")
            response_text = self.llm.complete_json(
                messages=[
                    {"role": "system", "content": DAG_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                model="gpt-5.1",
                temperature=0.7,
                operation_name="DAG Generation (gpt-5.1)",
            )

            # Parse LLM response
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"LLM returned invalid JSON: {e}") from e

            # Map LLM response keys to our schema
            model_id = generate_causal_model_id()
            edges_data = []
            for edge_raw in data.get("edges", []):
                edges_data.append({
                    "id": edge_raw["id"],
                    "from_node": edge_raw["from"],
                    "to_node": edge_raw["to"],
                    "user_var": edge_raw["userVar"],
                    "direction": edge_raw["direction"],
                    "header": edge_raw["header"],
                    "options": edge_raw["options"],
                    "default_option": edge_raw["default"],
                    "selected_option": None,
                })

            # Save to database
            orm_model = self.causal_model_repo.create_with_edges(
                model_id=model_id,
                experiment_id=experiment_id,
                label=data.get("label", "Modelo Causal"),
                intercept_mu=data.get("interceptMu", 0.1),
                intercept_sigma=data.get("interceptSigma", 0.4),
                nodes=data.get("nodes", []),
                edges=edges_data,
                raw_llm_response=data,
            )

            if span:
                span.set_attribute("model_id", model_id)
                span.set_attribute("node_count", len(data.get("nodes", [])))
                span.set_attribute("edge_count", len(edges_data))

            self.logger.info(
                f"Causal model generated: {model_id} "
                f"({len(data.get('nodes', []))} nodes, {len(edges_data)} edges)"
            )

            return self._model_to_dict(orm_model)

    def get_causal_model(self, experiment_id: str) -> dict | None:
        """
        Get the current causal model for an experiment.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Dict with model data, or None if no model exists.
        """
        orm_model = self.causal_model_repo.get_by_experiment(experiment_id)
        if orm_model is None:
            return None
        return self._model_to_dict(orm_model)

    def update_edge_selections(
        self,
        experiment_id: str,
        selections: dict[str, int],
    ) -> dict:
        """
        Update edge selections for the experiment's causal model.

        Args:
            experiment_id: Experiment ID.
            selections: Dict of {edge_id: selected_option_index}.

        Returns:
            Dict with {updated_count, all_answered, answered_count, total_edges}.

        Raises:
            ValueError: If no causal model exists for the experiment.
        """
        orm_model = self.causal_model_repo.get_by_experiment(experiment_id)
        if orm_model is None:
            raise ValueError(
                f"No causal model for experiment: {experiment_id}"
            )

        result = self.causal_model_repo.update_edge_selections(
            causal_model_id=orm_model.id,
            selections=selections,
        )

        # Reload model to get current state
        orm_model = self.causal_model_repo.get_by_experiment(experiment_id)
        total_edges = len(orm_model.edges) if orm_model else 0
        answered_count = sum(
            1 for e in (orm_model.edges if orm_model else [])
            if e.selected_option is not None
        )

        return {
            "updated_count": result["updated"],
            "all_answered": answered_count == total_edges,
            "answered_count": answered_count,
            "total_edges": total_edges,
        }

    def run_simulation(self, experiment_id: str) -> dict:
        """Run Monte Carlo simulation with current edge selections.

        Loads synths from the experiment's group, extracts userVars,
        runs simulation, computes segments and sensitivity, then
        generates AI interpretations.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Dict with full simulation results.

        Raises:
            ValueError: If no model or synths found.
        """
        with _tracer.start_as_current_span(
            "QuantitativeAnalysis: run_simulation",
            attributes={
                "experiment_id": experiment_id,
                "operation.type": "monte_carlo_simulation",
            },
        ) as span:
            # Load causal model
            orm_model = self.causal_model_repo.get_by_experiment(experiment_id)
            if orm_model is None:
                raise ValueError(f"No causal model for experiment: {experiment_id}")

            # Build edges list and selections dict
            edges_data = []
            selections = {}
            for e in orm_model.edges:
                edge_dict = {
                    "id": e.id,
                    "from_node": e.from_node,
                    "to_node": e.to_node,
                    "user_var": e.user_var,
                    "direction": e.direction,
                    "header": e.header,
                    "options": e.options,
                    "default_option": e.default_option,
                }
                edges_data.append(edge_dict)
                # Use selected_option if available, else default
                selections[e.id] = (
                    e.selected_option if e.selected_option is not None
                    else e.default_option
                )

            # Load synths from experiment's group
            synths_raw = self._load_synths_raw(experiment_id)
            if not synths_raw:
                raise ValueError(
                    f"No synths found for experiment: {experiment_id}"
                )

            n_synths = len(synths_raw)
            user_vars = [e["user_var"] for e in edges_data]
            user_var_matrix = extract_user_vars(synths_raw, user_vars)

            self.logger.info(
                f"Running simulation: {n_synths} synths, "
                f"{len(edges_data)} edges, 3000 iterations"
            )

            # Run main simulation
            mc_result = run_monte_carlo(
                edges_data, selections, user_var_matrix,
                orm_model.intercept_mu, orm_model.intercept_sigma,
                n_iterations=3000,
            )

            # Compute segments
            segments = compute_segments(
                edges_data, selections, synths_raw, user_var_matrix,
                orm_model.intercept_mu, orm_model.intercept_sigma,
            )

            # Run sensitivity analysis
            sensitivity = run_sensitivity(
                edges_data, selections, user_var_matrix,
                orm_model.intercept_mu, orm_model.intercept_sigma,
            )

            # Compute raw interpretations
            raw_interps = compute_raw_interpretations(
                mc_result["stats"], segments, sensitivity
            )

            # Save simulation run
            run_id = f"sr_{secrets.token_hex(4)}"
            orm_run = self.simulation_run_repo.create_run(
                run_id=run_id,
                experiment_id=experiment_id,
                causal_model_id=orm_model.id,
                n_iterations=3000,
                n_synths=n_synths,
                selections=selections,
                stats=mc_result["stats"],
                distribution=mc_result["distribution"],
                segments=segments,
                sensitivity=sensitivity,
            )

            if span:
                span.set_attribute("run_id", run_id)
                span.set_attribute("n_synths", n_synths)
                span.set_attribute("mean_adoption", mc_result["stats"]["mean"])

            self.logger.info(
                f"Simulation complete: {run_id} "
                f"(mean={mc_result['stats']['mean']}%)"
            )

            # Generate AI interpretations (async, 3 parallel calls)
            experiment = self.experiment_repo.get_by_id(experiment_id)
            exp_context = (
                f"{experiment.name}: {experiment.hypothesis}"
                if experiment else experiment_id
            )

            interpretations = self._generate_interpretations_sync(
                run_id=run_id,
                experiment_context=exp_context,
                raw_interps=raw_interps,
                sensitivity=sensitivity,
            )

            return self._run_to_dict(
                orm_run, mc_result["distribution"],
                segments, sensitivity, interpretations,
            )

    def get_simulation_results(self, experiment_id: str) -> dict | None:
        """Get the latest simulation results for an experiment.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Dict with simulation results, or None if no runs exist.
        """
        orm_run = self.simulation_run_repo.get_latest_by_experiment(experiment_id)
        if orm_run is None:
            return None

        # Build interpretations from ORM
        interps = {}
        for interp in (orm_run.interpretations or []):
            interps[interp.section] = {
                "raw_text": interp.raw_text,
                "ai_text": interp.ai_text,
            }

        return self._run_to_dict(
            orm_run,
            orm_run.distribution,
            orm_run.segments,
            orm_run.sensitivity,
            interps,
        )

    def generate_interview_guide(self, experiment_id: str) -> dict:
        """Generate interview guide from the latest simulation sensitivity.

        Calls the interview guide generator service with the top sensitivity
        premisses. Raises ValueError if no simulation results exist.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Dict with status confirmation.
        """
        orm_run = self.simulation_run_repo.get_latest_by_experiment(experiment_id)
        if orm_run is None:
            raise ValueError(
                f"No simulation results for experiment: {experiment_id}"
            )

        experiment = self.experiment_repo.get_by_id(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        sensitivity = orm_run.sensitivity or []

        with _tracer.start_as_current_span("generate-interview-guide"):
            self.interview_guide_service.generate_from_simulation_sync(
                experiment_id=experiment_id,
                name=experiment.name,
                hypothesis=experiment.hypothesis,
                sensitivity=sensitivity,
                description=getattr(experiment, "description", None),
            )
            self.logger.info(
                f"Interview guide generated for: {experiment_id}"
            )

        return {"status": "ok", "experiment_id": experiment_id}

    def _generate_interpretations_sync(
        self,
        run_id: str,
        experiment_context: str,
        raw_interps: dict[str, str],
        sensitivity: list[dict],
    ) -> dict[str, dict]:
        """Generate AI interpretations for all 3 sections.

        Calls gpt-4o-mini for each section with the INTERP_SYSTEM prompt.
        Returns dict of {section: {raw_text, ai_text}}.
        """
        sections = ["distribution", "segments", "sensitivity"]
        section_labels = {
            "distribution": "Distribuição",
            "segments": "Segmentos",
            "sensitivity": "Sensibilidade",
        }

        # Format sensitivity data for context
        sens_text = "\n".join(
            f"- {s['header']}: impacto {s['impact']}pp"
            for s in sensitivity[:5]
        )

        results = {}
        interpretations_to_save = []

        for section in sections:
            raw_text = raw_interps.get(section, "")
            user_msg = (
                f"Experimento: {experiment_context}\n"
                f"Seção: {section_labels[section]}\n"
                f"Dados brutos: {raw_text}\n"
                f"Análise de sensibilidade:\n{sens_text}"
            )

            with _tracer.start_as_current_span(
                f"QuantitativeAnalysis: interpret_{section}",
                attributes={
                    "run_id": run_id,
                    "section": section,
                    "operation.type": "ai_interpretation",
                },
            ):
                try:
                    ai_text = self.llm.complete(
                        messages=[
                            {"role": "system", "content": INTERP_SYSTEM_PROMPT},
                            {"role": "user", "content": user_msg},
                        ],
                        model="gpt-4o-mini",
                        temperature=0.5,
                        operation_name=f"Interpretation: {section}",
                    )
                except Exception as e:
                    self.logger.warning(
                        f"AI interpretation failed for {section}: {e}"
                    )
                    ai_text = raw_text  # Fallback to raw text

            interp_id = f"ai_{secrets.token_hex(4)}"
            results[section] = {"raw_text": raw_text, "ai_text": ai_text}
            interpretations_to_save.append({
                "id": interp_id,
                "simulation_run_id": run_id,
                "section": section,
                "raw_text": raw_text,
                "ai_text": ai_text,
                "model": "gpt-4o-mini",
            })

        # Save interpretations to DB
        self.simulation_run_repo.create_interpretations(interpretations_to_save)

        return results

    def _auto_generate_interview_guide(
        self,
        experiment_id: str,
        experiment,
        sensitivity: list[dict],
    ) -> None:
        """Auto-generate interview guide from simulation sensitivity results.

        Runs silently — errors are logged but do not block the simulation response.
        Overwrites any existing interview guide (FR-017).
        """
        try:
            self.interview_guide_service.generate_from_simulation_sync(
                experiment_id=experiment_id,
                name=experiment.name if experiment else experiment_id,
                hypothesis=experiment.hypothesis if experiment else "",
                sensitivity=sensitivity,
                description=getattr(experiment, "description", None),
            )
            self.logger.info(
                f"Interview guide auto-generated for: {experiment_id}"
            )
        except Exception as e:
            self.logger.error(
                f"Failed to auto-generate interview guide for {experiment_id}: {e}"
            )

    def _load_synths_raw(self, experiment_id: str) -> list[dict]:
        """Load raw synth data dicts for an experiment's synth group."""
        from sqlalchemy import select

        from synth_lab.models.orm.experiment import Experiment as ExperimentORM
        from synth_lab.models.orm.synth import Synth as SynthORM

        # Get experiment's synth_group_id
        stmt = select(ExperimentORM).where(ExperimentORM.id == experiment_id)
        experiment = self.synth_repo.session.execute(stmt).scalar_one_or_none()
        if not experiment or not experiment.synth_group_id:
            return []

        # Load synths from group
        stmt = (
            select(SynthORM)
            .where(
                SynthORM.synth_group_id == experiment.synth_group_id,
                SynthORM.data.isnot(None),
            )
            .limit(500)
        )
        orm_synths = list(self.synth_repo.session.execute(stmt).scalars().all())

        return [
            {"id": s.id, "data": s.data if isinstance(s.data, dict) else {}}
            for s in orm_synths
        ]

    def _run_to_dict(
        self,
        orm_run,
        distribution: list,
        segments: dict,
        sensitivity: list,
        interpretations: dict,
    ) -> dict:
        """Convert simulation run data to API response dict."""
        return {
            "id": orm_run.id,
            "experiment_id": orm_run.experiment_id,
            "causal_model_id": orm_run.causal_model_id,
            "n_iterations": orm_run.n_iterations,
            "n_synths": orm_run.n_synths,
            "stats": orm_run.stats,
            "distribution": distribution,
            "segments": segments,
            "sensitivity": sensitivity,
            "interpretations": interpretations,
            "created_at": orm_run.created_at.isoformat() if hasattr(orm_run.created_at, 'isoformat') else str(orm_run.created_at),
        }

    def _model_to_dict(self, orm_model) -> dict:
        """Convert ORM model + edges to API response dict."""
        edges = []
        for e in orm_model.edges:
            edges.append({
                "id": e.id,
                "from_node": e.from_node,
                "to_node": e.to_node,
                "user_var": e.user_var,
                "direction": e.direction,
                "header": e.header,
                "options": e.options,
                "default_option": e.default_option,
                "selected_option": e.selected_option,
            })

        return {
            "id": orm_model.id,
            "experiment_id": orm_model.experiment_id,
            "label": orm_model.label,
            "intercept_mu": orm_model.intercept_mu,
            "intercept_sigma": orm_model.intercept_sigma,
            "nodes": orm_model.nodes,
            "edges": edges,
            "created_at": orm_model.created_at.isoformat() if hasattr(orm_model.created_at, 'isoformat') else str(orm_model.created_at),
        }


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Service instantiation
    total_tests += 1
    try:
        service = QuantitativeAnalysisService()
        if service.llm is None:
            all_validation_failures.append("LLM client should not be None")
        if service.causal_model_repo is None:
            all_validation_failures.append("Causal model repo should not be None")
    except Exception as e:
        all_validation_failures.append(f"Service init failed: {e}")

    # Test 2: DAG_SYSTEM_PROMPT contains key elements
    total_tests += 1
    try:
        if "causal DAG" not in DAG_SYSTEM_PROMPT:
            all_validation_failures.append("Prompt missing 'causal DAG'")
        if "userVar" not in DAG_SYSTEM_PROMPT:
            all_validation_failures.append("Prompt missing 'userVar'")
        if "ageNorm" not in DAG_SYSTEM_PROMPT:
            all_validation_failures.append("Prompt missing 'ageNorm'")
    except Exception as e:
        all_validation_failures.append(f"Prompt check failed: {e}")

    # Test 3: Methods exist
    total_tests += 1
    try:
        service = QuantitativeAnalysisService()
        methods = [
            "generate_causal_model",
            "get_causal_model",
            "update_edge_selections",
            "run_simulation",
            "get_simulation_results",
        ]
        for method in methods:
            if not hasattr(service, method):
                all_validation_failures.append(f"Missing method: {method}")
    except Exception as e:
        all_validation_failures.append(f"Method check failed: {e}")

    if all_validation_failures:
        print(
            f"VALIDATION FAILED - {len(all_validation_failures)} of "
            f"{total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"VALIDATION PASSED - All {total_tests} tests produced expected results"
        )
        sys.exit(0)
