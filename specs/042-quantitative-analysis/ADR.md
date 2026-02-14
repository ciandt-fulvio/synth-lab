# ADR: Análise Quantitativa — Decisões Arquiteturais

1. **Simulação server-side**: Monte Carlo roda no backend (não no browser). Motivo: acesso direto aos synths do banco, isolamento de carga, reprodutibilidade com seed.
2. **Synths existentes como população**: usa synths do `synth_group` do experimento — não gera usuários aleatórios. Atributos demográficos (idade, renda, escolaridade) e sensitivities (digital_capability, risk_aversion, institutional_trust_level, friction_tolerance) são normalizados [0,1] e mapeados às 10 userVars do DAG.
3. **LLM split**: gpt-5.1 para geração do DAG + interview_guide (estrutural, precisa de qualidade), gpt-4o-mini para interpretações das 3 seções (paralelo, custo baixo). Todas as chamadas com Phoenix tracing.
4. **Persistência completa**: modelo causal, seleções do PM, resultados de simulação e interpretações são salvos no banco. Permite re-visitar resultados sem re-rodar.
5. **Aba única "Análise Quanti"**: fluxo linear na mesma aba — DAG → Likert → Simular → resultados → interview_guide auto-gerado. Não existe aba "Modelagem" separada.
6. **mu/sigma fixos**: as 5 opções Likert sempre usam os mesmos valores (0.80/0.15, 0.65/0.25, 0.50/0.50, 0.30/0.25, 0.15/0.15). O PM escolhe por concordância textual, não por valor numérico.
7. **Sensibilidade por aresta**: para cada aresta, fixa as demais e varia entre extremos (opção 0 vs opção 4). Impacto = |diferença das médias|. Roda com 800 iterações por variação (trade-off custo/precisão).
8. **Mapeamento userVar → synth**: 10 extractors fixos no backend (7 demográficos + 3 sensitivities). Não configurável pelo PM.
9. **Interview guide fusão direta**: questionário de campo (Malhotra) alimenta diretamente os campos da tabela `interview_guide` (context_definition, questions, context_examples). Auto-salva após simulação, sobrescrevendo guide anterior. `InterviewGuideGeneratorService` não é mais chamado na criação do experimento.
10. **Prompts do JSX reutilizados**: DAG_SYSTEM e INTERP_SYSTEM usados as-is (ajustando modelo e userVars). QUESTIONNAIRE_SYSTEM adaptado para output JSON no formato interview_guide.
