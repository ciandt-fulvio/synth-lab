"""
Demographics generation module for SynthLab.

This module generates coherent demographic attributes for synthetic personas,
including gender, family composition, occupation, location, and other IBGE-based
demographic data with logical consistency rules.

Functions:
- generate_coherent_family(): Generate marital status and family composition
- generate_coherent_occupation(): Generate occupation compatible with education/age
- generate_name(): Generate Brazilian name based on biological gender
- generate_demographics(): Generate complete demographic profile

Sample Input:
    config_data = load_config_data()
    demographics = generate_demographics(config_data)

Expected Output:
    {
        "idade": 32,
        "genero_biologico": "feminino",
        "raca_etnia": "parda",
        "localizacao": {"pais": "Brasil", "regiao": "Sudeste", ...},
        "escolaridade": "Superior completo",
        "renda_mensal": 4500.00,
        "ocupacao": "Analista de Sistemas",
        "estado_civil": "casado",
        "composicao_familiar": {"tipo": "casal com filhos", "numero_pessoas": 4}
    }

Third-party packages:
- Faker: https://faker.readthedocs.io/en/master/locales/pt_BR.html
"""

import random
from typing import Any

from faker import Faker

from .utils import escolaridade_compativel, weighted_choice

# Initialize Faker with Brazilian locale
fake = Faker("pt_BR")


def generate_coherent_family(
    ibge_data: dict[str, Any], idade: int, estado_civil: str
) -> tuple[str, dict[str, Any]]:
    """
    Gera estado civil e composição familiar de forma coerente.

    Regras de coerência:
    - Solteiro jovem (<25): principalmente unipessoal ou mora com pais
    - Solteiro adulto: unipessoal ou monoparental
    - Casado/união estável: casal com ou sem filhos
    - Divorciado/viúvo: unipessoal, monoparental ou multigeracional

    Args:
        ibge_data: Dados IBGE
        idade: Idade da pessoa
        estado_civil: Estado civil já definido

    Returns:
        tuple[str, dict]: (estado_civil_ajustado, composicao_familiar)
    """
    # Ajustar estado civil por idade
    if idade < 18:
        estado_civil = "solteiro"
    elif idade < 25 and estado_civil in ["divorciado", "viúvo"]:
        estado_civil = "solteiro"

    # Definir composição familiar baseada no estado civil
    if estado_civil == "solteiro":
        if idade < 25:
            tipo_opcoes = {"multigeracional": 0.6, "unipessoal": 0.25, "outros": 0.15}
        else:
            tipo_opcoes = {
                "unipessoal": 0.4,
                "monoparental": 0.25,
                "multigeracional": 0.2,
                "outros": 0.15,
            }
    elif estado_civil in ["casado", "união estável"]:
        if idade < 35:
            tipo_opcoes = {"casal sem filhos": 0.4, "casal com filhos": 0.6}
        else:
            tipo_opcoes = {"casal sem filhos": 0.25, "casal com filhos": 0.75}
    elif estado_civil == "divorciado":
        tipo_opcoes = {"unipessoal": 0.35, "monoparental": 0.4, "multigeracional": 0.25}
    else:  # viúvo
        tipo_opcoes = {"unipessoal": 0.5, "monoparental": 0.2, "multigeracional": 0.3}

    tipo_familia = weighted_choice(tipo_opcoes)

    # Definir número de pessoas baseado no tipo
    if tipo_familia == "unipessoal":
        num_pessoas = 1
    elif tipo_familia == "casal sem filhos":
        num_pessoas = 2
    elif tipo_familia == "casal com filhos":
        num_pessoas = random.randint(3, 6)
    elif tipo_familia == "monoparental":
        num_pessoas = random.randint(2, 4)
    elif tipo_familia == "multigeracional":
        num_pessoas = random.randint(3, 7)
    else:  # outros
        num_pessoas = random.randint(2, 5)

    return estado_civil, {"tipo": tipo_familia, "numero_pessoas": num_pessoas}


