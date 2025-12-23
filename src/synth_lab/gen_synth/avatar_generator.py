"""
Avatar Generator - Orquestra geração de avatares para synths.

Este módulo coordena todo o fluxo de geração de avatares:
- Validação de dados de synths
- Cálculo de número de blocos (User Story 2)
- Chamadas à API OpenAI
- Processamento e salvamento de imagens

Dependências: openai>=2.8.0, rich>=13.0.0, Pillow
Entrada: Lista de synths com dados demográficos
Saída: Arquivos PNG salvos em output/synths/avatar/
"""

import math
import os
import time
from pathlib import Path
from typing import Any

from loguru import logger
from openai import APIConnectionError, APIError, AuthenticationError, OpenAI, RateLimitError
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from synth_lab.gen_synth.avatar_image import save_base64_image, split_grid_image
from synth_lab.gen_synth.avatar_prompt import build_prompt
from synth_lab.infrastructure.phoenix_tracing import get_tracer

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("avatar-generator")

console = Console()

# Configuração de retry com exponential backoff (T043)
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # Segundos base para backoff exponencial
INTER_BLOCK_DELAY = 1.5  # Delay entre blocos para evitar rate limits (T049)


def load_synth_by_id(synth_id: str, synths_file: str | Path | None = None) -> dict[str, Any] | None:
    """
    Carrega dados de um synth por ID do banco de dados SQLite.

    Busca um synth específico pelo ID no banco de dados.
    Útil para gerar avatares de synths existentes (User Story 3).

    Args:
        synth_id: ID do synth a carregar (ex: "syn001")
        synths_file: Deprecated, ignorado (mantido para compatibilidade)

    Returns:
        dict | None: Dados do synth se encontrado, None caso contrário

    Examples:
        >>> synth = load_synth_by_id("syn001")
        >>> synth["id"]
        'syn001'
        >>> load_synth_by_id("nonexistent")
        None
    """
    from synth_lab.gen_synth.storage import get_synth_by_id

    try:
        synth = get_synth_by_id(synth_id)
        if synth:
            logger.debug(f"Synth encontrado: {synth_id}")
        else:
            logger.debug(f"Synth não encontrado: {synth_id}")
        return synth
    except Exception as e:
        logger.error(f"Erro ao carregar synth {synth_id}: {e}")
        return None


def load_synths_by_ids(
    synth_ids: list[str],
    synths_file: str | Path | None = None
) -> list[dict[str, Any]]:
    """
    Carrega múltiplos synths por lista de IDs do banco de dados.

    Carrega dados de vários synths de uma vez, filtrando IDs inexistentes.
    Útil para gerar avatares em lote para synths específicos (User Story 3).

    Args:
        synth_ids: Lista de IDs de synths a carregar (ex: ["syn001", "syn002"])
        synths_file: Deprecated, ignorado (mantido para compatibilidade)

    Returns:
        list[dict]: Lista de synths encontrados (pode ser menor que synth_ids se alguns não existirem)

    Examples:
        >>> synths = load_synths_by_ids(["syn001", "syn002", "syn003"])
        >>> len(synths)
        3
        >>> synths = load_synths_by_ids(["syn001", "nonexistent"])
        >>> len(synths)
        1
    """
    if not synth_ids:
        return []

    loaded_synths = []
    missing_ids = []

    for synth_id in synth_ids:
        synth = load_synth_by_id(synth_id)
        if synth:
            loaded_synths.append(synth)
        else:
            missing_ids.append(synth_id)

    if missing_ids:
        logger.warning(f"IDs não encontrados: {missing_ids}")

    logger.info(f"Carregados {len(loaded_synths)} de {len(synth_ids)} synths")
    return loaded_synths


