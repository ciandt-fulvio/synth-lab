"""
Quantitative analysis service for synth-lab.

Orchestrates causal model generation (2-pass LLM), edge selection management,
Monte Carlo simulation with enriched DAG (5 node types), and AI interpretations.

References:
    - Spec: specs/042-quantitative-analysis/spec.md
    - OpenAI Chat Completions: https://platform.openai.com/docs/api-reference/chat
    - Phoenix Tracing: https://docs.arize.com/phoenix

Sample usage:
    service = QuantitativeAnalysisService()
    model = service.generate_causal_model("exp_12345678")
"""

import random
import secrets

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.causal_model import (
    PRODUCT_CALIBRATION_VALUES,
    generate_causal_model_id,
)
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.causal_model_repository import CausalModelRepository
from synth_lab.repositories.experiment_repository import ExperimentRepository
from synth_lab.repositories.simulation_run_repository import SimulationRunRepository
from synth_lab.repositories.synth_repository import SynthRepository
from synth_lab.services.dag_generator import generate_options, generate_topology
from synth_lab.services.interview_guide_generator_service import (
    InterviewGuideGeneratorService,
)
from synth_lab.services.sensitivity_deriver import load_sensitivity_rules
from synth_lab.services.simulation_engine import (
    apply_product_scenario,
    build_base_node_values,
    build_node_values,
    compute_raw_interpretations,
    compute_segments_v2,
    run_monte_carlo_v2,
    run_monte_carlo_v2_per_synth,
    run_sensitivity_v2,
)
from synth_lab.services.simulation_summary_generator_service import (
    SimulationSummaryGeneratorService,
)

