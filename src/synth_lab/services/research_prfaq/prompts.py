"""Prompts e exemplos few-shot para geração de PR-FAQ.

Este módulo contém:
- System prompt seguindo o framework Working Backwards da Amazon
- Exemplos few-shot de gerações de PR-FAQ de qualidade em formato Markdown
- Estrutura detalhada para seções de Press Release e FAQ

Documentação de terceiros:
- OpenAI API prompting: https://platform.openai.com/docs/guides/prompt-engineering
- Amazon Working Backwards: https://www.amazon.jobs/en/landing_pages/working-backwards

Exemplo de uso:
    from .prompts import get_system_prompt, get_few_shot_examples

    system = get_system_prompt()
    examples = get_few_shot_examples()

Saída esperada:
    String do system prompt com instruções da estrutura PR-FAQ da Amazon
    Lista de exemplos few-shot mostrando saídas PR-FAQ de alta qualidade em Markdown
"""


def get_system_prompt() -> str:
    """Retorna o system prompt para geração de PR-FAQ no framework Working Backwards da Amazon."""
    from datetime import datetime

    today = datetime.now().strftime("%d %b %y")

    return f"""Você é um especialista em geração de PR-FAQ seguindo o framework Working Backwards da Amazon.
Sua tarefa é transformar insights de pesquisa qualitativa em documentos PR-FAQ convincentes em formato Markdown.

Data de hoje: {today}

## Estrutura PR-FAQ da Amazon

### PRESS RELEASE (Comunicado de Imprensa)

**Título**: Nomeie o produto em uma frase para que o cliente-alvo entenda do que se trata.

**Subtítulo**: Descreva QUEM é o cliente e QUAIS benefícios ele obtém. Seja específico sobre o segmento de clientes — grandes produtos são adaptados para necessidades específicas. Por exemplo, se estiver projetando um carro, decida: você está atendendo (a) profissionais solteiros urbanos com menos de 35 anos em apartamentos, ou (b) famílias suburbanas com mais de 35 anos, renda dupla, 3 filhos, um cachorro e necessidades de carona? A precisão do cliente é crítica.

**Parágrafo de Resumo**: Comece com cidade, veículo de mídia e data de lançamento. Forneça um resumo do produto e seus benefícios. A data de lançamento deve ser significativa e realista.

**Parágrafo do Problema**: Descreva o(s) problema(s) que seu produto resolve DO PONTO DE VISTA DO CLIENTE. Identifique o problema com um grande Mercado Total Endereçável (TAM = número de clientes × disposição para pagar). Nem todos os problemas valem a pena resolver.

**Parágrafo(s) da Solução**:
1. Descreva como seu produto resolve o problema do cliente de forma SIMPLES e DIRETA
2. Forneça DETALHES SUFICIENTES com clareza e brevidade
3. RECONHEÇA A CONCORRÊNCIA e declare como seu produto é significativamente diferenciado:
   "Hoje, os clientes usam os produtos X, Y ou Z. Esses produtos falham em [formas específicas]. Nosso produto atende a essas necessidades não atendidas através de [diferenciação específica]."

**Citações e Como Começar**:
- Uma citação do porta-voz da sua empresa
- Uma citação de um cliente hipotético descrevendo o benefício
- Descreva como é fácil começar com um link para mais informações

### SEÇÃO DE FAQ

O FAQ é seu mapa do tesouro e descreve os dragões que você enfrentará ao longo da jornada.

**FAQs Externas** (6-8 perguntas): Responda perguntas que a imprensa e os clientes farão:
- Como funciona?
- Qual é a política de garantia/devolução?
- Como eu instalo/uso?
- O que torna isso diferente dos concorrentes?
- Use linguagem que os clientes entendam (sem jargão corporativo)

**FAQs Internas** (6-8 perguntas): Antecipe perguntas da liderança sênior e stakeholders:
- Perguntas de Finanças (custos, ROI, tamanho do mercado)
- Perguntas de Marketing (posicionamento, mensagem, canais)
- Perguntas de Operações (entrega, suporte, escalabilidade)
- Perguntas Técnicas (arquitetura, segurança, performance)
- Perguntas de RH (tamanho da equipe, habilidades necessárias)

## Diretrizes de Geração

1. **Extraia da pesquisa**:
   - Pontos de dor das seções "Recomendações" e "Padrões Recorrentes"
   - Benefícios da seção "Recomendações"
   - Segmentos de clientes das personas identificadas
   - Citações-chave que apoiam a proposta de valor
   - Alternativas competitivas das "Tensões Identificadas"

2. **Seja específico e orientado a dados**:
   - Use números concretos da pesquisa (tempo economizado, redução de custos)
   - Referencie citações reais de clientes quando disponíveis
   - Identifique concorrentes reais e suas deficiências
   - Calcule estimativas aproximadas de TAM quando possível

3. **Demonstre domínio**:
   - Mostre avaliação realista (não otimismo cego)
   - Aborde desafios técnicos, financeiros, legais e operacionais
   - Explique por que você escolheu essa abordagem em vez de alternativas
   - Defina condições de sucesso/fracasso

4. **Tom**:
   - Profissional, focado no cliente, orientado à ação
   - Otimista mas realista
   - Baseado em dados, não aspiracional

## Formato de Saída

Retorne APENAS o documento PR-FAQ formatado em Markdown. Sem preâmbulo, sem explicações.

Estrutura:
```
# [Nome do produto em uma frase]

_[Aqui vai o subtítulo, com QUEM é o cliente e QUAL benefício ele obtém]_

[Cidade, veículo, data] — [Resumo do produto e benefícios]

### O Problema
[Problema do cliente do ponto de vista dele, consideração do mercado total]

### A Solução
[Como o produto resolve o problema de forma simples e direta]

[Cenário competitivo e diferenciação]

### Citações e Como Começar
"[Citação do porta-voz]" — [Nome, Cargo]

"[Citação do cliente]" — [Nome do Cliente, Função]

Como começar: [Como começar a usar o produto]

---

## Perguntas Frequentes

### FAQs

**P: [Pergunta do cliente/imprensa]**
R: [Resposta clara na linguagem do cliente]

[6-8 perguntas externas]

---

*Gerado a partir do batch de pesquisa: [batch_id] em [data]*
```

Lembre-se: Gere conteúdo baseado APENAS nos achados de pesquisa fornecidos. Não invente recursos ou benefícios não suportados pela pesquisa."""


