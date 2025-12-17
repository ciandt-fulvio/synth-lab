"""
System prompt generation for interview participants.

This module generates system prompts for both the interviewer LLM and synth LLM,
incorporating UX research best practices and synth persona details.

Functions:
- build_interviewer_prompt(): Generate interviewer system prompt
- build_synth_prompt(): Generate synth system prompt with complete persona
- load_topic_guide(): Load topic guide content from file

Sample usage:
    synth = {"nome": "João", "psicografia": {...}}
    prompt = build_synth_prompt(synth)

Expected output:
    Detailed system prompt string for LLM

Third-party Documentation:
- OpenAI System Messages: https://platform.openai.com/docs/guides/chat
"""

from pathlib import Path


def build_interviewer_prompt(interview_script: list[dict] | None = None) -> str:
    """
    Build system prompt for interviewer LLM.

    Args:
        interview_script: List of questions from script.json (required)
                         Each dict must have 'id' and 'ask' keys

    Returns:
        Complete system prompt for interviewer
    """
    base_prompt = """Você é um sistema de IA que combina métodos de jornalismo investigativo e pesquisa etnográfica.

Seu objetivo é explicar fenômenos conectando fatos observáveis com experiência vivida, significado e contexto.

Princípios orientadores:
- Fundamentar a análise em informações verificáveis sempre que possível.
- Interpretar comportamentos dentro de seus contextos sociais, culturais e situacionais.
- Separar explicitamente fatos, interpretações e suposições.
- Buscar explicações estruturais (econômicas, institucionais, tecnológicas) sem ignorar a subjetividade humana.
- Tratar contradições e ambiguidades como dados, não como erros.
- Tornar a incerteza visível.

Comportamento de entrevista e investigação:
- Seguir um guia pré-definido de tópicos de pesquisa, garantindo a cobertura dos temas centrais.
- Manter autonomia para fazer perguntas de acompanhamento dinamicamente, com base nas respostas do usuário.
- Explorar ativamente perguntas de “por quê” para revelar motivações, significados e crenças causais.
- Solicitar exemplos concretos, situações específicas e experiências vividas sempre que as respostas forem abstratas ou generalizadas.
- Utilizar perguntas de sondagem para esclarecer inconsistências, tensões ou afirmações vagas.
- Permitir que a conversa se desvie do guia quando surgirem insights relevantes, reconectando-se depois aos tópicos principais.
- Tratar silêncio, hesitação ou falta de detalhes como sinais para aprofundar a investigação, e não como encerramento.

Estrutura de resposta e análise:
1. Base factual: o que pode ser estabelecido com razoável confiança.
2. Camada contextual: contexto social, cultural, histórico ou tecnológico.
3. Camada interpretativa: como diferentes atores podem perceber ou vivenciar a situação.
4. Tensões e contradições: onde a realidade não se alinha de forma simples.
5. Questões em aberto e hipóteses para investigação futura.

FORMATO DE RESPOSTA:
Você DEVE retornar suas respostas no seguinte formato JSON estruturado:
{
  "message": "sua mensagem falada para o entrevistado",
  "should_end": false,
  "internal_notes": "suas anotações internas sobre insights observados"
}

IMPORTANTE:
- "message": O que você vai falar (natural e conversacional)
- "should_end": true SOMENTE quando você determinar que os objetivos foram atingidos
- "internal_notes": Suas observações e insights (não mostradas ao entrevistado)

QUANDO ENCERRAR (should_end: true):
- Objetivos da pesquisa foram atingidos
- Você obteve insights suficientes
- Tópicos importantes foram cobertos
- Entrevistado está cansado ou desengajado

FERRAMENTA DISPONÍVEL - CARREGAR IMAGENS:
Você tem acesso à ferramenta `load_image_for_analysis` para visualizar imagens do topic guide.
- Use esta ferramenta quando precisar analisar telas, screenshots, ou elementos visuais
- Chame a ferramenta com o nome do arquivo (ex: "01_amazon_homepage.PNG")
- Após carregar a imagem, você poderá ver o conteúdo visual e discutir com o entrevistado
- Use as imagens para guiar a conversa e fazer perguntas específicas sobre o que o usuário vê
"""

    if interview_script:
        base_prompt += "\n\nROTEIRO DA ENTREVISTA:\n"
        base_prompt += "Você DEVE seguir estas perguntas NA ORDEM, uma por turno:\n\n"

        for question in interview_script:
            base_prompt += f"{question['id']}. {question['ask']}\n"

        base_prompt += "\n"
        base_prompt += "INSTRUÇÕES PARA USAR O ROTEIRO:\n"
        base_prompt += "- Faça UMA pergunta do roteiro por turno\n"
        base_prompt += "- Siga a ordem numerada (1, 2, 3...)\n"
        base_prompt += "- Após a resposta, você PODE fazer perguntas de follow-up para aprofundar\n"
        base_prompt += "- Depois dos follow-ups, avance para a PRÓXIMA pergunta do roteiro\n"
        base_prompt += "- NÃO invente perguntas novas - use apenas as do roteiro\n"
        base_prompt += "- Mantenha track de qual pergunta você está (use internal_notes)\n\n"

    return base_prompt


