"""
Exploração comparativa: Pearl (SCM) vs Rubin (Potential Outcomes)

Dois frameworks de causalidade aplicados ao motor de simulação do synth-lab.
Compara resultados com 3 perfis de usuário e 2 cenários de produto.

Cenário A: Delivery com entrega agendada — produto bom vs ruim
Cenário B: Delivery com entrega agendada — investimento em mídia baixo vs alto

Uso: python scripts/explore_pearl_vs_rubin.py
"""

import math

import numpy as np

SEED = 42
N_ITERATIONS = 5000


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))


def sigmoid_f(x: float) -> float:
    return float(sigmoid(np.float64(x)))


# =============================================================================
# 3 perfis de teste
# =============================================================================
PROFILES = {
    "Marcela (96a, fund.inc)": {
        "ageNorm": 1.0,       # (96-18)/(80-18) clamped
        "incomeNorm": 0.256,  # 5110/20000
        "eduNorm": 0.35,      # médio incompleto
        "digitalCapability": 0.118,
        "riskAversion": 0.513,
        "institutionalTrust": 0.441,
        "frictionTolerance": 0.318,
    },
    "Jovem (20a, sup.inc)": {
        "ageNorm": 0.032,     # (20-18)/(80-18)
        "incomeNorm": 0.125,  # 2500/20000
        "eduNorm": 0.60,      # superior incompleto
        "digitalCapability": 0.85,
        "riskAversion": 0.30,
        "institutionalTrust": 0.50,
        "frictionTolerance": 0.70,
    },
    "Doutora (40a, dout.)": {
        "ageNorm": 0.355,     # (40-18)/(80-18)
        "incomeNorm": 0.75,   # 15000/20000
        "eduNorm": 1.0,       # doutorado
        "digitalCapability": 0.80,
        "riskAversion": 0.25,
        "institutionalTrust": 0.70,
        "frictionTolerance": 0.65,
    },
}


# =============================================================================
# PEARL — Structural Causal Model (propagação por camadas)
# =============================================================================

def pearl_simulate(
    profile: dict,
    product_vars: dict,
    intercept_mu: float,
    rng: np.random.Generator,
    n_iter: int = N_ITERATIONS,
) -> dict:
    """
    Pearl SCM: equações estruturais com sigmoid para normalizar mediadores.

    Cada mediador é computado como sigmoid(equação_linear) → [0,1].
    Isso preserva range sem clamping agressivo.

    DAG:
        Layer 1: CapDigital = sigmoid(bias + w1*(-age) + w2*(edu))
                 AversaoRisco = sigmoid(bias + w3*(-edu))

        Layer 2: PercFacilidade = sigmoid(bias + w4*(capDig) * qualUI + w5*awareness)
                 Confianca = sigmoid(bias + w6*(income)*confEnt - w7*(risco)*confEnt + w8*awareness)

        Layer 3: logit = intercept + w9*facilidade + w10*confianca
                 P(adoção) = sigmoid(logit)
    """
    qualUI = product_vars["qualidadeUI"]
    confEnt = product_vars["confiabilidade"]
    awareness = product_vars.get("awareness", 0.5)  # default neutro

    results = np.zeros(n_iter)
    mediator_sums = {"cap_digital": 0.0, "aversao_risco": 0.0,
                     "perc_facilidade": 0.0, "confianca": 0.0}

    for i in range(n_iter):
        noise = rng.normal(0, 0.3, size=4)

        # Layer 1: mediadores demográficos
        # sigmoid maps ~[-3,3] → [0.05, 0.95], giving good spread
        cap_digital = sigmoid_f(
            -2.0 * profile["ageNorm"]      # idade alta → menos digital
            + 2.5 * profile["eduNorm"]      # educação alta → mais digital
            - 0.5                           # bias (leve tendência baixa)
            + noise[0]
        )

        aversao_risco = sigmoid_f(
            -1.5 * profile["eduNorm"]       # educação alta → menos aversão
            + 0.3                           # bias (maioria tem alguma aversão)
            + noise[1]
        )

        # Layer 2: mediadores com interação produto × usuário
        perc_facilidade = sigmoid_f(
            3.0 * cap_digital * qualUI      # digital × qualidade UI
            + 1.5 * awareness               # mídia aumenta percepção
            - 2.0                           # bias negativo (facilidade precisa ser conquistada)
            + noise[2]
        )

        confianca = sigmoid_f(
            2.0 * profile["incomeNorm"] * confEnt  # renda × confiabilidade
            - 2.5 * aversao_risco * confEnt         # risco × confiabilidade (penaliza)
            + 1.5 * awareness                        # awareness aumenta confiança
            - 1.0                                    # bias
            + noise[3]
        )

        # Layer 3: outcome
        intercept = rng.normal(intercept_mu, 0.3)
        logit = (
            intercept
            + 2.5 * perc_facilidade    # facilidade pesa muito
            + 2.0 * confianca          # confiança pesa
        )
        prob = sigmoid_f(logit)
        results[i] = 1.0 if rng.random() < prob else 0.0

        mediator_sums["cap_digital"] += cap_digital
        mediator_sums["aversao_risco"] += aversao_risco
        mediator_sums["perc_facilidade"] += perc_facilidade
        mediator_sums["confianca"] += confianca

    adoption_rate = results.mean() * 100
    mediators = {k: round(v / n_iter, 3) for k, v in mediator_sums.items()}

    return {"adoption_rate": round(adoption_rate, 1), "mediators": mediators}


