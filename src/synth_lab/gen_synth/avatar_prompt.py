"""
Avatar Prompt Builder - Constrói prompts para geração de avatares via OpenAI API.

Este módulo cria prompts estruturados em português para a API de geração de imagens
da OpenAI, incluindo descrições detalhadas de 9 personas em formato de grid 3x3
com filtros visuais variados.

Dependências: random (stdlib)
Entrada: Lista de 9 dicionários de synth com dados demográficos
Saída: String formatada em português pronta para envio à API OpenAI
"""

import random
from typing import Any

# Filtros visuais disponíveis para os avatares (com probabilidade igual)
VISUAL_FILTERS = [
    "não usar filtro",
    "usar filtro B&W",
    "usar filtro sépia",
    "usar filtro warm",
    "usar filtro cold",
    "usar filtro soft/pastel",
    "usar filtro cinematic/teal & orange",
    "usar filtro vintage film grain",
]

FRAMING_TYPE = [
    # Aberto / contexto (35mm)
    "medium-wide framing, torso fully visible, camera at chest level, 35mm lens.",
    "upper-body framing, arms fully visible, camera at chest level, 35mm lens.",
    "waist-up framing, hands visible, torso fully visible, camera at chest level, 35mm lens.",
    # Padrão seguro (50mm)
    "mid-shot framing, torso fully visible, camera at chest level, 50mm lens.",
    "upper-body framing, arms fully visible, camera at chest level, 50mm lens.",
    # Fechado / retrato (85mm)
    "tight headshot, face centered, 85mm portrait lens.",
]


def assign_random_filters(count: int = 8) -> list[str]:
    """
    Atribui filtros visuais aleatórios para avatares.

    Args:
        count: Número de filtros a gerar (padrão: 9 para grid 3x3)

    Returns:
        list[str]: Lista de filtros selecionados aleatoriamente

    Examples:
        >>> filters = assign_random_filters(9)
        >>> len(filters)
        9
        >>> all(f in VISUAL_FILTERS for f in filters)
        True
    """
    return [random.choice(VISUAL_FILTERS) for _ in range(count)]


def build_synth_description(synth: dict[str, Any]) -> str:
    """
    Constrói descrição detalhada de um synth para o prompt.

    Extrai e formata todos os dados relevantes do synth incluindo:
    - Gênero e idade
    - Ocupação
    - Localização (cidade, estado)
    - Traços de personalidade marcantes
    - Interesses (quando disponíveis)
    - Etnia

    Args:
        synth: Dicionário de synth com dados completos

    Returns:
        str: Descrição formatada do synth

    Examples:
        >>> synth = {
        ...     "id": "test01",
        ...     "descricao": "Homem de 35 anos, engenheiro...",
        ...     "demografia": {"idade": 35, "genero_biologico": "masculino", ...}
        ... }
        >>> desc = build_synth_description(synth)
        >>> "Homem" in desc or "35" in desc
        True
    """
    # Se já existe descrição pronta, usar ela
    if "descricao" in synth and synth["descricao"]:
        return synth["descricao"]

    # Caso contrário, construir a partir dos campos individuais
    demografia = synth.get("demografia", {})
    psicografia = synth.get("psicografia", {})

    # Dados básicos
    idade = demografia.get("idade", "?")
    genero = demografia.get("genero_biologico", "")
    genero_texto = (
        "Homem" if genero == "masculino" else "Mulher" if genero == "feminino" else "Pessoa"
    )
    ocupacao = demografia.get("ocupacao", "profissional")
    etnia = demografia.get("raca_etnia", "")

    # Localização
    localizacao = demografia.get("localizacao", {})
    cidade = localizacao.get("cidade", "")
    estado = localizacao.get("estado", "")
    local_texto = f"mora em {cidade}, {estado}" if cidade and estado else ""

    # Traços de personalidade marcantes (Big Five > 60)
    big_five = psicografia.get("personalidade_big_five", {})
    tracos_marcantes = []
    mapa_tracos = {
        "abertura": "Abertura",
        "conscienciosidade": "Conscienciosidade",
        "extroversao": "Extroversão",
        "amabilidade": "Amabilidade",
        "neuroticismo": "Neuroticismo",
    }
    for traco, nome in mapa_tracos.items():
        valor = big_five.get(traco, 0)
        if valor > 60:
            tracos_marcantes.append(nome)

    tracos_texto = (
        f"Possui traços marcantes de {', '.join(tracos_marcantes)}. " if tracos_marcantes else ""
    )

    # Interesses
    interesses = psicografia.get("interesses", [])
    interesses_texto = f"Interesses: {', '.join(interesses[:3])}. " if interesses else ""

    # Montar descrição
    partes = [f"{genero_texto} de {idade} anos", ocupacao]
    if local_texto:
        partes[1] = f"{ocupacao}, {local_texto}"

    descricao = f"{partes[0]}, {partes[1]}. {tracos_texto}{interesses_texto}etnia {etnia}"
    return descricao.strip()