_tracer = get_tracer("quantitative-analysis-service")

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

    Handles DAG generation via LLM (2-pass), edge selection persistence,
    Monte Carlo simulation with enriched DAG, and AI interpretations.
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
        self.interview_guide_service = interview_guide_service or InterviewGuideGeneratorService(
            llm_client=self.llm
        )
        self.logger = logger.bind(component="quantitative_analysis")

    def generate_causal_model(self, experiment_id: str) -> dict:
        """
        Generate an enriched causal DAG for an experiment via 2-pass LLM.

        Pass 1: Topology (nodes, edges, configs) via gpt-5-mini.
        Pass 2: Likert options for calibratable edges via gpt-5-mini.

        Args:
            experiment_id: Parent experiment ID.

        Returns:
            Dict with model data (id, label, nodes, edges, node_metadata, etc.).

        Raises:
            ValueError: If experiment not found or missing required fields.
            RuntimeError: If LLM returns invalid JSON after retries.
        """
        with _tracer.start_as_current_span(
            "QuantitativeAnalysis: generate_causal_model",
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "experiment_id": experiment_id,
                "operation.type": "dag_generation_v2",
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
                raise ValueError(f"Experiment {experiment_id} missing name or hypothesis")

            # Delete existing model if any
            self.causal_model_repo.delete_by_experiment(experiment_id)

            # Load YAML sensitivity configs
            yaml_data = load_sensitivity_rules()
            yaml_sensitivities = yaml_data.get("sensitivities", {})

            # Build experiment context string
            experiment_context = f"Experimento: {name}\nHipótese: {hypothesis}\n"
            if description:
                experiment_context += f"Descrição: {description}\n"

            # Pass 1: Generate topology
            self.logger.info(f"Generating DAG topology for experiment: {experiment_id}")
            topology = generate_topology(self.llm, experiment_context, yaml_sensitivities)

            # Remove isolated nodes (no edges referencing them)
            edges = topology.get("edges", [])
            connected = set()
            for e in edges:
                connected.add(e.get("from", ""))
                connected.add(e.get("to", ""))
            original_count = len(topology.get("nodes", []))
            topology["nodes"] = [
                n for n in topology.get("nodes", []) if n["name"] in connected
            ]
            removed = original_count - len(topology["nodes"])
            if removed:
                self.logger.warning(f"Removed {removed} isolated node(s) from topology")

            # Pass 2: Generate options for interaction nodes
            self.logger.info(f"Generating node premissa options for experiment: {experiment_id}")
            options_data = generate_options(self.llm, topology)

            # Index node options by name
            options_by_name = {n["name"]: n for n in options_data.get("nodes", [])}

            # Build node_metadata from topology nodes
            node_metadata: dict[str, dict] = {}
            node_names: list[str] = []
            for node_raw in topology.get("nodes", []):
                node_name = node_raw["name"]
                node_names.append(node_name)
                meta: dict = {
                    "name": node_name,
                    "node_type": node_raw["type"],
                }
                if node_raw.get("sensitivity_key"):
                    meta["sensitivity_key"] = node_raw["sensitivity_key"]
                if node_raw.get("custom_config"):
                    meta["custom_config"] = node_raw["custom_config"]
                if node_raw["type"] == "product":
                    meta["product_calibration"] = "medium"  # default
                    meta["product_description"] = node_raw.get("description", "")
                if node_raw.get("description"):
                    meta["description"] = node_raw["description"]

                # Merge premissa options for interaction nodes (from LLM Pass 2)
                if node_raw["type"] == "interaction":
                    node_opt = options_by_name.get(node_name, {})
                    meta["header"] = node_opt.get("header", f"Peso de {node_name}")
                    meta["options"] = node_opt.get("options", [])
                    meta["default_option"] = node_opt.get("default", 2)
                    meta["selected_option"] = None

                # Outcome options are built from interaction names (after loop)
                if node_raw["type"] == "outcome":
                    meta["selected_option"] = None

                node_metadata[node_name] = meta

            # Build outcome node options from interaction node names
            interaction_names = [
                n["name"] for n in topology.get("nodes", [])
                if n["type"] == "interaction"
            ]
            for node_name, meta in node_metadata.items():
                if meta.get("node_type") == "outcome" and interaction_names:
                    meta["header"] = (
                        f"Qual dos itens abaixo tem mais influência para {node_name}?"
                    )
                    meta["options"] = [
                        {"text": name, "mu": 0, "sigma": 0}
                        for name in interaction_names
                    ]
                    meta["default_option"] = 0
                    node_metadata[node_name] = meta

            # Build edges data (structural only — no Likert options on edges)
            model_id = generate_causal_model_id()
            edges_data = []
            for edge_raw in topology.get("edges", []):
                edge_id = edge_raw["id"]

                # Determine user_var if source is a known sensitivity
                src_meta = node_metadata.get(edge_raw["from"], {})
                user_var = None
                if src_meta.get("sensitivity_key") in {
                    "risk_aversion", "institutional_trust_level",
                    "friction_tolerance", "digital_capability",
                }:
                    _sens_to_var = {
                        "risk_aversion": "riskAversion",
                        "institutional_trust_level": "institutionalTrust",
                        "friction_tolerance": "frictionTolerance",
                        "digital_capability": "digitalCapability",
                    }
                    user_var = _sens_to_var.get(src_meta["sensitivity_key"])

                edge_dict: dict = {
                    "id": edge_id,
                    "from_node": edge_raw["from"],
                    "to_node": edge_raw["to"],
                    "direction": edge_raw.get("direction", 1),
                    "edge_type": edge_raw.get("edge_type", "likert"),
                    "weight": edge_raw.get("weight"),
                    "user_var": user_var,
                    "header": f"{edge_raw['from']} → {edge_raw['to']}",
                    "options": None,
                    "default_option": 0,
                    "selected_option": None,
                }
                edges_data.append(edge_dict)

            # Save to database
            raw_response = {"topology": topology, "options": options_data}
            orm_model = self.causal_model_repo.create_with_edges(
                model_id=model_id,
                experiment_id=experiment_id,
                label=topology.get("label", "Modelo Causal"),
                intercept_mu=topology.get("interceptMu", 0.1),
                intercept_sigma=topology.get("interceptSigma", 0.4),
                nodes=node_names,
                edges=edges_data,
                raw_llm_response=raw_response,
                node_metadata=node_metadata,
            )

            if span:
                span.set_attribute("model_id", model_id)
                span.set_attribute("node_count", len(node_names))
                span.set_attribute("edge_count", len(edges_data))

            self.logger.info(
                f"Causal model generated: {model_id} "
                f"({len(node_names)} nodes, {len(edges_data)} edges)"
            )

            return self._model_to_dict(orm_model)

    def get_causal_model(self, experiment_id: str) -> dict | None:
        """Get the current causal model for an experiment."""
        orm_model = self.causal_model_repo.get_by_experiment(experiment_id)
        if orm_model is None:
            return None
        return self._model_to_dict(orm_model)

    def update_edge_selections(
        self,
        experiment_id: str,
        selections: dict[str, int],
    ) -> dict:
        """Update edge selections for the experiment's causal model."""
        orm_model = self.causal_model_repo.get_by_experiment(experiment_id)
        if orm_model is None:
            raise ValueError(f"No causal model for experiment: {experiment_id}")

        result = self.causal_model_repo.update_edge_selections(
            causal_model_id=orm_model.id,
            selections=selections,
        )

        # Reload model to get current state
        orm_model = self.causal_model_repo.get_by_experiment(experiment_id)
        total_edges = len(orm_model.edges) if orm_model else 0
        answered_count = sum(
            1 for e in (orm_model.edges if orm_model else []) if e.selected_option is not None
        )

        return {
            "updated_count": result["updated"],
            "all_answered": answered_count == total_edges,
            "answered_count": answered_count,
            "total_edges": total_edges,
        }

    def update_node_selections(
        self,
        experiment_id: str,
        selections: dict[str, int],
    ) -> dict:
        """Update premissa selections for interaction/outcome nodes.

        Args:
            experiment_id: Experiment ID.
            selections: Dict of {node_name: selected_option_index}.

        Returns:
            Dict with {updated_count, all_answered, answered_count, total_nodes}.

        Raises:
            ValueError: If no model found.
        """
        orm_model = self.causal_model_repo.get_by_experiment(experiment_id)
        if orm_model is None:
            raise ValueError(f"No causal model for experiment: {experiment_id}")

        node_metadata = dict(orm_model.node_metadata or {})
        updated = 0

        for node_name, option_index in selections.items():
            meta = node_metadata.get(node_name, {})
            if meta.get("node_type") not in ("interaction", "outcome"):
                continue
            if not meta.get("options"):
                continue
            meta["selected_option"] = option_index
            node_metadata[node_name] = meta
            updated += 1

        self.causal_model_repo.update_node_metadata(orm_model.id, node_metadata)

        # Count calibratable nodes
        calibratable = [
            m for m in node_metadata.values()
            if m.get("node_type") in ("interaction", "outcome") and m.get("options")
        ]
        answered = sum(1 for m in calibratable if m.get("selected_option") is not None)

        return {
            "updated_count": updated,
            "all_answered": answered == len(calibratable),
            "answered_count": answered,
            "total_nodes": len(calibratable),
        }

    def update_product_calibrations(
        self,
        experiment_id: str,
        calibrations: dict[str, str],
    ) -> dict:
        """Update product node calibrations.

        Args:
            experiment_id: Experiment ID.
            calibrations: Dict of {node_name: "low"/"medium"/"high"}.

        Returns:
            Dict with {updated_count}.

        Raises:
            ValueError: If no model or invalid calibration values.
        """
        orm_model = self.causal_model_repo.get_by_experiment(experiment_id)
        if orm_model is None:
            raise ValueError(f"No causal model for experiment: {experiment_id}")

        node_metadata = dict(orm_model.node_metadata or {})
        updated = 0

        for node_name, calibration in calibrations.items():
            if calibration not in PRODUCT_CALIBRATION_VALUES:
                raise ValueError(
                    f"Invalid calibration '{calibration}' for '{node_name}'. "
                    f"Must be one of: {list(PRODUCT_CALIBRATION_VALUES)}"
                )
            meta = node_metadata.get(node_name, {})
            if meta.get("node_type") != "product":
                continue
            meta["product_calibration"] = calibration
            node_metadata[node_name] = meta
            updated += 1

        self.causal_model_repo.update_node_metadata(orm_model.id, node_metadata)
        return {"updated_count": updated}

    def run_simulation(self, experiment_id: str) -> dict:
        """Run Monte Carlo simulation with enriched DAG.

        Uses v2 simulation engine with 5 node types and pre-computed node values.

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
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "experiment_id": experiment_id,
                "operation.type": "monte_carlo_simulation_v2",
            },
        ) as span:
            # Load causal model
            orm_model = self.causal_model_repo.get_by_experiment(experiment_id)
            if orm_model is None:
                raise ValueError(f"No causal model for experiment: {experiment_id}")

            node_metadata = orm_model.node_metadata or {}

            # Build edges list
            edges_data = []
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
                    "edge_type": e.edge_type,
                    "weight": e.weight,
                }
                edges_data.append(edge_dict)

            # Build node selections from node_metadata premissas
            node_selections: dict[str, int] = {}
            for node_name, meta in node_metadata.items():
                if meta.get("node_type") in ("interaction", "outcome") and meta.get("options"):
                    node_selections[node_name] = (
                        meta["selected_option"]
                        if meta.get("selected_option") is not None
                        else meta.get("default_option", 2)
                    )

            # Load synths
            synths_raw = self._load_synths_raw(experiment_id)
            if not synths_raw:
                raise ValueError(f"No synths found for experiment: {experiment_id}")

            n_synths = len(synths_raw)

            # Build sensitivity configs from YAML + custom
            yaml_data = load_sensitivity_rules()
            yaml_sensitivities = yaml_data.get("sensitivities", {})
            sensitivity_configs: dict[str, dict] = dict(yaml_sensitivities)

            # Add custom configs from node_metadata
            for meta in node_metadata.values():
                if meta.get("node_type") == "sensitivity" and meta.get("custom_config"):
                    sens_key = meta.get("sensitivity_key", "")
                    sensitivity_configs[sens_key] = meta["custom_config"]

            # Map product calibrations to values
            product_values: dict[str, float] = {}
            for node_name, meta in node_metadata.items():
                if meta.get("node_type") == "product":
                    calibration = meta.get("product_calibration", "medium")
                    product_values[node_name] = PRODUCT_CALIBRATION_VALUES.get(calibration, 0.5)

            self.logger.info(
                f"Running v2 simulation: {n_synths} synths, {len(edges_data)} edges"
            )

            # Build node values
            node_vals = build_node_values(
                synths_raw, node_metadata, edges_data,
                product_values, sensitivity_configs,
            )

            # Find outcome edges (edges pointing to the outcome node)
            outcome_node = None
            for node_name, meta in node_metadata.items():
                if meta.get("node_type") == "outcome":
                    outcome_node = node_name
                    break

            if outcome_node is None:
                # Fallback: last node in the list
                outcome_node = orm_model.nodes[-1] if orm_model.nodes else ""

            outcome_edges = [e for e in edges_data if e["to_node"] == outcome_node]

            # Run main simulation
            mc_result = run_monte_carlo_v2(
                outcome_edges, node_vals, node_selections, node_metadata,
                orm_model.intercept_mu, orm_model.intercept_sigma,
                n_iterations=3000,
            )

            # Compute segments
            segments = compute_segments_v2(
                outcome_edges, node_vals, node_selections, node_metadata,
                synths_raw,
                orm_model.intercept_mu, orm_model.intercept_sigma,
            )

            # Run sensitivity analysis
            sensitivity = run_sensitivity_v2(
                outcome_edges, node_vals, node_selections, node_metadata,
                orm_model.intercept_mu, orm_model.intercept_sigma,
            )

            # Compute raw interpretations
            raw_interps = compute_raw_interpretations(mc_result["stats"], segments, sensitivity)

            # Save simulation run
            run_id = f"sr_{secrets.token_hex(4)}"
            orm_run = self.simulation_run_repo.create_run(
                run_id=run_id,
                experiment_id=experiment_id,
                causal_model_id=orm_model.id,
                n_iterations=3000,
                n_synths=n_synths,
                selections=node_selections,
                stats=mc_result["stats"],
                distribution=mc_result["distribution"],
                segments=segments,
                sensitivity=sensitivity,
            )

            if span:
                span.set_attribute("run_id", run_id)
                span.set_attribute("n_synths", n_synths)
                span.set_attribute("mean_adoption", mc_result["stats"]["mean"])

            self.logger.info(f"Simulation complete: {run_id} (mean={mc_result['stats']['mean']}%)")

            # Generate AI interpretations
            experiment = self.experiment_repo.get_by_id(experiment_id)
            exp_context = (
                f"{experiment.name}: {experiment.hypothesis}" if experiment else experiment_id
            )

            interpretations = self._generate_interpretations_sync(
                run_id=run_id,
                experiment_context=exp_context,
                raw_interps=raw_interps,
                sensitivity=sensitivity,
            )

            # Mark simulation summary as generating
            from synth_lab.domain.entities.experiment_document import DocumentType
            from synth_lab.services.document_service import DocumentService

            try:
                DocumentService().start_generation(
                    experiment_id,
                    DocumentType.SIMULATION_SUMMARY,
                )
            except Exception as e:
                self.logger.warning(f"Could not mark summary as generating: {e}")

            # Auto-generate reports (non-blocking)
            import threading

            threading.Thread(
                target=self._auto_generate_simulation_summary,
                args=(experiment_id,),
                daemon=True,
            ).start()

            threading.Thread(
                target=self._auto_generate_interview_guide,
                args=(experiment_id, experiment, sensitivity),
                daemon=True,
            ).start()

            return self._run_to_dict(
                orm_run,
                mc_result["distribution"],
                segments,
                sensitivity,
                interpretations,
            )

    def get_simulation_results(self, experiment_id: str) -> dict | None:
        """Get the latest simulation results for an experiment."""
        orm_run = self.simulation_run_repo.get_latest_by_experiment(experiment_id)
        if orm_run is None:
            return None

        interps = {}
        for interp in orm_run.interpretations or []:
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
        """Generate interview guide from the latest simulation sensitivity."""
        orm_run = self.simulation_run_repo.get_latest_by_experiment(experiment_id)
        if orm_run is None:
            raise ValueError(f"No simulation results for experiment: {experiment_id}")

        experiment = self.experiment_repo.get_by_id(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        sensitivity = orm_run.sensitivity or []

        with _tracer.start_as_current_span(
            "QuantitativeAnalysis: generate_interview_guide",
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "experiment_id": experiment_id,
            },
        ):
            self.interview_guide_service.generate_from_simulation_sync(
                experiment_id=experiment_id,
                name=experiment.name,
                hypothesis=experiment.hypothesis,
                sensitivity=sensitivity,
                description=getattr(experiment, "description", None),
            )
            self.logger.info(f"Interview guide generated for: {experiment_id}")

        return {"status": "ok", "experiment_id": experiment_id}

    def _generate_interpretations_sync(
        self,
        run_id: str,
        experiment_context: str,
        raw_interps: dict[str, str],
        sensitivity: list[dict],
    ) -> dict[str, dict]:
        """Generate AI interpretations for all 3 sections."""
        sections = ["distribution", "segments", "sensitivity"]
        section_labels = {
            "distribution": "Distribuição",
            "segments": "Segmentos",
            "sensitivity": "Sensibilidade",
        }

        sens_text = "\n".join(f"- {s['header']}: impacto {s['impact']}pp" for s in sensitivity[:5])

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
                    SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
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
                    self.logger.warning(f"AI interpretation failed for {section}: {e}")
                    ai_text = raw_text

            interp_id = f"ai_{secrets.token_hex(4)}"
            results[section] = {"raw_text": raw_text, "ai_text": ai_text}
            interpretations_to_save.append(
                {
                    "id": interp_id,
                    "simulation_run_id": run_id,
                    "section": section,
                    "raw_text": raw_text,
                    "ai_text": ai_text,
                    "model": "gpt-4o-mini",
                }
            )

        self.simulation_run_repo.create_interpretations(interpretations_to_save)
        return results

    def _auto_generate_interview_guide(
        self, experiment_id: str, experiment, sensitivity: list[dict],
    ) -> None:
        """Auto-generate interview guide in background."""
        try:
            self.interview_guide_service.generate_from_simulation_sync(
                experiment_id=experiment_id,
                name=experiment.name if experiment else experiment_id,
                hypothesis=experiment.hypothesis if experiment else "",
                sensitivity=sensitivity,
                description=getattr(experiment, "description", None),
            )
            self.logger.info(f"Interview guide auto-generated for: {experiment_id}")
        except Exception as e:
            self.logger.error(f"Failed to auto-generate interview guide for {experiment_id}: {e}")

    def generate_simulation_summary(self, experiment_id: str) -> dict:
        """Manually (re)generate simulation summary report."""
        orm_run = self.simulation_run_repo.get_latest_by_experiment(experiment_id)
        if orm_run is None:
            raise ValueError(f"No simulation results for experiment: {experiment_id}")

        from synth_lab.domain.entities.experiment_document import DocumentType
        from synth_lab.services.document_service import DocumentService

        doc_service = DocumentService()
        doc_service.start_generation(experiment_id, DocumentType.SIMULATION_SUMMARY)

        try:
            generator = SimulationSummaryGeneratorService(llm_client=self.llm)
            generator.generate(experiment_id)
        except Exception as e:
            self.logger.error(f"Failed to generate simulation summary: {e}")
            doc_service.fail_generation(
                experiment_id, DocumentType.SIMULATION_SUMMARY, error_message=str(e),
            )
            raise

        return {"status": "ok", "experiment_id": experiment_id}

    def _auto_generate_simulation_summary(self, experiment_id: str) -> None:
        """Auto-generate simulation summary in background."""
        try:
            generator = SimulationSummaryGeneratorService(llm_client=self.llm)
            generator.generate(experiment_id)
            self.logger.info(f"Simulation summary auto-generated for: {experiment_id}")
        except Exception as e:
            self.logger.error(
                f"Failed to auto-generate simulation summary for {experiment_id}: {e}"
            )
            try:
                from synth_lab.domain.entities.experiment_document import DocumentType
                from synth_lab.services.document_service import DocumentService

                DocumentService().fail_generation(
                    experiment_id, DocumentType.SIMULATION_SUMMARY, error_message=str(e),
                )
            except Exception:
                pass

    def _generate_random_scenarios(
        self,
        node_metadata: dict,
        n_scenarios: int,
    ) -> list[dict[str, str]]:
        """Generate random product calibration scenarios.

        Each scenario samples {low, medium, high} independently for every
        product node. PM premissas (edges, interaction/outcome nodes) stay fixed.

        Args:
            node_metadata: DAG node metadata dict.
            n_scenarios: Number of scenarios to generate.

        Returns:
            List of dicts mapping product node names to calibration levels.
        """
        product_nodes = [
            name for name, meta in node_metadata.items()
            if meta.get("node_type") == "product"
        ]
        levels = ["low", "medium", "high"]
        return [
            {node: random.choice(levels) for node in product_nodes}
            for _ in range(n_scenarios)
        ]

    def run_multi_scenario_simulation(
        self,
        experiment_id: str,
        scenarios: list[dict[str, str]] | None = None,
        n_scenarios: int | None = None,
        n_repetitions: int = 10,
    ) -> dict:
        """Run multi-scenario simulation batch with per-synth results.

        If scenarios is None, auto-generates random scenarios by sampling
        {low, medium, high} for each product node.

        Args:
            experiment_id: Experiment ID.
            scenarios: Explicit product calibration dicts, or None for auto-gen.
            n_scenarios: Number of random scenarios (used only when scenarios is None).
                Falls back to SIMULATION_N_SCENARIOS config.
            n_repetitions: MC repetitions per synth (default 10).

        Returns:
            Dict with batch info and per-scenario results.
        """
        # Resolve scenario count for span attribute (before loading model)
        initial_n = len(scenarios) if scenarios else (n_scenarios or 0)

        with _tracer.start_as_current_span(
            "QuantitativeAnalysis: run_multi_scenario_simulation",
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "experiment_id": experiment_id,
                "operation.type": "multi_scenario_simulation",
                "n_scenarios": initial_n,
            },
        ) as span:
            # Load causal model
            orm_model = self.causal_model_repo.get_by_experiment(experiment_id)
            if orm_model is None:
                raise ValueError(f"No causal model for experiment: {experiment_id}")

            node_metadata = orm_model.node_metadata or {}

            # Auto-generate scenarios if not provided
            if scenarios is None:
                from synth_lab.infrastructure.config import SIMULATION_N_SCENARIOS

                effective_n = n_scenarios or SIMULATION_N_SCENARIOS
                scenarios = self._generate_random_scenarios(node_metadata, effective_n)
                self.logger.info(
                    f"Auto-generated {len(scenarios)} random scenarios "
                    f"for {sum(1 for m in node_metadata.values() if m.get('node_type') == 'product')} "
                    f"product nodes"
                )

            # Build edges list
            edges_data = []
            for e in orm_model.edges:
                edges_data.append({
                    "id": e.id,
                    "from_node": e.from_node,
                    "to_node": e.to_node,
                    "user_var": e.user_var,
                    "direction": e.direction,
                    "header": e.header,
                    "options": e.options,
                    "default_option": e.default_option,
                    "edge_type": e.edge_type,
                    "weight": e.weight,
                })

            # Build node selections
            node_selections: dict[str, int] = {}
            for node_name, meta in node_metadata.items():
                if meta.get("node_type") in ("interaction", "outcome") and meta.get("options"):
                    node_selections[node_name] = (
                        meta["selected_option"]
                        if meta.get("selected_option") is not None
                        else meta.get("default_option", 2)
                    )

            # Load ALL synths (no limit)
            synths_raw = self._load_synths_raw(experiment_id)
            if not synths_raw:
                raise ValueError(f"No synths found for experiment: {experiment_id}")

            n_synths = len(synths_raw)

            # Build sensitivity configs
            yaml_data = load_sensitivity_rules()
            yaml_sensitivities = yaml_data.get("sensitivities", {})
            sensitivity_configs: dict[str, dict] = dict(yaml_sensitivities)
            for meta in node_metadata.values():
                if meta.get("node_type") == "sensitivity" and meta.get("custom_config"):
                    sens_key = meta.get("sensitivity_key", "")
                    sensitivity_configs[sens_key] = meta["custom_config"]

            # Find outcome node and edges
            outcome_node = None
            for node_name, meta in node_metadata.items():
                if meta.get("node_type") == "outcome":
                    outcome_node = node_name
                    break
            if outcome_node is None:
                outcome_node = orm_model.nodes[-1] if orm_model.nodes else ""

            self.logger.info(
                f"Multi-scenario simulation: {len(scenarios)} scenarios, "
                f"{n_synths} synths, {n_repetitions} repetitions"
            )

            # Pre-compute invariant node values (demographic + sensitivity)
            base_values, sorted_names, child_parents = build_base_node_values(
                synths_raw, node_metadata, edges_data, sensitivity_configs,
            )

            # Pre-compute outcome edges (same for all scenarios)
            outcome_edges = [e for e in edges_data if e["to_node"] == outcome_node]

            # Create batch
            batch_id = f"sb_{secrets.token_hex(4)}"
            self.simulation_run_repo.create_batch(
                batch_id=batch_id,
                experiment_id=experiment_id,
                causal_model_id=orm_model.id,
                n_scenarios=len(scenarios),
                n_synths=n_synths,
                n_repetitions=n_repetitions,
            )

            scenario_results = []
            try:
                for scenario_idx, scenario_calibrations in enumerate(scenarios):
                    # Convert calibration strings to floats
                    product_values: dict[str, float] = {}
                    for node_name, meta in node_metadata.items():
                        if meta.get("node_type") == "product":
                            cal = scenario_calibrations.get(
                                node_name, meta.get("product_calibration", "medium")
                            )
                            product_values[node_name] = PRODUCT_CALIBRATION_VALUES.get(cal, 0.5)

                    # Apply scenario product values on top of cached base
                    node_vals = apply_product_scenario(
                        base_values, node_metadata, product_values,
                        sorted_names, child_parents, n_synths,
                    )

                    # Run per-synth MC simulation
                    mc_result = run_monte_carlo_v2_per_synth(
                        outcome_edges, node_vals, node_selections, node_metadata,
                        orm_model.intercept_mu, orm_model.intercept_sigma,
                        n_repetitions=n_repetitions,
                    )

                    # Build per-synth outcomes dict {synth_id: outcome}
                    per_synth_probs = mc_result["per_synth_probs"]
                    per_synth_outcomes = {
                        synth["id"]: round(float(per_synth_probs[i]), 2)
                        for i, synth in enumerate(synths_raw)
                    }

                    scenario_product_values = {
                        k: scenario_calibrations.get(k, "medium")
                        for k, m in node_metadata.items()
                        if m.get("node_type") == "product"
                    }

                    # Create simulation run (deferred commit)
                    run_id = f"sr_{secrets.token_hex(4)}"
                    self.simulation_run_repo.create_run(
                        run_id=run_id,
                        experiment_id=experiment_id,
                        causal_model_id=orm_model.id,
                        n_iterations=n_repetitions,
                        n_synths=n_synths,
                        selections=node_selections,
                        stats=mc_result["stats"],
                        distribution=mc_result["distribution"],
                        segments={},
                        sensitivity=[],
                        batch_id=batch_id,
                        product_values=scenario_product_values,
                        per_synth_outcomes=per_synth_outcomes,
                        auto_commit=False,
                    )

                    scenario_results.append({
                        "run_id": run_id,
                        "product_values": scenario_product_values,
                        "stats": mc_result["stats"],
                        "n_synths": n_synths,
                    })

                # Flush all runs + mark batch completed
                self.simulation_run_repo.flush_and_commit()
                self.simulation_run_repo.update_batch_status(batch_id, "completed")

            except Exception:
                self.simulation_run_repo.update_batch_status(batch_id, "failed")
                raise

            if span:
                span.set_attribute("batch_id", batch_id)
                span.set_attribute("n_synths", n_synths)

            return {
                "batch_id": batch_id,
                "experiment_id": experiment_id,
                "n_scenarios": len(scenarios),
                "n_synths": n_synths,
                "n_repetitions": n_repetitions,
                "status": "completed",
                "scenarios": scenario_results,
            }

    def _load_synths_raw(self, experiment_id: str) -> list[dict]:
        """Load raw synth data dicts for an experiment's synth group."""
        from sqlalchemy import select

        from synth_lab.models.orm.experiment import Experiment as ExperimentORM
        from synth_lab.models.orm.synth import Synth as SynthORM

        stmt = select(ExperimentORM).where(ExperimentORM.id == experiment_id)
        experiment = self.synth_repo.session.execute(stmt).scalar_one_or_none()
        if not experiment or not experiment.synth_group_id:
            return []

        stmt = (
            select(SynthORM)
            .where(
                SynthORM.synth_group_id == experiment.synth_group_id,
                SynthORM.data.isnot(None),
            )
        )
        orm_synths = list(self.synth_repo.session.execute(stmt).scalars().all())

        return [
            {"id": s.id, "data": s.data if isinstance(s.data, dict) else {}} for s in orm_synths
        ]

    def _run_to_dict(
        self, orm_run, distribution: list, segments: dict,
        sensitivity: list, interpretations: dict,
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
            "created_at": orm_run.created_at.isoformat()
            if hasattr(orm_run.created_at, "isoformat")
            else str(orm_run.created_at),
        }

    def _model_to_dict(self, orm_model) -> dict:
        """Convert ORM model + edges to API response dict."""
        edges = []
        for e in orm_model.edges:
            edges.append(
                {
                    "id": e.id,
                    "from_node": e.from_node,
                    "to_node": e.to_node,
                    "user_var": e.user_var,
                    "direction": e.direction,
                    "header": e.header,
                    "options": e.options or [],
                    "default_option": e.default_option,
                    "selected_option": e.selected_option,
                    "edge_type": e.edge_type,
                    "weight": e.weight,
                }
            )

        return {
            "id": orm_model.id,
            "experiment_id": orm_model.experiment_id,
            "label": orm_model.label,
            "intercept_mu": orm_model.intercept_mu,
            "intercept_sigma": orm_model.intercept_sigma,
            "nodes": orm_model.nodes,
            "node_metadata": orm_model.node_metadata,
            "edges": edges,
            "created_at": orm_model.created_at.isoformat()
            if hasattr(orm_model.created_at, "isoformat")
            else str(orm_model.created_at),
        }
