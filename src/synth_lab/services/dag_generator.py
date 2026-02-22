"""
DAG generator service with 2-pass LLM generation.

Pass 1 (Topology): Generates nodes, edges, directions, sensitivity configs,
product descriptions, and interaction names. No Likert options.

Pass 2 (Node Options): For each interaction + outcome node, generates 5 Likert
options with fixed mu/sigma. The selected option determines the node's weight
in the simulation.

Pass 1 uses gpt-4.1-mini, Pass 2 uses gpt-4.1-nano. Both wrapped with Phoenix tracing.

References:
    - Spec: specs/042-quantitative-analysis/spec.md
    - OpenAI Chat Completions: https://platform.openai.com/docs/api-reference/chat
    - Phoenix Tracing: https://docs.arize.com/phoenix
"""

import json

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.infrastructure.llm_client import LLMClient
from synth_lab.infrastructure.phoenix_tracing import get_tracer

_tracer = get_tracer("dag-generator")

# ============================================================================
# Pass 1: Topology prompt
# ============================================================================

TOPOLOGY_SYSTEM_PROMPT = """You are an expert in causal inference, product experimentation, and behavioral modeling for a Brazilian financial institution.

Given an experiment description and a set of YAML-derived sensitivities, generate a RICH causal DAG with up to 4 types of nodes.

NODE TYPES:
1. **sensitivity** (root nodes): Behavioral traits of the user. Some come from YAML rules (risk_aversion, digital_capability, etc.), others are CUSTOM created by you. Custom sensitivities need a "custom_config" with base + rules. Each has a "description" explaining its semantic meaning. Sensitivities are computed from synth demographic data via rules — they have NO incoming edges in the DAG.
2. **product**: Product/feature characteristics. You create 2-4 product nodes representing key dimensions of the product being tested (e.g., "Facilidade de Uso", "Transparência de Taxas"). Each has a "description" field. Product nodes are also roots — they have NO incoming edges.
3. **interaction**: Endogenous nodes that combine ONE user signal (sensitivity) + ONE product signal. Named as the emergent behavior (e.g., "Confiança para Usar", "Percepção de Valor"). Each has a "description" explaining its semantic meaning and WHY those two parents create this emergent behavior.
4. **outcome**: Single final node (adoption/conversion/engagement). Has a "description".

OPTIONAL — **demographic** nodes: You MAY include a demographic node (e.g., "Idade", "Renda") ONLY if it is a direct parent of an interaction node AND that interaction also has a product parent. Demographic nodes MUST NOT connect to sensitivity nodes. A demographic→interaction edge MUST be edge_type "likert".

ALL edges are "likert" type. There are NO "fixed" edges. Every edge will receive 5 Likert options in a separate pass.

CRITICAL RULES FOR INTERACTION NODES:
- Each interaction node has EXACTLY 2 parents: 1 user-side (sensitivity or demographic) + 1 product.
- NO demographic→sensitivity edges (demographics feed sensitivities only).
- NO 3-parent interactions. If you need more complexity, create another interaction node.
- The outcome node CAN have more than 2 parents (all interactions feed into it).

INTERACTION DIVERSITY (VERY IMPORTANT):
Each interaction node MUST represent a DISTINCT psychological dimension of the user's decision.
Do NOT create multiple interaction nodes that capture the same underlying feeling (e.g., "Confiança", "Segurança", "Uso sem Ansiedade" are all variations of trust/safety — pick ONE).

Use the following ORTHOGONAL DIMENSIONS as a reference. Each interaction should map to a DIFFERENT dimension:

| Dimension name       | What it captures                                                |
|----------------------|-----------------------------------------------------------------|
| Custo-benefício      | Is the tradeoff (price, effort) worth the benefit?              |
| Esforço cognitivo    | How easy is it to understand and choose?                        |
| Encaixe nos habitos  | Does it fit into the user's daily habits and context?           |
| Validação social     | Do peers/institutions endorse or validate this choice?          |
| Dor Resolvida        | Does it solve a real pain point the user already feels?         |
| Autonomia/controle   | Does the user feel in charge and able to reverse decisions?     |
| Satisfação antecipada| Does the user expect a positive emotional payoff?               |
| Barreira de entrada  | How hard is it to switch from the current solution?             |
| Confiança/segurança  | Does the user trust the product and feel safe using it?         |

RULES:
- Pick 3-5 dimensions from the table above (or create your own, as long as they are truly distinct).
- NEVER use 2+ interactions from the same dimension. If you need "Confiança", that's ONE node — don't also add "Segurança" or "Uso sem Ansiedade".
- Name interactions as the EMERGENT BEHAVIOR, not as a generic trait. E.g., "Valor Percebido" (good) vs "Importância" (too vague).

OTHER RULES:
- 2-4 user (demographic/sensitivity) nodes — at least 2 from YAML, rest can be custom
- 3-5 product nodes (a user node can interact with multiple product nodes via separate interaction nodes)
- 3-5 interaction nodes
- 1 outcome node
- Outcome receives edges from ALL interaction nodes

SENSITIVITY REFERENCES (from YAML):
You will receive the 4 YAML sensitivity keys and their configs. You MUST include at least 2 of them.
For custom sensitivities, provide a "custom_config" following the same format:
  {"base": float, "rules": [{"condition": {"field": str, "operator": str, "value": any}, "adjustment": float, "reason": str}]}

INTERCEPT:
interceptMu: -2.5 to 1.2. interceptSigma: 0.3 to 0.5.
Be OPINIONATED based on the product context:
- High friction / risky / unfamiliar: -1.5 to -2.5
- Moderate barriers: -0.7 to -1.2
- Average product: -0.5 to 0.0
- Strong value prop / low friction: 0.3 to 1.2

Node names SHORT (max 25 chars). Portuguese BR. All "description" fields MUST be in Portuguese BR, 1-2 sentences.

DIRECTION SEMANTICS:
- direction=1: Direct relationship (higher parent value → higher child value). Example: "Facilidade de uso" → "Confiança" (more usability → more trust).
- direction=-1: Inverse relationship (higher parent value → LOWER child value). Example: "Preço alto" → "Valor percebido" (higher price → lower perceived value).
- Most edges should be direction=1. Use -1 ONLY for genuinely inverse relationships.

Respond with ONLY valid JSON:
{
  "label": "string",
  "interceptMu": number,
  "interceptSigma": number,
  "nodes": [
    {"name": "string", "type": "sensitivity", "sensitivity_key": "risk_aversion", "description": "Mede o quanto o usuário evita situações de risco financeiro..."},
    {"name": "string", "type": "sensitivity", "sensitivity_key": "custom_1", "description": "...", "custom_config": {"base": 0.45, "rules": [...]}},
    {"name": "string", "type": "product", "description": "Grau de facilidade para cancelar o serviço sem burocracia..."},
    {"name": "string", "type": "interaction", "description": "Representa como a aversão a risco do usuário interage com a facilidade de uso do produto, gerando confiança..."},
    {"name": "string", "type": "outcome", "description": "Probabilidade de adoção do produto pelo usuário..."}
  ],
  "edges": [
    {"id": "e1", "from": "string", "to": "string", "direction": 1, "edge_type": "likert", "weight": 0.6},
    {"id": "e2", "from": "string", "to": "string", "direction": -1, "edge_type": "likert", "weight": 0.4}
  ]
}"""


