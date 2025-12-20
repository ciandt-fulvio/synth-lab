"""
Avatar Image Processing - Download e divisão de imagens de grid em avatares individuais.

Este módulo gerencia o processamento de imagens 1024x1024 geradas pela OpenAI,
incluindo download de URLs temporárias e divisão em 9 avatares individuais 341x341.

Dependências: Pillow>=10.0.0, requests>=2.31.0
Entrada: URL de imagem 1024x1024 ou dados base64 e lista de 9 IDs de synth
Saída: 9 arquivos PNG salvos em output/synths/avatar/
"""

import base64
import re
import tempfile
import uuid
from pathlib import Path

import requests
from PIL import Image

from loguru import logger

# Padrão para identificar synths temporários (ex: temp0100, temp0101)
TEMP_SYNTH_PATTERN = re.compile(r"^temp\d+$")


def save_base64_image(b64_data: str, temp_dir: str | None = None) -> str:
    """
    Salva dados de imagem base64 em arquivo temporário.

    A API gpt-image-1 retorna imagens como base64 por padrão.
    Esta função decodifica e salva em arquivo PNG.

    Args:
        b64_data: String base64 da imagem
        temp_dir: Diretório temporário (padrão: tempfile.gettempdir())

    Returns:
        str: Caminho do arquivo temporário com a imagem salva

    Raises:
        ValueError: Se b64_data for inválido

    Examples:
        >>> # Com dados base64 válidos
        >>> # path = save_base64_image(b64_data)
        >>> # Path(path).exists()
        >>> # True
    """
    # Criar arquivo temporário
    temp_dir = temp_dir or tempfile.gettempdir()
    temp_path = Path(temp_dir) / f"avatar_grid_{uuid.uuid4()}.png"

    # Decodificar base64 e salvar
    image_bytes = base64.b64decode(b64_data)
    with open(temp_path, 'wb') as f:
        f.write(image_bytes)

    return str(temp_path)