def assign_random_framing(count: int = 6) -> list[str]:
    return [random.choice(FRAMING_TYPE) for _ in range(count)]


def build_prompt(synths: list[dict[str, Any]]) -> str:
    """
    Constrói prompt completo em português para geração de avatares em grid 3x3.

    Gera um prompt detalhado que instrui a API a criar uma imagem dividida
    em 9 partes iguais (3x3), cada uma com um avatar baseado
    nas descrições dos synths fornecidos.

    Args:
        synths: Lista de exatamente 9 dicionários de synth

    Returns:
        str: Prompt formatado em português pronto para envio à API OpenAI

    Raises:
        ValueError: Se lista não contém exatamente 9 synths

    Examples:
        >>> synth = {
        ...     "id": "abc123",
        ...     "descricao": "Homem de 35 anos, engenheiro...",
        ...     "demografia": {"idade": 35, "genero_biologico": "masculino", ...}
        ... }
        >>> prompt = build_prompt([synth] * 9)
        >>> "9 partes iguais" in prompt
        True
    """
    if len(synths) != 9:
        raise ValueError(f"Esperado exatamente 9 synths, recebido {len(synths)}")

    # Atribuir filtros aleatórios
    filters = assign_random_filters(8)

    framing = assign_random_framing(6)

    # Construir descrições numeradas dos blocos
    descricoes_blocos = "\n".join(
        [
            f"Bloco {i + 1}:\n{framing[i]}\n{build_synth_description(synths[i])}\n{filters[i]}\n"
            for i in range(9)
        ]
    )

    from rich.console import Console

    console = Console()

    framing_texto = ", ".join([f"bloco{i + 1}: {d}" for i, d in enumerate(framing)])
    console.print(framing_texto)

    # Montar prompt completo em português
    prompt = f"""Crie uma imagem dividida em uma grade 3x3, com 9 blocos iguais.
Cada bloco representa uma fotografia independente.
Cada bloco deve respeitar estritamente o enquadramento indicado.
Estilo fotorrealista.

Regras globais de variação visual:
Cada bloco deve ter fundo diferente, coerente com a profissão da pessoa, preferencialmente levemente desfocado (bokeh).
Cores, estampas de roupa e acessórios (óculos, brincos, itens no cabelo, etc.) devem variar entre os blocos.
Ocasionalmente, incluir um elemento visual sutil relacionado à profissão.

{descricoes_blocos}

Restrição adicional:
Não gerar close-ups fora dos blocos explicitamente marcados como headshot.
"""

    return prompt