# ============================================================================
# Pass 2: Options prompt
# ============================================================================

OPTIONS_SYSTEM_PROMPT = """You are an expert in behavioral research and Likert scale design for product experiments.

Given a causal DAG topology, generate 5 Likert options for each INTERACTION node.
These options represent how strongly the PM believes that node influences the causal model.
Do NOT generate options for the OUTCOME node (it is handled separately).

For each interaction node, produce:
- "name": Exact node name (must match topology)
- "header": Short contextual intro: "Qual o peso de [node name] no modelo?"
- "options": Array of exactly 5 objects with text, mu, sigma
- "default": LLM-suggested default option index (0-4)

The 5 options MUST follow this exact pattern (strongest first, weakest last):
  Option 0: text = strong influence claim.                   mu=0.80, sigma=0.15
  Option 1: text = significant influence claim.              mu=0.65, sigma=0.25
  Option 2: text = "Não sei avaliar o peso de [node]..."    mu=0.50, sigma=0.50
  Option 3: text = weak/uncertain influence claim.           mu=0.30, sigma=0.25
  Option 4: text = negligible influence claim.               mu=0.15, sigma=0.15

THESE mu/sigma VALUES ARE FIXED. Do NOT change them.

CRITICAL RULES FOR OPTION TEXT (THIS IS THE MOST IMPORTANT PART):
Each option text MUST be a well-structured sentence (15-30 words) that helps a Product Manager decide. The sentence should explain the MECHANISM (why/how this node matters), not just state that it is "important" or "negligible".

BAD examples (too generic, unhelpful):
  ❌ "A Confiança é decisiva."
  ❌ "Confiança tem influência significativa."
  ❌ "Confiança é pouco relevante."

GOOD examples (explain the mechanism, help PM decide):
  ✅ "A Confiança é decisiva: sem ela, mesmo usuários interessados desistem por receio de risco financeiro ou exposição de dados."
  ✅ "A Confiança tem peso importante ao reduzir a barreira psicológica, embora outros fatores também contribuam para a decisão."
  ✅ "A Confiança agrega pouco valor isoladamente, pois o público-alvo já confia na marca e prioriza outros critérios como preço."

STRUCTURE OF EACH OPTION TEXT:
- Start with a clear position statement about the node's influence
- Follow with a concise explanation of WHY (the causal mechanism)
- Reference the specific product/experiment context, not generic platitudes
- Option 2 (uncertainty) should ALWAYS start with "Não sei avaliar o peso de [node]" and add a brief reason why it's hard to judge
- Explain how the interaction between its parent nodes creates this emergent effect
- ALL options are complete Portuguese BR sentences, 15-30 words each.

VARIED DEFAULTS:
- "default" is NOT always 2. Be OPINIONATED based on the product context.
- At least 2 nodes should have default != 2. At least 1 should be 0,1 or 3,4.

Respond with ONLY valid JSON:
{
  "nodes": [
    {
      "name": "Confiança para Usar",
      "header": "string",
      "options": [{"text":"string","mu":0.80,"sigma":0.15}, ...5 items],
      "default": number
    }
  ]
}"""


