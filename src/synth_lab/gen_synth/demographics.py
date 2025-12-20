"""
Demographics generation module for Synth Lab.

This module generates coherent demographic attributes for synthetic personas,
including gender, family composition, occupation, location, and other IBGE-based
demographic data with logical consistency rules.

Functions:
- generate_coherent_gender(): Generate biological gender and gender identity
- generate_coherent_family(): Generate marital status and family composition
- generate_coherent_occupation(): Generate occupation compatible with education/age
- generate_name(): Generate Brazilian name based on gender identity
- generate_demographics(): Generate complete demographic profile

Sample Input:
    config_data = load_config_data()
    demographics = generate_demographics(config_data)

Expected Output:
    {
        "idade": 32,
        "genero_biologico": "feminino",
        "identidade_genero": "mulher cis",
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


def generate_coherent_gender(ibge_data: dict[str, Any]) -> tuple[str, str]:
    """
    Gera gênero biológico e identidade de gênero de forma coerente.

    A grande maioria da população tem identidade de gênero alinhada com
    o gênero biológico (cisgênero). Pessoas trans e não-binárias são
    geradas de acordo com estimativas populacionais (~1-2%).

    Args:
        ibge_data: Dados IBGE com distribuições demográficas

    Returns:
        tuple[str, str]: (genero_biologico, identidade_genero)
    """
    genero_biologico = weighted_choice(ibge_data["genero_biologico"])

    # 98% são cisgênero
    if random.random() < 0.98:
        if genero_biologico == "feminino":
            identidade_genero = "mulher cis"
        elif genero_biologico == "masculino":
            identidade_genero = "homem cis"
        else:  # intersexo
            identidade_genero = random.choice(["mulher cis", "homem cis", "não-binário"])
    else:
        # 2% são trans ou não-binário
        opcoes_trans = ["mulher trans", "homem trans", "não-binário", "outro"]
        pesos_trans = [0.35, 0.35, 0.25, 0.05]
        identidade_genero = random.choices(opcoes_trans, weights=pesos_trans, k=1)[0]

    return genero_biologico, identidade_genero


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
        o
        for o in ocupacoes
        if escolaridade_compativel(escolaridade, o["escolaridade_minima"])
    ]

    # Excluir categorias incompatíveis com idade
    # Estudante: apenas para menores de 30 (ou até 35 para pós-graduação)
    if idade >= 30:
        ocupacoes_compativeis = [
            o for o in ocupacoes_compativeis if o["categoria"] != "estudante"
        ]

    # Aposentado: apenas para 55+ (algumas aposentadorias precoces)
    if idade < 55:
        ocupacoes_compativeis = [
            o for o in ocupacoes_compativeis if o["categoria"] != "aposentado"
        ]

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
                opcoes_jovem = [
                    o for o in ocupacoes_compativeis if o["categoria"] == "estudante"
                ]
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
    Gera nome brasileiro usando Faker pt_BR baseado no gênero.

    Usa identidade de gênero para determinar o nome, não gênero biológico,
    pois pessoas trans geralmente usam nomes alinhados com sua identidade.

    Args:
        demographics: Dicionário com dados demográficos incluindo identidade_genero

    Returns:
        str: Nome completo brasileiro
    """
    identidade = demographics["identidade_genero"]

    # Determinar se nome deve ser feminino ou masculino
    # Gera nome pelo gênero de identidade
    if identidade in ["mulher cis", "mulher trans"]:
        nome = fake.name_female()
    elif identidade in ["homem cis", "homem trans"]:
        nome = fake.name_male()
    else:
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
        escolaridade = random.choice(
            ["Fundamental incompleto", "Fundamental completo"]
        )
    elif idade < 18:
        escolaridade = random.choice(
            ["Fundamental incompleto", "Fundamental completo", "Médio incompleto"]
        )
    elif idade < 22:
        # Não pode ter pós-graduação
        if escolaridade == "Pós-graduação":
            escolaridade = random.choice(["Superior incompleto", "Superior completo"])

    # Gênero coerente
    genero_biologico, identidade_genero = generate_coherent_gender(ibge_data)

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
        "identidade_genero": identidade_genero,
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

    # Test 1: Generate coherent gender
    total_tests += 1
    try:
        genero_bio, identidade = generate_coherent_gender(config["ibge"])
        assert genero_bio in ["masculino", "feminino", "intersexo"]
        assert identidade in [
            "homem cis",
            "mulher cis",
            "homem trans",
            "mulher trans",
            "não-binário",
            "outro",
        ]
        # Verify coherence for cis people
        if identidade == "mulher cis":
            if genero_bio not in ["feminino", "intersexo"]:
                all_validation_failures.append(
                    f"Gender coherence: mulher cis with genero_biologico={genero_bio}"
                )
        if identidade == "homem cis":
            if genero_bio not in ["masculino", "intersexo"]:
                all_validation_failures.append(
                    f"Gender coherence: homem cis with genero_biologico={genero_bio}"
                )
        print(f"Test 1: generate_coherent_gender() -> ({genero_bio}, {identidade})")
    except Exception as e:
        all_validation_failures.append(f"Test 1 (generate_coherent_gender): {str(e)}")

    # Test 2: Generate coherent family
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
            f"Test 2: generate_coherent_family() -> {estado_civil}, "
            f"{comp_familiar['tipo']}, {comp_familiar['numero_pessoas']} pessoas"
        )
    except Exception as e:
        all_validation_failures.append(f"Test 2 (generate_coherent_family): {str(e)}")

    # Test 3: Generate coherent occupation
    total_tests += 1
    try:
        ocupacao, esc = generate_coherent_occupation(
            config["occupations"], "Superior completo", 30
        )
        assert "nome" in ocupacao
        assert "faixa_salarial" in ocupacao
        assert "escolaridade_minima" in ocupacao
        print(f"Test 3: generate_coherent_occupation() -> {ocupacao['nome']}, esc={esc}")
    except Exception as e:
        all_validation_failures.append(f"Test 3 (generate_coherent_occupation): {str(e)}")

    # Test 4: Generate name
    total_tests += 1
    try:
        test_demo = {"identidade_genero": "mulher cis"}
        nome = generate_name(test_demo)
        assert isinstance(nome, str)
        assert len(nome) > 3
        print(f"Test 4: generate_name() -> {nome}")
    except Exception as e:
        all_validation_failures.append(f"Test 4 (generate_name): {str(e)}")

    # Test 5: Generate complete demographics
    total_tests += 1
    try:
        demo = generate_demographics(config)
        assert "idade" in demo
        assert "genero_biologico" in demo
        assert "identidade_genero" in demo
        assert "localizacao" in demo
        assert "escolaridade" in demo
        assert "renda_mensal" in demo
        assert "ocupacao" in demo
        assert "estado_civil" in demo
        assert "composicao_familiar" in demo
        assert demo["idade"] >= 18
        assert demo["renda_mensal"] >= 0
        print(
            f"Test 5: generate_demographics() -> idade={demo['idade']}, "
            f"ocupacao={demo['ocupacao']}, renda=R${demo['renda_mensal']:.2f}"
        )
    except Exception as e:
        all_validation_failures.append(f"Test 5 (generate_demographics): {str(e)}")

    # Test 6: Batch consistency test
    total_tests += 1
    try:
        batch_errors = []
        for i in range(10):
            demo = generate_demographics(config)
            # Check gender coherence
            if demo["identidade_genero"] == "mulher cis" and demo["genero_biologico"] not in [
                "feminino",
                "intersexo",
            ]:
                batch_errors.append(
                    f"Batch {i}: mulher cis with genero_biologico={demo['genero_biologico']}"
                )
            if demo["identidade_genero"] == "homem cis" and demo["genero_biologico"] not in [
                "masculino",
                "intersexo",
            ]:
                batch_errors.append(
                    f"Batch {i}: homem cis with genero_biologico={demo['genero_biologico']}"
                )
            # Check family coherence
            if demo["composicao_familiar"]["tipo"] == "unipessoal":
                if demo["composicao_familiar"]["numero_pessoas"] != 1:
                    batch_errors.append(
                        f"Batch {i}: unipessoal with {demo['composicao_familiar']['numero_pessoas']} pessoas"
                    )
        if batch_errors:
            all_validation_failures.extend(batch_errors)
        else:
            print("Test 6: Batch of 10 demographics all coherent")
    except Exception as e:
        all_validation_failures.append(f"Test 6 (batch consistency): {str(e)}")

    # Final validation result
    print(f"\n{'='*60}")
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)
