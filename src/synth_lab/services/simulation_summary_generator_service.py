"""
Simulation Summary Generator Service for synth-lab.

Generates rich markdown reports combining simulation results, interpretations,
synth group demographics, and interview guide content. Uses a hybrid approach:
- Data sections (tables, stats): built programmatically (deterministic)
- Interpretation sections: reuse existing AI interpretations from simulation run
- One LLM call: for "Descobertas Principais"

Saves documents to experiment_documents table using DocumentType.SIMULATION_SUMMARY.

References:
    - Pattern: services/research_summary_generator_service.py
    - DocumentService: services/document_service.py
    - SimulationRunRepository: repositories/simulation_run_repository.py
"""

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.experiment_document import DocumentType
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.experiment_repository import ExperimentRepository
from synth_lab.repositories.interview_guide_repository import InterviewGuideRepository
from synth_lab.repositories.simulation_run_repository import SimulationRunRepository
from synth_lab.services.document_service import DocumentService
from synth_lab.services.synth_group_service import SynthGroupService

_tracer = get_tracer("simulation-summary-generator")

# LLM prompt for generating holistic summary
_SUMMARY_LINES = [
    "Você é um consultor sênior de estratégia de produto",
    "em uma instituição financeira brasileira.",
    "",
    "Você recebe os resultados completos de uma simulação",
    "Monte Carlo de adoção de produto, incluindo",
    "estatísticas, segmentação e análise de sensibilidade.",
    "",
    "Produza uma seção de Descobertas Principais em Português BR:",
    "- 3-5 parágrafos sintetizando os achados mais importantes",
    "- Comece com o resultado geral (taxa média e intervalo)",
    "- Destaque segmentos com maior e menor propensão",
    "- Identifique premissas de maior impacto (sensibilidade)",
    "- Conclua: o experimento vale a pena prosseguir?",
    "",
    "REGRAS:",
    "- Português BR. Referencie o produto/funcionalidade real.",
    "- NÃO inclua tabelas de dados (já estão no relatório).",
    "- NÃO inclua títulos/headers markdown (## etc).",
    "- Responda APENAS com os parágrafos, sem preâmbulo.",
]
SUMMARY_SYSTEM_PROMPT = "\n".join(_SUMMARY_LINES)