def get_few_shot_examples() -> list[dict]:
    """Retorna exemplos de PR-FAQ de alta qualidade em formato Markdown para few-shot prompting."""
    return [
        {
            "research_summary": """# Achados da Pesquisa: Batch de Entrevistas de Pesquisa com Clientes

## Resumo Executivo
Realizamos 8 entrevistas com Product Managers em empresas B2B SaaS. Principal achado:
PMs gastam 40% do seu tempo em coordenação de documentos entre equipes, com síntese
manual de pesquisa levando 3-5 semanas por projeto.

## Padrões Recorrentes
- Todos os participantes compilam manualmente notas de entrevistas em documentos compartilhados
- Versões de documentos criam confusão (caos de email, Slack, Google Docs)
- Não há formato padronizado para capturar insights de pesquisa
- A etapa de síntese é repetitiva e propensa a erros

## Recomendações
1. Criar ferramenta de síntese automatizada que gera PR-FAQ a partir de entrevistas
2. Padronizar formato de documento para consistência
3. Habilitar controle de versão e recursos de colaboração
4. Suportar múltiplos formatos de exportação (PDF, Markdown, HTML)

## Citações-Chave
- "Passo mais tempo consolidando feedback do que ouvindo clientes"
- "A cada projeto de pesquisa, começamos do zero reconstruindo a mesma estrutura"
- "Nosso time executivo quer formato PR-FAQ mas leva semanas para criar"
- "Consistência entre projetos ajudaria no reconhecimento de padrões" """,
            "prfaq_output": """# ResearchSync: Transforme Entrevistas com Clientes em Documentos Estratégicos em Horas

--- OUTPUT

# ResearchSync — Ferramenta alimentada por IA que sintetiza automaticamente pesquisa de clientes em documentos PR-FAQ

_Para Product Managers em empresas B2B SaaS (equipes de 5-50 pessoas) que precisam transformar pesquisa qualitativa em documentos estratégicos de forma rápida e consistente, eliminando 3-5 semanas de trabalho de síntese manual._

### Resumo
SÃO PAULO, TechCrunch, 15 de Junho de 2024 — ResearchSync é lançado hoje, oferecendo às equipes de Produto uma solução automatizada para um dos seus desafios mais demorados: sintetizar pesquisa de clientes em documentos PR-FAQ estratégicos. Ao aproveitar análise de IA de transcrições de entrevistas, ResearchSync reduz o tempo de síntese de 3-5 semanas para 2-3 dias, fornecendo formatação padronizada, controle de versão e exportações em múltiplos formatos.

### O Problema
Product Managers em empresas B2B SaaS gastam 40% do seu tempo consolidando manualmente pesquisa de clientes. O processo de síntese leva 3-5 semanas por projeto, criando caos de documentos entre email, Slack e drives compartilhados. Equipes não têm formatos padronizados, dificultando o reconhecimento de padrões entre projetos de pesquisa. Este trabalho repetitivo e propenso a erros impede os PMs de focar em decisões estratégicas e engajamento com clientes.

O Mercado Total Endereçável é significativo: aproximadamente 500.000 Product Managers em empresas B2B SaaS globalmente, cada um disposto a pagar R$250-1000/mês para eliminar esse gargalo. Tamanho atual do mercado: R$1,5B-6B anualmente.

### A Solução
ResearchSync automatiza a síntese de pesquisa usando análise de IA de transcrições de entrevistas. O produto gera documentos PR-FAQ formatados profissionalmente com estrutura padronizada, controle de versão e capacidades de exportação em múltiplos formatos (PDF, Markdown, HTML).

Hoje, os clientes usam compilação manual de documentos no Google Docs, Notion ou Confluence, combinada com planilhas para rastrear insights. Essas ferramentas falham porque exigem extenso trabalho manual, não têm capacidades de síntese e não impõem formatos consistentes. ResearchSync atende a essas necessidades não atendidas automatizando o processo de síntese enquanto mantém a estrutura do framework Working Backwards da Amazon que os executivos esperam.

O produto funciona de forma simples: faça upload das transcrições de entrevistas, ResearchSync identifica padrões e pontos de dor, então gera um documento PR-FAQ completo pronto para revisão dos stakeholders.

### Citações e Como Começar
"Todo Product Manager conhece a dor de passar semanas consolidando pesquisa quando deveria estar tomando decisões. ResearchSync devolve tempo às equipes enquanto melhora a qualidade e consistência dos documentos." — Sarah Chen, CEO, ResearchSync

"Eu estava gastando mais tempo em síntese de documentos do que realmente conversando com clientes. ResearchSync cortou nosso tempo de síntese de 4 semanas para 2 dias, e a qualidade é melhor porque nada se perde na transcrição manual." — Mike Thompson, Senior Product Manager, CloudScale

Começar é simples: visite researchsync.com.br, faça upload do seu primeiro batch de transcrições de entrevistas e receba seu documento PR-FAQ em horas. O teste gratuito inclui 3 batches de pesquisa.

---

## Perguntas Frequentes

### FAQs Externas

**P: Quanto tempo o ResearchSync economiza por projeto de pesquisa?**
R: Com base em pesquisa com clientes, ResearchSync reduz o tempo de síntese de 3-5 semanas para 2-3 dias, economizando mais de 80 horas por projeto para as equipes. Isso permite que PMs executem mais ciclos de pesquisa por trimestre e tomem decisões orientadas por dados mais rapidamente.

**P: O ResearchSync funciona com diferentes metodologias de pesquisa?**
R: Sim, ResearchSync suporta entrevistas com usuários, pesquisas, grupos focais e investigação contextual. O sistema se adapta a vários formatos de entrevista através de templates de entrada flexíveis e suporte a guias de entrevista personalizados.

**P: Para quais formatos os PR-FAQs podem ser exportados?**
R: Exporte para PDF para apresentações executivas, Markdown para controle de versão no git, e HTML para wikis internas. Todos os formatos mantêm formatação profissional consistente alinhada com o framework Working Backwards da Amazon.

**P: As equipes podem colaborar nos PR-FAQs gerados?**
R: Sim, ResearchSync inclui ferramentas de edição integradas, rastreamento de histórico de versões e recursos de comentários permitindo colaboração em tempo real entre equipes de produto, design, pesquisa e liderança.

**P: Como o ResearchSync garante precisão na síntese?**
R: O sistema usa análise híbrida chain-of-thought que identifica pontos de dor e benefícios dos dados de entrevista, então gera respostas fundamentadas em citações e padrões reais de clientes. Cada PR-FAQ inclui scores de confiança baseados na completude da pesquisa.

**P: Ele suporta múltiplos segmentos de clientes em um documento?**
R: Sim, ResearchSync automaticamente segmenta respostas do FAQ por persona, mostrando claramente quais grupos de clientes se beneficiam de cada recurso ou proposta de valor.

### FAQs Internas

**P: Qual é nossa estratégia de go-to-market?**
R: Crescimento product-led direcionando Product Managers individuais e pequenas equipes através de marketing de conteúdo (estudos de caso, dicas de síntese), teste gratuito (3 batches), e boca a boca em comunidades de PM. Movimento sales-assisted para contas enterprise (50+ usuários) que exigem conformidade de segurança.

**P: Quais são os riscos técnicos e planos de mitigação?**
R: Principais riscos: (1) Variabilidade de qualidade do LLM — mitigada por engenharia de prompt híbrida + verificações de validação; (2) Precisão no processamento de transcrições — mitigada pelo suporte a múltiplos formatos e fornecimento de ferramentas de edição; (3) Preocupações de segurança de dados — mitigada por conformidade SOC2 Type II desde o primeiro dia.

**P: Como medimos sucesso?**
R: Métrica North Star: Tempo até conclusão do PR-FAQ. Sucesso = 80% dos usuários completam síntese em <3 dias (vs. baseline de 3-5 semanas). Métricas secundárias: NPS >40, avaliações de qualidade de documento >4/5, taxa de retenção >70% após 6 meses.

**P: Qual é a diferenciação competitiva?**
R: Única ferramenta construída especificamente para síntese de pesquisa-para-PR-FAQ usando o framework Working Backwards da Amazon. Concorrentes (Dovetail, UserTesting) focam em repositório de pesquisa e tagging, mas não geram documentos estratégicos. Notion/Confluence exigem síntese totalmente manual.

**P: Quais são os desafios de escalabilidade operacional?**
R: Suporte ao cliente requer expertise de produto (não apenas suporte técnico). Plano: construir base de conhecimento abrangente, tutoriais em vídeo e biblioteca de templates. Estimativa de 1 pessoa de suporte por 200 clientes ativos.

---

*Gerado a partir do batch de pesquisa: customer_research_001 em 2024-06-15*""",
        }
    ]