def find_synths_without_avatars(
    synths_file: str | Path | None = None,
    avatar_dir: str | Path = "output/synths/avatar"
) -> list[dict[str, Any]]:
    """
    Encontra todos os synths que ainda não possuem arquivo de avatar.

    Carrega todos os synths do banco de dados e verifica quais não têm
    arquivo .png correspondente no diretório de avatares.

    Args:
        synths_file: Deprecated, ignorado (mantido para compatibilidade)
        avatar_dir: Diretório onde avatares são salvos

    Returns:
        list[dict]: Lista de synths sem avatar

    Examples:
        >>> synths = find_synths_without_avatars()
        >>> len(synths)  # Número de synths sem avatar
        15
        >>> synths[0]["id"]
        'syn001'
    """
    from synth_lab.gen_synth.storage import load_synths

    avatar_path = Path(avatar_dir)

    # Criar diretório de avatares se não existir
    avatar_path.mkdir(parents=True, exist_ok=True)

    try:
        # Carregar todos os synths do banco
        all_synths = load_synths()

        # Filtrar synths sem avatar
        synths_without_avatars = []
        for synth in all_synths:
            synth_id = synth.get("id")
            if not synth_id:
                continue

            avatar_file = avatar_path / f"{synth_id}.png"
            if not avatar_file.exists():
                synths_without_avatars.append(synth)

        logger.info(
            f"Encontrados {len(synths_without_avatars)} synths sem avatar "
            f"de {len(all_synths)} totais"
        )
        return synths_without_avatars

    except Exception as e:
        logger.error(f"Erro ao buscar synths sem avatar: {e}")
        return []


def calculate_block_count(synth_count: int, blocks: int | None = None) -> int:
    """
    Calcula número de blocos de avatares a gerar.

    Args:
        synth_count: Número de synths disponíveis
        blocks: Número de blocos especificado pelo usuário (sobrescreve cálculo)

    Returns:
        int: Número de blocos a gerar (1 bloco = 9 avatares)

    Raises:
        ValueError: Se blocks for negativo ou zero (quando especificado)

    Examples:
        >>> calculate_block_count(9, None)
        1
        >>> calculate_block_count(10, None)
        2
        >>> calculate_block_count(9, blocks=3)
        3
    """
    # User Story 2: Validação do parâmetro blocks (T030)
    if blocks is not None:
        if blocks <= 0:
            raise ValueError("O parâmetro 'blocks' deve ser um número positivo maior que zero")
        return blocks

    # Cálculo padrão: baseado em synth_count
    if synth_count == 0:
        return 0

    # Arredonda para cima: 10 synths = 2 blocos (9 + 1)
    return math.ceil(synth_count / 9)


def validate_synth_for_avatar(synth: dict[str, Any]) -> bool:
    """
    Valida se synth possui campos obrigatórios para geração de avatar.

    Campos obrigatórios:
    - id (6 caracteres)
    - demografia.idade
    - demografia.genero_biologico
    - demografia.raca_etnia
    - demografia.ocupacao

    Args:
        synth: Dicionário com dados do synth

    Returns:
        bool: True se válido, False caso contrário

    Examples:
        >>> synth = {
        ...     "id": "abc123",
        ...     "demografia": {
        ...         "idade": 35,
        ...         "genero_biologico": "masculino",
        ...         "raca_etnia": "branco",
        ...         "ocupacao": "engenheiro"
        ...     }
        ... }
        >>> validate_synth_for_avatar(synth)
        True
    """
    # Verifica id
    if "id" not in synth or not synth["id"]:
        return False

    # Verifica demografia
    if "demografia" not in synth:
        return False

    demografia = synth["demografia"]

    # Verifica campos obrigatórios
    required_fields = ["idade", "genero_biologico", "raca_etnia", "ocupacao"]
    for field in required_fields:
        if field not in demografia or not demografia[field]:
            return False

    return True