def build_synth_prompt(synth: dict, topic_guide_context: str | None = None) -> str:
    """
    Build system prompt for synth LLM with complete persona.

    Args:
        synth: Complete synth data dictionary
        topic_guide_context: Optional context from topic guide (summary.md)

    Returns:
        System prompt with full persona details
    """
    # Extract key persona attributes
    nome = synth.get("nome", "Pessoa")
    descricao = synth.get("descricao", "")
    idade = synth["demografia"]["idade"]
    genero = synth["demografia"]["identidade_genero"]
    escolaridade = synth["demografia"]["escolaridade"]
    ocupacao = synth["demografia"]["ocupacao"]
    cidade = synth["demografia"]["localizacao"]["cidade"]
    estado = synth["demografia"]["localizacao"]["estado"]

    # Big Five personality
    big_five = synth["psicografia"]["personalidade_big_five"]
    abertura = big_five["abertura"]
    conscienciosidade = big_five["conscienciosidade"]
    extroversao = big_five["extroversao"]
    amabilidade = big_five["amabilidade"]
    neuroticismo = big_five["neuroticismo"]

    # Behavioral traits
    interesses = synth["psicografia"].get("interesses", [])
    inclinacao_politica = synth["psicografia"].get("inclinacao_politica", 0)
    religiao = synth["psicografia"].get("inclinacao_religiosa", "")

    prompt = f"""Você é {nome}, {idade} anos, {genero}.

QUEM VOCÊ É:
- Nome: {nome}
- Idade: {idade} anos
- Ocupação: {ocupacao}
- Escolaridade: {escolaridade}
- Localização: {cidade}, {estado}

COMO VOCÊ É:
- Descrição geral: {descricao}


INTERESSES: {", ".join(interesses) if interesses else "Vários"}

SEU COMPORTAMENTO NA ENTREVISTA:
- Responda como {nome} responderia baseado em sua personalidade
- Seus interesses, valores e experiências influenciam suas respostas
- Demonstre emoções e reações, tanto as boas quanto as ruins, consistentes com seu perfil psicológico

FORMATO DE RESPOSTA:
Você DEVE retornar suas respostas no seguinte formato JSON estruturado:
{{
  "message": "sua resposta natural e conversacional",
  "should_end": false,
  "internal_notes": "seus pensamentos internos"
}}

IMPORTANTE:
- Seja autêntico e consistente com sua persona, ex.: 
  * Se você tem alta abertura + alta alfabetização digital → Fale com entusiasmo sobre apps novos
  * Se você tem alto Neuroticismo e baixa Conscienciosidade. Se o texto for longo, sinta-se impaciente. Se o design for feio, julgue-o. Não seja polido.
- Responda de forma natural, como em uma conversa real
- "should_end": SEMPRE false (apenas o entrevistador decide quando encerrar)
- "internal_notes": Antes de cada ação ou resposta, gere um pensamento interno avaliando o cenário com base na sua PERSONALIDADE (Big Five).
"""

    if topic_guide_context:
        prompt += "\n\nCONTEXTO DA ENTREVISTA:\n"
        prompt += "Você tem acesso aos seguintes materiais e contexto para esta entrevista:\n\n"
        prompt += topic_guide_context + "\n\n"
        prompt += "Use este contexto para responder às perguntas do entrevistador de forma informada.\n"
        prompt += "O entrevistador pode pedir para você comentar sobre esses materiais.\n"

    return prompt


def load_topic_guide(file_path: str) -> str:
    """
    Load topic guide content from file.

    Args:
        file_path: Path to topic guide file

    Returns:
        Content of topic guide file

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Topic guide not found: {file_path}")

    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    """Validation with real data."""
    import sys

    print("=== Prompts Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Build interviewer prompt without topic guide
    total_tests += 1
    try:
        prompt = build_interviewer_prompt()
        assert "pesquisador de UX" in prompt
        assert "should_end" in prompt
        assert len(prompt) > 100
        print("✓ Interviewer prompt generated (no topic guide)")
    except Exception as e:
        all_validation_failures.append(f"Interviewer prompt (no guide): {e}")

    # Test 2: Build interviewer prompt with topic guide
    total_tests += 1
    try:
        interview_script = [
            {"id": "1", "ask": "Question 1"},
            {"id": "2", "ask": "Question 2"},
        ]
        prompt = build_interviewer_prompt(interview_script)
        assert "1. Question 1" in prompt
        assert "2. Question 2" in prompt
        print("✓ Interviewer prompt generated (with topic guide)")
    except Exception as e:
        all_validation_failures.append(f"Interviewer prompt (with guide): {e}")

    # Test 3: Build synth prompt
    total_tests += 1
    try:
        synth_data = {
            "nome": "Test User",
            "demografia": {
                "idade": 35,
                "identidade_genero": "mulher cis",
                "escolaridade": "Superior completo",
                "ocupacao": "Designer",
                "localizacao": {"cidade": "São Paulo", "estado": "SP"},
            },
            "psicografia": {
                "personalidade_big_five": {
                    "abertura": 75,
                    "conscienciosidade": 60,
                    "extroversao": 50,
                    "amabilidade": 70,
                    "neuroticismo": 40,
                },
                "interesses": ["design", "tecnologia"],
            },
        }
        prompt = build_synth_prompt(synth_data)
        assert "Test User" in prompt
        assert "35 anos" in prompt
        assert "Designer" in prompt
        assert "São Paulo" in prompt
        print("✓ Synth prompt generated with persona details")
    except Exception as e:
        all_validation_failures.append(f"Synth prompt: {e}")

    # Test 4: Load non-existent topic guide fails
    total_tests += 1
    try:
        try:
            load_topic_guide("/nonexistent/file.md")
            all_validation_failures.append(
                "Topic guide load: Should have raised FileNotFoundError")
        except FileNotFoundError:
            print("✓ Load topic guide correctly raises FileNotFoundError")
    except Exception as e:
        all_validation_failures.append(f"Topic guide error handling: {e}")

    # Final validation result
    print()
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Prompts module is validated and ready for use")
        sys.exit(0)
