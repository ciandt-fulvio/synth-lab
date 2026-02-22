"""
Monte Carlo simulation engine for quantitative analysis.

Pure computation module: no I/O, no database, no LLM calls.
All functions operate on plain dicts/lists and NumPy arrays.

Formulas from: specs/042-quantitative-analysis/spec.md (Apêndice D)

References:
    - NumPy docs: https://numpy.org/doc/stable/reference/random/generator.html
"""

import math
from typing import Any

import numpy as np

# -- Constants --
BUDGET = 3.0  # total logit swing
DEFAULT_N_ITERATIONS = 3000
SENSITIVITY_ITERATIONS = 800

# Education level mapping (ordered by approximate education years)
_EDUCATION_MAP: dict[str, float] = {
    "sem escolaridade": 0.0,
    "fundamental incompleto": 0.15,
    "fundamental completo": 0.25,
    "médio incompleto": 0.35,
    "médio completo": 0.45,
    "superior incompleto": 0.60,
    "superior completo": 0.75,
    "pós-graduação": 0.85,
    "mestrado": 0.90,
    "doutorado": 1.0,
}


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp value to [lo, hi]."""
    return max(lo, min(hi, value))


def _normalize(value: float, min_val: float, max_val: float) -> float:
    """Normalize value from [min_val, max_val] to [0, 1]."""
    if max_val <= min_val:
        return 0.5
    return _clamp((value - min_val) / (max_val - min_val))


# -- UserVar Extractors --
# Each extractor takes a synth dict and returns a float in [0, 1].


def _extract_age_norm(synth: dict) -> float:
    """Normalize age from [18, 80] → [0, 1]."""
    demo = synth.get("data", {}).get("demografia", {})
    age = demo.get("idade")
    if age is None:
        return 0.5
    return _normalize(float(age), 18.0, 80.0)


def _extract_income_norm(synth: dict) -> float:
    """Normalize monthly income from [0, 20000] → [0, 1]."""
    demo = synth.get("data", {}).get("demografia", {})
    income = demo.get("renda_mensal")
    if income is None:
        return 0.5
    return _normalize(float(income), 0.0, 20000.0)


def _extract_edu_norm(synth: dict) -> float:
    """Map education level string to [0, 1] via lookup table."""
    demo = synth.get("data", {}).get("demografia", {})
    edu = demo.get("escolaridade", "")
    if not edu:
        return 0.5
    # Case-insensitive fuzzy match
    edu_lower = edu.lower().strip()
    for key, val in _EDUCATION_MAP.items():
        if key in edu_lower or edu_lower in key:
            return val
    return 0.5


def _extract_family_size_norm(synth: dict) -> float:
    """Normalize family size from [1, 8] → [0, 1]."""
    demo = synth.get("data", {}).get("demografia", {})
    comp = demo.get("composicao_familiar", {})
    if isinstance(comp, dict):
        size = comp.get("numero_pessoas")
    else:
        size = None
    if size is None:
        return 0.5
    return _normalize(float(size), 1.0, 8.0)


def _extract_has_visual_disab(synth: dict) -> float:
    """1.0 if visual disability exists and != 'nenhuma', else 0.0."""
    defic = synth.get("data", {}).get("deficiencias", {})
    visual = defic.get("visual")
    if isinstance(visual, dict):
        tipo = visual.get("tipo", "nenhuma")
    elif isinstance(visual, str):
        tipo = visual
    else:
        return 0.0
    return 0.0 if tipo.lower() in ("nenhuma", "") else 1.0


def _extract_has_motor_disab(synth: dict) -> float:
    """1.0 if motor disability exists and != 'nenhuma', else 0.0."""
    defic = synth.get("data", {}).get("deficiencias", {})
    motora = defic.get("motora")
    if isinstance(motora, dict):
        tipo = motora.get("tipo", "nenhuma")
    elif isinstance(motora, str):
        tipo = motora
    else:
        return 0.0
    return 0.0 if tipo.lower() in ("nenhuma", "") else 1.0


def _extract_sensitivity(synth: dict, key: str) -> float:
    """Extract a sensitivity value (already [0, 1]) with 0.5 default."""
    sensitivities = synth.get("data", {}).get("sensitivities", {})
    val = sensitivities.get(key)
    if val is None:
        return 0.5
    return _clamp(float(val))


def _extract_digital_capability(synth: dict) -> float:
    return _extract_sensitivity(synth, "digital_capability")


def _extract_risk_aversion(synth: dict) -> float:
    return _extract_sensitivity(synth, "risk_aversion")


def _extract_institutional_trust(synth: dict) -> float:
    return _extract_sensitivity(synth, "institutional_trust_level")


def _extract_friction_tolerance(synth: dict) -> float:
    return _extract_sensitivity(synth, "friction_tolerance")


# Registry mapping userVar names to extractor functions
USERVAR_EXTRACTORS: dict[str, Any] = {
    "ageNorm": _extract_age_norm,
    "incomeNorm": _extract_income_norm,
    "eduNorm": _extract_edu_norm,
    "familySizeNorm": _extract_family_size_norm,
    "hasVisualDisab": _extract_has_visual_disab,
    "hasMotorDisab": _extract_has_motor_disab,
    "digitalCapability": _extract_digital_capability,
    "riskAversion": _extract_risk_aversion,
    "institutionalTrust": _extract_institutional_trust,
    "frictionTolerance": _extract_friction_tolerance,
}


def extract_user_vars(synths: list[dict], user_vars: list[str]) -> np.ndarray:
    """Extract userVar values for all synths.

    Args:
        synths: List of synth dicts (with 'data' nested field).
        user_vars: List of userVar names (one per edge).

    Returns:
        NumPy array of shape (n_synths, n_vars) with values in [0, 1].
    """
    n_synths = len(synths)
    n_vars = len(user_vars)
    result = np.full((n_synths, n_vars), 0.5)

    for j, var_name in enumerate(user_vars):
        extractor = USERVAR_EXTRACTORS.get(var_name)
        if extractor is None:
            continue
        for i, synth in enumerate(synths):
            result[i, j] = extractor(synth)

    return result


def _sigmoid(x: np.ndarray) -> np.ndarray:
    """Vectorized sigmoid: 1 / (1 + exp(-x))."""
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))


def run_monte_carlo(
    edges: list[dict],
    selections: dict[str, int],
    user_var_matrix: np.ndarray,
    intercept_mu: float,
    intercept_sigma: float,
    n_iterations: int = DEFAULT_N_ITERATIONS,
    seed: int | None = None,
) -> dict:
    """Run Monte Carlo simulation per Apêndice D formulas.

    Args:
        edges: List of edge dicts with id, direction, options, default_option.
        selections: Map of edge_id → selected option index.
        user_var_matrix: Shape (n_synths, n_edges) from extract_user_vars.
        intercept_mu: Model intercept mean.
        intercept_sigma: Model intercept standard deviation.
        n_iterations: Number of Monte Carlo iterations.
        seed: Random seed for reproducibility.

    Returns:
        Dict with keys: distribution (list[float]), stats (dict).
    """
    rng = np.random.default_rng(seed)
    n_synths = user_var_matrix.shape[0]
    n_edges = len(edges)
    per_edge_scale = BUDGET / max(math.sqrt(n_edges), 1.0)

    # Precompute edge parameters
    beta_mus = np.zeros(n_edges)
    beta_sigmas = np.zeros(n_edges)
    directions = np.zeros(n_edges)

    for i, edge in enumerate(edges):
        edge_id = edge["id"]
        selected = selections.get(edge_id, edge.get("default_option", 2))
        opt = edge["options"][selected]
        d = edge["direction"]
        beta_mus[i] = opt["mu"] * per_edge_scale * d
        beta_sigmas[i] = opt["sigma"] * per_edge_scale
        directions[i] = d

    distribution = np.zeros(n_iterations)

    for s in range(n_iterations):
        intercept = rng.normal(intercept_mu, intercept_sigma)
        coefs = rng.normal(beta_mus, beta_sigmas)  # shape (n_edges,)

        # logit = intercept + sum(coef_i * userVar_i) for each synth
        logits = intercept + user_var_matrix @ coefs  # shape (n_synths,)
        probs = _sigmoid(logits)
        adopted = rng.random(n_synths) < probs
        distribution[s] = adopted.sum() / n_synths * 100  # percentage

    dist_list = distribution.tolist()
    stats = {
        "mean": round(float(np.mean(distribution)), 1),
        "median": round(float(np.median(distribution)), 1),
        "std": round(float(np.std(distribution)), 1),
        "p10": round(float(np.percentile(distribution, 10)), 1),
        "p90": round(float(np.percentile(distribution, 90)), 1),
    }

    return {"distribution": dist_list, "stats": stats}


def compute_segments(
    edges: list[dict],
    selections: dict[str, int],
    synths: list[dict],
    user_var_matrix: np.ndarray,
    intercept_mu: float,
    intercept_sigma: float,
    seed: int | None = None,
) -> dict:
    """Compute adoption rate by demographic segments.

    Buckets:
    - age: 18-29, 30-49, 50+
    - income: baixa (<3000), media (3000-10000), alta (>10000)
    - education: baixa (<=fundamental), media (medio), alta (>=superior)
    """
    rng = np.random.default_rng(seed)
    n_synths = len(synths)
    n_edges = len(edges)
    per_edge_scale = BUDGET / max(math.sqrt(n_edges), 1.0)

    # Single representative iteration with many synths (use mean coefficients)
    # For segment analysis, run a quick simulation to get per-synth adoption rates
    n_segment_iters = 500
    adoption_counts = np.zeros(n_synths)

    beta_mus = np.zeros(n_edges)
    beta_sigmas = np.zeros(n_edges)
    for i, edge in enumerate(edges):
        edge_id = edge["id"]
        selected = selections.get(edge_id, edge.get("default_option", 2))
        opt = edge["options"][selected]
        beta_mus[i] = opt["mu"] * per_edge_scale * edge["direction"]
        beta_sigmas[i] = opt["sigma"] * per_edge_scale

    for _ in range(n_segment_iters):
        intercept = rng.normal(intercept_mu, intercept_sigma)
        coefs = rng.normal(beta_mus, beta_sigmas)
        logits = intercept + user_var_matrix @ coefs
        probs = _sigmoid(logits)
        adopted = rng.random(n_synths) < probs
        adoption_counts += adopted

    per_synth_rate = adoption_counts / n_segment_iters * 100

    # Build segment buckets
    def _bucket_stats(indices: list[int]) -> dict:
        if not indices:
            return {"rate": 0.0, "count": 0}
        rates = per_synth_rate[indices]
        return {"rate": round(float(np.mean(rates)), 1), "count": len(indices)}

    # Age buckets
    age_18_29: list[int] = []
    age_30_49: list[int] = []
    age_50_plus: list[int] = []
    for i, synth in enumerate(synths):
        age = synth.get("data", {}).get("demografia", {}).get("idade")
        if age is None:
            age_30_49.append(i)  # default to middle
        elif age < 30:
            age_18_29.append(i)
        elif age < 50:
            age_30_49.append(i)
        else:
            age_50_plus.append(i)

    # Income buckets
    inc_low: list[int] = []
    inc_mid: list[int] = []
    inc_high: list[int] = []
    for i, synth in enumerate(synths):
        income = synth.get("data", {}).get("demografia", {}).get("renda_mensal")
        if income is None:
            inc_mid.append(i)
        elif income < 3000:
            inc_low.append(i)
        elif income <= 10000:
            inc_mid.append(i)
        else:
            inc_high.append(i)

    # Education buckets
    edu_low: list[int] = []
    edu_mid: list[int] = []
    edu_high: list[int] = []
    low_edu_keys = {"sem escolaridade", "fundamental incompleto", "fundamental completo"}
    mid_edu_keys = {"médio incompleto", "médio completo"}
    for i, synth in enumerate(synths):
        raw = synth.get("data", {}).get("demografia", {}).get("escolaridade") or ""
        edu = raw.lower().strip()
        if edu in low_edu_keys:
            edu_low.append(i)
        elif edu in mid_edu_keys:
            edu_mid.append(i)
        else:
            edu_high.append(i)

    return {
        "age": {
            "18-29": _bucket_stats(age_18_29),
            "30-49": _bucket_stats(age_30_49),
            "50+": _bucket_stats(age_50_plus),
        },
        "income": {
            "baixa": _bucket_stats(inc_low),
            "media": _bucket_stats(inc_mid),
            "alta": _bucket_stats(inc_high),
        },
        "education": {
            "baixa": _bucket_stats(edu_low),
            "media": _bucket_stats(edu_mid),
            "alta": _bucket_stats(edu_high),
        },
    }


def run_sensitivity(
    edges: list[dict],
    selections: dict[str, int],
    user_var_matrix: np.ndarray,
    intercept_mu: float,
    intercept_sigma: float,
    seed: int | None = None,
) -> list[dict]:
    """Run sensitivity analysis per Apêndice D.

    For each edge: fix all others, vary between option 0 (strong) and option 4 (weak).
    Impact = |mean_low - mean_high|.

    Returns list sorted by impact descending.
    """
    results = []

    for idx, edge in enumerate(edges):
        edge_id = edge["id"]

        # Low: set this edge to option 0 (strongest)
        sel_low = {**selections, edge_id: 0}
        res_low = run_monte_carlo(
            edges, sel_low, user_var_matrix,
            intercept_mu, intercept_sigma,
            n_iterations=SENSITIVITY_ITERATIONS,
            seed=seed,
        )

        # High: set this edge to option 4 (weakest)
        sel_high = {**selections, edge_id: 4}
        res_high = run_monte_carlo(
            edges, sel_high, user_var_matrix,
            intercept_mu, intercept_sigma,
            n_iterations=SENSITIVITY_ITERATIONS,
            seed=(seed + idx + 1) if seed is not None else None,
        )

        mean_low = res_low["stats"]["mean"]
        mean_high = res_high["stats"]["mean"]
        impact = round(abs(mean_low - mean_high), 1)

        results.append({
            "edge_id": edge_id,
            "header": edge.get("header", ""),
            "impact": impact,
            "mean_low": mean_low,
            "mean_high": mean_high,
        })

    results.sort(key=lambda x: x["impact"], reverse=True)
    return results


# ============================================================================
# V2 functions for enriched DAG (5 node types, 4 layers)
# ============================================================================


def _topological_sort(nodes: list[dict], edges: list[dict]) -> list[str]:
    """Topological sort of node names using Kahn's algorithm.

    Args:
        nodes: List of node dicts with 'name' key.
        edges: List of edge dicts with 'from' and 'to' keys.

    Returns:
        Sorted list of node names.
    """
    from collections import deque

    node_names = [n["name"] for n in nodes]
    in_degree = {name: 0 for name in node_names}
    adjacency: dict[str, list[str]] = {name: [] for name in node_names}

    for e in edges:
        src = e.get("from_node", e.get("from", ""))
        dst = e.get("to_node", e.get("to", ""))
        if src in adjacency and dst in in_degree:
            adjacency[src].append(dst)
            in_degree[dst] += 1

    queue = deque(name for name in node_names if in_degree[name] == 0)
    sorted_names: list[str] = []

    while queue:
        node = queue.popleft()
        sorted_names.append(node)
        for neighbor in adjacency.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Add any remaining nodes (shouldn't happen in a valid DAG)
    for name in node_names:
        if name not in sorted_names:
            sorted_names.append(name)

    return sorted_names


def build_node_values(
    synths: list[dict],
    node_metadata: dict[str, dict],
    edges: list[dict],
    product_values: dict[str, float],
    sensitivity_configs: dict[str, dict],
    seed: int | None = None,
) -> dict[str, np.ndarray]:
    """Compute value for every node for every synth.

    Topological order:
    1. Demographic: extract from synth (ageNorm, incomeNorm, etc.)
    2. Sensitivity: compute_sensitivity_for_config() per synth
    3. Product: constant value broadcast to n_synths
    4. Interaction: f(parent values * weights * directions)
    5. Outcome: not computed here (done by Monte Carlo)

    Args:
        synths: List of synth dicts.
        node_metadata: Per-node metadata dict.
        edges: List of edge dicts.
        product_values: Product node name → numeric value (0.2/0.5/0.8).
        sensitivity_configs: Sensitivity key → config dict with base/rules.
        seed: Random seed.

    Returns:
        Dict of node_name → np.ndarray of shape (n_synths,).
    """
    from synth_lab.services.sensitivity_deriver import compute_sensitivity_for_config

    n_synths = len(synths)
    node_values: dict[str, np.ndarray] = {}

    # Build nodes list for topological sort
    nodes_list = [{"name": name} for name in node_metadata]
    sorted_names = _topological_sort(nodes_list, edges)

    # Build adjacency: child → list of (parent_name, weight, direction)
    child_parents: dict[str, list[tuple[str, float, int]]] = {}
    for e in edges:
        src = e.get("from_node", e.get("from", ""))
        dst = e.get("to_node", e.get("to", ""))
        weight = e.get("weight", 0.5)
        direction = e.get("direction", 1)
        child_parents.setdefault(dst, []).append((src, weight, direction))

    # Map demographic node names to extractors
    _DEMOGRAPHIC_EXTRACTORS = {
        "ageNorm": _extract_age_norm,
        "incomeNorm": _extract_income_norm,
        "eduNorm": _extract_edu_norm,
        "familySizeNorm": _extract_family_size_norm,
    }

    # Infer which extractor to use for demographic nodes based on name
    _DEMO_NAME_MAP = {
        "idade": "ageNorm",
        "renda": "incomeNorm",
        "escolaridade": "eduNorm",
        "família": "familySizeNorm",
        "tamanho": "familySizeNorm",
    }

    for name in sorted_names:
        meta = node_metadata.get(name, {})
        node_type = meta.get("node_type", "interaction")

        if node_type == "demographic":
            # Find best extractor by name matching
            name_lower = name.lower()
            extractor_key = None
            for keyword, var_key in _DEMO_NAME_MAP.items():
                if keyword in name_lower:
                    extractor_key = var_key
                    break

            if extractor_key and extractor_key in _DEMOGRAPHIC_EXTRACTORS:
                extractor = _DEMOGRAPHIC_EXTRACTORS[extractor_key]
                values = np.array([extractor(s) for s in synths])
            else:
                values = np.full(n_synths, 0.5)
            node_values[name] = values

        elif node_type == "sensitivity":
            sens_key = meta.get("sensitivity_key", "")
            config = sensitivity_configs.get(sens_key, meta.get("custom_config", {}))
            if not config:
                config = {"base": 0.5, "rules": []}

            values = np.zeros(n_synths)
            for i, synth in enumerate(synths):
                synth_data = synth.get("data", {})
                s = seed + i if seed is not None else None
                values[i] = compute_sensitivity_for_config(synth_data, config, seed=s)
            node_values[name] = values

        elif node_type == "product":
            prod_val = product_values.get(name, 0.5)
            node_values[name] = np.full(n_synths, prod_val)

        elif node_type == "interaction":
            # Combine parent values: mean(effective_i * weight_i), clamped [0,1]
            # direction=1 → use value as-is; direction=-1 → inverse (1 - value)
            parents = child_parents.get(name, [])
            if parents:
                weighted_sum = np.zeros(n_synths)
                total_weight = 0.0
                for parent_name, weight, direction in parents:
                    parent_vals = node_values.get(parent_name, np.full(n_synths, 0.5))
                    effective_vals = parent_vals if direction == 1 else (1.0 - parent_vals)
                    weighted_sum += effective_vals * weight
                    total_weight += abs(weight)
                if total_weight > 0:
                    interaction_val = weighted_sum / total_weight
                else:
                    interaction_val = np.full(n_synths, 0.5)
                node_values[name] = np.clip(interaction_val, 0.0, 1.0)
            else:
                node_values[name] = np.full(n_synths, 0.5)

        elif node_type == "outcome":
            # Outcome computed by Monte Carlo, skip here
            pass

    return node_values


def build_base_node_values(
    synths: list[dict],
    node_metadata: dict[str, dict],
    edges: list[dict],
    sensitivity_configs: dict[str, dict],
    seed: int | None = None,
) -> tuple[dict[str, np.ndarray], list[str], dict[str, list[tuple[str, float, int]]]]:
    """Pre-compute invariant node values (demographic + sensitivity) for batch reuse.

    Only computes demographic and sensitivity nodes. Product and interaction nodes
    are scenario-dependent and must be applied per scenario via apply_product_scenario().

    Args:
        synths: List of synth dicts.
        node_metadata: Per-node metadata dict.
        edges: List of edge dicts.
        sensitivity_configs: Sensitivity key -> config dict.
        seed: Random seed.

    Returns:
        Tuple of:
            base_values: Dict of node_name -> np.ndarray for demographic + sensitivity nodes.
            sorted_names: Topological order of all node names.
            child_parents: Adjacency dict {child -> [(parent, weight, direction)]}.
    """
    from synth_lab.services.sensitivity_deriver import compute_sensitivity_for_config

    n_synths = len(synths)
    base_values: dict[str, np.ndarray] = {}

    nodes_list = [{"name": name} for name in node_metadata]
    sorted_names = _topological_sort(nodes_list, edges)

    child_parents: dict[str, list[tuple[str, float, int]]] = {}
    for e in edges:
        src = e.get("from_node", e.get("from", ""))
        dst = e.get("to_node", e.get("to", ""))
        weight = e.get("weight", 0.5)
        direction = e.get("direction", 1)
        child_parents.setdefault(dst, []).append((src, weight, direction))

    _DEMOGRAPHIC_EXTRACTORS = {
        "ageNorm": _extract_age_norm,
        "incomeNorm": _extract_income_norm,
        "eduNorm": _extract_edu_norm,
        "familySizeNorm": _extract_family_size_norm,
    }
    _DEMO_NAME_MAP = {
        "idade": "ageNorm",
        "renda": "incomeNorm",
        "escolaridade": "eduNorm",
        "família": "familySizeNorm",
        "tamanho": "familySizeNorm",
    }

    for name in sorted_names:
        meta = node_metadata.get(name, {})
        node_type = meta.get("node_type", "interaction")

        if node_type == "demographic":
            name_lower = name.lower()
            extractor_key = None
            for keyword, var_key in _DEMO_NAME_MAP.items():
                if keyword in name_lower:
                    extractor_key = var_key
                    break
            if extractor_key and extractor_key in _DEMOGRAPHIC_EXTRACTORS:
                values = np.array([_DEMOGRAPHIC_EXTRACTORS[extractor_key](s) for s in synths])
            else:
                values = np.full(n_synths, 0.5)
            base_values[name] = values

        elif node_type == "sensitivity":
            sens_key = meta.get("sensitivity_key", "")
            config = sensitivity_configs.get(sens_key, meta.get("custom_config", {}))
            if not config:
                config = {"base": 0.5, "rules": []}
            values = np.zeros(n_synths)
            for i, synth in enumerate(synths):
                synth_data = synth.get("data", {})
                s = seed + i if seed is not None else None
                values[i] = compute_sensitivity_for_config(synth_data, config, seed=s)
            base_values[name] = values

    return base_values, sorted_names, child_parents


def apply_product_scenario(
    base_values: dict[str, np.ndarray],
    node_metadata: dict[str, dict],
    product_values: dict[str, float],
    sorted_names: list[str],
    child_parents: dict[str, list[tuple[str, float, int]]],
    n_synths: int,
) -> dict[str, np.ndarray]:
    """Apply scenario-specific product values and recompute interaction nodes.

    Takes pre-computed base values (demographic + sensitivity) and adds product
    and interaction node values for a specific scenario.

    Args:
        base_values: Pre-computed invariant node values.
        node_metadata: Per-node metadata dict.
        product_values: Product node name -> numeric value (0.2/0.5/0.8).
        sorted_names: Topological order from build_base_node_values().
        child_parents: Adjacency from build_base_node_values().
        n_synths: Number of synths.

    Returns:
        Complete dict of node_name -> np.ndarray for all node types.
    """
    node_values = dict(base_values)  # shallow copy (arrays are read-only here)

    for name in sorted_names:
        meta = node_metadata.get(name, {})
        node_type = meta.get("node_type", "interaction")

        if node_type == "product":
            prod_val = product_values.get(name, 0.5)
            node_values[name] = np.full(n_synths, prod_val)

        elif node_type == "interaction":
            parents = child_parents.get(name, [])
            if parents:
                weighted_sum = np.zeros(n_synths)
                total_weight = 0.0
                for parent_name, weight, direction in parents:
                    parent_vals = node_values.get(parent_name, np.full(n_synths, 0.5))
                    effective_vals = parent_vals if direction == 1 else (1.0 - parent_vals)
                    weighted_sum += effective_vals * weight
                    total_weight += abs(weight)
                if total_weight > 0:
                    interaction_val = weighted_sum / total_weight
                else:
                    interaction_val = np.full(n_synths, 0.5)
                node_values[name] = np.clip(interaction_val, 0.0, 1.0)
            else:
                node_values[name] = np.full(n_synths, 0.5)

    return node_values


def _compute_outcome_weight_multipliers(
    outcome_edges: list[dict],
    node_metadata: dict[str, dict],
    node_selections: dict[str, int],
) -> np.ndarray:
    """Compute weight multipliers based on outcome node's "most important" selection.

    The outcome node's options list interaction node names. The selected one gets
    2x weight, others get 1x, normalized so average stays at 1.0.

    If n interactions: selected gets 2n/(n+1), others get n/(n+1).

    Args:
        outcome_edges: Edges pointing to the outcome node.
        node_metadata: Per-node metadata.
        node_selections: Node selections including outcome.

    Returns:
        Array of shape (n_edges,) with multipliers.
    """
    n_edges = len(outcome_edges)
    multipliers = np.ones(n_edges)

    # Find outcome node and its selection
    outcome_name = None
    if outcome_edges:
        outcome_name = outcome_edges[0].get("to_node", outcome_edges[0].get("to", ""))

    if not outcome_name:
        return multipliers

    outcome_meta = node_metadata.get(outcome_name, {})
    outcome_options = outcome_meta.get("options", [])

    if not outcome_options or outcome_meta.get("node_type") != "outcome":
        return multipliers

    selected_idx = node_selections.get(
        outcome_name, outcome_meta.get("default_option", 0)
    )
    if selected_idx >= len(outcome_options):
        selected_idx = 0

    # The selected option text is the name of the "most important" interaction
    selected_interaction = outcome_options[selected_idx].get("text", "")

    if not selected_interaction:
        return multipliers

    # Build source node map for edges
    edge_sources = [
        e.get("from_node", e.get("from", "")) for e in outcome_edges
    ]

    # Apply 2x to selected, 1x to others, then normalize
    # With n edges: selected = 2, others = 1, total = n+1
    # Normalize by n/(n+1) so average = 1.0
    n = n_edges
    norm_factor = n / (n + 1) if n > 0 else 1.0

    for i, src in enumerate(edge_sources):
        if src == selected_interaction:
            multipliers[i] = 2.0 * norm_factor
        else:
            multipliers[i] = 1.0 * norm_factor

    return multipliers


def run_monte_carlo_v2(
    outcome_edges: list[dict],
    node_values: dict[str, np.ndarray],
    node_selections: dict[str, int],
    node_metadata: dict[str, dict],
    intercept_mu: float,
    intercept_sigma: float,
    n_iterations: int = DEFAULT_N_ITERATIONS,
    seed: int | None = None,
) -> dict:
    """Monte Carlo simulation using pre-computed node values and node-level premissas.

    Coefficients come from the SOURCE NODE's premissa options (not from edges).
    Each interaction node has 5 Likert options; the selected mu/sigma
    determine how strongly that node influences the outcome.

    The outcome node's selection determines which interaction is "most important"
    and gets a 2x weight multiplier (others get 1x, normalized).

    Args:
        outcome_edges: Edges pointing to the outcome node.
        node_values: Pre-computed node values from build_node_values().
        node_selections: Map of node_name → selected option index.
        node_metadata: Per-node metadata with options.
        intercept_mu: Model intercept mean.
        intercept_sigma: Model intercept std dev.
        n_iterations: Number of Monte Carlo iterations.
        seed: Random seed.

    Returns:
        Dict with keys: distribution (list[float]), stats (dict).
    """
    rng = np.random.default_rng(seed)
    n_edges = len(outcome_edges)
    if n_edges == 0:
        return {"distribution": [50.0] * n_iterations, "stats": {
            "mean": 50.0, "median": 50.0, "std": 0.0, "p10": 50.0, "p90": 50.0,
        }}

    # Get n_synths from first available node value
    n_synths = 0
    for vals in node_values.values():
        n_synths = len(vals)
        break

    if n_synths == 0:
        return {"distribution": [50.0] * n_iterations, "stats": {
            "mean": 50.0, "median": 50.0, "std": 0.0, "p10": 50.0, "p90": 50.0,
        }}

    per_edge_scale = BUDGET / max(math.sqrt(n_edges), 1.0)

    # Compute outcome weight multipliers (2x for "most important" interaction)
    weight_multipliers = _compute_outcome_weight_multipliers(
        outcome_edges, node_metadata, node_selections,
    )

    # Build input matrix: node values for each outcome edge's source
    input_matrix = np.full((n_synths, n_edges), 0.5)
    beta_mus = np.zeros(n_edges)
    beta_sigmas = np.zeros(n_edges)

    for i, edge in enumerate(outcome_edges):
        src = edge.get("from_node", edge.get("from", ""))
        input_matrix[:, i] = node_values.get(src, np.full(n_synths, 0.5))
        d = edge.get("direction", 1)

        # Get mu/sigma from the source node's premissa options
        src_meta = node_metadata.get(src, {})
        src_options = src_meta.get("options", [])

        if src_options:
            selected = node_selections.get(src, src_meta.get("default_option", 2))
            opt = src_options[selected] if selected < len(src_options) else src_options[2]
            beta_mus[i] = opt["mu"] * per_edge_scale * d * weight_multipliers[i]
            beta_sigmas[i] = opt["sigma"] * per_edge_scale * weight_multipliers[i]
        else:
            # Fallback: use edge weight directly
            weight = edge.get("weight", 0.5)
            beta_mus[i] = weight * per_edge_scale * d * weight_multipliers[i]
            beta_sigmas[i] = 0.1 * per_edge_scale * weight_multipliers[i]

    distribution = np.zeros(n_iterations)

    for s in range(n_iterations):
        intercept = rng.normal(intercept_mu, intercept_sigma)
        coefs = rng.normal(beta_mus, beta_sigmas)
        logits = intercept + input_matrix @ coefs
        probs = _sigmoid(logits)
        adopted = rng.random(n_synths) < probs
        distribution[s] = adopted.sum() / n_synths * 100

    dist_list = distribution.tolist()
    stats = {
        "mean": round(float(np.mean(distribution)), 1),
        "median": round(float(np.median(distribution)), 1),
        "std": round(float(np.std(distribution)), 1),
        "p10": round(float(np.percentile(distribution, 10)), 1),
        "p90": round(float(np.percentile(distribution, 90)), 1),
    }

    return {"distribution": dist_list, "stats": stats}


def compute_segments_v2(
    outcome_edges: list[dict],
    node_values: dict[str, np.ndarray],
    node_selections: dict[str, int],
    node_metadata: dict[str, dict],
    synths: list[dict],
    intercept_mu: float,
    intercept_sigma: float,
    seed: int | None = None,
) -> dict:
    """Compute segments using v2 node values and node-level premissas."""
    rng = np.random.default_rng(seed)
    n_synths = len(synths)
    n_edges = len(outcome_edges)

    if n_edges == 0 or n_synths == 0:
        empty_bucket = {"rate": 0.0, "count": 0}
        return {
            "age": {"18-29": empty_bucket, "30-49": empty_bucket, "50+": empty_bucket},
            "income": {"baixa": empty_bucket, "media": empty_bucket, "alta": empty_bucket},
            "education": {"baixa": empty_bucket, "media": empty_bucket, "alta": empty_bucket},
        }

    per_edge_scale = BUDGET / max(math.sqrt(n_edges), 1.0)

    # Compute outcome weight multipliers
    weight_multipliers = _compute_outcome_weight_multipliers(
        outcome_edges, node_metadata, node_selections,
    )

    # Build input matrix
    input_matrix = np.full((n_synths, n_edges), 0.5)
    beta_mus = np.zeros(n_edges)
    beta_sigmas = np.zeros(n_edges)

    for i, edge in enumerate(outcome_edges):
        src = edge.get("from_node", edge.get("from", ""))
        input_matrix[:, i] = node_values.get(src, np.full(n_synths, 0.5))
        d = edge.get("direction", 1)

        src_meta = node_metadata.get(src, {})
        src_options = src_meta.get("options", [])

        if src_options:
            selected = node_selections.get(src, src_meta.get("default_option", 2))
            opt = src_options[selected] if selected < len(src_options) else src_options[2]
            beta_mus[i] = opt["mu"] * per_edge_scale * d * weight_multipliers[i]
            beta_sigmas[i] = opt["sigma"] * per_edge_scale * weight_multipliers[i]
        else:
            weight = edge.get("weight", 0.5)
            beta_mus[i] = weight * per_edge_scale * d * weight_multipliers[i]
            beta_sigmas[i] = 0.1 * per_edge_scale * weight_multipliers[i]

    n_segment_iters = 500
    adoption_counts = np.zeros(n_synths)

    for _ in range(n_segment_iters):
        intercept = rng.normal(intercept_mu, intercept_sigma)
        coefs = rng.normal(beta_mus, beta_sigmas)
        logits = intercept + input_matrix @ coefs
        probs = _sigmoid(logits)
        adopted = rng.random(n_synths) < probs
        adoption_counts += adopted

    per_synth_rate = adoption_counts / n_segment_iters * 100

    def _bucket_stats(indices: list[int]) -> dict:
        if not indices:
            return {"rate": 0.0, "count": 0}
        rates = per_synth_rate[indices]
        return {"rate": round(float(np.mean(rates)), 1), "count": len(indices)}

    # Same bucketing as v1
    age_18_29: list[int] = []
    age_30_49: list[int] = []
    age_50_plus: list[int] = []
    for i, synth in enumerate(synths):
        age = synth.get("data", {}).get("demografia", {}).get("idade")
        if age is None:
            age_30_49.append(i)
        elif age < 30:
            age_18_29.append(i)
        elif age < 50:
            age_30_49.append(i)
        else:
            age_50_plus.append(i)

    inc_low: list[int] = []
    inc_mid: list[int] = []
    inc_high: list[int] = []
    for i, synth in enumerate(synths):
        income = synth.get("data", {}).get("demografia", {}).get("renda_mensal")
        if income is None:
            inc_mid.append(i)
        elif income < 3000:
            inc_low.append(i)
        elif income <= 10000:
            inc_mid.append(i)
        else:
            inc_high.append(i)

    edu_low: list[int] = []
    edu_mid: list[int] = []
    edu_high: list[int] = []
    low_edu_keys = {"sem escolaridade", "fundamental incompleto", "fundamental completo"}
    mid_edu_keys = {"médio incompleto", "médio completo"}
    for i, synth in enumerate(synths):
        raw = synth.get("data", {}).get("demografia", {}).get("escolaridade") or ""
        edu = raw.lower().strip()
        if edu in low_edu_keys:
            edu_low.append(i)
        elif edu in mid_edu_keys:
            edu_mid.append(i)
        else:
            edu_high.append(i)

    return {
        "age": {
            "18-29": _bucket_stats(age_18_29),
            "30-49": _bucket_stats(age_30_49),
            "50+": _bucket_stats(age_50_plus),
        },
        "income": {
            "baixa": _bucket_stats(inc_low),
            "media": _bucket_stats(inc_mid),
            "alta": _bucket_stats(inc_high),
        },
        "education": {
            "baixa": _bucket_stats(edu_low),
            "media": _bucket_stats(edu_mid),
            "alta": _bucket_stats(edu_high),
        },
    }


def run_sensitivity_v2(
    outcome_edges: list[dict],
    node_values: dict[str, np.ndarray],
    node_selections: dict[str, int],
    node_metadata: dict[str, dict],
    intercept_mu: float,
    intercept_sigma: float,
    seed: int | None = None,
) -> list[dict]:
    """Run sensitivity analysis on node-level premissas.

    For each source node with options: varies between option 0 and option 4.
    Measures impact on outcome.

    Returns list sorted by impact descending.
    """
    results = []

    # Find unique source nodes that have premissa options
    calibratable_sources = set()
    for edge in outcome_edges:
        src = edge.get("from_node", edge.get("from", ""))
        src_meta = node_metadata.get(src, {})
        if src_meta.get("options"):
            calibratable_sources.add(src)

    for idx, node_name in enumerate(sorted(calibratable_sources)):
        node_meta = node_metadata.get(node_name, {})

        # Low: set this node to option 0 (strongest)
        sel_low = {**node_selections, node_name: 0}
        res_low = run_monte_carlo_v2(
            outcome_edges, node_values, sel_low, node_metadata,
            intercept_mu, intercept_sigma,
            n_iterations=SENSITIVITY_ITERATIONS,
            seed=seed,
        )

        # High: set this node to option 4 (weakest)
        sel_high = {**node_selections, node_name: 4}
        res_high = run_monte_carlo_v2(
            outcome_edges, node_values, sel_high, node_metadata,
            intercept_mu, intercept_sigma,
            n_iterations=SENSITIVITY_ITERATIONS,
            seed=(seed + idx + 1) if seed is not None else None,
        )

        mean_low = res_low["stats"]["mean"]
        mean_high = res_high["stats"]["mean"]
        impact = round(abs(mean_low - mean_high), 1)

        results.append({
            "edge_id": node_name,  # Use node_name as identifier
            "header": node_meta.get("header", node_name),
            "impact": impact,
            "mean_low": mean_low,
            "mean_high": mean_high,
        })

    results.sort(key=lambda x: x["impact"], reverse=True)
    return results


def run_monte_carlo_v2_per_synth(
    outcome_edges: list[dict],
    node_values: dict[str, np.ndarray],
    node_selections: dict[str, int],
    node_metadata: dict[str, dict],
    intercept_mu: float,
    intercept_sigma: float,
    n_repetitions: int = 10,
    seed: int | None = None,
) -> dict:
    """Monte Carlo simulation returning per-synth adoption probabilities.

    Runs n_repetitions MC draws, each sampling intercept + coefficients once,
    computing per-synth sigmoid probabilities, then averaging over repetitions.

    Args:
        outcome_edges: Edges pointing to the outcome node.
        node_values: Pre-computed node values from build_node_values().
        node_selections: Map of node_name -> selected option index.
        node_metadata: Per-node metadata with options.
        intercept_mu: Model intercept mean.
        intercept_sigma: Model intercept std dev.
        n_repetitions: Number of MC repetitions to average (default 10).
        seed: Random seed.

    Returns:
        Dict with keys:
            per_synth_probs: np.ndarray of shape (n_synths,) — mean adoption prob [0,1]
            distribution: list[float] — one aggregate adoption % per repetition
            stats: dict — mean, median, std, p10, p90
    """
    rng = np.random.default_rng(seed)
    n_edges = len(outcome_edges)

    if n_edges == 0:
        n_synths = 0
        for vals in node_values.values():
            n_synths = len(vals)
            break
        return {
            "per_synth_probs": np.full(max(n_synths, 1), 0.5),
            "distribution": [50.0] * n_repetitions,
            "stats": {"mean": 50.0, "median": 50.0, "std": 0.0, "p10": 50.0, "p90": 50.0},
        }

    # Get n_synths from first available node value
    n_synths = 0
    for vals in node_values.values():
        n_synths = len(vals)
        break

    if n_synths == 0:
        return {
            "per_synth_probs": np.array([]),
            "distribution": [50.0] * n_repetitions,
            "stats": {"mean": 50.0, "median": 50.0, "std": 0.0, "p10": 50.0, "p90": 50.0},
        }

    per_edge_scale = BUDGET / max(math.sqrt(n_edges), 1.0)

    # Compute outcome weight multipliers
    weight_multipliers = _compute_outcome_weight_multipliers(
        outcome_edges, node_metadata, node_selections,
    )

    # Build input matrix
    input_matrix = np.full((n_synths, n_edges), 0.5)
    beta_mus = np.zeros(n_edges)
    beta_sigmas = np.zeros(n_edges)

    for i, edge in enumerate(outcome_edges):
        src = edge.get("from_node", edge.get("from", ""))
        input_matrix[:, i] = node_values.get(src, np.full(n_synths, 0.5))
        d = edge.get("direction", 1)

        src_meta = node_metadata.get(src, {})
        src_options = src_meta.get("options", [])

        if src_options:
            selected = node_selections.get(src, src_meta.get("default_option", 2))
            opt = src_options[selected] if selected < len(src_options) else src_options[2]
            beta_mus[i] = opt["mu"] * per_edge_scale * d * weight_multipliers[i]
            beta_sigmas[i] = opt["sigma"] * per_edge_scale * weight_multipliers[i]
        else:
            weight = edge.get("weight", 0.5)
            beta_mus[i] = weight * per_edge_scale * d * weight_multipliers[i]
            beta_sigmas[i] = 0.1 * per_edge_scale * weight_multipliers[i]

    # Accumulate per-synth probabilities over repetitions
    prob_accumulator = np.zeros(n_synths)
    distribution = np.zeros(n_repetitions)

    for r in range(n_repetitions):
        intercept = rng.normal(intercept_mu, intercept_sigma)
        coefs = rng.normal(beta_mus, beta_sigmas)
        logits = intercept + input_matrix @ coefs
        probs = _sigmoid(logits)
        prob_accumulator += probs
        distribution[r] = float(np.mean(probs)) * 100  # aggregate adoption %

    per_synth_probs = prob_accumulator / n_repetitions  # mean prob per synth

    stats = {
        "mean": round(float(np.mean(distribution)), 1),
        "median": round(float(np.median(distribution)), 1),
        "std": round(float(np.std(distribution)), 1),
        "p10": round(float(np.percentile(distribution, 10)), 1),
        "p90": round(float(np.percentile(distribution, 90)), 1),
    }

    return {
        "per_synth_probs": per_synth_probs,
        "distribution": distribution.tolist(),
        "stats": stats,
    }


def extract_demographics(synth: dict) -> dict:
    """Extract demographics from a synth dict for dag_values storage.

    Returns a compact dict with age, income, education, family composition.
    """
    demo = synth.get("data", {}).get("demografia", {})
    result: dict[str, Any] = {}
    if "idade" in demo:
        result["idade"] = demo["idade"]
    if "renda_mensal" in demo:
        result["renda_mensal"] = demo["renda_mensal"]
    if "escolaridade" in demo:
        result["escolaridade"] = demo["escolaridade"]
    if "composicao_familiar" in demo:
        result["composicao_familiar"] = demo["composicao_familiar"]
    return result


def compute_raw_interpretations(
    stats: dict,
    segments: dict,
    sensitivity: list[dict],
) -> dict[str, str]:
    """Generate raw_text strings for each section (no LLM).

    Per Apêndice D:
    - Distribution: confidence interval + uncertainty classification
    - Segments: best/worst segment, ratio, most discriminating factor
    - Sensitivity: top premisses by impact
    """
    # Distribution
    std = stats["std"]
    if std > 3.0:
        uncertainty = "alta"
    elif std > 1.5:
        uncertainty = "moderada"
    else:
        uncertainty = "baixa"

    dist_text = (
        f"Com 80% de confiança, a taxa de adoção fica entre {stats['p10']}% e {stats['p90']}%. "
        f"A estimativa central é {stats['mean']}%. "
        f"Incerteza {uncertainty} (desvio padrão: {std}pp)."
    )

    # Segments
    all_segs = []
    for dim_name, dim_data in segments.items():
        for seg_name, seg_data in dim_data.items():
            if seg_data["count"] > 0:
                all_segs.append((dim_name, seg_name, seg_data["rate"], seg_data["count"]))

    if all_segs:
        best = max(all_segs, key=lambda x: x[2])
        worst = min(all_segs, key=lambda x: x[2])
        ratio = round(best[2] / max(worst[2], 0.1), 1)

        # Most discriminating factor: max range within a dimension
        dim_ranges = {}
        for dim_name in ("age", "income", "education"):
            rates = [v["rate"] for v in segments[dim_name].values() if v["count"] > 0]
            if len(rates) >= 2:
                dim_ranges[dim_name] = max(rates) - min(rates)
        most_discrim = max(dim_ranges, key=dim_ranges.get) if dim_ranges else "age"

        dim_labels = {"age": "idade", "income": "renda", "education": "escolaridade"}

        # Spread significance per dimension
        def _spread_significance(spread_pp: float) -> str:
            if spread_pp < 5.0:
                return "diferença não relevante para decisão de segmentação"
            elif spread_pp <= 15.0:
                return "diferença moderada"
            else:
                return "diferença relevante — considere rollout segmentado"

        spread_parts = []
        for dim_name in ("age", "income", "education"):
            rates = [v["rate"] for v in segments[dim_name].values() if v["count"] > 0]
            if len(rates) >= 2:
                spread_pp = round(max(rates) - min(rates), 1)
                sig = _spread_significance(spread_pp)
                spread_parts.append(
                    f"{dim_labels[dim_name]}: Δ{spread_pp}pp ({sig})"
                )

        seg_text = (
            f"Melhor segmento: {best[1]} ({best[0]}) com {best[2]}%. "
            f"Pior: {worst[1]} ({worst[0]}) com {worst[2]}%. Ratio: {ratio}x. "
            f"Fator mais discriminante: {dim_labels.get(most_discrim, most_discrim)}. "
            + " | ".join(spread_parts)
        )
    else:
        seg_text = "Sem dados suficientes para análise de segmentos."

    # Sensitivity
    if sensitivity:
        top = sensitivity[0]
        sens_text = f"Premissa mais impactante: {top['header']} ({top['impact']}pp)."
        if len(sensitivity) > 1:
            second = sensitivity[1]
            if top["impact"] > 0 and second["impact"] / top["impact"] > 0.6:
                sens_text += f" Segunda: {second['header']} ({second['impact']}pp)."

        low_impact = [
            s for s in sensitivity
            if top["impact"] > 0 and s["impact"] / top["impact"] < 0.2
        ]
        if low_impact:
            sens_text += f" {len(low_impact)} premissa(s) de baixo impacto relativo."
    else:
        sens_text = "Sem dados de sensibilidade."

    return {
        "distribution": dist_text,
        "segments": seg_text,
        "sensitivity": sens_text,
    }
