"""
Simula o resultado para synth 0wrccz / run sr_bed5cead usando o mecanismo
(1-x) consistente nas camadas 2 e 3, e compara com o mecanismo atual.

Dados hardcoded a partir das queries anteriores — sem dependência de DB.
"""
import math
import numpy as np

# ── Dados do synth 0wrccz ────────────────────────────────────────────────────
SENSITIVITY = {
    "Aversão a Risco":      0.7759,
    "Confiança Instit.":    0.2590,
    "Tolerância a Atrito":  0.4349,
    "Planejamento Rotina":  0.4140,  # sem valor armazenado; base=0.45, nenhuma regra bateu
}
PRODUCT = {
    "Agendamento Claro":        0.8,   # high
    "Flexibilidade de Mudança": 0.2,   # low
    "Precisão da Entrega":      0.8,   # high
    "Transparência do Status":  0.2,   # low
}

# ── Topologia ────────────────────────────────────────────────────────────────
# edges_into_interaction: (pai, direction)
INTERACTION_PARENTS = {
    "Sensação de Controle":      [("Tolerância a Atrito", +1), ("Agendamento Claro", +1)],
    "Confiança de Cumprimento":  [("Confiança Instit.",   +1), ("Transparência do Status", +1)],
    "Esforço p/ Ajustar Agenda": [("Aversão a Risco",    +1), ("Flexibilidade de Mudança", -1)],
    "Encaixe na Rotina":         [("Planejamento Rotina", +1), ("Precisão da Entrega", +1)],
}

# edges_into_outcome: (interaction_node, direction_to_outcome)
OUTCOME_EDGES = [
    ("Sensação de Controle",      +1),
    ("Confiança de Cumprimento",  +1),
    ("Esforço p/ Ajustar Agenda", -1),
    ("Encaixe na Rotina",         +1),
]

# ── Seleções do PM ───────────────────────────────────────────────────────────
# options: [(mu, sigma), ...]  — fixas pelo sistema
OPTIONS = {0: (0.80, 0.15), 1: (0.65, 0.25), 2: (0.50, 0.50),
           3: (0.30, 0.25), 4: (0.15, 0.15)}

SELECTIONS = {
    "Sensação de Controle":      1,   # mu=0.65
    "Confiança de Cumprimento":  1,   # mu=0.65
    "Esforço p/ Ajustar Agenda": 0,   # mu=0.80
    "Encaixe na Rotina":         1,   # mu=0.65
    "Uso Recorrente":            0,   # "mais importante" = Sensação de Controle
}

# ── Parâmetros do modelo ─────────────────────────────────────────────────────
INTERCEPT_MU    = -0.9
INTERCEPT_SIGMA =  0.4
N_REPS          = 10
BUDGET          = 3.0


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))


def layer1_values():
    return {**SENSITIVITY, **PRODUCT}


# ── Camada 2: compute interaction nodes ──────────────────────────────────────

def compute_interactions_current(layer1):
    """Atual: effective = (1-x) se dir=-1, depois média simples."""
    result = {}
    for node, parents in INTERACTION_PARENTS.items():
        total, count = 0.0, 0
        for parent, direction in parents:
            val = layer1[parent]
            eff = val if direction == 1 else (1 - val)
            total += eff
            count += 1
        result[node] = total / count
    return result


# Nota: no mecanismo atual a camada 2 JÁ usa (1-x).
# A diferença está apenas na camada 3 (sinal do coeficiente vs inversão do input).
compute_interactions_new = compute_interactions_current   # idêntico


# ── Camada 3: weight multipliers (2x para "mais importante") ────────────────

def weight_multipliers(n_edges):
    most_important = SELECTIONS["Uso Recorrente"]           # índice da opção
    # opção 0 do outcome = "Sensação de Controle"
    most_important_node = ["Sensação de Controle",
                           "Confiança de Cumprimento",
                           "Esforço p/ Ajustar Agenda",
                           "Encaixe na Rotina"][most_important]
    norm = n_edges / (n_edges + 1)
    return [
        2.0 * norm if node == most_important_node else 1.0 * norm
        for node, _ in OUTCOME_EDGES
    ]


# ── Monte Carlo: mecanismo ATUAL ─────────────────────────────────────────────

def mc_current(interactions, seed=None):
    """
    Camada 3 atual:
      - dir=-1 → beta_mu negativo
      - input = interaction_val (direto)
    """
    rng = np.random.default_rng(seed)
    n = len(OUTCOME_EDGES)
    scale = BUDGET / math.sqrt(n)
    mults = weight_multipliers(n)

    inputs   = np.zeros(n)
    beta_mus = np.zeros(n)
    beta_sigs = np.zeros(n)

    for i, (node, direction) in enumerate(OUTCOME_EDGES):
        mu, sigma = OPTIONS[SELECTIONS[node]]
        inputs[i]    = interactions[node]
        beta_mus[i]  = mu * scale * direction * mults[i]   # negativo se dir=-1
        beta_sigs[i] = sigma * scale * mults[i]

    probs = []
    for _ in range(N_REPS):
        intercept = rng.normal(INTERCEPT_MU, INTERCEPT_SIGMA)
        coefs     = rng.normal(beta_mus, beta_sigs)
        logit     = intercept + np.dot(inputs, coefs)
        probs.append(float(sigmoid(np.array([logit]))[0]))

    return probs


# ── Monte Carlo: mecanismo NOVO ──────────────────────────────────────────────

