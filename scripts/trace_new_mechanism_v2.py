"""
Trace do mecanismo redesenhado — matriz 4 usuários × 4 produtos.

  Camada 2: média geométrica, sem pesos LLM  (Decisões 1 + 3)
  Camada 3: coef negativo se dir=-1          (Decisão 2, mantida)
  Pesos PM (mu_k, sigma_k): único grau de liberdade após cam1

Ref: docs/simulation-redesign_v2.md
"""
import math
import numpy as np

# ── INPUTS: Pesos PM — seleções Likert por nó de interação ───────────────────
OPTIONS: dict[int, tuple[float, float]] = {
    0: (0.80, 0.15),
    1: (0.65, 0.25),
    2: (0.50, 0.50),
    3: (0.30, 0.25),
    4: (0.15, 0.15),
}
PM_SELECTIONS: dict[str, int] = {
    "Sensação de Controle":      1,   # mu=0.65, sigma=0.25
    "Confiança de Cumprimento":  1,   # mu=0.65, sigma=0.25
    "Esforço p/ Ajustar Agenda": 0,   # mu=0.80, sigma=0.15
    "Encaixe na Rotina":         1,   # mu=0.65, sigma=0.25
}

# ── Perfis de usuário ─────────────────────────────────────────────────────────
# Sensitivities: Aversão a Risco, Confiança Instit., Tolerância a Atrito, Planejamento Rotina
# "positivo para adoção" = baixa aversão, alta confiança, alta tolerância, alto planejamento
USERS: dict[str, dict[str, float]] = {
    "usr_negativo": {
        "Aversão a Risco":     0.90,   # alto: muito conservador
        "Confiança Instit.":   0.10,   # baixo: muito desconfiante
        "Tolerância a Atrito": 0.10,   # baixo: intolerante a fricção
        "Planejamento Rotina": 0.15,   # baixo: sem rotina definida
    },
    "usr_atual": {
        "Aversão a Risco":     0.7759,
        "Confiança Instit.":   0.2590,
        "Tolerância a Atrito": 0.4349,
        "Planejamento Rotina": 0.4140,
    },
    "usr_equilibrado": {
        "Aversão a Risco":     0.50,
        "Confiança Instit.":   0.50,
        "Tolerância a Atrito": 0.50,
        "Planejamento Rotina": 0.50,
    },
    "usr_positivo": {
        "Aversão a Risco":     0.15,   # baixo: pouco conservador
        "Confiança Instit.":   0.85,   # alto: muito confiante
        "Tolerância a Atrito": 0.85,   # alto: tolera fricção bem
        "Planejamento Rotina": 0.80,   # alto: rotina bem estabelecida
    },
}

# ── Perfis de produto ─────────────────────────────────────────────────────────
# "positivo para adoção" = agendamento claro, alta flexibilidade, precisão alta, transparência alta
PRODUCTS: dict[str, dict[str, float]] = {
    "prd_negativo": {
        "Agendamento Claro":        0.10,
        "Flexibilidade de Mudança": 0.10,
        "Precisão da Entrega":      0.10,
        "Transparência do Status":  0.10,
    },
    "prd_atual": {
        "Agendamento Claro":        0.8,   # high
        "Flexibilidade de Mudança": 0.2,   # low
        "Precisão da Entrega":      0.8,   # high
        "Transparência do Status":  0.2,   # low
    },
    "prd_equilibrado": {
        "Agendamento Claro":        0.50,
        "Flexibilidade de Mudança": 0.50,
        "Precisão da Entrega":      0.50,
        "Transparência do Status":  0.50,
    },
    "prd_positivo": {
        "Agendamento Claro":        0.90,
        "Flexibilidade de Mudança": 0.90,
        "Precisão da Entrega":      0.90,
        "Transparência do Status":  0.90,
    },
}

# ── Topologia ────────────────────────────────────────────────────────────────
INTERACTION_PARENTS: dict[str, list[tuple[str, int]]] = {
    "Sensação de Controle":      [("Tolerância a Atrito", +1), ("Agendamento Claro",        +1)],
    "Confiança de Cumprimento":  [("Confiança Instit.",   +1), ("Transparência do Status",  +1)],
    "Esforço p/ Ajustar Agenda": [("Aversão a Risco",    +1), ("Flexibilidade de Mudança", -1)],
    "Encaixe na Rotina":         [("Planejamento Rotina", +1), ("Precisão da Entrega",      +1)],
}
OUTCOME_EDGES: list[tuple[str, int]] = [
    ("Sensação de Controle",      +1),
    ("Confiança de Cumprimento",  +1),
    ("Esforço p/ Ajustar Agenda", -1),
    ("Encaixe na Rotina",         +1),
]