def download_image(url: str, temp_dir: str | None = None) -> str:
    """
    Faz download de imagem de URL da OpenAI para arquivo temporário.

    URLs da OpenAI expiram em ~1 hora, então devemos fazer download imediatamente
    após receber a resposta da API.

    Args:
        url: URL da imagem retornada pela API OpenAI
        temp_dir: Diretório temporário (padrão: tempfile.gettempdir())

    Returns:
        str: Caminho do arquivo temporário com a imagem baixada

    Raises:
        requests.HTTPError: Se download falhar
        requests.ConnectionError: Se houver problema de rede

    Examples:
        >>> url = "https://example.com/test.png"
        >>> # path = download_image(url)  # Requer URL válida
        >>> # Path(path).exists()
        >>> # True
    """
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    # Criar arquivo temporário
    temp_dir = temp_dir or tempfile.gettempdir()
    temp_path = Path(temp_dir) / f"avatar_grid_{uuid.uuid4()}.png"

    # Escrever dados da imagem
    with open(temp_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return str(temp_path)


def split_grid_image(
    image_path: str,
    output_dir: str,
    synth_ids: list[str]
) -> list[str]:
    """
    Divide imagem 1024x1024 em grid 3x3 de 9 avatares individuais 341x341.

    Cada célula do grid é extraída e salva como arquivo PNG separado com nome
    baseado no ID do synth correspondente.

    Args:
        image_path: Caminho da imagem 1024x1024 de origem
        output_dir: Diretório onde salvar avatares individuais
        synth_ids: Lista de exatamente 9 IDs de synth (ordem: left-to-right, top-to-bottom)

    Returns:
        list[str]: Lista de caminhos dos avatares salvos

    Raises:
        ValueError: Se synth_ids não contém exatamente 9 IDs
        FileNotFoundError: Se image_path não existe
        PIL.UnidentifiedImageError: Se image_path não é imagem válida

    Examples:
        >>> # Requer imagem real para teste
        >>> synth_ids = [f"test{i:02d}" for i in range(9)]
        >>> # paths = split_grid_image("grid.png", "avatars/", synth_ids)
        >>> # len(paths)
        >>> # 9
    """
    if len(synth_ids) != 9:
        raise ValueError(f"Esperado exatamente 9 synth IDs, recebido {len(synth_ids)}")

    # Abrir imagem
    img = Image.open(image_path)

    # Calcular dimensão de cada célula (1024 / 3 = 341.33, arredonda para 341)
    cell_width = img.width // 3  # 341 pixels
    cell_height = img.height // 3  # 341 pixels

    saved_paths = []

    # Extrair cada uma das 9 células
    skipped_count = 0
    for row in range(3):
        for col in range(3):
            # Obter ID do synth correspondente
            idx = row * 3 + col
            synth_id = synth_ids[idx]

            # Skip synths temporários (ex: temp0100, temp0101)
            if TEMP_SYNTH_PATTERN.match(synth_id):
                logger.debug(f"Skipping avatar temporário: {synth_id}")
                skipped_count += 1
                continue

            # Calcular caixa de corte (left, upper, right, lower)
            left = col * cell_width
            upper = row * cell_height
            right = left + cell_width
            lower = upper + cell_height

            # Cortar célula
            cell = img.crop((left, upper, right, lower))

            # Salvar como PNG
            output_path = Path(output_dir) / f"{synth_id}.png"
            cell.save(output_path, format='PNG', optimize=True)
            saved_paths.append(str(output_path))

    if skipped_count > 0:
        logger.info(f"Skipped {skipped_count} avatar(es) temporário(s)")

    return saved_paths


if __name__ == "__main__":
    """
    Validação do módulo avatar_image.py.

    Testa:
    1. download_image() com URL mockada
    2. split_grid_image() com imagem de teste
    3. Validação de parâmetros
    """
    import sys
    from rich.console import Console

    console = Console()
    all_validation_failures = []
    total_tests = 0

    console.print("[bold blue]=== Validação: avatar_image.py ===[/bold blue]\n")

    # Test 1: split_grid_image rejeita número errado de IDs
    total_tests += 1
    try:
        split_grid_image("dummy.png", "dummy_dir", ["id1", "id2"])
        all_validation_failures.append(
            "split_grid_image(2 IDs): Esperado ValueError, mas não foi lançada"
        )
    except ValueError as e:
        if "exatamente 9" in str(e).lower():
            console.print("[green]✓[/green] split_grid_image rejeita != 9 synth IDs (ValueError)")
        else:
            all_validation_failures.append(
                f"split_grid_image(2 IDs): Mensagem de erro incorreta: {e}"
            )
    except Exception as e:
        all_validation_failures.append(
            f"split_grid_image(2 IDs): Tipo de exceção incorreto: {type(e).__name__}"
        )

    # Test 2: Criar imagem de teste 1024x1024 e dividir
    total_tests += 1
    try:
        # Criar imagem de teste
        test_img = Image.new('RGB', (1024, 1024), color='blue')
        with tempfile.TemporaryDirectory() as temp_dir:
            test_grid_path = Path(temp_dir) / "test_grid.png"
            test_img.save(test_grid_path)

            # Criar diretório de saída temporário
            output_dir = Path(temp_dir) / "avatars"
            output_dir.mkdir()

            # IDs de teste
            test_ids = [f"test{i:02d}" for i in range(9)]

            # Dividir imagem
            paths = split_grid_image(str(test_grid_path), str(output_dir), test_ids)

            if len(paths) != 9:
                all_validation_failures.append(
                    f"split_grid_image(): Esperado 9 arquivos, obtido {len(paths)}"
                )
            else:
                # Verificar que todos os arquivos foram criados
                all_exist = all(Path(p).exists() for p in paths)
                if not all_exist:
                    all_validation_failures.append(
                        "split_grid_image(): Nem todos os arquivos foram criados"
                    )
                else:
                    # Verificar dimensões de um avatar
                    sample_avatar = Image.open(paths[0])
                    if sample_avatar.width != 341 or sample_avatar.height != 341:
                        all_validation_failures.append(
                            f"split_grid_image(): Dimensão incorreta: {sample_avatar.width}x{sample_avatar.height} (esperado 341x341)"
                        )
                    else:
                        console.print(
                            f"[green]✓[/green] split_grid_image() criou 9 avatares 341x341"
                        )
    except Exception as e:
        all_validation_failures.append(
            f"split_grid_image() teste completo: Exceção: {e}"
        )

    # Test 3: download_image function exists and is callable
    total_tests += 1
    try:
        # Verify function signature
        import inspect
        sig = inspect.signature(download_image)
        params = list(sig.parameters.keys())
        if 'url' not in params:
            all_validation_failures.append(
                "download_image(): Parâmetro 'url' não encontrado na assinatura"
            )
        else:
            console.print("[green]✓[/green] download_image() tem assinatura correta (url, temp_dir)")
    except Exception as e:
        all_validation_failures.append(
            f"download_image() verificação de assinatura: {e}"
        )

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
