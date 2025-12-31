"""
LLM-powered cluster labeling service.

Generates descriptive names for clusters using LLM analysis of cluster
characteristics (traits, success rates, sizes).

Functions:
- generate_labels(): Generate descriptive names for all clusters in a single LLM call

References:
    - Entities: src/synth_lab/domain/entities/cluster_result.py
    - LLM Client: src/synth_lab/infrastructure/llm_client.py
    - Config: src/synth_lab/infrastructure/config.py (REASONING_MODEL)

Sample usage:
    from synth_lab.services.simulation.cluster_labeling_service import ClusterLabelingService
    from synth_lab.domain.entities.cluster_result import ClusterProfile

    service = ClusterLabelingService()
    profiles = [ClusterProfile(...), ClusterProfile(...)]
    labels = service.generate_labels(profiles)
    # Returns: {0: "Exploradores Cautelosos", 1: "Usuários Confiantes"}

Expected output:
    Dict mapping cluster_id to descriptive name (2-4 words in Portuguese)
"""

import json

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.cluster_result import ClusterProfile
from synth_lab.infrastructure.config import REASONING_MODEL
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("cluster-labeling-service")


class ClusterLabelingError(Exception):
    """Error raised when cluster labeling fails."""

    pass


class ClusterLabelingService:
    """LLM-powered cluster name generator."""

    # Human-readable labels for latent traits
    TRAIT_LABELS = {
        "capability_mean": "Capacidade",
        "trust_mean": "Confiança",
        "friction_tolerance_mean": "Tolerância",
        "exploration_prob": "Prob. Exploração",
    }

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        """
        Initialize with optional LLM client.

        Args:
            llm_client: LLM client instance. If None, uses global client.
        """
        self.llm = llm_client or get_llm_client()
        self.logger = logger.bind(component="cluster_labeling_service")

    def generate_labels(
        self, profiles: list[ClusterProfile]
    ) -> dict[int, dict[str, str]]:
        """
        Generate descriptive names and explanations for all clusters in a single LLM call.

        Args:
            profiles: List of ClusterProfile with cluster characteristics.

        Returns:
            Dict mapping cluster_id to {"name": "...", "explanation": "..."}.
            Falls back to generic values if LLM fails.
        """
        if not profiles:
            return {}

        span_name = f"ClusterLabeling | {len(profiles)} clusters"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "cluster.count": len(profiles),
                "operation.type": "cluster_labeling",
                "llm.model": REASONING_MODEL,
            },
        ):
            self.logger.info(f"Generating labels for {len(profiles)} clusters")

            prompt = self._build_prompt(profiles)

            try:
                response_str = self.llm.complete_json(
                    messages=[{"role": "user", "content": prompt}],
                    model=REASONING_MODEL,
                    temperature=0.7,
                )

                labels = self._parse_response(response_str, profiles)
                self.logger.info(f"Generated labels: {labels}")
                return labels

            except Exception as e:
                self.logger.error(f"Failed to generate cluster labels: {e}")
                # Fallback to generic names
                return {
                    p.cluster_id: {
                        "name": f"Cluster {p.cluster_id + 1}",
                        "explanation": "",
                    }
                    for p in profiles
                }

    def _build_prompt(self, profiles: list[ClusterProfile]) -> str:
        """
        Build prompt for LLM with all cluster data.

        Args:
            profiles: List of ClusterProfile entities.

        Returns:
            Formatted prompt string.
        """
        clusters_text = []

        for profile in profiles:
            # Format trait values with human-readable labels
            trait_lines = []
            for trait_key, trait_label in self.TRAIT_LABELS.items():
                value = profile.centroid.get(trait_key, 0)
                # Classify as alta/média/baixa based on value
                if value >= 0.7:
                    level = "alta"
                elif value <= 0.3:
                    level = "baixa"
                else:
                    level = "média"
                trait_lines.append(f"- {trait_label}: {value:.2f} ({level})")

            # Format high/low traits with human-readable names
            high_traits_labels = [
                self.TRAIT_LABELS.get(t, t) for t in profile.high_traits
            ]
            low_traits_labels = [self.TRAIT_LABELS.get(t, t) for t in profile.low_traits]

            cluster_block = f"""<cluster_{profile.cluster_id}>
- Tamanho: {profile.size} usuários ({profile.percentage:.1f}%)
- Taxa de sucesso: {profile.avg_success_rate * 100:.0f}%
{chr(10).join(trait_lines)}
- Traits acima da média: {', '.join(high_traits_labels) if high_traits_labels else 'nenhum'}
- Traits abaixo da média: {', '.join(low_traits_labels) if low_traits_labels else 'nenhum'}
</cluster_{profile.cluster_id}>"""

            clusters_text.append(cluster_block)

        return f"""Você é um especialista em análise comportamental de usuários.

Analise os clusters abaixo e gere para cada um:
1. Um nome descritivo (3 a 5 palavras, em português)
2. Uma breve explicação (10-15 palavras) que justifique o nome

## Regras para os nomes
- Devem ser DISTINTOS entre si (cada cluster com nome único)
- Baseados nas características comportamentais predominantes
- Memoráveis e intuitivos
- Focados no COMPORTAMENTO, não em julgamentos de valor
- Evite termos genéricos como "Grupo A" ou "Cluster 1"

## Regras para as explicações
- Máximo de 15 palavras
- Destaque os traits mais marcantes que definem o cluster
- Use linguagem simples e direta

## Contexto dos Traits
- Capacidade: habilidade técnica do usuário para completar tarefas (0-1)
- Confiança: disposição para seguir recomendações do sistema (0-1)
- Tolerância: resiliência a erros, atrasos e fricção na experiência (0-1)
- Prob. Exploração: tendência a explorar alternativas e funcionalidades (0-1)

## Clusters

{chr(10).join(clusters_text)}

## Formato de Resposta (JSON)
Responda APENAS com o JSON abaixo, sem texto adicional:
{{
  "clusters": [
    {{"cluster_id": 0, "name": "Nome Descritivo", "explanation": "Breve explicação"}},
    {{"cluster_id": 1, "name": "Nome Descritivo", "explanation": "Breve explicação"}}
  ]
}}"""

    def _parse_response(
        self, response_str: str, profiles: list[ClusterProfile]
    ) -> dict[int, dict[str, str]]:
        """
        Parse LLM response and extract cluster names and explanations.

        Args:
            response_str: JSON string from LLM.
            profiles: Original profiles for fallback.

        Returns:
            Dict mapping cluster_id to {"name": "...", "explanation": "..."}.
        """
        try:
            data = json.loads(response_str)
            clusters = data.get("clusters", [])

            labels: dict[int, dict[str, str]] = {}
            for item in clusters:
                cluster_id = item.get("cluster_id")
                name = item.get("name", "").strip()
                explanation = item.get("explanation", "").strip()

                if cluster_id is not None and name:
                    labels[cluster_id] = {
                        "name": name,
                        "explanation": explanation,
                    }

            # Ensure all clusters have labels (fallback for missing ones)
            for profile in profiles:
                if profile.cluster_id not in labels:
                    labels[profile.cluster_id] = {
                        "name": f"Cluster {profile.cluster_id + 1}",
                        "explanation": "",
                    }

            return labels

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return {
                p.cluster_id: {
                    "name": f"Cluster {p.cluster_id + 1}",
                    "explanation": "",
                }
                for p in profiles
            }