def mc_new(interactions, seed=None):
    """
    Camada 3 novo:
      - dir=-1 → input = (1 - interaction_val), coef sempre positivo
      - beta_mu = mu * scale * mults[i]  (sem o direction)
    """
    rng = np.random.default_rng(seed)
    n = len(OUTCOME_EDGES)
    scale = BUDGET / math.sqrt(n)
    mults = weight_multipliers(n)

    inputs    = np.zeros(n)
    beta_mus  = np.zeros(n)
    beta_sigs = np.zeros(n)

    for i, (node, direction) in enumerate(OUTCOME_EDGES):
        mu, sigma = OPTIONS[SELECTIONS[node]]
        val = interactions[node]
        inputs[i]    = val if direction == 1 else (1 - val)   # inversão no input
        beta_mus[i]  = mu * scale * mults[i]                  # sempre positivo
        beta_sigs[i] = sigma * scale * mults[i]

    probs = []
    for _ in range(N_REPS):
        intercept = rng.normal(INTERCEPT_MU, INTERCEPT_SIGMA)
        coefs     = rng.normal(beta_mus, beta_sigs)
        logit     = intercept + np.dot(inputs, coefs)
        probs.append(float(sigmoid(np.array([logit]))[0]))

    return probs


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    layer1       = layer1_values()
    interactions = compute_interactions_current(layer1)  # camada 2 idêntica

    print("=" * 60)
    print("CAMADA 1 — inputs")
    print("=" * 60)
    for k, v in layer1.items():
        print(f"  {k:35s} = {v:.4f}")

    print("\n" + "=" * 60)
    print("CAMADA 2 — interaction nodes  [mecanismo: (1-x)]")
    print("=" * 60)
    for node, parents in INTERACTION_PARENTS.items():
        vals = []
        for parent, direction in parents:
            raw = layer1[parent]
            eff = raw if direction == 1 else (1 - raw)
            vals.append(eff)
            d = "direto " if direction == 1 else "1-x    "
            print(f"  {d}  {parent:35s} → eff = {eff:.4f}")
        print(f"         {'→ ' + node:37s} = {sum(vals)/len(vals):.4f}")
        print()

    n = len(OUTCOME_EDGES)
    scale = BUDGET / math.sqrt(n)
    mults = weight_multipliers(n)

    print("=" * 60)
    print("CAMADA 3 — comparação dos dois mecanismos")
    print("=" * 60)
    print(f"  per_edge_scale = 3.0 / sqrt({n}) = {scale:.4f}")
    print(f"  weight multipliers: {[round(m,3) for m in mults]}")
    print(f"    (Sensação de Controle = 'mais importante' → mult=1.60)")
    print()

    print(f"  {'Node':30s} {'dir':4s} {'sel':4s} {'mu':5s}  "
          f"{'input_atual':11s} {'βmu_atual':9s}  "
          f"{'input_novo':10s} {'βmu_novo':8s}")
    print("  " + "-" * 80)
    for i, (node, direction) in enumerate(OUTCOME_EDGES):
        mu, _ = OPTIONS[SELECTIONS[node]]
        val = interactions[node]
        # atual
        inp_a  = val
        bmu_a  = mu * scale * direction * mults[i]
        # novo
        inp_n  = val if direction == 1 else (1 - val)
        bmu_n  = mu * scale * mults[i]
        print(f"  {node:30s} {direction:+3d}  {SELECTIONS[node]:4d}  {mu:.2f}  "
              f"{inp_a:11.4f} {bmu_a:+9.4f}  "
              f"{inp_n:10.4f} {bmu_n:+8.4f}")

    # Logit determinístico (sem ruído)
    def det_logit(mechanism):
        logit = INTERCEPT_MU
        for i, (node, direction) in enumerate(OUTCOME_EDGES):
            mu, _ = OPTIONS[SELECTIONS[node]]
            val = interactions[node]
            if mechanism == "atual":
                inp  = val
                beta = mu * scale * direction * mults[i]
            else:
                inp  = val if direction == 1 else (1 - val)
                beta = mu * scale * mults[i]
            logit += beta * inp
        return logit

    l_atual = det_logit("atual")
    l_novo  = det_logit("novo")

    print()
    print(f"  Logit determinístico (sem ruído):")
    print(f"    atual: {l_atual:+.4f}  → prob = {sigmoid(np.array([l_atual]))[0]:.4f}")
    print(f"    novo:  {l_novo:+.4f}  → prob = {sigmoid(np.array([l_novo]))[0]:.4f}")

    # Monte Carlo com seed fixo
    SEED = 42
    probs_atual = mc_current(interactions, seed=SEED)
    probs_novo  = mc_new(interactions, seed=SEED)

    avg_atual = sum(probs_atual) / N_REPS
    avg_novo  = sum(probs_novo)  / N_REPS

    print()
    print("=" * 60)
    print(f"MONTE CARLO — {N_REPS} repetições (seed={SEED})")
    print("=" * 60)
    print(f"  {'rep':4s}  {'prob atual':11s}  {'prob novo':10s}")
    for r, (pa, pn) in enumerate(zip(probs_atual, probs_novo)):
        print(f"  {r:4d}  {pa:.4f}       {pn:.4f}")
    print(f"  {'AVG':4s}  {avg_atual:.4f}       {avg_novo:.4f}")
    print(f"  {'RND':4s}  {round(avg_atual,2)}          {round(avg_novo,2)}")
    print()
    print(f"  Resultado armazenado (original, sem seed): 0.56")
    print(f"  Mecanismo atual  (seed=42): {round(avg_atual, 2)}")
    print(f"  Mecanismo novo   (seed=42): {round(avg_novo,  2)}")


if __name__ == "__main__":
    main()