def generate_avatar_block(
    synths: list[dict[str, Any]],
    client: OpenAI,
    avatar_dir: Path,
    block_num: int = 1
) -> list[str]:
    """
    Gera um bloco de 9 avatares via OpenAI API.

    Orquestra o fluxo completo:
    1. Validar synths
    2. Construir prompt
    3. Chamar API OpenAI
    4. Baixar imagem
    5. Dividir em 9 avatares
    6. Salvar arquivos

    Args:
        synths: Lista de exatamente 9 synths
        client: Cliente OpenAI configurado
        avatar_dir: Diretório para salvar avatares
        block_num: Número do bloco (para logging)

    Returns:
        list[str]: Caminhos dos 9 avatares salvos

    Raises:
        ValueError: Se synths inválidos ou != 9
        APIError: Se erro na chamada OpenAI
    """
    if len(synths) != 9:
        raise ValueError(f"Esperado 9 synths, recebido {len(synths)}")

    synth_ids = [s.get("id", "unknown") for s in synths]

    with _tracer.start_as_current_span(
        "generate_avatar_block",
        attributes={
            "block_num": block_num,
            "synth_count": len(synths),
            "synth_ids": ",".join(synth_ids),
        },
    ) as span:
        # Validar todos os synths
        for synth in synths:
            if not validate_synth_for_avatar(synth):
                synth_id = synth.get("id", "unknown")
                logger.warning(f"Synth {synth_id} possui dados incompletos para avatar")
                raise ValueError(f"Synth {synth_id} não possui campos demográficos obrigatórios")

        # Construir prompt
        logger.info(f"Construindo prompt para bloco {block_num}")
        prompt = build_prompt(synths)
        logger.debug(f"Prompt gerado: {prompt}")

        # Chamar API OpenAI com retry e exponential backoff (T043)
        logger.info(f"Chamando OpenAI API para bloco {block_num}")

        response = None
        for attempt in range(MAX_RETRIES):
            try:
                response = client.images.generate(
                    model="gpt-image-1",  # Modelo gpt-image-1 (mini não suporta response_format)
                    prompt=prompt,
                    n=1,
                    size="1024x1024"
                    # Nota: gpt-image-1 retorna b64_json por padrão
                )
                break  # Sucesso, sair do loop

            except RateLimitError as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = BACKOFF_FACTOR ** attempt  # 1s, 2s, 4s
                    logger.warning(f"Rate limit excedido, tentando novamente em {wait_time}s... (tentativa {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Rate limit excedido após {MAX_RETRIES} tentativas: {e}")
                    if span:
                        span.set_attribute("error", f"Rate limit: {e}")
                    raise

            except APIConnectionError as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = BACKOFF_FACTOR ** attempt
                    logger.warning(f"Erro de conexão, tentando novamente em {wait_time}s... (tentativa {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Erro de conexão após {MAX_RETRIES} tentativas: {e}")
                    if span:
                        span.set_attribute("error", f"Connection error: {e}")
                    raise

            except APIError as e:
                # Erros de API geralmente não são recuperáveis, não retentar
                logger.error(f"Erro na API OpenAI: {e}")
                if span:
                    span.set_attribute("error", f"API error: {e}")
                raise

        if response is None:
            raise APIError("Falha ao obter resposta da API após todas as tentativas")

        # Obter dados base64 da imagem (gpt-image-1 retorna b64_json por padrão)
        image_base64 = response.data[0].b64_json
        if image_base64 is None:
            raise APIError("API retornou resposta sem dados de imagem (b64_json é None)")
        logger.info(f"Imagem gerada, base64 length: {len(image_base64)} chars")

        # Salvar imagem base64 em arquivo temporário
        logger.info("Salvando imagem do grid 3x3")
        grid_image_path = save_base64_image(image_base64)
        logger.debug(f"Imagem salva em: {grid_image_path}")

        # Extrair IDs dos synths
        synth_ids_for_split = [synth["id"] for synth in synths]

        # Dividir imagem
        logger.info("Dividindo grid em 9 avatares individuais")
        avatar_paths = split_grid_image(grid_image_path, str(avatar_dir), synth_ids_for_split)

        # Atualizar avatar_path no banco de dados para cada synth
        # Nota: avatar_paths pode ter menos de 9 itens se houver synths temporários
        # Usamos o nome do arquivo para identificar o synth_id correto
        from synth_lab.gen_synth.storage import update_avatar_path

        for avatar_path in avatar_paths:
            # Extrair synth_id do nome do arquivo (ex: "output/synths/avatar/abc123.png" -> "abc123")
            synth_id = Path(avatar_path).stem
            update_avatar_path(synth_id, avatar_path)

        # Limpar arquivo temporário
        Path(grid_image_path).unlink(missing_ok=True)
        logger.debug(f"Arquivo temporário removido: {grid_image_path}")

        logger.info(f"Bloco {block_num} completo: {len(avatar_paths)} avatares gerados")

        if span:
            span.set_attribute("avatars_generated", len(avatar_paths))

        return avatar_paths