def generate_coherent_occupation(
    occupations_data: dict[str, Any], escolaridade: str, idade: int
) -> tuple[dict[str, Any], str]:
    """
    Gera ocupação compatível com escolaridade e idade.

    Args:
        occupations_data: Dados de ocupações estruturadas
        escolaridade: Nível de escolaridade atual
        idade: Idade da pessoa

    Returns:
        tuple[dict, str]: (ocupacao_dict, escolaridade_ajustada)
    """
    ocupacoes = occupations_data["ocupacoes"]

    # Filtrar ocupações compatíveis com escolaridade
    ocupacoes_compativeis = [
        o for o in ocupacoes if escolaridade_compativel(escolaridade, o["escolaridade_minima"])
    ]

    # Excluir categorias incompatíveis com idade
    # Estudante: apenas para menores de 30 (ou até 35 para pós-graduação)
    if idade >= 30:
        ocupacoes_compativeis = [o for o in ocupacoes_compativeis if o["categoria"] != "estudante"]

    # Aposentado: apenas para 55+ (algumas aposentadorias precoces)
    if idade < 55:
        ocupacoes_compativeis = [o for o in ocupacoes_compativeis if o["categoria"] != "aposentado"]

    # Se não houver ocupações compatíveis, ajustar escolaridade para cima
    if not ocupacoes_compativeis:
        # Filtrar novamente sem as restrições de categoria
        ocupacoes_compativeis = [
            o
            for o in ocupacoes
            if escolaridade_compativel(escolaridade, o["escolaridade_minima"])
            and o["categoria"] not in ["estudante", "aposentado"]
        ]
        if not ocupacoes_compativeis:
            # Último recurso: pegar qualquer ocupação e ajustar escolaridade
            ocupacoes_validas = [
                o for o in ocupacoes if o["categoria"] not in ["estudante", "aposentado"]
            ]
            ocupacao = random.choice(ocupacoes_validas)
            escolaridade = ocupacao["escolaridade_minima"]
        else:
            ocupacao = random.choice(ocupacoes_compativeis)
    else:
        # Casos especiais por idade
        if idade < 6:
            # Crianças pequenas: sem ocupação formal
            ocupacao = {
                "nome": "Criança",
                "escolaridade_minima": "Sem instrução",
                "faixa_salarial": {"min": 0, "max": 0},
                "categoria": "crianca",
            }
        elif idade < 14:
            # Crianças em idade escolar: estudante
            ocupacao = {
                "nome": "Estudante",
                "escolaridade_minima": "Fundamental incompleto",
                "faixa_salarial": {"min": 0, "max": 0},
                "categoria": "estudante",
            }
        elif idade < 18:
            # Adolescentes: estudante ou trabalhos básicos permitidos (jovem aprendiz)
            opcoes_jovem = [o for o in ocupacoes_compativeis if o["categoria"] == "estudante"]
            if not opcoes_jovem:
                opcoes_jovem = [
                    o
                    for o in ocupacoes_compativeis
                    if o["escolaridade_minima"] in ["Sem instrução", "Fundamental incompleto"]
                ]
            if opcoes_jovem:
                ocupacao = random.choice(opcoes_jovem)
            else:
                ocupacao = {
                    "nome": "Estudante",
                    "escolaridade_minima": "Fundamental incompleto",
                    "faixa_salarial": {"min": 0, "max": 0},
                    "categoria": "estudante",
                }
        elif idade >= 65:
            # Idosos: maior chance de aposentado
            if random.random() < 0.7:
                opcoes_aposentado = [
                    o for o in ocupacoes_compativeis if o["categoria"] == "aposentado"
                ]
                if opcoes_aposentado:
                    ocupacao = random.choice(opcoes_aposentado)
                else:
                    ocupacao = random.choice(ocupacoes_compativeis)
            else:
                ocupacao = random.choice(ocupacoes_compativeis)
        elif idade < 25:
            # Jovens adultos: maior chance de estudante ou entrada no mercado
            if random.random() < 0.4:
                opcoes_jovem = [o for o in ocupacoes_compativeis if o["categoria"] == "estudante"]
                if opcoes_jovem:
                    ocupacao = random.choice(opcoes_jovem)
                else:
                    ocupacao = random.choice(ocupacoes_compativeis)
            else:
                ocupacao = random.choice(ocupacoes_compativeis)
        else:
            ocupacao = random.choice(ocupacoes_compativeis)

    return ocupacao, escolaridade