# =============================================================================
# Validation
# =============================================================================
if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Build prompt formatting
    total_tests += 1
    try:
        service = ClusterLabelingService()

        # Create mock profiles
        mock_profiles = [
            ClusterProfile(
                cluster_id=0,
                size=25,
                percentage=31.25,
                centroid={
                    "capability_mean": 0.72,
                    "trust_mean": 0.45,
                    "friction_tolerance_mean": 0.68,
                    "exploration_prob": 0.33,
                },
                avg_success_rate=0.28,
                avg_failed_rate=0.42,
                avg_did_not_try_rate=0.30,
                high_traits=["capability_mean", "friction_tolerance_mean"],
                low_traits=["trust_mean"],
                suggested_label="Test",
                synth_ids=["s1", "s2"],
            ),
            ClusterProfile(
                cluster_id=1,
                size=35,
                percentage=43.75,
                centroid={
                    "capability_mean": 0.35,
                    "trust_mean": 0.82,
                    "friction_tolerance_mean": 0.55,
                    "exploration_prob": 0.71,
                },
                avg_success_rate=0.65,
                avg_failed_rate=0.20,
                avg_did_not_try_rate=0.15,
                high_traits=["trust_mean", "exploration_prob"],
                low_traits=["capability_mean"],
                suggested_label="Test",
                synth_ids=["s3", "s4", "s5"],
            ),
        ]

        prompt = service._build_prompt(mock_profiles)

        # Verify prompt contains expected elements
        if "<cluster_0>" not in prompt:
            all_validation_failures.append("Prompt missing cluster_0 tag")
        if "<cluster_1>" not in prompt:
            all_validation_failures.append("Prompt missing cluster_1 tag")
        if "Capacidade: 0.72" not in prompt:
            all_validation_failures.append("Prompt missing capability value")
        if "Taxa de sucesso: 28%" not in prompt:
            all_validation_failures.append("Prompt missing success rate")
        if "Confiança" not in prompt:
            all_validation_failures.append("Prompt missing trust trait label")

        print("✓ Prompt build test passed")

    except Exception as e:
        all_validation_failures.append(f"Prompt build test failed: {e}")

    # Test 2: Parse response with name and explanation
    total_tests += 1
    try:
        service = ClusterLabelingService()

        mock_response = json.dumps(
            {
                "clusters": [
                    {
                        "cluster_id": 0,
                        "name": "Exploradores Cautelosos",
                        "explanation": "Alta capacidade mas baixa confiança no sistema.",
                    },
                    {
                        "cluster_id": 1,
                        "name": "Usuários Confiantes",
                        "explanation": "Seguem recomendações e exploram novas funcionalidades.",
                    },
                ]
            }
        )

        labels = service._parse_response(mock_response, mock_profiles)

        if labels.get(0, {}).get("name") != "Exploradores Cautelosos":
            all_validation_failures.append(
                f"Expected name 'Exploradores Cautelosos', got '{labels.get(0, {}).get('name')}'"
            )
        expected_explanation = "Alta capacidade mas baixa confiança no sistema."
        if labels.get(0, {}).get("explanation") != expected_explanation:
            all_validation_failures.append(
                f"Expected explanation for cluster 0, got '{labels.get(0, {}).get('explanation')}'"
            )
        if labels.get(1, {}).get("name") != "Usuários Confiantes":
            all_validation_failures.append(
                f"Expected name 'Usuários Confiantes', got '{labels.get(1, {}).get('name')}'"
            )

        print("✓ Parse response test passed")

    except Exception as e:
        all_validation_failures.append(f"Parse response test failed: {e}")

    # Test 3: Fallback on invalid JSON
    total_tests += 1
    try:
        service = ClusterLabelingService()

        invalid_response = "not valid json"
        labels = service._parse_response(invalid_response, mock_profiles)

        if labels.get(0, {}).get("name") != "Cluster 1":
            all_validation_failures.append(
                f"Expected fallback 'Cluster 1', got '{labels.get(0, {}).get('name')}'"
            )
        if labels.get(1, {}).get("name") != "Cluster 2":
            all_validation_failures.append(
                f"Expected fallback 'Cluster 2', got '{labels.get(1, {}).get('name')}'"
            )
        if labels.get(0, {}).get("explanation") != "":
            got_explanation = labels.get(0, {}).get("explanation")
            all_validation_failures.append(
                f"Expected empty explanation on fallback, got '{got_explanation}'"
            )

        print("✓ Fallback test passed")

    except Exception as e:
        all_validation_failures.append(f"Fallback test failed: {e}")

    # Test 4: Empty profiles
    total_tests += 1
    try:
        service = ClusterLabelingService()
        labels = service.generate_labels([])

        if labels != {}:
            all_validation_failures.append(f"Expected empty dict, got {labels}")

        print("✓ Empty profiles test passed")

    except Exception as e:
        all_validation_failures.append(f"Empty profiles test failed: {e}")

    # Final validation result
    if all_validation_failures:
        n_failures = len(all_validation_failures)
        print(f"\n❌ VALIDATION FAILED - {n_failures} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"\n✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
