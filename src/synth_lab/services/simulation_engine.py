"""
Monte Carlo simulation engine for quantitative analysis.

Pure computation module: no I/O, no database, no LLM calls.
All functions operate on plain dicts/lists and NumPy arrays.

Formulas from: specs/042-quantitative-analysis/spec.md (Apêndice D)

References:
    - NumPy docs: https://numpy.org/doc/stable/reference/random/generator.html
"""

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
    per_edge_scale = BUDGET / max(n_edges, 1)

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
    per_edge_scale = BUDGET / max(n_edges, 1)

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