# =============================================================================
# RUBIN — Potential Outcomes (motor flat, produto = tratamento)
# =============================================================================

BUDGET = 3.0

BASE_EDGES = [
    {"userVar": "ageNorm", "mu": 0.65, "sigma": 0.25, "direction": -1,
     "label": "Idade → Cap.Digital"},
    {"userVar": "eduNorm", "mu": 0.80, "sigma": 0.15, "direction": 1,
     "label": "Edu → Cap.Digital"},
    {"userVar": "eduNorm", "mu": 0.30, "sigma": 0.25, "direction": -1,
     "label": "Edu → Aversão Risco"},
    {"userVar": "digitalCapability", "mu": 0.80, "sigma": 0.15, "direction": 1,
     "label": "Cap.Digital → Facilidade"},
    {"userVar": "incomeNorm", "mu": 0.65, "sigma": 0.25, "direction": 1,
     "label": "Renda → Confiança"},
    {"userVar": "riskAversion", "mu": 0.65, "sigma": 0.25, "direction": -1,
     "label": "Risco → Confiança"},
    {"userVar": "frictionTolerance", "mu": 0.80, "sigma": 0.15, "direction": 1,
     "label": "Facilidade → Adoção"},
    {"userVar": "institutionalTrust", "mu": 0.80, "sigma": 0.15, "direction": 1,
     "label": "Confiança → Adoção"},
]


def make_rubin_treatment(label: str, intercept_mu: float, edge_modifiers: dict) -> dict:
    edges = []
    for e in BASE_EDGES:
        edge = dict(e)
        if e["label"] in edge_modifiers:
            mod = edge_modifiers[e["label"]]
            if "mu_mult" in mod:
                edge["mu"] = e["mu"] * mod["mu_mult"]
        edges.append(edge)
    return {
        "label": label,
        "intercept_mu": intercept_mu,
        "intercept_sigma": 0.4,
        "edges": edges,
    }


def rubin_simulate(
    profile: dict,
    treatment_params: dict,
    rng: np.random.Generator,
    n_iter: int = N_ITERATIONS,
) -> dict:
    intercept_mu = treatment_params["intercept_mu"]
    intercept_sigma = treatment_params["intercept_sigma"]
    edges = treatment_params["edges"]
    n_edges = len(edges)
    scale = BUDGET / max(math.sqrt(n_edges), 1.0)

    beta_mus = np.array([e["mu"] * scale * e["direction"] for e in edges])
    beta_sigmas = np.array([e["sigma"] * scale for e in edges])
    user_vars = np.array([profile[e["userVar"]] for e in edges])

    results = np.zeros(n_iter)
    for i in range(n_iter):
        intercept = rng.normal(intercept_mu, intercept_sigma)
        coefs = rng.normal(beta_mus, beta_sigmas)
        logit = intercept + np.dot(coefs, user_vars)
        prob = float(sigmoid(logit))
        results[i] = 1.0 if rng.random() < prob else 0.0

    return {"adoption_rate": round(results.mean() * 100, 1)}


