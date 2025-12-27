Perfeito. Template mínimo, operacional e reutilizável.
Cabe numa página e força disciplina.

⸻

Template de Scorecard de Feature (v1)

1. Identificação
	•	Feature: ______________________
	•	Cenário: ______________________
	•	Data: ______________________
	•	Avaliadores: ______________________

⸻

2. Dimensões (0 = baixo / 1 = alto)

Dimensão	Score	Regra objetiva (marcar o que se aplica)
Complexity	☐ 0.0–1.0	☐ +0.2 por conceito novo☐ +0.2 estados invisíveis☐ +0.2 termos técnicos☐ +0.2 ação irreversível☐ +0.2 feedback fraco
Initial Effort	☐	☐ uso imediato (0.1)☐ 1–2 passos (0.3)☐ configuração (0.5)☐ onboarding dedicado (0.7+)
Perceived Risk	☐	☐ reversível (0.1)☐ afeta dados (0.4)☐ afeta dinheiro/reputação (0.7+)
Time to Value	☐	☐ imediato (0.1)☐ mesma sessão (0.3)☐ acumulado (0.6)☐ futuro/incerto (0.8+)


⸻

3. Justificativa curta (obrigatória)

Por que esse score?
(1–2 frases objetivas, sem adjetivos vagos)

________________________________________________________________


⸻

4. Incerteza assumida (obrigatório)

Dimensão	Min	Max
Complexity	☐	☐
Initial Effort	☐	☐
Perceived Risk	☐	☐
Time to Value	☐	☐


⸻

5. Output para simulação

feature = {
  "complexity": (min, max),
  "initial_effort": (min, max),
  "perceived_risk": (min, max),
  "time_to_value": (min, max)
}