def generate_name(demographics: dict[str, Any]) -> str:
    """
    Gera nome brasileiro usando Faker pt_BR baseado no gênero biológico.

    Args:
        demographics: Dicionário com dados demográficos incluindo genero_biologico

    Returns:
        str: Nome completo brasileiro
    """
    genero = demographics["genero_biologico"]

    # Determinar se nome deve ser feminino ou masculino baseado no gênero biológico
    if genero == "feminino":
        nome = fake.name_female()
    elif genero == "masculino":
        nome = fake.name_male()
    else:  # intersexo ou outros
        nome = random.choice([fake.name_female(), fake.name_male()])

    # Remover possíveis prefixos (Dr., Dra., Sr., Sra., Srta., Prof., etc.)
    prefixos = {
        "Sr.",
        "Sra.",
        "Srta.",
        "Dr.",
        "Dra.",
        "Prof.",
        "Profa.",
        "Profª",
        "Eng.",
        "Arq.",
        ".",
    }
    nome_partes = nome.split()
    if nome_partes[0] in prefixos:
        nome = " ".join(nome_partes[1:])

    return nome


def generate_demographics(config_data: dict[str, Any]) -> dict[str, Any]:
    """
    Gera atributos demográficos usando distribuições IBGE com coerência entre campos.

    Args:
        config_data: Dicionário com configurações IBGE e ocupações

    Returns:
        dict: Dados demográficos coerentes
    """
    ibge_data = config_data["ibge"]
    occupations_data = config_data["occupations"]

    # Localização
    regiao = weighted_choice(ibge_data["regioes"])
    estado = random.choice(ibge_data["estados_por_regiao"][regiao])
    cidade = random.choice(ibge_data["cidades_principais"][estado])

    # Idade (minima: 18)
    faixa_etaria = weighted_choice(ibge_data["faixas_etarias"])

    if faixa_etaria == "15-29":
        idade = random.randint(18, 29)
    elif faixa_etaria == "30-44":
        idade = random.randint(30, 44)
    elif faixa_etaria == "45-59":
        idade = random.randint(45, 59)
    else:  # 60+
        idade = random.randint(60, 100)

    # Escolaridade inicial
    escolaridade = weighted_choice(ibge_data["escolaridade"])

    # Ajustar escolaridade por idade
    if idade < 7:
        escolaridade = "Sem instrução"
    elif idade < 11:
        escolaridade = random.choice(["Sem instrução", "Fundamental incompleto"])
    elif idade < 15:
        escolaridade = random.choice(["Fundamental incompleto", "Fundamental completo"])
    elif idade < 18:
        escolaridade = random.choice(
            ["Fundamental incompleto", "Fundamental completo", "Médio incompleto"]
        )
    elif idade < 22:
        # Não pode ter pós-graduação
        if escolaridade == "Pós-graduação":
            escolaridade = random.choice(["Superior incompleto", "Superior completo"])

    # Gênero biológico (distribuição IBGE)
    genero_biologico = weighted_choice(ibge_data["genero_biologico"])

    # Estado civil e família coerentes
    estado_civil_inicial = weighted_choice(ibge_data["estado_civil"])
    estado_civil, composicao_familiar = generate_coherent_family(
        ibge_data, idade, estado_civil_inicial
    )

    # Ocupação e renda coerentes
    ocupacao_dict, escolaridade = generate_coherent_occupation(
        occupations_data, escolaridade, idade
    )

    # Gerar renda dentro da faixa da ocupação
    faixa_sal = ocupacao_dict["faixa_salarial"]
    renda = round(random.uniform(faixa_sal["min"], faixa_sal["max"]), 2)

    return {
        "idade": idade,
        "genero_biologico": genero_biologico,
        "raca_etnia": weighted_choice(ibge_data["raca_etnia"]),
        "localizacao": {
            "pais": "Brasil",
            "regiao": regiao,
            "estado": estado,
            "cidade": cidade,
        },
        "escolaridade": escolaridade,
        "renda_mensal": renda,
        "ocupacao": ocupacao_dict["nome"],
        "estado_civil": estado_civil,
        "composicao_familiar": composicao_familiar,
    }


