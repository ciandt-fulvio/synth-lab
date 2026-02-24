"""
Trace simulation calculation step by step for a specific synth and simulation run.

Usage:
    uv run scripts/trace_simulation.py sr_bed5cead 0wrccz
"""
import json
import math
import sys

import numpy as np
import sqlalchemy as sa
from dotenv import load_dotenv

# Load env from docker/.env.dev
load_dotenv("docker/.env.dev")

import os

DATABASE_URL = os.environ.get("DATABASE_URL", "").replace(
    "postgres-dev", "localhost"
)
if not DATABASE_URL:
    DATABASE_URL = "postgresql://synthlab:synthlab@localhost:5432/synthlab"


def get_engine():
    return sa.create_engine(DATABASE_URL)


def query_one(engine, sql, **params):
    with engine.connect() as conn:
        result = conn.execute(sa.text(sql), params)
        row = result.fetchone()
        if row is None:
            return None
        return dict(row._mapping)


def query_all(engine, sql, **params):
    with engine.connect() as conn:
        result = conn.execute(sa.text(sql), params)
        return [dict(r._mapping) for r in result.fetchall()]


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))


def main():
    run_id = sys.argv[1] if len(sys.argv) > 1 else "sr_bed5cead"
    synth_id = sys.argv[2] if len(sys.argv) > 2 else "0wrccz"

    engine = get_engine()

    print("=" * 80)
    print(f"TRACE: Simulation Run = {run_id}, Synth = {synth_id}")
    print("=" * 80)

    # 1. Load simulation run
    run = query_one(engine, "SELECT * FROM simulation_runs WHERE id = :id", id=run_id)
    if not run:
        print(f"ERROR: Simulation run {run_id} not found")
        sys.exit(1)

    print(f"\n--- SIMULATION RUN ---")
    print(f"  n_iterations (repetitions): {run['n_iterations']}")
    print(f"  n_synths: {run['n_synths']}")
    print(f"  batch_id: {run['batch_id']}")

    selections = run["selections"]
    print(f"  selections: {json.dumps(selections, indent=4)}")

    product_values_str = run["product_values"]
    print(f"  product_values (stored strings): {json.dumps(product_values_str, indent=4)}")

    per_synth_outcomes = run["per_synth_outcomes"]
    stored_result = per_synth_outcomes.get(synth_id)
    print(f"\n  >>> STORED RESULT for {synth_id}: {stored_result}")

    # 2. Load causal model
    cm = query_one(
        engine, "SELECT * FROM causal_models WHERE id = :id", id=run["causal_model_id"]
    )
    print(f"\n--- CAUSAL MODEL ---")
    print(f"  id: {cm['id']}")
    print(f"  intercept_mu: {cm['intercept_mu']}")
    print(f"  intercept_sigma: {cm['intercept_sigma']}")
    print(f"  nodes: {cm['nodes']}")

    node_metadata = cm["node_metadata"]
    print(f"\n--- NODE METADATA ---")
    for name, meta in node_metadata.items():
        ntype = meta.get("node_type", "?")
        print(f"  [{ntype.upper():12s}] {name}")
        if ntype == "sensitivity":
            print(f"      sensitivity_key: {meta.get('sensitivity_key')}")
            if meta.get("custom_config"):
                cc = meta["custom_config"]
                print(f"      custom_config: base={cc.get('base')}, rules={len(cc.get('rules', []))}")
        elif ntype == "product":
            print(f"      product_calibration: {meta.get('product_calibration')}")
        elif ntype == "interaction":
            options = meta.get("options", [])
            print(f"      header: {meta.get('header')}")
            for i, opt in enumerate(options):
                marker = " <-- SELECTED" if selections.get(name) == i else ""
                print(f"      option[{i}]: mu={opt['mu']:.2f}, sigma={opt['sigma']:.2f}, text={opt['text'][:60]}{marker}")
            sel_idx = selections.get(name)
            if sel_idx is not None:
                print(f"      selected_option: {sel_idx}")
        elif ntype == "outcome":
            options = meta.get("options", [])
            print(f"      header: {meta.get('header')}")
            for i, opt in enumerate(options):
                marker = " <-- SELECTED" if selections.get(name) == i else ""
                print(f"      option[{i}]: mu={opt.get('mu', 'N/A')}, text={opt.get('text', 'N/A')[:60]}{marker}")

    # 3. Load edges
    edges = query_all(
        engine,
        "SELECT * FROM causal_edges WHERE causal_model_id = :cm_id ORDER BY id",
        cm_id=cm["id"],
    )
    print(f"\n--- EDGES ({len(edges)}) ---")
    for e in edges:
        print(
            f"  {e['id']:4s}: {e['from_node']:30s} -> {e['to_node']:30s}  "
            f"dir={e['direction']:+d}  weight={e['weight']}"
        )

    # 4. Load synth
    synth = query_one(engine, "SELECT * FROM synths WHERE id = :id", id=synth_id)
    synth_data = synth["data"]
    demo = synth_data.get("demografia", {})
    sens = synth_data.get("sensitivities", {})

    print(f"\n--- SYNTH: {synth['nome']} ({synth_id}) ---")
    print(f"  idade: {demo.get('idade')}")
    print(f"  renda_mensal: {demo.get('renda_mensal')}")
    print(f"  escolaridade: {demo.get('escolaridade')}")
    print(f"  composicao_familiar: {demo.get('composicao_familiar')}")
    print(f"  stored sensitivities:")
    for k, v in sens.items():
        print(f"    {k}: {v}")

    # ============================================================
    # STEP-BY-STEP CALCULATION
    # ============================================================

    print("\n" + "=" * 80)
    print("STEP-BY-STEP CALCULATION")
    print("=" * 80)

    # --- STEP 1: Map product calibration strings to numeric ---
    PRODUCT_CALIBRATION_VALUES = {"low": 0.2, "medium": 0.5, "high": 0.8}
    numeric_product_values = {}
    for name, meta in node_metadata.items():
        if meta.get("node_type") == "product":
            cal_str = product_values_str.get(name, "medium")
            numeric_product_values[name] = PRODUCT_CALIBRATION_VALUES.get(cal_str, 0.5)

    print(f"\n--- STEP 1: Product calibration → numeric ---")
    for name, val in numeric_product_values.items():
        print(f"  {name}: '{product_values_str.get(name)}' → {val}")

    # --- STEP 2: Compute sensitivity node values ---
    # NOTE: The simulation recomputes sensitivities via compute_sensitivity_for_config
    # with NO seed, so they are random each time. We CANNOT reproduce exactly.
    # But we can show the algorithm.

    print(f"\n--- STEP 2: Sensitivity node values (recomputed, non-deterministic) ---")
    print(f"  WARNING: The simulation recomputes sensitivities with seed=None,")
    print(f"  so the exact values used are NOT the stored synth sensitivities.")
    print(f"  We'll show the config and what the Beta distribution parameters would be.")

    # Load YAML sensitivity rules
    from synth_lab.services.sensitivity_deriver import (
        compute_sensitivity_for_config,
        evaluate_condition,
        load_sensitivity_rules,
    )

    yaml_data = load_sensitivity_rules()
    yaml_sensitivities = yaml_data.get("sensitivities", {})
    sensitivity_configs = dict(yaml_sensitivities)
    for meta in node_metadata.values():
        if meta.get("node_type") == "sensitivity" and meta.get("custom_config"):
            sens_key = meta.get("sensitivity_key", "")
            sensitivity_configs[sens_key] = meta["custom_config"]

    sensitivity_node_values_for_synth = {}
    for name, meta in node_metadata.items():
        if meta.get("node_type") != "sensitivity":
            continue
        sens_key = meta.get("sensitivity_key", "")
        config = sensitivity_configs.get(sens_key, meta.get("custom_config", {}))
        if not config:
            config = {"base": 0.5, "rules": []}

        # Show the rule evaluation
        base = float(config.get("base", 0.5))
        mean = base
        print(f"\n  Node: {name} (sensitivity_key={sens_key})")
        print(f"    config base: {base}")
        for rule in config.get("rules", []):
            condition = rule.get("condition", {})
            matches = evaluate_condition(condition, synth_data)
            adj = rule.get("adjustment", 0.0)
            reason = rule.get("reason", "")
            if matches:
                mean += adj
                print(f"    MATCH: {reason} → adjustment={adj:+.2f} → new mean={mean:.4f}")
            else:
                print(f"    skip:  {reason} (condition not met)")
        mean_clamped = max(0.01, min(0.99, mean))
        strength = int(config.get("strength", 15))
        alpha = mean_clamped * strength
        beta_param = (1.0 - mean_clamped) * strength
        print(f"    final mean (clamped): {mean_clamped:.4f}")
        print(f"    Beta(alpha={alpha:.2f}, beta={beta_param:.2f}) with strength={strength}")
        print(f"    stored synth sensitivity ({sens_key}): {sens.get(sens_key, 'N/A')}")

        # Sample a value (this won't match the simulation's value but shows the distribution)
        # For the trace, let's use the stored sensitivity as a reasonable proxy
        stored_val = sens.get(sens_key)
        if stored_val is not None:
            sensitivity_node_values_for_synth[name] = float(stored_val)
            print(f"    >>> Using stored value as proxy: {stored_val}")
        else:
            # sample one
            rng = np.random.default_rng(42)
            sampled = round(float(rng.beta(alpha, beta_param)), 4)
            sensitivity_node_values_for_synth[name] = sampled
            print(f"    >>> Sampled value (seed=42): {sampled}")

    # --- STEP 3: Topological sort and compute interaction nodes ---
    print(f"\n--- STEP 3: Topological sort ---")

    # Build edges dict for child_parents
    child_parents = {}
    for e in edges:
        src = e["from_node"]
        dst = e["to_node"]
        weight = e["weight"]
        direction = e["direction"]
        child_parents.setdefault(dst, []).append((src, weight, direction))

    # Build topological order
    from collections import deque

    node_names = list(node_metadata.keys())
    in_degree = {name: 0 for name in node_names}
    adjacency = {name: [] for name in node_names}
    for e in edges:
        src, dst = e["from_node"], e["to_node"]
        if src in adjacency and dst in in_degree:
            adjacency[src].append(dst)
            in_degree[dst] += 1

    queue = deque(name for name in node_names if in_degree[name] == 0)
    sorted_names = []
    while queue:
        node = queue.popleft()
        sorted_names.append(node)
        for neighbor in adjacency.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    print(f"  Topological order:")
    for i, name in enumerate(sorted_names):
        ntype = node_metadata.get(name, {}).get("node_type", "?")
        print(f"    {i}: {name} ({ntype})")

    # --- STEP 4: Compute all node values for this synth ---
    print(f"\n--- STEP 4: Compute node values for synth {synth_id} ---")

    node_values_for_synth = {}

    for name in sorted_names:
        meta = node_metadata.get(name, {})
        ntype = meta.get("node_type", "interaction")

        if ntype == "sensitivity":
            val = sensitivity_node_values_for_synth.get(name, 0.5)
            node_values_for_synth[name] = val
            print(f"  {name} (sensitivity): {val:.4f}")

        elif ntype == "product":
            val = numeric_product_values.get(name, 0.5)
            node_values_for_synth[name] = val
            print(f"  {name} (product): {val}")

        elif ntype == "interaction":
            parents = child_parents.get(name, [])
            if parents:
                weighted_sum = 0.0
                total_weight = 0.0
                print(f"\n  {name} (interaction): computing from parents...")
                for parent_name, weight, direction in parents:
                    parent_val = node_values_for_synth.get(parent_name, 0.5)
                    effective_val = parent_val if direction == 1 else (1.0 - parent_val)
                    contribution = effective_val * weight
                    weighted_sum += contribution
                    total_weight += abs(weight)
                    dir_label = "direct" if direction == 1 else "INVERSE"
                    print(
                        f"    parent={parent_name:30s} val={parent_val:.4f} "
                        f"dir={direction:+d}({dir_label}) eff_val={effective_val:.4f} "
                        f"weight={weight:.2f} contribution={contribution:.4f}"
                    )
                if total_weight > 0:
                    interaction_val = weighted_sum / total_weight
                else:
                    interaction_val = 0.5
                interaction_val = max(0.0, min(1.0, interaction_val))
                node_values_for_synth[name] = interaction_val
                print(
                    f"    weighted_sum={weighted_sum:.4f} / total_weight={total_weight:.2f} "
                    f"= {interaction_val:.4f}"
                )
            else:
                node_values_for_synth[name] = 0.5
                print(f"  {name} (interaction, no parents): 0.5")

        elif ntype == "outcome":
            print(f"  {name} (outcome): computed by Monte Carlo (below)")

    # --- STEP 5: Identify outcome edges and source nodes ---
    print(f"\n--- STEP 5: Outcome edges ---")

    outcome_node = None
    for name, meta in node_metadata.items():
        if meta.get("node_type") == "outcome":
            outcome_node = name
            break

    outcome_edges = [e for e in edges if e["to_node"] == outcome_node]
    print(f"  Outcome node: {outcome_node}")
    print(f"  Outcome edges: {len(outcome_edges)}")
    for e in outcome_edges:
        print(f"    {e['id']}: {e['from_node']} → {outcome_node}  dir={e['direction']:+d}  weight={e['weight']}")

    n_edges = len(outcome_edges)
    per_edge_scale = 3.0 / max(math.sqrt(n_edges), 1.0)
    print(f"\n  BUDGET = 3.0")
    print(f"  n_outcome_edges = {n_edges}")
    print(f"  per_edge_scale = 3.0 / sqrt({n_edges}) = {per_edge_scale:.4f}")

    # --- STEP 6: Outcome weight multipliers (2x for "most important") ---
    print(f"\n--- STEP 6: Outcome weight multipliers ---")

    outcome_meta = node_metadata.get(outcome_node, {})
    outcome_options = outcome_meta.get("options", [])
    outcome_sel = selections.get(outcome_node, outcome_meta.get("default_option", 0))
    print(f"  Outcome selected_option index: {outcome_sel}")

    if outcome_options and outcome_sel < len(outcome_options):
        selected_interaction = outcome_options[outcome_sel].get("text", "")
        print(f"  'Most important' interaction: {selected_interaction}")
    else:
        selected_interaction = ""

    multipliers = np.ones(n_edges)
    n = n_edges
    norm_factor = n / (n + 1) if n > 0 else 1.0
    print(f"  norm_factor = {n} / ({n} + 1) = {norm_factor:.4f}")

    edge_sources = [e["from_node"] for e in outcome_edges]
    for i, src in enumerate(edge_sources):
        if src == selected_interaction:
            multipliers[i] = 2.0 * norm_factor
        else:
            multipliers[i] = 1.0 * norm_factor

    print(f"  Weight multipliers:")
    for i, (src, m) in enumerate(zip(edge_sources, multipliers)):
        marker = " *** MOST IMPORTANT (2x)" if src == selected_interaction else ""
        print(f"    edge[{i}] src={src:30s} multiplier={m:.4f}{marker}")

    # --- STEP 7: Build beta_mus and beta_sigmas for outcome edges ---
    print(f"\n--- STEP 7: Beta parameters per outcome edge ---")

    input_values = np.zeros(n_edges)
    beta_mus = np.zeros(n_edges)
    beta_sigmas = np.zeros(n_edges)

    for i, edge in enumerate(outcome_edges):
        src = edge["from_node"]
        src_val = node_values_for_synth.get(src, 0.5)
        input_values[i] = src_val
        d = edge["direction"]

        src_meta = node_metadata.get(src, {})
        src_options = src_meta.get("options", [])

        if src_options:
            selected = selections.get(src, src_meta.get("default_option", 2))
            opt = src_options[selected] if selected < len(src_options) else src_options[2]
            mu = opt["mu"]
            sigma = opt["sigma"]
            beta_mus[i] = mu * per_edge_scale * d * multipliers[i]
            beta_sigmas[i] = sigma * per_edge_scale * multipliers[i]
            print(
                f"  edge[{i}] src={src:30s}  node_val={src_val:.4f}  "
                f"selected_opt={selected}  mu_raw={mu:.2f}  sigma_raw={sigma:.2f}  "
                f"dir={d:+d}  mult={multipliers[i]:.4f}"
            )
            print(
                f"         beta_mu = {mu:.2f} * {per_edge_scale:.4f} * {d:+d} * {multipliers[i]:.4f} = {beta_mus[i]:.4f}"
            )
            print(
                f"         beta_sigma = {sigma:.2f} * {per_edge_scale:.4f} * {multipliers[i]:.4f} = {beta_sigmas[i]:.4f}"
            )
        else:
            weight = edge["weight"]
            beta_mus[i] = weight * per_edge_scale * d * multipliers[i]
            beta_sigmas[i] = 0.1 * per_edge_scale * multipliers[i]
            print(
                f"  edge[{i}] src={src:30s}  node_val={src_val:.4f}  "
                f"NO options, using weight={weight}  dir={d:+d}  mult={multipliers[i]:.4f}"
            )
            print(f"         beta_mu={beta_mus[i]:.4f}  beta_sigma={beta_sigmas[i]:.4f}")

    # --- STEP 8: Monte Carlo simulation (single synth) ---
    print(f"\n--- STEP 8: Monte Carlo simulation ---")
    print(f"  intercept_mu = {cm['intercept_mu']}")
    print(f"  intercept_sigma = {cm['intercept_sigma']}")
    print(f"  n_repetitions = {run['n_iterations']}")
    print(f"\n  input_values (this synth's interaction node values):")
    for i, e in enumerate(outcome_edges):
        print(f"    [{i}] {e['from_node']:30s} = {input_values[i]:.4f}")
    print(f"\n  beta_mus:    {[round(x, 4) for x in beta_mus]}")
    print(f"  beta_sigmas: {[round(x, 4) for x in beta_sigmas]}")

    # Run 10 repetitions with a fixed seed to show the mechanics
    rng = np.random.default_rng(42)
    n_reps = run["n_iterations"]
    prob_sum = 0.0
    distribution = []

    print(f"\n  Running {n_reps} repetitions (seed=42 for illustration):")
    for r in range(n_reps):
        intercept = rng.normal(cm["intercept_mu"], cm["intercept_sigma"])
        coefs = rng.normal(beta_mus, beta_sigmas)
        logit = intercept + np.dot(input_values, coefs)
        prob = float(sigmoid(np.array([logit]))[0])
        prob_sum += prob
        distribution.append(prob)
        print(
            f"    rep[{r}]: intercept={intercept:+.4f}  coefs={[round(c, 4) for c in coefs]}  "
            f"logit={logit:+.4f}  prob={prob:.4f}"
        )

    avg_prob = prob_sum / n_reps
    print(f"\n  Average prob over {n_reps} reps: {avg_prob:.4f}")
    print(f"  Rounded to 2 decimals: {round(avg_prob, 2)}")
    print(f"\n  >>> STORED RESULT: {stored_result}")
    print(f"  >>> OUR RESULT:    {round(avg_prob, 2)}")
    print(f"\n  NOTE: Our result may differ from stored because:")
    print(f"    1. Random seed was different (simulation used no seed)")
    print(f"    2. Sensitivity values were recomputed (we used stored proxy)")
    print(f"    3. But the FORMULA and DIRECTION of computation should match")

    # --- STEP 9: Sanity check — is the logit direction correct? ---
    print(f"\n{'=' * 80}")
    print("ANALYSIS: Is the logic correct?")
    print("=" * 80)

    print(f"\n1. INTERACTION NODE COMPUTATION:")
    for name in sorted_names:
        meta = node_metadata.get(name, {})
        if meta.get("node_type") != "interaction":
            continue
        parents = child_parents.get(name, [])
        val = node_values_for_synth.get(name)
        print(f"\n  {name} = {val:.4f}")
        for pname, w, d in parents:
            pval = node_values_for_synth.get(pname, 0.5)
            eff = pval if d == 1 else (1.0 - pval)
            print(f"    {pname}={pval:.4f}, dir={d:+d}, eff={eff:.4f}, weight={w}")
            if d == -1:
                print(f"      → INVERSE: higher {pname} means LOWER contribution to {name}")

    print(f"\n2. OUTCOME LOGIT DIRECTION:")
    print(f"  Formula: logit = intercept + Σ(coef_i * node_val_i)")
    print(f"  Where coef_i ~ Normal(beta_mu_i, beta_sigma_i)")
    print(f"  And beta_mu_i = option_mu * per_edge_scale * direction * weight_multiplier")
    for i, edge in enumerate(outcome_edges):
        src = edge["from_node"]
        d = edge["direction"]
        src_meta = node_metadata.get(src, {})
        selected = selections.get(src, src_meta.get("default_option", 2))
        src_options = src_meta.get("options", [])
        opt = src_options[selected] if src_options and selected < len(src_options) else {"mu": 0, "sigma": 0}
        print(
            f"\n  Edge {edge['id']}: {src} → {outcome_node}")
        print(
            f"    direction={d:+d}, option[{selected}].mu={opt['mu']:.2f}")
        print(
            f"    beta_mu={beta_mus[i]:+.4f}, meaning: "
            f"{'positive' if beta_mus[i] > 0 else 'NEGATIVE'} coefficient")
        print(
            f"    node_val={input_values[i]:.4f}")
        print(
            f"    Expected contribution to logit: "
            f"beta_mu * node_val = {beta_mus[i]:.4f} * {input_values[i]:.4f} = {beta_mus[i] * input_values[i]:.4f}")

    # Mean logit approximation
    mean_logit = cm["intercept_mu"] + np.dot(beta_mus, input_values)
    mean_prob = float(sigmoid(np.array([mean_logit]))[0])
    print(f"\n3. MEAN LOGIT APPROXIMATION (no randomness):")
    print(f"  mean_logit = intercept_mu + Σ(beta_mu_i * node_val_i)")
    print(f"  = {cm['intercept_mu']:.4f} + {np.dot(beta_mus, input_values):.4f}")
    print(f"  = {mean_logit:.4f}")
    print(f"  sigmoid({mean_logit:.4f}) = {mean_prob:.4f}")
    print(f"  This is the 'center' probability before noise from sigma terms")

    print(f"\n{'=' * 80}")
    print(f"SUMMARY")
    print(f"{'=' * 80}")
    print(f"  Synth: {synth['nome']} ({synth_id})")
    print(f"  Stored result: {stored_result}")
    print(f"  Mean logit (deterministic center): {mean_logit:.4f}")
    print(f"  Mean prob (deterministic center):  {mean_prob:.4f} ({mean_prob*100:.1f}%)")
    print(f"  MC result (our seed=42):           {round(avg_prob, 2)}")


if __name__ == "__main__":
    main()