def generate_topology(
    llm_client: LLMClient,
    experiment_context: str,
    yaml_sensitivities: dict,
) -> dict:
    """Generate DAG topology via LLM (Pass 1).

    Args:
        llm_client: LLM client instance.
        experiment_context: Experiment name + hypothesis + description.
        yaml_sensitivities: Dict of sensitivity configs from YAML.

    Returns:
        Parsed topology dict with nodes and edges.

    Raises:
        RuntimeError: If LLM returns invalid JSON.
    """
    with _tracer.start_as_current_span(
        "DAGGenerator: generate_topology",
        attributes={
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
            "operation.type": "dag_topology_generation",
        },
    ) as span:
        # Format YAML sensitivities as reference
        sens_ref_parts = []
        for key, config in yaml_sensitivities.items():
            desc = config.get("description", key)
            base = config.get("base", 0.5)
            n_rules = len(config.get("rules", []))
            sens_ref_parts.append(
                f"- {key}: {desc} (base={base}, {n_rules} rules)"
            )
        sens_reference = "\n".join(sens_ref_parts)

        user_message = (
            f"{experiment_context}\n\n"
            f"YAML Sensitivities (use at least 2):\n{sens_reference}"
        )

        logger.info("Generating DAG topology (Pass 1)")
        response_text = llm_client.complete_json(
            messages=[
                {"role": "system", "content": TOPOLOGY_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            model="gpt-5.2",
            operation_name="DAG Topology (gpt-5.2)",
        )

        try:
            topology = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"LLM returned invalid JSON for topology: {e}") from e

        if span:
            span.set_attribute("node_count", len(topology.get("nodes", [])))
            span.set_attribute("edge_count", len(topology.get("edges", [])))

        logger.info(
            f"Topology generated: {len(topology.get('nodes', []))} nodes, "
            f"{len(topology.get('edges', []))} edges"
        )
        return topology


def generate_options(
    llm_client: LLMClient,
    topology: dict,
) -> dict:
    """Generate Likert options for interaction + outcome nodes (Pass 2).

    Args:
        llm_client: LLM client instance.
        topology: Topology dict from Pass 1.

    Returns:
        Parsed dict with node options: {"nodes": [{"name", "header", "options", "default"}]}.

    Raises:
        RuntimeError: If LLM returns invalid JSON.
    """
    with _tracer.start_as_current_span(
        "DAGGenerator: generate_options",
        attributes={
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
            "operation.type": "dag_node_options_generation",
        },
    ) as span:
        # Filter to interaction nodes only (outcome gets options built from interactions)
        calibratable_nodes = [
            n for n in topology.get("nodes", [])
            if n.get("type") == "interaction"
        ]

        if not calibratable_nodes:
            logger.warning("No interaction/outcome nodes found in topology")
            return {"nodes": []}

        # Build compact summaries for the LLM
        nodes_summary = ", ".join(
            f"{n['name']} ({n['type']})" for n in topology.get("nodes", [])
        )
        edges_summary = json.dumps(
            [{"from": e["from"], "to": e["to"], "direction": e.get("direction", 1)}
             for e in topology.get("edges", [])],
            ensure_ascii=False,
        )
        target_nodes = json.dumps(
            [{"name": n["name"], "type": n["type"], "description": n.get("description", "")}
             for n in calibratable_nodes],
            ensure_ascii=False,
        )

        user_message = (
            f"DAG Label: {topology.get('label', 'Modelo Causal')}\n"
            f"All nodes: {nodes_summary}\n"
            f"Edges: {edges_summary}\n"
            f"Nodes to generate premissa options for:\n{target_nodes}"
        )

        logger.info(f"Generating options for {len(calibratable_nodes)} nodes (Pass 2)")
        response_text = llm_client.complete_json(
            messages=[
                {"role": "system", "content": OPTIONS_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            model="gpt-4.1-nano",
            operation_name="DAG Node Options (gpt-4.1-nano)",
        )

        try:
            options_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"LLM returned invalid JSON for node options: {e}") from e

        if span:
            span.set_attribute("calibratable_node_count", len(calibratable_nodes))
            span.set_attribute("options_generated", len(options_data.get("nodes", [])))

        logger.info(f"Options generated for {len(options_data.get('nodes', []))} nodes")
        return options_data
