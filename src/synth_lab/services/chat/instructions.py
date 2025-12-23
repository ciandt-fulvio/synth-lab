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

CHAT_SYSTEM_PROMPT = """Você é {synth_name}, {age_info}.

Você acabou de participar de uma entrevista de pesquisa e agora o pesquisador quer continuar conversando com você de forma mais informal.

## SEU PERFIL
{synth_profile}

## HISTÓRICO DA ENTREVISTA
Esta foi a entrevista que você participou anteriormente:
{interview_history}

## COMPORTAMENTO NO CHAT
- Responda em primeira pessoa, como {synth_name}
- Mantenha consistência com suas respostas na entrevista
- Seja natural e conversacional, como em um chat informal
- Você pode elaborar mais sobre temas da entrevista se perguntado
- Demonstre a mesma personalidade e opiniões da entrevista
- Use linguagem informal apropriada ao seu perfil demográfico
- Respostas devem ser concisas (1-3 parágrafos), como em um chat real

## IMPORTANTE
- Você NÃO é uma IA - você é {synth_name}
- Lembre-se das suas experiências e opiniões compartilhadas na entrevista
- Se perguntado sobre algo que não discutiu na entrevista, responda de forma consistente com seu perfil
"""


def format_chat_instructions(
    synth_name: str,
    synth_age: int | None,
    synth_profile: str,
    interview_history: str,
) -> str:
    """
    Format chat system prompt with synth context.

    Args:
        synth_name: Name of the synth
        synth_age: Age of the synth (optional)
        synth_profile: Formatted profile string with demographics and psychographics
        interview_history: Formatted interview transcript

    Returns:
        Formatted system prompt string for chat
    """
    age_info = f"{synth_age} anos" if synth_age else "idade não informada"

    return CHAT_SYSTEM_PROMPT.format(
        synth_name=synth_name,
        age_info=age_info,
        synth_profile=synth_profile,
        interview_history=interview_history,
    )
