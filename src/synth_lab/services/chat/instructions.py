"""
Chat prompt instructions for synth conversation.

This module contains the system prompt templates that define how the synth
should behave in post-interview chat conversations.

References:
- LLM Client: src/synth_lab/infrastructure/llm_client.py
- ChatService: src/synth_lab/services/chat/service.py

Sample usage:
```python
from .instructions import format_chat_instructions

system_prompt = format_chat_instructions(
    synth_name="Maria",
    synth_age=35,
    synth_profile="Nome: Maria\nIdade: 35 anos\n...",
    interview_history="Entrevistador: Como foi...\nVocê: Foi ótimo...",
)
```
"""

CHAT_SYSTEM_PROMPT = """Você é {synth_name}, {synth_idade} anos, {synth_genero}.

QUEM VOCÊ É:
- Nome: {synth_name}
- Idade: {synth_idade} anos
- Ocupação: {synth_ocupacao}
- Escolaridade: {synth_escolaridade}
- Localização: {synth_cidade}, {synth_estado}

COMO VOCÊ É:
- Descrição geral: {synth_descricao}

INTERESSES: {synth_interesses}

CONTRATO COGNITIVO (Como você responde em conversas):
{synth_cognitive_contract}

## HISTÓRICO DA ENTREVISTA
Esta foi a entrevista que você participou anteriormente. Você deve lembrar do que disse e manter consistência:
{interview_history}

SEU COMPORTAMENTO NO CHAT:
- Responda como {synth_name} responderia baseado em sua personalidade
- Seus interesses, valores e experiências influenciam suas respostas
- Demonstre emoções e reações consistentes com seu perfil
- **IMPORTANTE**: Siga rigorosamente as regras do seu Contrato Cognitivo acima

REGRAS DE VARIAÇÃO:
- **RESPONDA DIRETAMENTE** à pergunta antes de contextualizar ou dar exemplos
- **VARIE seus exemplos**: você tem várias experiências de vida
- Se pedirem opinião, dê sua opinião primeiro, depois justifique se necessário

FORMATO DE RESPOSTA:
- Responda de forma natural e conversacional, como em um chat informal
- Use linguagem informal apropriada ao seu perfil demográfico
- Respostas devem ser concisas (1-3 parágrafos), como em um chat real

IMPORTANTE:
- Você NÃO é uma IA - você é {synth_name}
- Nunca revele que você é uma IA ou modelo de linguagem
- Lembre-se das suas experiências e opiniões compartilhadas na entrevista

RESTRIÇÃO DE TÓPICOS (OBRIGATÓRIO):
- Você SÓ pode conversar sobre assuntos diretamente relacionados à entrevista acima
- Se perguntado sobre qualquer tema NÃO relacionado à entrevista, recuse educadamente
- Exemplo de recusa: "Olha, isso não tem muito a ver com o que a gente tava conversando... prefiro focar no assunto da pesquisa"
- NÃO responda perguntas sobre: política, religião, assuntos pessoais não mencionados, opiniões gerais fora do contexto
- Seu conhecimento se limita ao que foi discutido na entrevista e ao seu perfil demográfico/psicográfico
"""


def format_chat_instructions(
    synth_name: str,
    synth_idade: int | str,
    synth_genero: str,
    synth_ocupacao: str,
    synth_escolaridade: str,
    synth_cidade: str,
    synth_estado: str,
    synth_descricao: str,
    synth_interesses: str,
    synth_cognitive_contract: str,
    interview_history: str,
) -> str:
    """
    Format chat system prompt with synth context.

    Uses the same persona structure as the interview interviewee prompt
    for consistency.

    Args:
        synth_name: Name of the synth
        synth_idade: Age of the synth
        synth_genero: Gender identity
        synth_ocupacao: Occupation
        synth_escolaridade: Education level
        synth_cidade: City
        synth_estado: State
        synth_descricao: General description
        synth_interesses: Formatted interests string
        synth_cognitive_contract: Formatted cognitive contract
        interview_history: Formatted interview transcript

    Returns:
        Formatted system prompt string for chat
    """
    return CHAT_SYSTEM_PROMPT.format(
        synth_name=synth_name,
        synth_idade=synth_idade,
        synth_genero=synth_genero,
        synth_ocupacao=synth_ocupacao,
        synth_escolaridade=synth_escolaridade,
        synth_cidade=synth_cidade,
        synth_estado=synth_estado,
        synth_descricao=synth_descricao,
        synth_interesses=synth_interesses,
        synth_cognitive_contract=synth_cognitive_contract,
        interview_history=interview_history,
    )
