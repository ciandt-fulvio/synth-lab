"""
HypothesisParametrizerService for causal simulation system.

Quantifies variables with probability distributions, ranges, and correlations
using LLM to suggest reasonable parameters.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
    - SciPy distributions: https://docs.scipy.org/doc/scipy/reference/stats.html
"""

import json
from typing import Any

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.causal_dag import CausalDAG
from synth_lab.domain.entities.hypothesis import (
    BernoulliParams,
    BetaParams,
    Correlation,
    DistributionType,
    Hypothesis,
    LogNormalParams,
    NormalParams,
    ScenarioOption,
    TriangularParams,
    UniformParams,
)
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer

_tracer = get_tracer("hypothesis-parametrizer-service")

# Model for hypothesis parametrization (needs reasoning for reasonable ranges)
PARAMETRIZER_MODEL = "gpt-4o"


class HypothesisParametrizerService:
    """
    Service for quantifying variables with probability distributions.

    Uses LLM to suggest distribution types and parameters based on variable
    characteristics and domain knowledge.
    """

    def __init__(self, llm_client: LLMClient | None = None):
        """
        Initialize HypothesisParametrizerService.

        Args:
            llm_client: LLM client for generation. Defaults to singleton.
        """
        self.llm = llm_client or get_llm_client()
        self.logger = logger.bind(component="hypothesis_parametrizer_service")

    def quantify(self, simulation_id: str, dag: CausalDAG) -> list[Hypothesis]:
        """
        Quantify all variables in DAG with probability distributions.

        Args:
            simulation_id: Parent simulation ID
            dag: Validated causal DAG

        Returns:
            List of Hypothesis entities (one per variable)

        Raises:
            ValueError: If parametrization fails

        Example:
            >>> parametrizer = HypothesisParametrizerService()
            >>> hypotheses = parametrizer.quantify("sim_12345678", dag)
            >>> for hyp in hypotheses:
            ...     print(f"{hyp.variable_name}: {hyp.distribution_type}")
        """
        span_name = f"HypothesisParametrizer | {len(dag.nodes)} variables"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "operation.type": "hypothesis_parametrization",
                "llm.model": PARAMETRIZER_MODEL,
                "simulation.id": simulation_id,
                "dag.num_variables": len(dag.nodes),
            },
        ):
            try:
                # Build prompt for hypothesis parametrization
                prompt = self._build_parametrization_prompt(dag)

                # Call LLM with gpt-4o (reasoning needed)
                self.logger.info(
                    f"Quantifying {len(dag.nodes)} variables for simulation {simulation_id}"
                )
                llm_response_str = self.llm.complete_json(
                    messages=[{"role": "user", "content": prompt}],
                    model=PARAMETRIZER_MODEL,
                )

                # Parse LLM response
                llm_response = json.loads(llm_response_str)

                # Convert to Hypothesis entities
                hypotheses = self._parse_hypotheses_response(
                    simulation_id, dag, llm_response
                )

                self.logger.info(
                    f"Successfully quantified {len(hypotheses)} hypotheses"
                )

                return hypotheses

            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse LLM response as JSON: {e}"
                self.logger.error(error_msg)
                raise ValueError(error_msg) from e

            except Exception as e:
                error_msg = f"Hypothesis parametrization failed: {e}"
                self.logger.error(error_msg)
                raise ValueError(error_msg) from e

    def _build_parametrization_prompt(self, dag: CausalDAG) -> str:
        """
        Build prompt for hypothesis parametrization.

        Args:
            dag: Causal DAG with variables

        Returns:
            Formatted prompt string
        """
        # Serialize variables for prompt
        variables_summary = []
        controllable_vars = []
        for var in dag.nodes:
            variables_summary.append(
                f"- {var.id}: {var.name} ({var.type}, {var.scope}, controllability={var.controllability})"
            )
            # Track controllable variables
            if var.controllability in ["high", "medium"]:
                controllable_vars.append(f"  - {var.name} (controllability={var.controllability})")

        variables_text = "\n".join(variables_summary)
        controllable_text = "\n".join(controllable_vars) if controllable_vars else "(Nenhuma variável controlável)"

        return f"""Você é um especialista em estatística quantificando variáveis com distribuições de probabilidade para simulação.

**Variáveis para quantificar**:
{variables_text}

**Tarefa**: Para cada variável, sugira uma distribuição de probabilidade com parâmetros REALISTAS baseados em conhecimento de domínio.

**IMPORTANTE**: NÃO use valores genéricos (50%, ranges 0-100, etc). Use seu conhecimento sobre o domínio para sugerir valores PROVÁVEIS e realistas.

**EXEMPLOS DE RACIOCÍNIO** (few-shot learning):

**Exemplo 1: Taxa de Conversão E-commerce**
```
Variável: "taxa_conversao" (taxa de visitantes que compram)
Raciocínio: E-commerce típico tem conversão de 2-5% (cold traffic) ou 8-15% (warm traffic).
Usar Beta(2, 18) resulta em média ~10%, concentrada entre 5-20%, o que é REALISTA para e-commerce.
NÃO usar uniform(0, 1) ou Beta(5, 5) que daria média de 50% - irrealista!
```
Distribuição escolhida: Beta(alpha=2.0, beta=18.0)

**Exemplo 2: Churn Mensal SaaS B2B**
```
Variável: "taxa_churn_mensal" (% de clientes que cancelam por mês)
Raciocínio: SaaS B2B saudável tem churn de 3-7% ao mês. Churn muito baixo (<1%) é raro,
churn alto (>15%) indica problemas sérios. Beta(1.5, 18.5) concentra em 5-8%, realista para B2B.
NÃO usar ranges 0-100% ou mode=50% - isso não representa a realidade!
```
Distribuição escolhida: Beta(alpha=1.5, beta=18.5)

**Exemplo 3: Ticket Médio de Produto**
```
Variável: "valor_ticket" (valor médio de compra em R$)
Raciocínio: Produtos têm preço base típico (ex: R$50-80), com alguns valores mais altos (cauda longa).
LogNormal(mean=4.0, sigma=0.6) gera distribuição com mediana ~R$55 e cauda até R$200-300.
NÃO usar uniform(0, 1000) ou normal com range simétrico - valores monetários são assimétricos!
```
Distribuição escolhida: LogNormal(mean=4.0, sigma=0.6)

**Exemplo 4: Tempo de Onboarding (dias)**
```
Variável: "tempo_onboarding" (dias para cliente completar setup)
Raciocínio: Processo típico leva 5-10 dias, com mode em 7 dias. Extremos: mínimo 3 dias (power user),
máximo 20 dias (casos complexos). Triangular(min=3, mode=7, max=20) reflete essa realidade.
NÃO usar uniform(0, 100) ou mode=50 - onboarding não demora 50 dias tipicamente!
```
Cenários controláveis: "Simples" (min=3, mode=5, max=7), "Normal" (min=5, mode=7, max=12), "Complexo" (min=10, mode=15, max=20)

**Exemplo 5: Probabilidade de Falha Técnica**
```
Variável: "falha_tecnica" (se ocorre falha no checkout)
Raciocínio: Sistemas bem mantidos têm 98-99% uptime. Falhas ocorrem em ~1-3% das transações.
Bernoulli(p=0.02) representa 2% de falhas, realista para e-commerce maduro.
NÃO usar p=0.5 - isso significaria 50% de falhas, o que seria catastrófico!
```
Distribuição escolhida: Bernoulli(p=0.02)

---

**INSTRUÇÕES PARA SUAS HIPÓTESES**:
1. **PENSE** no valor mais provável para cada variável baseado no domínio
2. **JUSTIFIQUE** mentalmente por que aqueles ranges fazem sentido
3. **EVITE** valores genéricos (50%, 0-100, distribuições simétricas quando não aplicável)
4. **USE** conhecimento de benchmarks, realidade de mercado, física do problema

**Distribuições disponíveis**:
1. **uniform**: Uniforme(low, high) - Probabilidade igual em todo o intervalo
   - Use para: Variáveis desconhecidas, sem conhecimento prévio
   - Exemplo: {{\"type\": \"uniform\", \"params\": {{\"low\": 0.0, \"high\": 1.0}}}}

2. **normal**: Normal(mean, std) - Distribuição em forma de sino
   - Use para: Métricas contínuas com tendência central
   - Exemplo: {{\"type\": \"normal\", \"params\": {{\"mean\": 0.5, \"std\": 0.1}}}}

3. **beta**: Beta(alpha, beta) - Distribuição limitada [0, 1]
   - Use para: Probabilidades, taxas, percentuais
   - Exemplo: {{\"type\": \"beta\", \"params\": {{\"alpha\": 3.0, \"beta\": 7.0}}}}

4. **lognormal**: LogNormal(mean, sigma) - Apenas positiva, assimétrica à direita
   - Use para: Valores monetários, durações de tempo, taxas de crescimento
   - Exemplo: {{\"type\": \"lognormal\", \"params\": {{\"mean\": 3.0, \"sigma\": 0.5}}}}

5. **bernoulli**: Bernoulli(p) - Resultados binários (0 ou 1)
   - Use para: Eventos binários, resultados sim/não
   - Exemplo: {{\"type\": \"bernoulli\", \"params\": {{\"p\": 0.3}}}}

**Diretrizes CRÍTICAS**:
- **SEJA OPINIONATED**: Use conhecimento de domínio para sugerir valores PROVÁVEIS, não genéricos
- **NÃO use 50% ou 0.5 como default**: Pense no valor real mais provável para aquela variável
- **NÃO use ranges 0-100**: Use ranges realistas baseados no contexto (ex: taxa conversão 0.02-0.15, não 0-1)
- **Distribuição Beta para taxas**: alpha e beta devem refletir assimetria realista (ex: Beta(2,18) para 10%, não Beta(5,5) para 50%)
- **LogNormal para valores monetários**: mean e sigma devem gerar valores concentrados em faixa realista
- **Bernoulli para eventos raros**: p deve ser baixo (<0.1) para falhas/eventos infrequentes
- **Triangular para controláveis**: mode deve ser o valor ESPERADO no cenário base, não o meio aritmético
- Sugira 1-3 correlações chave entre variáveis (apenas se causalmente significativas)

**CENÁRIOS QUALITATIVOS** (para variáveis controláveis):
Para variáveis com **controllability = high ou medium**, você DEVE gerar cenários qualitativos.
Estas são as variáveis controláveis identificadas:
{controllable_text}

Para cada variável controlável, crie 2-4 cenários qualitativos com:
- **value**: identificador interno (ex: "low", "medium", "high" ou "simple", "intermediate", "advanced")
- **label**: rótulo descritivo CURTO em português, APENAS palavras qualitativas (ex: "Baixo", "Médio", "Alto")
- **min_value**, **mode**, **max_value**: valores numéricos REALISTAS da distribuição triangular

IMPORTANTE: Os labels devem ser APENAS palavras qualitativas, SEM faixas numéricas ou unidades.

**Exemplos de cenários REALISTAS** (NOT generic!):

**Taxa de desconto (percentual 0-1)**:
- "Baixo": min=0.05, mode=0.08, max=0.12 (descontos de 5-12%)
- "Médio": min=0.10, mode=0.15, max=0.20 (descontos de 10-20%)
- "Alto": min=0.18, mode=0.25, max=0.35 (descontos de 18-35%)

**Investimento em marketing (R$ milhares)**:
- "Baixo": min=10, mode=15, max=25 (R$ 10-25k)
- "Médio": min=20, mode=35, max=60 (R$ 20-60k)
- "Alto": min=50, mode=80, max=120 (R$ 50-120k)

**Tempo de entrega (dias)**:
- "Rápido": min=1, mode=2, max=3 (1-3 dias)
- "Normal": min=3, mode=5, max=7 (3-7 dias)
- "Lento": min=7, mode=10, max=15 (7-15 dias)

**Complexidade de interface (escala 0-10)**:
- "Simples": min=2, mode=3, max=4 (muito intuitivo)
- "Moderado": min=4, mode=6, max=7 (equilíbrio)
- "Complexo": min=7, mode=8, max=9 (feature-rich)

**REGRAS para cenários controláveis**:
1. **NÃO use min=0, max=100, mode=50** - isso é genérico e irrealista
2. **PENSE** no range realista para aquela variável específica
3. O **mode** deve ser o valor ESPERADO naquele cenário, não o meio aritmético
4. Os ranges podem se SOBREPOR (ex: "Médio" pode ir de 10-20, "Alto" de 18-35)
5. O cenário do meio (ex: "medium") deve ser marcado como default (selected_scenario)

**Formato de saída** (apenas JSON, sem markdown):
{{
  "hypotheses": [
    {{
      "variable_id": "var_001",
      "variable_name": "nome_variavel",
      "distribution_type": "uniform|normal|beta|lognormal|bernoulli",
      "parameters": {{}},  // Parâmetros específicos da distribuição
      "correlations": [  // Opcional, apenas se significativo
        {{
          "with_variable_id": "var_002",
          "with_variable_name": "outra_var",
          "correlation": 0.6,
          "rationale": "Por que estas variáveis são correlacionadas"
        }}
      ],
      "scenario_options": [  // OBRIGATÓRIO para variáveis com controllability=high/medium
        {{
          "value": "low",
          "label": "Baixo",
          "min_value": 0.05,
          "mode": 0.08,
          "max_value": 0.12
        }},
        {{
          "value": "medium",
          "label": "Médio",
          "min_value": 0.10,
          "mode": 0.15,
          "max_value": 0.20
        }},
        {{
          "value": "high",
          "label": "Alto",
          "min_value": 0.18,
          "mode": 0.25,
          "max_value": 0.35
        }}
      ],
      "selected_scenario": "medium"  // Cenário padrão (geralmente o do meio)
    }}
  ]
}}

**LEMBRE-SE**: Cada variável tem seu próprio contexto. Use conhecimento de domínio para sugerir valores PROVÁVEIS e REALISTAS.
NÃO caia na armadilha de usar valores genéricos (50%, 0-100, distribuições simétricas para tudo).

**CHECKLIST FINAL antes de retornar**:
✓ Nenhuma incerteza crítica tem mode=50 ou range 0-100?
✓ Distribuições Beta têm alpha e beta que refletem assimetria realista?
✓ Cenários controláveis têm ranges específicos do domínio, não genéricos?
✓ Valores LogNormal geram ranges monetários realistas?
✓ Probabilidades Bernoulli são baixas (<0.1) para eventos raros?

Retorne APENAS o objeto JSON, sem texto ou formatação adicional.
"""

    def _parse_hypotheses_response(
        self, simulation_id: str, dag: CausalDAG, response: dict[str, Any]
    ) -> list[Hypothesis]:
        """
        Parse LLM response into Hypothesis entities.

        Maps LLM-generated variable IDs to actual DAG variable IDs using name lookup.

        Args:
            simulation_id: Parent simulation ID
            dag: Causal DAG (for variable lookup)
            response: Parsed JSON response from LLM

        Returns:
            List of Hypothesis entities
        """
        hypotheses = []

        # Create mappings from variable name to actual DAG variable ID
        name_to_id = {node.name: node.id for node in dag.nodes}

        for hyp_data in response.get("hypotheses", []):
            # Parse distribution type with fallback for unsupported types
            raw_dist_type = hyp_data["distribution_type"]
            try:
                dist_type = DistributionType(raw_dist_type)
            except ValueError:
                self.logger.warning(
                    f"Unsupported distribution type '{raw_dist_type}', "
                    f"falling back to uniform"
                )
                dist_type = DistributionType.UNIFORM

            # Parse distribution parameters
            params_data = hyp_data["parameters"]
            if dist_type == DistributionType.UNIFORM:
                # Handle fallback case with default params
                params = UniformParams(
                    low=params_data.get("low", 0.0),
                    high=params_data.get("high", 1.0),
                )
            elif dist_type == DistributionType.NORMAL:
                params = NormalParams(**params_data)
            elif dist_type == DistributionType.BETA:
                params = BetaParams(**params_data)
            elif dist_type == DistributionType.LOGNORMAL:
                params = LogNormalParams(**params_data)
            elif dist_type == DistributionType.BERNOULLI:
                params = BernoulliParams(**params_data)
            else:
                # This shouldn't happen due to fallback above
                params = UniformParams(low=0.0, high=1.0)

            # Get actual variable ID from DAG (LLM might use different format)
            var_name = hyp_data["variable_name"]
            actual_var_id = name_to_id.get(var_name, hyp_data["variable_id"])

            # Parse correlations with mapped IDs
            correlations = []
            for corr_data in hyp_data.get("correlations", []):
                corr_var_name = corr_data["with_variable_name"]
                actual_corr_id = name_to_id.get(
                    corr_var_name, corr_data["with_variable_id"]
                )
                correlations.append(
                    Correlation(
                        with_variable_id=actual_corr_id,
                        with_variable_name=corr_var_name,
                        correlation=corr_data["correlation"],
                        rationale=corr_data["rationale"],
                    )
                )

            # Parse scenario options (for controllable variables)
            scenario_options = None
            selected_scenario = None
            if "scenario_options" in hyp_data and hyp_data["scenario_options"]:
                scenario_options = []
                for scenario_data in hyp_data["scenario_options"]:
                    scenario_options.append(
                        ScenarioOption(
                            value=scenario_data["value"],
                            label=scenario_data["label"],
                            distribution_params=TriangularParams(
                                min_value=scenario_data["min_value"],
                                mode=scenario_data["mode"],
                                max_value=scenario_data["max_value"],
                            ),
                        )
                    )
                selected_scenario = hyp_data.get("selected_scenario")

            hypotheses.append(
                Hypothesis(
                    simulation_id=simulation_id,
                    variable_id=actual_var_id,
                    variable_name=var_name,
                    distribution_type=dist_type,
                    parameters=params,
                    correlations=correlations,
                    scenario_options=scenario_options,
                    selected_scenario=selected_scenario,
                )
            )

        return hypotheses