class SimulationSummaryGeneratorService:
    """Generates simulation summary reports as experiment documents.

    Uses a template+LLM hybrid approach:
    - Programmatic sections: stats tables, histograms, rankings
    - Reused AI text: existing interpretations from the simulation run
    - Fresh LLM call: holistic summary ("Descobertas Principais")
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        document_service: DocumentService | None = None,
        simulation_run_repo: SimulationRunRepository | None = None,
        experiment_repo: ExperimentRepository | None = None,
        synth_group_service: SynthGroupService | None = None,
        interview_guide_repo: InterviewGuideRepository | None = None,
    ):
        self.llm = llm_client or get_llm_client()
        self.document_service = document_service or DocumentService()
        self.simulation_run_repo = simulation_run_repo or SimulationRunRepository()
        self.experiment_repo = experiment_repo or ExperimentRepository()
        self.synth_group_service = synth_group_service or SynthGroupService()
        self.interview_guide_repo = interview_guide_repo or InterviewGuideRepository()
        self._logger = logger.bind(component="simulation_summary_generator")

    def generate(
        self,
        experiment_id: str,
        model: str = "gpt-4o-mini",
    ) -> None:
        """Generate simulation summary report and save as experiment document.

        Args:
            experiment_id: Parent experiment ID.
            model: LLM model for the AI sections.
        """
        with _tracer.start_as_current_span(
            "SimulationSummaryGenerator: generate",
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "experiment_id": experiment_id,
                "model": model,
            },
        ) as span:
            # 1. Load experiment
            experiment = self.experiment_repo.get_by_id(experiment_id)
            if not experiment:
                raise ValueError(f"Experiment not found: {experiment_id}")

            exp_name = experiment.name or experiment_id
            exp_hypothesis = experiment.hypothesis or ""
            exp_description = getattr(experiment, "description", None) or ""

            # 2. Load latest simulation run
            orm_run = self.simulation_run_repo.get_latest_by_experiment(experiment_id)
            if orm_run is None:
                raise ValueError(f"No simulation results for: {experiment_id}")

            stats = orm_run.stats or {}
            distribution = orm_run.distribution or []
            segments = orm_run.segments or {}
            sensitivity = orm_run.sensitivity or []

            # Build interpretations dict
            interpretations: dict[str, dict] = {}
            for interp in orm_run.interpretations or []:
                interpretations[interp.section] = {
                    "raw_text": interp.raw_text,
                    "ai_text": interp.ai_text,
                }

            # 3. Load synth group statistics
            synth_group_id = getattr(experiment, "synth_group_id", None)
            group_stats = None
            if synth_group_id:
                try:
                    group_stats = self.synth_group_service.get_group_statistics(synth_group_id)
                except Exception as e:
                    self._logger.warning(f"Could not load group stats: {e}")

            # 4. Load interview guide (if exists)
            guide_markdown = None
            try:
                guide = self.interview_guide_repo.get_by_experiment_id(experiment_id)
                if guide and guide.questions:
                    guide_markdown = guide.questions
            except Exception as e:
                self._logger.warning(f"Could not load interview guide: {e}")

            # 5. Generate AI descobertas (1 LLM call)
            descobertas = self._generate_ai_sections(
                exp_name,
                exp_hypothesis,
                exp_description,
                stats,
                segments,
                sensitivity,
                model,
            )

            # 6. Assemble full markdown
            markdown = self._assemble_report(
                exp_name=exp_name,
                exp_hypothesis=exp_hypothesis,
                exp_description=exp_description,
                stats=stats,
                distribution=distribution,
                segments=segments,
                sensitivity=sensitivity,
                interpretations=interpretations,
                descobertas=descobertas,
                group_stats=group_stats,
                guide_markdown=guide_markdown,
                n_synths=orm_run.n_synths or 0,
                n_iterations=orm_run.n_iterations or 0,
            )

            if span:
                span.set_attribute("report_length", len(markdown))

            # 7. Save via document service
            self.document_service.save_document(
                experiment_id=experiment_id,
                document_type=DocumentType.SIMULATION_SUMMARY,
                markdown_content=markdown,
                source_id=None,
                model=model,
                metadata={
                    "simulation_run_id": orm_run.id,
                    "n_synths": orm_run.n_synths,
                    "n_iterations": orm_run.n_iterations,
                    "mean_adoption": stats.get("mean"),
                },
            )

            self._logger.info(
                f"Simulation summary generated for {experiment_id} ({len(markdown)} chars)"
            )

    def _generate_ai_sections(
        self,
        name: str,
        hypothesis: str,
        description: str,
        stats: dict,
        segments: dict,
        sensitivity: list[dict],
        model: str,
    ) -> str:
        """Generate AI descobertas section via single LLM call.

        Returns the descobertas text string.
        """
        # Build context for LLM
        stats_text = (
            f"Média: {stats.get('mean', 0):.1f}%, "
            f"Mediana: {stats.get('median', 0):.1f}%, "
            f"P10: {stats.get('p10', 0):.1f}%, "
            f"P90: {stats.get('p90', 0):.1f}%, "
            f"Desvio: {stats.get('std', 0):.1f}%"
        )

        # Segments summary
        segments_text_parts = []
        for seg_name, seg_data in segments.items():
            if isinstance(seg_data, dict):
                buckets = seg_data.get("buckets", [])
                for b in buckets[:3]:
                    label = b.get("label", "?")
                    rate = b.get("adoption_rate", 0)
                    segments_text_parts.append(f"  {seg_name}/{label}: {rate:.1f}%")
        segments_text = "\n".join(segments_text_parts[:12])

        # Sensitivity summary
        sens_text = "\n".join(
            f"- {s.get('header', '?')}: impacto {s.get('impact', 0):.2f}pp "
            f"(baixo={s.get('mean_low', 0):.1f}%, alto={s.get('mean_high', 0):.1f}%)"
            for s in sensitivity[:5]
        )

        user_prompt = (
            f"EXPERIMENTO: {name}\n"
            f"HIPÓTESE: {hypothesis}\n"
            f"DESCRIÇÃO: {description or 'Não fornecida'}\n\n"
            f"ESTATÍSTICAS:\n{stats_text}\n\n"
            f"SEGMENTOS:\n{segments_text}\n\n"
            f"SENSIBILIDADE:\n{sens_text}"
        )

        with _tracer.start_as_current_span(
            "SimulationSummaryGenerator: AI sections",
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "model": model,
            },
        ):
            try:
                response = self.llm.complete(
                    messages=[
                        {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    model=model,
                    temperature=0.5,
                    operation_name="Simulation Summary: AI Sections",
                )
                text = response.strip()
                # Strip any markdown headers the LLM might add
                for header in [
                    "## Descobertas Principais",
                    "## DESCOBERTAS PRINCIPAIS",
                ]:
                    if text.startswith(header):
                        text = text[len(header) :].strip()
                return text
            except Exception as e:
                self._logger.warning(f"AI sections generation failed: {e}")
                return "_Não foi possível gerar as descobertas automaticamente._"

    def _assemble_report(
        self,
        exp_name: str,
        exp_hypothesis: str,
        exp_description: str,
        stats: dict,
        distribution: list,
        segments: dict,
        sensitivity: list[dict],
        interpretations: dict,
        descobertas: str,
        group_stats: object | None,
        guide_markdown: str | None,
        n_synths: int,
        n_iterations: int,
    ) -> str:
        """Assemble the full markdown report from all sections."""
        parts: list[str] = []

        # Title
        parts.append(f"# Resumo da Simulação: {exp_name}\n")

        # Context
        parts.append("## Contexto do Problema\n")
        parts.append(f"**Hipótese:** {exp_hypothesis}\n")
        if exp_description:
            parts.append(f"{exp_description}\n")
        parts.append(f"*Simulação com {n_synths} synths e {n_iterations} iterações Monte Carlo.*\n")

        # Descobertas Principais (from LLM)
        parts.append("## Descobertas Principais\n")
        parts.append(descobertas + "\n")

        # Distribuição de Adoção
        parts.append(self._build_distribution_section(stats, distribution, interpretations))

        # Análise por Segmentos
        parts.append(self._build_segments_section(segments, interpretations))

        # Análise de Sensibilidade
        parts.append(self._build_sensitivity_section(sensitivity, interpretations))

        # Separator
        parts.append("---\n")

        # Anexo A: Demografia
        if group_stats:
            parts.append(self._build_demographics_appendix(group_stats))

        # Anexo B: Roteiro
        if guide_markdown:
            parts.append(self._build_interview_appendix(guide_markdown))

        return "\n".join(parts)

    def _build_distribution_section(
        self,
        stats: dict,
        distribution: list,
        interpretations: dict,
    ) -> str:
        """Build distribution section with stats table + histogram + AI text."""
        lines: list[str] = []
        lines.append("## Distribuição de Adoção\n")

        # Stats table
        lines.append("| Métrica | Valor |")
        lines.append("|---------|-------|")
        lines.append(f"| Média | {stats.get('mean', 0):.1f}% |")
        lines.append(f"| Mediana | {stats.get('median', 0):.1f}% |")
        lines.append(f"| P10 | {stats.get('p10', 0):.1f}% |")
        lines.append(f"| P90 | {stats.get('p90', 0):.1f}% |")
        lines.append(f"| Desvio Padrão | {stats.get('std', 0):.1f}% |")
        lines.append("")

        # Unicode histogram
        if distribution:
            lines.append(self._build_unicode_histogram(distribution))
            lines.append("")

        # AI interpretation
        dist_interp = interpretations.get("distribution", {})
        ai_text = dist_interp.get("ai_text", "")
        if ai_text:
            lines.append(f"> {ai_text}\n")

        return "\n".join(lines)

    def _build_segments_section(
        self,
        segments: dict,
        interpretations: dict,
    ) -> str:
        """Build segments section with tables per segment + AI text."""
        lines: list[str] = []
        lines.append("## Análise por Segmentos\n")

        segment_labels = {
            "age": "Faixa Etária",
            "income": "Faixa de Renda",
            "education": "Escolaridade",
        }

        for seg_key, seg_label in segment_labels.items():
            seg_data = segments.get(seg_key, {})
            buckets = seg_data.get("buckets", []) if isinstance(seg_data, dict) else []
            if not buckets:
                continue

            lines.append(f"### {seg_label}\n")
            lines.append("| Segmento | Taxa de Adoção | N |")
            lines.append("|----------|---------------|---|")
            for b in buckets:
                label = b.get("label", "?")
                rate = b.get("adoption_rate", 0)
                count = b.get("count", 0)
                lines.append(f"| {label} | {rate:.1f}% | {count} |")
            lines.append("")

        # AI interpretation
        seg_interp = interpretations.get("segments", {})
        ai_text = seg_interp.get("ai_text", "")
        if ai_text:
            lines.append(f"> {ai_text}\n")

        return "\n".join(lines)

    def _build_sensitivity_section(
        self,
        sensitivity: list[dict],
        interpretations: dict,
    ) -> str:
        """Build sensitivity section with ranked table + impact bars + AI text."""
        lines: list[str] = []
        lines.append("## Análise de Sensibilidade\n")

        if not sensitivity:
            lines.append("_Sem dados de sensibilidade disponíveis._\n")
            return "\n".join(lines)

        # Ranked table
        lines.append("| # | Premissa | Impacto (pp) | Baixo | Alto |")
        lines.append("|---|----------|-------------|-------|------|")
        for i, s in enumerate(sensitivity, 1):
            header = s.get("header", "?")
            impact = s.get("impact", 0)
            mean_low = s.get("mean_low", 0)
            mean_high = s.get("mean_high", 0)
            lines.append(f"| {i} | {header} | {impact:.2f} | {mean_low:.1f}% | {mean_high:.1f}% |")
        lines.append("")

        # Impact bars
        max_impact = max((s.get("impact", 0) for s in sensitivity), default=1)
        if max_impact > 0:
            lines.append("**Impacto relativo:**\n")
            for s in sensitivity[:5]:
                header = s.get("header", "?")
                impact = s.get("impact", 0)
                bar_len = int((impact / max_impact) * 20) if max_impact > 0 else 0
                bar = "█" * bar_len + "░" * (20 - bar_len)
                lines.append(f"- {header}: `{bar}` {impact:.2f}pp")
            lines.append("")

        # AI interpretation
        sens_interp = interpretations.get("sensitivity", {})
        ai_text = sens_interp.get("ai_text", "")
        if ai_text:
            lines.append(f"> {ai_text}\n")

        return "\n".join(lines)

    def _build_unicode_histogram(self, distribution: list) -> str:
        """Build a simple unicode bar histogram from distribution data."""
        if not distribution:
            return ""

        # Distribution is a list of adoption rate values — bin them
        lines: list[str] = []
        lines.append("```")

        # Create bins (0-10, 10-20, ..., 90-100)
        bins = [0] * 10
        for val in distribution:
            v = float(val) if not isinstance(val, (int, float)) else val
            idx = min(int(v / 10), 9)
            bins[idx] += 1

        max_count = max(bins) if bins else 1
        for i, count in enumerate(bins):
            bar_len = int((count / max_count) * 30) if max_count > 0 else 0
            label = f"{i * 10:>3}-{(i + 1) * 10:<3}%"
            bar = "█" * bar_len
            lines.append(f"  {label} | {bar} ({count})")

        lines.append("```")
        return "\n".join(lines)

    def _build_demographics_appendix(self, group_stats: object) -> str:
        """Build demographics appendix from SynthGroupStatistics."""
        lines: list[str] = []
        lines.append("## Anexo A: Demografia e Sensibilidades do Grupo\n")

        demographics = getattr(group_stats, "demographics", None)
        if not demographics:
            lines.append("_Dados demográficos não disponíveis._\n")
            return "\n".join(lines)

        # Age histogram
        age = getattr(demographics, "age", None)
        if age and getattr(age, "buckets", None):
            lines.append("### Distribuição de Idade\n")
            lines.append("| Faixa | Qtd | % |")
            lines.append("|-------|-----|---|")
            for b in age.buckets:
                lines.append(f"| {b.label} | {b.count} | {b.percentage:.1f}% |")
            lines.append(f"\n*Média: {age.mean:.1f} anos, Desvio: {age.std_dev:.1f}*\n")

        # Income histogram
        income = getattr(demographics, "income", None)
        if income and getattr(income, "buckets", None):
            lines.append("### Distribuição de Renda\n")
            lines.append("| Faixa | Qtd | % |")
            lines.append("|-------|-----|---|")
            for b in income.buckets:
                lines.append(f"| {b.label} | {b.count} | {b.percentage:.1f}% |")
            lines.append(f"\n*Média: R$ {income.mean:,.0f}, Desvio: R$ {income.std_dev:,.0f}*\n")

        # Education breakdown
        education = getattr(demographics, "education", None)
        if education:
            lines.append("### Escolaridade\n")
            lines.append("| Nível | Qtd | % |")
            lines.append("|-------|-----|---|")
            for cat in education:
                lines.append(f"| {cat.label} | {cat.count} | {cat.percentage:.1f}% |")
            lines.append("")

        # Disability stats
        disability = getattr(demographics, "disability", None)
        if disability:
            lines.append("### Pessoas com Deficiência\n")
            lines.append(
                f"- PcD: {disability.pcd_count} ({disability.pcd_percentage:.1f}%)\n"
                f"- Sem deficiência: {disability.non_pcd_count} "
                f"({disability.non_pcd_percentage:.1f}%)\n"
            )

        # Sensitivities
        sensitivities = getattr(group_stats, "sensitivities", None)
        if sensitivities:
            distributions = getattr(sensitivities, "distributions", {})
            if distributions:
                sens_labels = {
                    "digitalCapability": "Capacidade Digital",
                    "riskAversion": "Aversão a Risco",
                    "institutionalTrust": "Confiança Institucional",
                    "frictionTolerance": "Tolerância a Fricção",
                }
                lines.append("### Sensibilidades do Grupo\n")
                for key, label in sens_labels.items():
                    hist = distributions.get(key)
                    if hist and getattr(hist, "buckets", None):
                        lines.append(f"**{label}** (média: {hist.mean:.2f})\n")

        return "\n".join(lines)

    def _build_interview_appendix(self, guide_markdown: str) -> str:
        """Build interview guide appendix."""
        lines: list[str] = []
        lines.append("## Anexo B: Roteiro de Entrevista\n")
        lines.append(guide_markdown)
        lines.append("")
        return "\n".join(lines)