if __name__ == "__main__":
    """
    Validação do módulo avatar_prompt.py.

    Testa:
    1. Função assign_random_filters() retorna 9 filtros válidos
    2. Função build_prompt() gera prompt válido com 9 synths
    3. Função build_synth_description() gera descrições corretas
    4. Prompt contém todos os elementos esperados em português
    """
    import sys

    from rich.console import Console

    console = Console()
    all_validation_failures = []
    total_tests = 0

    console.print("[bold blue]=== Validação: avatar_prompt.py ===[/bold blue]\n")

    # Test 1: assign_random_filters retorna 9 filtros
    total_tests += 1
    filters = assign_random_filters(9)
    if len(filters) != 9:
        all_validation_failures.append(
            f"assign_random_filters(9): Esperado 9 filtros, obtido {len(filters)}"
        )
    elif not all(f in VISUAL_FILTERS for f in filters):
        all_validation_failures.append(
            f"assign_random_filters(9): Filtros inválidos encontrados: {filters}"
        )
    else:
        console.print(
            f"[green]✓[/green] assign_random_filters(9) retornou {len(filters)} filtros válidos"
        )

    # Test 2: build_synth_description com synth completo
    total_tests += 1
    synth_completo = {
        "id": "test01",
        "descricao": "Homem de 42 anos, entregador, mora em Rio de Janeiro, RJ. etnia asiatico",
        "demografia": {
            "idade": 42,
            "genero_biologico": "masculino",
            "raca_etnia": "asiatico",
            "ocupacao": "entregador",
            "localizacao": {"cidade": "Rio de Janeiro", "estado": "RJ"},
        },
    }
    desc = build_synth_description(synth_completo)
    if "42" not in desc or "entregador" not in desc.lower():
        all_validation_failures.append(
            f"build_synth_description(): Descrição incompleta: {desc[:50]}..."
        )
    else:
        console.print("[green]✓[/green] build_synth_description() gerou descrição válida")

    # Test 3: build_synth_description sem campo descricao (constrói a partir dos campos)
    total_tests += 1
    synth_sem_desc = {
        "id": "test02",
        "demografia": {
            "idade": 35,
            "genero_biologico": "feminino",
            "raca_etnia": "pardo",
            "ocupacao": "professora",
            "localizacao": {"cidade": "Salvador", "estado": "BA"},
        },
        "psicografia": {
            "personalidade_big_five": {
                "abertura": 75,
                "conscienciosidade": 80,
                "extroversao": 45,
                "amabilidade": 50,
                "neuroticismo": 30,
            },
            "interesses": ["leitura", "música", "viagens"],
        },
    }
    desc = build_synth_description(synth_sem_desc)
    if "Mulher" not in desc or "35" not in desc or "Salvador" not in desc:
        all_validation_failures.append(
            f"build_synth_description() (sem descricao): Construção incorreta: {desc[:80]}..."
        )
    else:
        console.print(
            "[green]✓[/green] build_synth_description() constrói descrição a partir de campos"
        )

    # Test 4: build_prompt com 9 synths
    total_tests += 1
    mock_synths = [
        {
            "id": f"test{i:02d}",
            "descricao": f"{'Homem' if i % 2 == 0 else 'Mulher'} de {30 + i} anos, profissional, mora em São Paulo, SP. etnia branco",
            "demografia": {
                "idade": 30 + i,
                "genero_biologico": "masculino" if i % 2 == 0 else "feminino",
                "raca_etnia": "branco",
                "ocupacao": "profissional",
            },
        }
        for i in range(9)
    ]

    try:
        prompt = build_prompt(mock_synths)
        checks = [
            ("9 partes iguais" in prompt, "9 partes iguais"),
            ("3 linhas" in prompt, "3 linhas"),
            ('1. "descricao"' in prompt, "descrição numerada"),
            ("bokeh" in prompt.lower(), "bokeh"),
            ("filtro" in prompt.lower(), "filtro"),
        ]
        failed_checks = [name for passed, name in checks if not passed]
        if failed_checks:
            all_validation_failures.append(f"build_prompt(): Faltam elementos: {failed_checks}")
        else:
            console.print(
                f"[green]✓[/green] build_prompt(9 synths) gerou prompt válido ({len(prompt)} chars)"
            )
            console.print("\n[dim]Preview do prompt:[/dim]")
            console.print(f"[dim]{prompt[:500]}...[/dim]")
    except Exception as e:
        all_validation_failures.append(f"build_prompt(9 synths): Exceção lançada: {e}")

    # Test 5: build_prompt rejeita número errado de synths
    total_tests += 1
    try:
        prompt = build_prompt(mock_synths[:5])
        all_validation_failures.append(
            "build_prompt(5 synths): Esperado ValueError, mas não foi lançada"
        )
    except ValueError as e:
        if "exatamente 9 synths" in str(e).lower():
            console.print(
                "[green]✓[/green] build_prompt rejeita lista com != 9 synths (ValueError)"
            )
        else:
            all_validation_failures.append(
                f"build_prompt(5 synths): Mensagem de erro incorreta: {e}"
            )
    except Exception as e:
        all_validation_failures.append(
            f"build_prompt(5 synths): Tipo de exceção incorreto: {type(e).__name__}"
        )

    # Final validation result
    console.print(f"\n{'=' * 60}")
    if all_validation_failures:
        console.print(
            f"[red]❌ VALIDATION FAILED - {len(all_validation_failures)} de {total_tests} testes falharam:[/red]"
        )
        for failure in all_validation_failures:
            console.print(f"  [red]•[/red] {failure}")
        sys.exit(1)
    else:
        console.print(
            f"[green]✅ VALIDATION PASSED - Todos os {total_tests} testes produziram resultados esperados[/green]"
        )
        console.print("Função validada - testes formais podem ser executados")
        sys.exit(0)