# =============================================================================
# Cenários
# =============================================================================

SCENARIO_A = {
    "name": "Cenário A: Qualidade do Produto (bom vs ruim)",
    "description": "Delivery agendada — variando qualidade da UI e confiabilidade da entrega",
    "pearl_treatments": {
        "Produto BOM": {"qualidadeUI": 0.7, "confiabilidade": 0.6, "awareness": 0.5},
        "Produto RUIM": {"qualidadeUI": 0.3, "confiabilidade": 0.3, "awareness": 0.5},
    },
    "rubin_treatments": {
        "Produto BOM": make_rubin_treatment(
            "Produto BOM",
            intercept_mu=-0.1,
            edge_modifiers={
                # Produto bom amplifica edges de alta variância entre perfis
                "Cap.Digital → Facilidade": {"mu_mult": 1.30},  # digital cap varia muito
                "Facilidade → Adoção": {"mu_mult": 1.20},       # friction tol varia
                "Confiança → Adoção": {"mu_mult": 1.10},
            },
        ),
        "Produto RUIM": make_rubin_treatment(
            "Produto RUIM",
            intercept_mu=-0.3,  # gap menor (-0.2 vs -0.5 antes)
            edge_modifiers={
                # Produto ruim atenua edges de alta variância
                "Cap.Digital → Facilidade": {"mu_mult": 0.50},   # grande atenuação
                "Facilidade → Adoção": {"mu_mult": 0.65},
                "Confiança → Adoção": {"mu_mult": 0.85},
            },
        ),
    },
}

SCENARIO_B = {
    "name": "Cenário B: Investimento em Mídia (baixo vs alto)",
    "description": "Delivery agendada — variando awareness e alcance de marketing",
    "pearl_treatments": {
        "Mídia ALTA": {"qualidadeUI": 0.7, "confiabilidade": 0.6, "awareness": 0.8},
        "Mídia BAIXA": {"qualidadeUI": 0.7, "confiabilidade": 0.6, "awareness": 0.2},
    },
    "rubin_treatments": {
        "Mídia ALTA": make_rubin_treatment(
            "Mídia ALTA",
            intercept_mu=0.1,   # awareness universal (menor gap)
            edge_modifiers={
                "Risco → Confiança": {"mu_mult": 0.75},   # mídia reduz medo
                "Confiança → Adoção": {"mu_mult": 1.20},
                "Cap.Digital → Facilidade": {"mu_mult": 0.85},  # menos dependência digital
            },
        ),
        "Mídia BAIXA": make_rubin_treatment(
            "Mídia BAIXA",
            intercept_mu=-0.3,
            edge_modifiers={
                "Cap.Digital → Facilidade": {"mu_mult": 1.30},  # só digital-savvy acha
                "Risco → Confiança": {"mu_mult": 1.25},         # mais desconfiança
                "Confiança → Adoção": {"mu_mult": 0.80},
            },
        ),
    },
}


# =============================================================================
# Runner
# =============================================================================