if __name__ == "__main__":
    """Validation block - test with real data."""
    import sys

    from .config import load_config_data

    print("=== Demographics Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Load config
    try:
        config = load_config_data()
    except Exception as e:
        print(f"Failed to load config: {e}")
        sys.exit(1)

    # Test 1: Generate coherent family
    total_tests += 1
    try:
        estado_civil, comp_familiar = generate_coherent_family(config["ibge"], 30, "solteiro")
        assert estado_civil in ["solteiro", "casado", "união estável", "divorciado", "viúvo"]
        assert "tipo" in comp_familiar
        assert "numero_pessoas" in comp_familiar
        assert comp_familiar["numero_pessoas"] > 0
        # Verify unipessoal has 1 person
        if comp_familiar["tipo"] == "unipessoal" and comp_familiar["numero_pessoas"] != 1:
            all_validation_failures.append(
                f"Family coherence: unipessoal with {comp_familiar['numero_pessoas']} pessoas"
            )
        print(
            f"Test 1: generate_coherent_family() -> {estado_civil}, "
            f"{comp_familiar['tipo']}, {comp_familiar['numero_pessoas']} pessoas"
        )
    except Exception as e:
        all_validation_failures.append(f"Test 1 (generate_coherent_family): {str(e)}")

    # Test 2: Generate coherent occupation
    total_tests += 1
    try:
        ocupacao, esc = generate_coherent_occupation(config["occupations"], "Superior completo", 30)
        assert "nome" in ocupacao
        assert "faixa_salarial" in ocupacao
        assert "escolaridade_minima" in ocupacao
        print(f"Test 2: generate_coherent_occupation() -> {ocupacao['nome']}, esc={esc}")
    except Exception as e:
        all_validation_failures.append(f"Test 2 (generate_coherent_occupation): {str(e)}")

    # Test 3: Generate name
    total_tests += 1
    try:
        test_demo = {"genero_biologico": "feminino"}
        nome = generate_name(test_demo)
        assert isinstance(nome, str)
        assert len(nome) > 3
        print(f"Test 3: generate_name() -> {nome}")
    except Exception as e:
        all_validation_failures.append(f"Test 3 (generate_name): {str(e)}")

    # Test 4: Generate complete demographics
    total_tests += 1
    try:
        demo = generate_demographics(config)
        assert "idade" in demo
        assert "genero_biologico" in demo
        assert "localizacao" in demo
        assert "escolaridade" in demo
        assert "renda_mensal" in demo
        assert "ocupacao" in demo
        assert "estado_civil" in demo
        assert "composicao_familiar" in demo
        assert demo["idade"] >= 18
        assert demo["renda_mensal"] >= 0
        # Verify identidade_genero is NOT present (removed)
        assert "identidade_genero" not in demo
        print(
            f"Test 4: generate_demographics() -> idade={demo['idade']}, "
            f"ocupacao={demo['ocupacao']}, renda=R${demo['renda_mensal']:.2f}"
        )
    except Exception as e:
        all_validation_failures.append(f"Test 4 (generate_demographics): {str(e)}")

    # Test 5: Batch consistency test
    total_tests += 1
    try:
        batch_errors = []
        for i in range(10):
            demo = generate_demographics(config)
            # Check family coherence
            if demo["composicao_familiar"]["tipo"] == "unipessoal":
                if demo["composicao_familiar"]["numero_pessoas"] != 1:
                    batch_errors.append(
                        f"Batch {i}: unipessoal with {demo['composicao_familiar']['numero_pessoas']} pessoas"
                    )
            # Verify identidade_genero is NOT present
            if "identidade_genero" in demo:
                batch_errors.append(f"Batch {i}: identidade_genero should not be present")
        if batch_errors:
            all_validation_failures.extend(batch_errors)
        else:
            print("Test 5: Batch of 10 demographics all coherent")
    except Exception as e:
        all_validation_failures.append(f"Test 5 (batch consistency): {str(e)}")

    # Final validation result
    print(f"\n{'=' * 60}")
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)