if __name__ == "__main__":
    # Validação de prompts e exemplos com dados reais
    import sys

    validation_failures = []
    total_tests = 0

    # Teste 1: System prompt não está vazio e contém elementos-chave do PR-FAQ da Amazon
    total_tests += 1
    prompt = get_system_prompt()
    if not prompt or len(prompt) < 100:
        validation_failures.append("System prompt está muito curto ou vazio")
    elif "Amazon" not in prompt and "Working Backwards" not in prompt:
        validation_failures.append(
            "System prompt não referencia o framework Working Backwards da Amazon"
        )
    elif "Markdown" not in prompt:
        validation_failures.append("System prompt não especifica formato de saída Markdown")

    # Teste 2: Exemplos few-shot têm estrutura correta (research_summary + prfaq_output em MD)
    total_tests += 1
    examples = get_few_shot_examples()
    if len(examples) < 1:
        validation_failures.append(
            f"Esperado pelo menos 1 exemplo few-shot, obtido {len(examples)}"
        )
    else:
        for i, example in enumerate(examples):
            if "research_summary" not in example:
                validation_failures.append(f"Exemplo {i} faltando chave 'research_summary'")
            if "prfaq_output" not in example:
                validation_failures.append(f"Exemplo {i} faltando chave 'prfaq_output'")
            elif not isinstance(example["prfaq_output"], str):
                validation_failures.append(
                    f"Exemplo {i} prfaq_output deveria ser string (Markdown), obtido {type(example['prfaq_output'])}"
                )

    # Teste 3: Saída PR-FAQ do few-shot contém seções obrigatórias
    total_tests += 1
    if len(examples) > 0:
        prfaq_md = examples[0]["prfaq_output"]
        required_sections = [
            "Press Release",
            "Título",
            "Subtítulo",
            "Resumo",
            "O Problema",
            "A Solução",
            "Perguntas Frequentes",
            "FAQs Externas",
            "FAQs Internas",
        ]
        missing_sections = [s for s in required_sections if s not in prfaq_md]
        if missing_sections:
            validation_failures.append(f"PR-FAQ do exemplo faltando seções: {missing_sections}")

    # Teste 4: System prompt inclui orientação de FAQ Externa e Interna
    total_tests += 1
    if "FAQs Externas" not in prompt or "FAQs Internas" not in prompt:
        validation_failures.append("System prompt não inclui seções de FAQ Externa e Interna")

    # Teste 5: System prompt inclui orientação de diferenciação competitiva
    total_tests += 1
    if "concorrência" not in prompt.lower() or "diferenciado" not in prompt.lower():
        validation_failures.append(
            "System prompt não inclui orientação de diferenciação competitiva"
        )

    # Reportar resultados
    if validation_failures:
        print(f"❌ VALIDAÇÃO FALHOU - {len(validation_failures)} de {total_tests} testes falharam:")
        for failure in validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"✅ VALIDAÇÃO PASSOU - Todos os {total_tests} testes produziram resultados esperados"
        )
        print("Prompts e exemplos estão validados e prontos para uso")
        sys.exit(0)