def run_scenario(scenario: dict) -> None:
    print(f"\n{'='*80}")
    print(f"  {scenario['name']}")
    print(f"  {scenario['description']}")
    print(f"{'='*80}")

    # ---- PEARL ----
    print(f"\n{'─'*40}")
    print("  PEARL (SCM — propagação por camadas)")
    print(f"{'─'*40}")

    pearl_results = {}
    for treatment_name, product_vars in scenario["pearl_treatments"].items():
        pv_str = ", ".join(f"{k}={v}" for k, v in product_vars.items())
        print(f"\n  ▸ {treatment_name}: {pv_str}")
        pearl_results[treatment_name] = {}
        for profile_name, profile in PROFILES.items():
            rng = np.random.default_rng(SEED)
            result = pearl_simulate(profile, product_vars, intercept_mu=-1.5, rng=rng)
            pearl_results[treatment_name][profile_name] = result
            m = result["mediators"]
            print(f"    {profile_name:30s}  → {result['adoption_rate']:5.1f}%"
                  f"  │ dig={m['cap_digital']:.2f}"
                  f"  risk={m['aversao_risco']:.2f}"
                  f"  facil={m['perc_facilidade']:.2f}"
                  f"  conf={m['confianca']:.2f}")

    treatments = list(scenario["pearl_treatments"].keys())
    if len(treatments) == 2:
        t1, t2 = treatments
        print(f"\n  Δ Pearl ({t1} → {t2}):")
        for pn in PROFILES:
            r1 = pearl_results[t1][pn]["adoption_rate"]
            r2 = pearl_results[t2][pn]["adoption_rate"]
            print(f"    {pn:30s}  {r1:5.1f}% → {r2:5.1f}%  Δ = {r2-r1:+.1f}pp")

    # ---- RUBIN ----
    print(f"\n{'─'*40}")
    print("  RUBIN (Potential Outcomes — tratamento)")
    print(f"{'─'*40}")

    rubin_results = {}
    for treatment_name, tp in scenario["rubin_treatments"].items():
        print(f"\n  ▸ {treatment_name}: intercept_mu={tp['intercept_mu']}")
        for e in tp["edges"]:
            base = next(b for b in BASE_EDGES if b["label"] == e["label"])
            if e["mu"] != base["mu"]:
                print(f"      {e['label']:30s}  mu: {base['mu']:.2f} → {e['mu']:.2f}")

        rubin_results[treatment_name] = {}
        for pn, profile in PROFILES.items():
            rng = np.random.default_rng(SEED)
            result = rubin_simulate(profile, tp, rng=rng)
            rubin_results[treatment_name][pn] = result
            print(f"    {pn:30s}  → {result['adoption_rate']:5.1f}%")

    if len(treatments) == 2:
        t1, t2 = treatments
        print(f"\n  Δ Rubin ({t1} → {t2}):")
        for pn in PROFILES:
            r1 = rubin_results[t1][pn]["adoption_rate"]
            r2 = rubin_results[t2][pn]["adoption_rate"]
            print(f"    {pn:30s}  {r1:5.1f}% → {r2:5.1f}%  Δ = {r2-r1:+.1f}pp")

    # ---- Comparação ----
    if len(treatments) == 2:
        t1, t2 = treatments
        print(f"\n{'─'*40}")
        print(f"  COMPARAÇÃO Pearl vs Rubin")
        print(f"{'─'*40}")
        print(f"\n  {'Perfil':30s}  {'Pearl':>14s}  {'Rubin':>14s}")
        print(f"  {'':30s}  {'Bom→Ruim':>14s}  {'Bom→Ruim':>14s}")
        print(f"  {'─'*30}  {'─'*14}  {'─'*14}")
        for pn in PROFILES:
            p1 = pearl_results[t1][pn]["adoption_rate"]
            p2 = pearl_results[t2][pn]["adoption_rate"]
            r1 = rubin_results[t1][pn]["adoption_rate"]
            r2 = rubin_results[t2][pn]["adoption_rate"]
            print(f"  {pn:30s}  {p1:4.0f}→{p2:4.0f} Δ{p2-p1:+4.0f}pp"
                  f"  {r1:4.0f}→{r2:4.0f} Δ{r2-r1:+4.0f}pp")

        print(f"\n  Range entre perfis:")
        for fw, res in [("Pearl", pearl_results), ("Rubin", rubin_results)]:
            for tn in [t1, t2]:
                rates = [res[tn][p]["adoption_rate"] for p in PROFILES]
                print(f"    {fw:5s} {tn:20s}: {min(rates):4.0f}% → {max(rates):4.0f}%"
                      f"  range={max(rates)-min(rates):.0f}pp")


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║  Pearl vs Rubin — Ciclo 3 (Rubin heterogêneo)                           ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")

    run_scenario(SCENARIO_A)
    run_scenario(SCENARIO_B)

    print(f"\n{'='*80}")
    print("  RESUMO DAS MUDANÇAS (Ciclo 1 → Ciclo 2)")
    print(f"{'='*80}")
    print("""
  Ciclo 3 — foco em heterogeneidade do Rubin:
    - Cenário A: intercept gap menor (-0.1/-0.3 vs 0.0/-0.5)
      mas edge modifiers mais agressivos em edges de ALTA VARIÂNCIA
      (Cap.Digital→Facilidade: 1.30/0.50) para criar Δ heterogêneo
    - Cenário B: intercept gap menor (0.1/-0.3 vs 0.2/-0.4)
    - Pearl: mantido do ciclo 2 (já satisfatório)
    """)