def generate_avatars(
    synths: list[dict[str, Any]] | None = None,
    blocks: int | None = None,
    avatar_dir: Path | None = None,
    api_key: str | None = None,
    synth_ids: list[str] | None = None,
    synths_file: str | Path = "output/synths/synths.json"
) -> list[str]:
    """
    Gera avatares para lista de synths.

    User Story 2: Suporta parâmetro 'blocks' para controle de quantidade (T029)
    User Story 3: Suporta carregar synths existentes por ID (T037)

    Args:
        synths: Lista de synths para gerar avatares (ou None se usando synth_ids)
        blocks: Número de blocos a gerar (sobrescreve cálculo automático)
        avatar_dir: Diretório onde salvar avatares (padrão: output/synths/avatar/)
        api_key: Chave API OpenAI (padrão: variável ambiente OPENAI_API_KEY)
        synth_ids: Lista de IDs de synths existentes para carregar (User Story 3)
        synths_file: Caminho para arquivo synths.json (usado com synth_ids)

    Returns:
        list[str]: Lista de caminhos dos avatares gerados

    Raises:
        ValueError: Se parâmetros inválidos ou IDs não encontrados
        AuthenticationError: Se API key inválida
        APIError: Se erro na API OpenAI

    Examples:
        >>> # User Story 1: Gerar para novos synths
        >>> synths = [{"id": "test01", "demografia": {...}}, ...]
        >>> paths = generate_avatars(synths, blocks=2)
        >>> len(paths)
        18  # 2 blocos × 9 avatares

        >>> # User Story 3: Gerar para synths existentes
        >>> paths = generate_avatars(synth_ids=["syn001", "syn002", "syn003"])
        >>> len(paths)
        9  # 1 bloco de 9 avatares
    """
    # User Story 3: Carregar synths por ID se fornecidos (T037, T039)
    if synth_ids is not None:
        if synths is not None:
            raise ValueError("Forneça 'synths' OU 'synth_ids', não ambos")

        # Carregar synths do arquivo
        synths = load_synths_by_ids(synth_ids, synths_file)

        # Validar que todos os IDs foram encontrados (T039)
        if len(synths) < len(synth_ids):
            loaded_ids = {s["id"] for s in synths}
            missing_ids = [sid for sid in synth_ids if sid not in loaded_ids]
            raise ValueError(f"IDs de synth não encontrados: {missing_ids}")

        logger.info(f"Carregados {len(synths)} synths por ID para geração de avatares")

    elif synths is None:
        raise ValueError("Forneça 'synths' ou 'synth_ids'")

    # User Story 2: Cálculo de blocos com suporte a override (T028, T029)
    block_count = calculate_block_count(len(synths), blocks=blocks)

    if block_count == 0:
        console.print("[yellow]Nenhum bloco de avatares a gerar (synth_count=0, blocks=None)[/yellow]")
        return []

    # Configurar diretório de avatares
    if avatar_dir is None:
        from synth_lab.gen_synth.config import SYNTHS_DIR
        avatar_dir = SYNTHS_DIR / "avatar"

    avatar_dir = Path(avatar_dir)
    avatar_dir.mkdir(parents=True, exist_ok=True)

    # User Story 3: Check for existing avatar files and warn user (T038)
    if synth_ids is not None:
        existing_avatars = []
        for synth in synths:
            avatar_file = avatar_dir / f"{synth['id']}.png"
            if avatar_file.exists():
                existing_avatars.append(synth['id'])

        if existing_avatars:
            console.print(f"\n[yellow]⚠️  Aviso: {len(existing_avatars)} avatar(es) já existe(m):[/yellow]")
            for synth_id in existing_avatars[:5]:  # Show first 5
                console.print(f"  - {synth_id}.png")
            if len(existing_avatars) > 5:
                console.print(f"  ... e mais {len(existing_avatars) - 5}")

            # Ask for confirmation
            console.print("\n[bold yellow]Sobrescrever avatares existentes?[/bold yellow]")
            response = input("Digite 'sim' para continuar, ou qualquer outra coisa para cancelar: ")
            if response.lower() not in ['sim', 's', 'yes', 'y']:
                console.print("[red]Geração de avatares cancelada pelo usuário.[/red]")
                return []

            console.print("[green]Continuando com sobrescrita...[/green]\n")

    # Configurar API key
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY não encontrada. "
                "Configure com: export OPENAI_API_KEY='sua-chave-aqui'"
            )

    # Inicializar cliente OpenAI
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        raise AuthenticationError(f"Erro ao inicializar cliente OpenAI: {e}")

    generated_paths = []

    # User Story 2: Progress messages mostram "bloco X de Y" (T031)
    console.print(f"\n[bold blue]Gerando {block_count} bloco(s) de avatares...[/bold blue]")

    for block_num in range(1, block_count + 1):
        # User Story 2: Mensagem de progresso com informação de blocos (T031)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"[cyan]Gerando avatares (bloco {block_num} de {block_count})...[/cyan]",
                total=None
            )

            # Determinar synths para este bloco
            start_idx = (block_num - 1) * 9
            end_idx = start_idx + 9

            # Se não temos synths suficientes, gerar synths adicionais temporários
            if len(synths) < end_idx:
                # Para User Story 2: quando blocks > synth_count, gerar synths temporários
                block_synths = synths[start_idx:] if start_idx < len(synths) else []
                needed = 9 - len(block_synths)
                if needed > 0:
                    logger.info(f"Bloco {block_num}: {len(block_synths)} synths reais + {needed} fallbacks")
                    # Criar synths temporários para completar o bloco
                    for i in range(needed):
                        temp_synth = {
                            "id": f"temp{block_num:02d}{i:02d}",
                            "descricao": f"Pessoa de {25 + i * 5} anos, profissional brasileiro(a). etnia mista",
                            "demografia": {
                                "idade": 25 + i * 5,
                                "genero_biologico": "masculino" if i % 2 == 0 else "feminino",
                                "raca_etnia": ["branco", "pardo", "preto", "asiatico", "indigena"][i % 5],
                                "ocupacao": ["profissional", "estudante", "comerciante", "artista", "servidor público"][i % 5]
                            }
                        }
                        block_synths.append(temp_synth)
            else:
                block_synths = synths[start_idx:end_idx]
                logger.info(f"Bloco {block_num}: {len(block_synths)} synths reais")

            # Log dos synths que serão usados
            for i, s in enumerate(block_synths, 1):
                synth_id = s.get("id", "?")
                descricao = s.get("descricao", "sem descrição")[:50]
                logger.debug(f"  [{i}] {synth_id}: {descricao}...")

            # Gerar bloco de avatares
            try:
                block_paths = generate_avatar_block(
                    block_synths,
                    client,
                    avatar_dir,
                    block_num=block_num
                )
                generated_paths.extend(block_paths)

                progress.update(task, description=f"[green]✓ Bloco {block_num}/{block_count} completo[/green]")
                console.print(
                    f"  [green]✓[/green] Bloco {block_num}/{block_count}: "
                    f"{len(block_paths)} avatares gerados"
                )
            except Exception as e:
                logger.error(f"Erro ao gerar bloco {block_num}: {e}")
                console.print(
                    f"  [red]✗[/red] Bloco {block_num}/{block_count} falhou: {e}"
                )
                raise

            # T049: Adicionar delay entre blocos para evitar rate limits
            if block_num < block_count:
                logger.debug(f"Aguardando {INTER_BLOCK_DELAY}s antes do próximo bloco...")
                time.sleep(INTER_BLOCK_DELAY)

    console.print(f"\n[green]{len(generated_paths)} avatares gerados com sucesso![/green]")
    console.print(f"Avatares salvos em: {avatar_dir}")

    return generated_paths