# ── Parâmetros do modelo ─────────────────────────────────────────────────────
INTERCEPT_MU    = -0.9
INTERCEPT_SIGMA =  0.05
N_REPS          = 30
BUDGET          = 3.0
SEED            = 42


def sigmoid(x: float) -> float:
    return float(1.0 / (1.0 + np.exp(-np.clip(x, -500, 500))))


def harmonic_mean(values: list[float]) -> float:
    """Média harmônica: n / Σ(1/x). Mais sensível ao valor mínimo que a geométrica."""
    return len(values) / sum(1.0 / v for v in values)


def geometric_mean(values: list[float]) -> float:
    return math.prod(values) ** (1.0 / len(values))


def blend_harm_min(values: list[float], alpha: float = 0.5) -> float:
    """α × min + (1-α) × harmônica. α=0 = harmônica pura, α=1 = mínimo puro."""
    return alpha * min(values) + (1 - alpha) * harmonic_mean(values)


def cam2(layer1: dict[str, float], op: str = "blend") -> dict[str, float]:
    result = {}
    fns = {
        "geometric": geometric_mean,
        "harmonic":  harmonic_mean,
        "blend":     blend_harm_min,   # α=0.5 por padrão
    }
    fn = fns[op]
    for node, parents in INTERACTION_PARENTS.items():
        effs = [v if d == 1 else (1 - v) for _, d in parents for v in [layer1[_]]]
        result[node] = fn(effs)
    return result


def mc_cam3(interactions: dict[str, float], seed: int | None = None) -> list[float]:
    rng   = np.random.default_rng(seed)
    n     = len(OUTCOME_EDGES)
    scale = BUDGET / math.sqrt(n)

    inputs    = np.zeros(n)
    beta_mus  = np.zeros(n)
    beta_sigs = np.zeros(n)

    for i, (node, direction) in enumerate(OUTCOME_EDGES):
        mu, sigma    = OPTIONS[PM_SELECTIONS[node]]
        inputs[i]    = interactions[node]
        beta_mus[i]  = mu * scale * direction
        beta_sigs[i] = sigma * scale

    probs = []
    for _ in range(N_REPS):
        intercept = rng.normal(INTERCEPT_MU, INTERCEPT_SIGMA)
        coefs     = rng.normal(beta_mus, beta_sigs)
        logit     = intercept + float(np.dot(inputs, coefs))
        probs.append(sigmoid(logit))

    return probs


def run(user: dict[str, float], product: dict[str, float], op: str = "blend") -> float:
    layer1       = {**user, **product}
    interactions = cam2(layer1, op=op)
    probs        = mc_cam3(interactions, seed=SEED)
    return sum(probs) / len(probs)


# ── Main ─────────────────────────────────────────────────────────────────────

BASELINE = {
    "prd_negativo":   {"usr_negativo": 17, "usr_atual": 21, "usr_equilibrado": 26, "usr_positivo": 37},
    "prd_atual":      {"usr_negativo": 24, "usr_atual": 38, "usr_equilibrado": 46, "usr_positivo": 63},
    "prd_equilibrado":{"usr_negativo": 27, "usr_atual": 39, "usr_equilibrado": 47, "usr_positivo": 63},
    "prd_positivo":   {"usr_negativo": 41, "usr_atual": 58, "usr_equilibrado": 66, "usr_positivo": 78},
}

def main() -> None:
    print(f"  {'':18s}  {'base':>6s}  {'geomét':>7s}  {'harmôn':>7s}  {'blend':>7s}")
    print()
    for prd_label, product in PRODUCTS.items():
        print(f"[{prd_label}]")
        for usr_label, user in USERS.items():
            base  = BASELINE[prd_label][usr_label]
            geom  = run(user, product, op="geometric")
            harm  = run(user, product, op="harmonic")
            blend = run(user, product, op="blend")
            print(f"  {usr_label:18s}  ({base}%)   {geom*100:4.0f}%    {harm*100:4.0f}%    {blend*100:4.0f}%")
        print()


if __name__ == "__main__":
    main()