if __name__ == "__main__":
    """
    Validação do módulo avatar_generator.py.

    Testa:
    1. Função calculate_block_count() com diferentes cenários
    2. Função validate_synth_for_avatar() com dados válidos/inválidos
    3. Validação do parâmetro blocks (User Story 2)
    """
    import sys

    all_validation_failures = []
    total_tests = 0

    console.print("[bold blue]=== Validação: avatar_generator.py ===[/bold blue]\n")

    # Test 1: calculate_block_count - caso exato (9 synths)
    total_tests += 1
    result = calculate_block_count(9, blocks=None)
    expected = 1
    if result != expected:
        all_validation_failures.append(
            f"calculate_block_count(9, None): Esperado {expected}, obtido {result}"
        )
    else:
        console.print("[green]✓[/green] calculate_block_count(9) = 1")

    # Test 2: calculate_block_count - arredonda para cima (10 synths)
    total_tests += 1
    result = calculate_block_count(10, blocks=None)
    expected = 2
    if result != expected:
        all_validation_failures.append(
            f"calculate_block_count(10, None): Esperado {expected}, obtido {result}"
        )
    else:
        console.print("[green]✓[/green] calculate_block_count(10) = 2 (arredonda para cima)")

    # Test 3: calculate_block_count - override com blocks (User Story 2)
    total_tests += 1
    result = calculate_block_count(9, blocks=3)
    expected = 3
    if result != expected:
        all_validation_failures.append(
            f"calculate_block_count(9, blocks=3): Esperado {expected}, obtido {result}"
        )
    else:
        console.print("[green]✓[/green] calculate_block_count(9, blocks=3) = 3 (override)")

    # Test 4: calculate_block_count - validação de blocks negativo (User Story 2)
    total_tests += 1
    try:
        result = calculate_block_count(9, blocks=-1)
        all_validation_failures.append(
            "calculate_block_count(9, blocks=-1): Esperado ValueError, mas não foi lançada"
        )
    except ValueError as e:
        if "positivo" in str(e):
            console.print("[green]✓[/green] calculate_block_count rejeita blocks=-1 (ValueError)")
        else:
            all_validation_failures.append(
                f"calculate_block_count(9, blocks=-1): Mensagem de erro incorreta: {e}"
            )

    # Test 5: validate_synth_for_avatar - synth válido
    total_tests += 1
    valid_synth = {
        "id": "abc123",
        "demografia": {
            "idade": 35,
            "genero_biologico": "masculino",
            "raca_etnia": "branco",
            "ocupacao": "engenheiro"
        }
    }
    result = validate_synth_for_avatar(valid_synth)
    if result is not True:
        all_validation_failures.append(
            f"validate_synth_for_avatar (válido): Esperado True, obtido {result}"
        )
    else:
        console.print("[green]✓[/green] validate_synth_for_avatar aceita synth válido")

    # Test 6: validate_synth_for_avatar - synth sem id
    total_tests += 1
    invalid_synth = {
        "demografia": {
            "idade": 35,
            "genero_biologico": "masculino",
            "raca_etnia": "branco",
            "ocupacao": "engenheiro"
        }
    }
    result = validate_synth_for_avatar(invalid_synth)
    if result is not False:
        all_validation_failures.append(
            f"validate_synth_for_avatar (sem id): Esperado False, obtido {result}"
        )
    else:
        console.print("[green]✓[/green] validate_synth_for_avatar rejeita synth sem id")

    # Test 7: validate_synth_for_avatar - synth sem idade
    total_tests += 1
    invalid_synth_2 = {
        "id": "abc123",
        "demografia": {
            "genero_biologico": "masculino",
            "raca_etnia": "branco",
            "ocupacao": "engenheiro"
        }
    }
    result = validate_synth_for_avatar(invalid_synth_2)
    if result is not False:
        all_validation_failures.append(
            f"validate_synth_for_avatar (sem idade): Esperado False, obtido {result}"
        )
    else:
        console.print("[green]✓[/green] validate_synth_for_avatar rejeita synth sem idade")

    # Final validation result
    console.print(f"\n{'='*60}")
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
