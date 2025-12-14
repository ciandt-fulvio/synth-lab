#!/usr/bin/env python3
"""
Gerador de Synths (Personas Sintéticas Brasileiras).

Este script gera personas sintéticas com atributos demográficos, psicográficos,
comportamentais e cognitivos realistas baseados em dados do IBGE e pesquisas verificadas.

Fontes:
- IBGE Censo 2022, PNAD 2022/2023, PNS 2019
- TIC Domicílios 2023 (CETIC.br)
- DataSenado 2024
- Pesquisa TIM + USP

Faker pt_BR: https://faker.readthedocs.io/en/master/locales/pt_BR.html
"""

import json
import random
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from faker import Faker
import jsonschema
from jsonschema import Draft202012Validator

# Configuration paths
DATA_DIR = Path(__file__).parent.parent / "data"
CONFIG_DIR = DATA_DIR / "config"
SCHEMAS_DIR = DATA_DIR / "schemas"
SYNTHS_DIR = DATA_DIR / "synths"
SCHEMA_PATH = SCHEMAS_DIR / "synth-schema.json"

# Initialize Faker with Brazilian locale
fake = Faker("pt_BR")

# Escolaridade order for comparison
ESCOLARIDADE_ORDEM = [
    "Sem instrução",
    "Fundamental incompleto",
    "Fundamental completo",
    "Médio incompleto",
    "Médio completo",
    "Superior incompleto",
    "Superior completo",
    "Pós-graduação",
]


def load_config_data() -> dict[str, Any]:
    """
    Carrega todos os arquivos de configuração JSON do diretório data/config/.

    Returns:
        dict[str, Any]: Dicionário com todas as configurações carregadas
    """
    config_files = {
        "ibge": CONFIG_DIR / "ibge_distributions.json",
        "occupations": CONFIG_DIR / "occupations_structured.json",
        "interests_hobbies": CONFIG_DIR / "interests_hobbies.json",
    }

    config = {}
    for key, path in config_files.items():
        with open(path, "r", encoding="utf-8") as f:
            config[key] = json.load(f)

    return config


def gerar_id(tamanho: int = 6) -> str:
    """
    Gera um ID alfanumérico aleatório de tamanho especificado.

    Args:
        tamanho: Tamanho do ID (padrão: 6 caracteres)

    Returns:
        str: ID alfanumérico único
    """
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=tamanho))


def weighted_choice(options: dict[str, float]) -> str:
    """Seleciona uma opção baseada em pesos/probabilidades."""
    choices = list(options.keys())
    weights = list(options.values())
    return random.choices(choices, weights=weights, k=1)[0]


def normal_distribution(
    mean: float = 50, std: float = 15, min_val: int = 0, max_val: int = 100
) -> int:
    """Gera valor de distribuição normal limitado entre min_val e max_val."""
    value = random.gauss(mean, std)
    return max(min_val, min(max_val, round(value)))


def escolaridade_index(escolaridade: str) -> int:
    """Retorna o índice da escolaridade na ordem hierárquica."""
    try:
        return ESCOLARIDADE_ORDEM.index(escolaridade)
    except ValueError:
        return 0


def escolaridade_compativel(escolaridade: str, escolaridade_minima: str) -> bool:
    """Verifica se a escolaridade é compatível (maior ou igual) à mínima exigida."""
    return escolaridade_index(escolaridade) >= escolaridade_index(escolaridade_minima)


def generate_coherent_gender(ibge_data: dict[str, Any]) -> tuple[str, str]:
    """
    Gera gênero biológico e identidade de gênero de forma coerente.

    A grande maioria da população tem identidade de gênero alinhada com
    o gênero biológico (cisgênero). Pessoas trans e não-binárias são
    geradas de acordo com estimativas populacionais (~1-2%).

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
                o for o in ocupacoes
                if o["categoria"] not in ["estudante", "aposentado"]
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


def generate_demographics(config_data: dict[str, Any]) -> dict[str, Any]:
    """
    Gera atributos demográficos usando distribuições IBGE com coerência entre campos.

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


def generate_name(demographics: dict[str, Any]) -> str:
    """
    Gera nome brasileiro usando Faker pt_BR baseado no gênero.

    Usa identidade de gênero para determinar o nome, não gênero biológico,
    pois pessoas trans geralmente usam nomes alinhados com sua identidade.
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
        "Sr.", "Sra.", "Srta.", "Dr.", "Dra.", "Prof.", "Profa.", "Profª", "Eng.", "Arq."
    }
    nome_partes = nome.split()
    if nome_partes[0] in prefixos:
        nome = " ".join(nome_partes[1:])

    return nome


def generate_big_five() -> dict[str, int]:
    """
    Gera traços de personalidade Big Five com distribuição Normal(μ=50, σ=15).
    """
    return {
        "abertura": normal_distribution(50, 15, 0, 100),
        "conscienciosidade": normal_distribution(50, 15, 0, 100),
        "extroversao": normal_distribution(50, 15, 0, 100),
        "amabilidade": normal_distribution(50, 15, 0, 100),
        "neuroticismo": normal_distribution(50, 15, 0, 100),
    }


def generate_psychographics(
    big_five: dict[str, int], config_data: dict[str, Any]
) -> dict[str, Any]:
    """
    Gera atributos psicográficos (valores, interesses, hobbies, política, religião).
    """
    ibge = config_data["ibge"]
    interests = config_data["interests_hobbies"]

    # Valores (3-5 itens)
    valores = random.sample(interests["valores"], k=random.randint(3, 5))

    # Interesses (3-10 itens, correlacionados com abertura)
    num_interesses = 3 + (big_five["abertura"] // 20)
    interesses_list = random.sample(interests["interesses"], k=min(num_interesses, 10))

    # Hobbies (3-7 itens)
    hobbies = random.sample(interests["hobbies"], k=random.randint(3, 7))

    # Inclinação política (DataSenado 2024)
    distribuicao = ibge["inclinacao_politica_distribuicao"]
    categoria = weighted_choice(distribuicao)

    if categoria == "esquerda":
        inclinacao_politica = random.randint(-100, -20)
    elif categoria == "direita":
        inclinacao_politica = random.randint(20, 100)
    elif categoria == "centro":
        inclinacao_politica = random.randint(-20, 20)
    elif categoria == "neutro":
        inclinacao_politica = random.randint(-10, 10)
    else:  # nao_sabe
        inclinacao_politica = 0

    return {
        "personalidade_big_five": big_five,
        "valores": valores,
        "interesses": interesses_list,
        "hobbies": hobbies,
        "estilo_vida": "",  # Será derivado depois
        "inclinacao_politica": inclinacao_politica,
        "inclinacao_religiosa": weighted_choice(ibge["religiao"]),
    }


def generate_behavior(
    demographics: dict[str, Any], config_data: dict[str, Any]
) -> dict[str, Any]:
    """Gera atributos comportamentais (consumo, tecnologia, mídia)."""
    interests = config_data["interests_hobbies"]
    idade = demographics["idade"]
    renda = demographics["renda_mensal"]

    # Ajustar uso de tecnologia por idade e renda
    tem_smartphone = renda > 800 or idade < 50
    tem_computador = renda > 2000 or (idade < 40 and renda > 1500)
    tem_tablet = random.random() < (0.4 if renda > 5000 else 0.15)
    tem_smartwatch = random.random() < (0.3 if renda > 8000 else 0.1)

    # Tempo em redes sociais inversamente correlacionado com idade
    base_redes = 60 - (idade * 0.5)
    redes_sociais = max(5, min(70, int(base_redes + random.randint(-15, 15))))

    return {
        "habitos_consumo": {
            "frequencia_compras": random.choice(
                ["diária", "semanal", "quinzenal", "mensal", "esporádica"]
            ),
            "preferencia_canal": weighted_choice(
                {"loja física": 0.3, "e-commerce": 0.3, "híbrido": 0.4}
            ),
            "categorias_preferidas": random.sample(
                interests["categorias_compras"], k=random.randint(2, 5)
            ),
        },
        "uso_tecnologia": {
            "smartphone": tem_smartphone,
            "computador": tem_computador,
            "tablet": tem_tablet,
            "smartwatch": tem_smartwatch,
        },
        "padroes_midia": {
            "tv_aberta": random.randint(0, 35),
            "streaming": random.randint(0, 50),
            "redes_sociais": redes_sociais,
        },
        "fonte_noticias": random.sample(
            interests["fontes_noticias"], k=random.randint(2, 5)
        ),
        "comportamento_compra": {
            "impulsivo": normal_distribution(50, 20, 0, 100),
            "pesquisa_antes_comprar": normal_distribution(60, 20, 0, 100),
        },
        "lealdade_marca": normal_distribution(50, 20, 0, 100),
        "engajamento_redes_sociais": {
            "plataformas": random.sample(
                interests["plataformas_redes_sociais"], k=random.randint(2, 6)
            ),
            "frequencia_posts": random.choice(
                ["nunca", "raro", "ocasional", "frequente", "muito frequente"]
            ),
        },
    }


def generate_disabilities(ibge_data: dict[str, Any]) -> dict[str, Any]:
    """Gera deficiências usando distribuições IBGE PNS 2019 (8.4% pelo menos uma)."""
    deficiencias_dist = ibge_data["deficiencias"]

    tem_deficiencia = random.random() > deficiencias_dist["nenhuma"]

    if not tem_deficiencia:
        return {
            "visual": {"tipo": "nenhuma"},
            "auditiva": {"tipo": "nenhuma"},
            "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": False},
            "cognitiva": {"tipo": "nenhuma"},
        }

    return {
        "visual": {
            "tipo": random.choice(["nenhuma", "leve", "moderada", "severa", "cegueira"])
        },
        "auditiva": {
            "tipo": random.choice(["nenhuma", "leve", "moderada", "severa", "surdez"])
        },
        "motora": {
            "tipo": random.choice(["nenhuma", "leve", "moderada", "severa"]),
            "usa_cadeira_rodas": random.random() < 0.1,
        },
        "cognitiva": {
            "tipo": random.choice(["nenhuma", "leve", "moderada", "severa"])
        },
    }


def generate_tech_capabilities(
    demographics: dict[str, Any], disabilities: dict[str, Any]
) -> dict[str, Any]:
    """Gera capacidades tecnológicas correlacionadas com idade e escolaridade."""
    idade = demographics["idade"]
    escolaridade = demographics["escolaridade"]

    # Alfabetização digital correlacionada negativamente com idade
    # e positivamente com escolaridade
    base_digital = 80 - (idade * 0.5)
    bonus_escolaridade = escolaridade_index(escolaridade) * 5
    alfabetizacao = max(10, min(100, int(base_digital + bonus_escolaridade)))

    return {
        "alfabetizacao_digital": alfabetizacao,
        "dispositivos": {
            "principal": random.choice(["smartphone", "computador", "tablet"]),
            "qualidade": weighted_choice(
                {"novo": 0.3, "intermediário": 0.5, "antigo": 0.2}
            ),
        },
        "preferencias_acessibilidade": {
            "zoom_fonte": (
                100
                if disabilities["visual"]["tipo"] == "nenhuma"
                else random.randint(120, 200)
            ),
            "alto_contraste": disabilities["visual"]["tipo"]
            in ["severa", "cegueira"],
        },
        "velocidade_digitacao": max(10, min(120, 70 - idade // 2)),
        "frequencia_internet": random.choice(["diária", "semanal", "mensal", "rara"]),
        "familiaridade_plataformas": {
            "e_commerce": normal_distribution(50, 25, 0, 100),
            "banco_digital": normal_distribution(50, 25, 0, 100),
            "redes_sociais": normal_distribution(60, 25, 0, 100),
        },
    }


def generate_behavioral_biases() -> dict[str, int]:
    """Gera 7 vieses comportamentais com Normal(μ=50, σ=20)."""
    return {
        "aversao_perda": normal_distribution(50, 20, 0, 100),
        "desconto_hiperbolico": normal_distribution(50, 20, 0, 100),
        "suscetibilidade_chamariz": normal_distribution(50, 20, 0, 100),
        "ancoragem": normal_distribution(50, 20, 0, 100),
        "vies_confirmacao": normal_distribution(50, 20, 0, 100),
        "vies_status_quo": normal_distribution(50, 20, 0, 100),
        "sobrecarga_informacao": normal_distribution(50, 20, 0, 100),
    }


def derive_archetype(demographics: dict[str, Any], big_five: dict[str, int]) -> str:
    """Gera arquétipo automaticamente: {Faixa Etária} {Região} {Perfil Psicográfico}."""
    idade = demographics["idade"]
    if idade < 18:
        faixa = "Adolescente"
    elif idade < 30:
        faixa = "Jovem Adulto"
    elif idade < 45:
        faixa = "Adulto"
    elif idade < 60:
        faixa = "Meia-Idade"
    else:
        faixa = "Idoso"

    regiao = demographics["localizacao"]["regiao"]

    # Traço dominante do Big Five
    tracos = {
        "Criativo": big_five["abertura"],
        "Organizado": big_five["conscienciosidade"],
        "Social": big_five["extroversao"],
        "Empático": big_five["amabilidade"],
        "Ansioso": big_five["neuroticismo"],
    }
    perfil = max(tracos, key=tracos.get)   # type: ignore

    return f"{faixa} {regiao} {perfil}"


def derive_lifestyle(big_five: dict[str, int]) -> str:
    """Deriva estilo de vida dos traços Big Five."""
    extroversao = big_five["extroversao"]
    neuroticismo = big_five["neuroticismo"]
    abertura = big_five["abertura"]

    if extroversao > 60 and neuroticismo < 40:
        return "Ativo e social"
    elif extroversao < 40 and neuroticismo > 60:
        return "Reservado e cauteloso"
    elif abertura > 70:
        return "Criativo e explorador"
    elif big_five["conscienciosidade"] > 70:
        return "Disciplinado e focado"
    else:
        return "Equilibrado e moderado"


def derive_description(synth_data: dict[str, Any]) -> str:
    """Gera descrição textual do Synth (mínimo 50 caracteres)."""
    demo = synth_data["demografia"]
    psico = synth_data["psicografia"]

    # Usar identidade de gênero para artigo
    identidade = demo["identidade_genero"]
    if identidade in ["mulher cis", "mulher trans"]:
        genero_artigo = "Mulher"
    elif identidade in ["homem cis", "homem trans"]:
        genero_artigo = "Homem"
    else:
        genero_artigo = "Pessoa"

    desc = f"{genero_artigo} de {demo['idade']} anos, {demo['ocupacao'].lower()}, "
    desc += f"mora em {demo['localizacao']['cidade']}, {demo['localizacao']['estado']}. "

    big_five = psico["personalidade_big_five"]
    tracos_altos = [k.capitalize() for k, v in big_five.items() if v > 60]
    if tracos_altos:
        desc += f"Possui traços marcantes de {', '.join(tracos_altos[:2])}. "

    # Adicionar informação sobre interesses se descrição ainda curta
    if len(desc) < 50 and psico["interesses"]:
        desc += f"Interesses: {', '.join(psico['interesses'][:3])}."

    return desc


def generate_photo_link(name: str) -> str:
    """Gera link para foto usando ui-avatars.com API."""
    name_encoded = name.replace(" ", "+")
    return f"https://ui-avatars.com/api/?name={name_encoded}&size=256&background=random"


def assemble_synth(config: dict[str, Any]) -> dict[str, Any]:
    """Monta Synth completo combinando todos os atributos gerados."""
    synth_id = gerar_id()

    # Gerar todos os atributos com coerência
    demographics = generate_demographics(config)
    name = generate_name(demographics)
    big_five = generate_big_five()
    psychographics = generate_psychographics(big_five, config)
    behavior = generate_behavior(demographics, config)
    disabilities = generate_disabilities(config["ibge"])
    tech_caps = generate_tech_capabilities(demographics, disabilities)
    biases = generate_behavioral_biases()

    # Campos derivados
    psychographics["estilo_vida"] = derive_lifestyle(big_five)

    synth = {
        "id": synth_id,
        "nome": name,
        "arquetipo": derive_archetype(demographics, big_five),
        "descricao": "",  # Será preenchido depois
        "link_photo": generate_photo_link(name),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "demografia": demographics,
        "psicografia": psychographics,
        "comportamento": behavior,
        "deficiencias": disabilities,
        "capacidades_tecnologicas": tech_caps,
        "vieses": biases,
    }

    # Gerar descrição com synth completo
    synth["descricao"] = derive_description(synth)

    return synth


def save_synth(synth_dict: dict[str, Any], output_dir: Path = SYNTHS_DIR) -> None:
    """Salva Synth como {id}.json no diretório especificado."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{synth_dict['id']}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(synth_dict, f, ensure_ascii=False, indent=2)

    print(f"Synth salvo: {output_path}")


def validate_synth(
    synth_dict: dict[str, Any], schema_path: Path = SCHEMA_PATH
) -> tuple[bool, list[str]]:
    """
    Valida Synth contra JSON Schema e retorna status e lista de erros.

    Args:
        synth_dict: Dicionário do Synth a validar
        schema_path: Caminho para o arquivo de schema JSON

    Returns:
        tuple[bool, list[str]]: (is_valid, error_messages)
    """
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        validator = Draft202012Validator(schema)
        errors = []

        for error in validator.iter_errors(synth_dict):
            path = " -> ".join(str(p) for p in error.path) if error.path else "root"
            errors.append(f"{path}: {error.message}")

        return (len(errors) == 0, errors)

    except FileNotFoundError:
        return (False, [f"Schema não encontrado: {schema_path}"])
    except json.JSONDecodeError as e:
        return (False, [f"Erro ao parsear schema: {str(e)}"])


def validate_single_file(file_path: Path, schema_path: Path = SCHEMA_PATH) -> None:
    """
    Valida um único arquivo JSON de Synth contra o schema.

    Args:
        file_path: Caminho para o arquivo JSON do Synth
        schema_path: Caminho para o schema JSON
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            synth_data = json.load(f)

        is_valid, errors = validate_synth(synth_data, schema_path)

        if is_valid:
            print(f"✓ {file_path.name}: VÁLIDO")
        else:
            print(f"✗ {file_path.name}: FALHOU")
            for error in errors:
                print(f"  - {error}")

    except FileNotFoundError:
        print(f"✗ {file_path.name}: Arquivo não encontrado")
    except json.JSONDecodeError as e:
        print(f"✗ {file_path.name}: JSON inválido - {str(e)}")


def validate_batch(
    synths_dir: Path = SYNTHS_DIR, schema_path: Path = SCHEMA_PATH
) -> dict[str, Any]:
    """
    Valida todos os arquivos JSON em um diretório contra o schema.

    Returns:
        dict: Estatísticas de validação (total, valid, invalid, errors)
    """
    json_files = list(synths_dir.glob("*.json"))

    if not json_files:
        print(f"Nenhum arquivo JSON encontrado em {synths_dir}")
        return {"total": 0, "valid": 0, "invalid": 0, "errors": []}

    stats = {"total": len(json_files), "valid": 0, "invalid": 0, "errors": []}

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                synth_data = json.load(f)

            is_valid, errors = validate_synth(synth_data, schema_path)

            if is_valid:
                stats["valid"] += 1
                print(f"✓ {file_path.name}")
            else:
                stats["invalid"] += 1
                print(f"✗ {file_path.name}")
                for error in errors:
                    print(f"  - {error}")
                stats["errors"].append({"file": file_path.name, "errors": errors})

        except Exception as e:
            stats["invalid"] += 1
            error_msg = f"Erro ao processar {file_path.name}: {str(e)}"
            print(f"✗ {error_msg}")
            stats["errors"].append({"file": file_path.name, "errors": [error_msg]})

    return stats


def analyze_regional_distribution(synths_dir: Path = SYNTHS_DIR) -> dict[str, Any]:
    """Analisa distribuição regional dos Synths gerados vs IBGE."""
    config = load_config_data()
    ibge_dist = config["ibge"]["regioes"]

    json_files = list(synths_dir.glob("*.json"))
    if not json_files:
        return {"error": "Nenhum Synth encontrado"}

    region_counts = {}
    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            synth = json.load(f)
            regiao = synth["demografia"]["localizacao"]["regiao"]
            region_counts[regiao] = region_counts.get(regiao, 0) + 1

    total = len(json_files)
    analysis = {}
    for regiao, ibge_pct in ibge_dist.items():
        actual_count = region_counts.get(regiao, 0)
        actual_pct = (actual_count / total) * 100
        error = abs(actual_pct - (ibge_pct * 100))
        analysis[regiao] = {
            "ibge": ibge_pct * 100,
            "actual": actual_pct,
            "count": actual_count,
            "error": error,
        }

    return {"total": total, "regions": analysis}


def analyze_age_distribution(synths_dir: Path = SYNTHS_DIR) -> dict[str, Any]:
    """Analisa distribuição etária dos Synths gerados vs IBGE."""
    config = load_config_data()
    ibge_dist = config["ibge"]["faixas_etarias"]

    json_files = list(synths_dir.glob("*.json"))
    if not json_files:
        return {"error": "Nenhum Synth encontrado"}

    age_counts = {}
    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            synth = json.load(f)
            idade = synth["demografia"]["idade"]
            if idade < 15:
                faixa = "0-14"
            elif idade < 30:
                faixa = "15-29"
            elif idade < 45:
                faixa = "30-44"
            elif idade < 60:
                faixa = "45-59"
            else:
                faixa = "60+"
            age_counts[faixa] = age_counts.get(faixa, 0) + 1

    total = len(json_files)
    analysis = {}
    for faixa, ibge_pct in ibge_dist.items():
        actual_count = age_counts.get(faixa, 0)
        actual_pct = (actual_count / total) * 100
        error = abs(actual_pct - (ibge_pct * 100))
        analysis[faixa] = {
            "ibge": ibge_pct * 100,
            "actual": actual_pct,
            "count": actual_count,
            "error": error,
        }

    return {"total": total, "age_groups": analysis}


def main(quantidade: int = 1, show_progress: bool = True) -> list[dict[str, Any]]:
    """
    Função principal: carrega config e gera Synths.

    Args:
        quantidade: Número de synths a gerar (padrão: 1)
        show_progress: Mostrar progresso durante geração

    Returns:
        list[dict]: Lista de synths gerados
    """
    print(f"=== Gerando {quantidade} Synth(s) ===")
    config = load_config_data()

    # Track IDs to prevent duplicates
    existing_ids = set()
    synths_dir_files = list(SYNTHS_DIR.glob("*.json"))
    for file_path in synths_dir_files:
        existing_ids.add(file_path.stem)

    synths_gerados = []
    for i in range(quantidade):
        # Generate with unique ID check
        max_attempts = 10
        for attempt in range(max_attempts):
            synth = assemble_synth(config)
            if synth["id"] not in existing_ids:
                existing_ids.add(synth["id"])
                break
            if attempt == max_attempts - 1:
                # Force new ID on last attempt
                synth["id"] = gerar_id(8)  # Use longer ID

        save_synth(synth)
        synths_gerados.append(synth)

        if show_progress:
            if quantidade > 10 and (i + 1) % 10 == 0:
                print(f"  [{i+1}/{quantidade}] Gerados...")
            elif quantidade <= 10:
                print(f"  [{i+1}/{quantidade}] {synth['nome']} ({synth['id']})")

    print(f"\n{quantidade} synth(s) gerado(s) com sucesso!")
    return synths_gerados


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Gerador de Synths (Personas Sintéticas Brasileiras)")
    parser.add_argument(
        "-n", "--quantidade",
        type=int,
        default=1,
        help="Número de synths a gerar (padrão: 1)"
    )
    parser.add_argument(
        "--validar",
        action="store_true",
        help="Executar testes de validação em vez de gerar synths"
    )
    parser.add_argument(
        "--validate-file",
        type=str,
        metavar="FILE",
        help="Validar um único arquivo JSON de Synth contra o schema"
    )
    parser.add_argument(
        "--validate-all",
        action="store_true",
        help="Validar todos os Synths em data/synths/ contra o schema"
    )
    parser.add_argument(
        "--analyze",
        type=str,
        choices=["region", "age", "all"],
        help="Analisar distribuição demográfica dos Synths gerados vs IBGE"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        metavar="DIR",
        help="Diretório de saída para synths gerados (padrão: data/synths/)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Modo silencioso - suprimir output verboso"
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Mostrar estatísticas de performance (tempo total, synths/segundo)"
    )

    args = parser.parse_args()

    # Modo validação de arquivo único
    if args.validate_file:
        file_path = Path(args.validate_file)
        print(f"=== Validando arquivo: {file_path} ===\n")
        validate_single_file(file_path)
        sys.exit(0)

    # Modo validação de todos os arquivos
    if args.validate_all:
        print(f"=== Validando todos os Synths em {SYNTHS_DIR} ===\n")
        stats = validate_batch(SYNTHS_DIR)
        print(f"\n{'='*60}")
        print(f"Total: {stats['total']} arquivo(s)")
        print(f"Válidos: {stats['valid']}")
        print(f"Inválidos: {stats['invalid']}")
        if stats['invalid'] > 0:
            print(f"\n{stats['invalid']} arquivo(s) com erros de validação")
            sys.exit(1)
        else:
            print(f"\n✓ Todos os arquivos passaram na validação!")
            sys.exit(0)

    # Modo análise de distribuição
    if args.analyze:
        print(f"=== Análise de Distribuição Demográfica ===\n")

        if args.analyze in ["region", "all"]:
            print("--- Distribuição Regional ---")
            result = analyze_regional_distribution()
            if "error" in result:
                print(f"Erro: {result['error']}")
            else:
                print(f"Total de Synths: {result['total']}\n")
                print(f"{'Região':<15} {'IBGE %':<10} {'Real %':<10} {'Count':<8} {'Erro %':<10}")
                print("-" * 60)
                for regiao, data in result["regions"].items():
                    print(
                        f"{regiao:<15} {data['ibge']:>7.2f}%  {data['actual']:>7.2f}%  "
                        f"{data['count']:>5}    {data['error']:>7.2f}%"
                    )
                print()

        if args.analyze in ["age", "all"]:
            print("--- Distribuição Etária ---")
            result = analyze_age_distribution()
            if "error" in result:
                print(f"Erro: {result['error']}")
            else:
                print(f"Total de Synths: {result['total']}\n")
                print(f"{'Faixa':<10} {'IBGE %':<10} {'Real %':<10} {'Count':<8} {'Erro %':<10}")
                print("-" * 60)
                for faixa, data in result["age_groups"].items():
                    print(
                        f"{faixa:<10} {data['ibge']:>7.2f}%  {data['actual']:>7.2f}%  "
                        f"{data['count']:>5}    {data['error']:>7.2f}%"
                    )
        sys.exit(0)

    if not args.validar:
        # Modo normal: gerar synths
        import time

        # Override global output directory if specified
        output_dir = Path(args.output) if args.output else SYNTHS_DIR
        quiet = args.quiet

        # Start timing for benchmark
        start_time = time.time()

        # Update save_synth to use custom output directory
        original_save = save_synth
        def save_with_custom_dir(synth_dict, output_dir_override=output_dir):
            return original_save(synth_dict, output_dir_override)

        # Generate synths
        if not quiet:
            synths = main(args.quantidade, show_progress=True)
        else:
            # Suppress print statements temporarily
            import os
            devnull = open(os.devnull, 'w')
            old_stdout = sys.stdout
            sys.stdout = devnull
            synths = main(args.quantidade, show_progress=False)
            sys.stdout = old_stdout
            devnull.close()
            print(f"{args.quantidade} synth(s) gerado(s).")

        # Show benchmark if requested
        if args.benchmark:
            elapsed = time.time() - start_time
            rate = args.quantidade / elapsed if elapsed > 0 else 0
            print(f"\n=== Benchmark ===")
            print(f"Tempo total: {elapsed:.2f}s")
            print(f"Taxa: {rate:.1f} synths/segundo")

        sys.exit(0)

    # Modo validação
    print("=== VALIDACAO DO GERADOR DE SYNTHS ===\n")

    all_failures = []
    total_tests = 0

    # Teste 1: Carregar configurações
    total_tests += 1
    try:
        config = load_config_data()
        assert "ibge" in config and "occupations" in config and "interests_hobbies" in config
        print(f"Teste 1: Configuracoes carregadas ({len(config)} arquivos)")
    except Exception as e:
        all_failures.append(f"Teste 1 (load_config): {str(e)}")

    # Teste 2: Gerar ID único
    total_tests += 1
    try:
        id1, id2 = gerar_id(), gerar_id()
        assert len(id1) == 6 and id1 != id2 and id1.isalnum()
        print(f"Teste 2: IDs unicos gerados ({id1}, {id2})")
    except Exception as e:
        all_failures.append(f"Teste 2 (gerar_id): {str(e)}")

    # Teste 3: Gerar Synth completo
    total_tests += 1
    try:
        synth = assemble_synth(config)
        assert synth["id"] and len(synth["id"]) == 6
        assert synth["nome"] and len(synth["nome"]) > 5
        assert 0 <= synth["demografia"]["idade"] <= 120
        assert synth["demografia"]["renda_mensal"] >= 0
        assert len(synth["psicografia"]["valores"]) >= 3
        assert len(synth["psicografia"]["hobbies"]) >= 3
        print(f"Teste 3: Synth completo gerado ({synth['nome']}, {synth['id']})")
    except Exception as e:
        all_failures.append(f"Teste 3 (assemble_synth): {str(e)}")

    # Teste 4: Coerência gênero biológico vs identidade
    total_tests += 1
    try:
        demo = synth["demografia"]
        gb = demo["genero_biologico"]
        ig = demo["identidade_genero"]

        # Verificar coerência: cis deve corresponder ao gênero biológico
        coerente = True
        if ig == "mulher cis" and gb != "feminino":
            coerente = False
        if ig == "homem cis" and gb != "masculino":
            coerente = False

        assert coerente, f"Incoerencia: genero_biologico={gb}, identidade_genero={ig}"
        print(f"Teste 4: Coerencia genero OK (biologico={gb}, identidade={ig})")
    except Exception as e:
        all_failures.append(f"Teste 4 (coerencia genero): {str(e)}")

    # Teste 5: Coerência estado civil vs composição familiar
    total_tests += 1
    try:
        demo = synth["demografia"]
        ec = demo["estado_civil"]
        cf = demo["composicao_familiar"]

        # Verificar regras básicas
        coerente = True
        msg = ""

        # Solteiro não pode ser "casal com/sem filhos"
        if ec == "solteiro" and cf["tipo"] in ["casal com filhos", "casal sem filhos"]:
            coerente = False
            msg = f"Solteiro com tipo={cf['tipo']}"

        # Casal deve ter pelo menos 2 pessoas
        if cf["tipo"] in ["casal com filhos", "casal sem filhos"] and cf["numero_pessoas"] < 2:
            coerente = False
            msg = f"Casal com {cf['numero_pessoas']} pessoa(s)"

        # Unipessoal deve ter exatamente 1 pessoa
        if cf["tipo"] == "unipessoal" and cf["numero_pessoas"] != 1:
            coerente = False
            msg = f"Unipessoal com {cf['numero_pessoas']} pessoas"

        assert coerente, f"Incoerencia familia: {msg}"
        print(f"Teste 5: Coerencia familia OK (estado_civil={ec}, tipo={cf['tipo']}, pessoas={cf['numero_pessoas']})")
    except Exception as e:
        all_failures.append(f"Teste 5 (coerencia familia): {str(e)}")

    # Teste 6: Coerência ocupação vs escolaridade
    total_tests += 1
    try:
        demo = synth["demografia"]
        ocupacao = demo["ocupacao"]
        escolaridade = demo["escolaridade"]

        # Encontrar a ocupação no config
        ocupacao_info = None
        for o in config["occupations"]["ocupacoes"]:
            if o["nome"] == ocupacao:
                ocupacao_info = o
                break

        if ocupacao_info:
            esc_min = ocupacao_info["escolaridade_minima"]
            compativel = escolaridade_compativel(escolaridade, esc_min)
            assert compativel, f"Escolaridade {escolaridade} incompativel com {ocupacao} (min: {esc_min})"
            print(f"Teste 6: Coerencia ocupacao OK ({ocupacao}, escolaridade={escolaridade})")
        else:
            print(f"Teste 6: Ocupacao {ocupacao} nao encontrada no config (AVISO)")
    except Exception as e:
        all_failures.append(f"Teste 6 (coerencia ocupacao): {str(e)}")

    # Teste 7: Coerência renda vs ocupação
    total_tests += 1
    try:
        demo = synth["demografia"]
        ocupacao = demo["ocupacao"]
        renda = demo["renda_mensal"]

        # Encontrar a ocupação no config
        ocupacao_info = None
        for o in config["occupations"]["ocupacoes"]:
            if o["nome"] == ocupacao:
                ocupacao_info = o
                break

        if ocupacao_info:
            faixa = ocupacao_info["faixa_salarial"]
            dentro_faixa = faixa["min"] <= renda <= faixa["max"]
            assert dentro_faixa, f"Renda R${renda} fora da faixa [{faixa['min']}-{faixa['max']}] para {ocupacao}"
            print(f"Teste 7: Coerencia renda OK (R${renda:.2f} para {ocupacao})")
        else:
            print(f"Teste 7: Ocupacao {ocupacao} nao encontrada no config (AVISO)")
    except Exception as e:
        all_failures.append(f"Teste 7 (coerencia renda): {str(e)}")

    # Teste 8: Salvar Synth
    total_tests += 1
    try:
        save_synth(synth)
        saved_path = SYNTHS_DIR / f"{synth['id']}.json"
        assert saved_path.exists()
        with open(saved_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["id"] == synth["id"]
        print(f"Teste 8: Synth salvo e carregado ({saved_path})")
    except Exception as e:
        all_failures.append(f"Teste 8 (save_synth): {str(e)}")

    # Teste 9: Campos obrigatórios presentes
    total_tests += 1
    try:
        required_keys = [
            "id",
            "nome",
            "arquetipo",
            "descricao",
            "demografia",
            "psicografia",
            "comportamento",
            "deficiencias",
            "capacidades_tecnologicas",
            "vieses",
        ]
        for key in required_keys:
            assert key in synth, f"Campo obrigatorio ausente: {key}"
        print(f"Teste 9: Todos os {len(required_keys)} campos obrigatorios presentes")
    except Exception as e:
        all_failures.append(f"Teste 9 (campos obrigatorios): {str(e)}")

    # Teste 10: Gerar múltiplos synths e verificar coerência
    total_tests += 1
    try:
        synths_gerados = [assemble_synth(config) for _ in range(10)]
        erros_coerencia = []

        for i, s in enumerate(synths_gerados):
            demo = s["demografia"]

            # Verificar coerência gênero
            gb = demo["genero_biologico"]
            ig = demo["identidade_genero"]
            if ig == "mulher cis" and gb != "feminino":
                erros_coerencia.append(f"Synth {i}: mulher cis com genero_biologico={gb}")
            if ig == "homem cis" and gb != "masculino":
                erros_coerencia.append(f"Synth {i}: homem cis com genero_biologico={gb}")

            # Verificar coerência família
            ec = demo["estado_civil"]
            cf = demo["composicao_familiar"]
            if ec == "solteiro" and cf["tipo"] in ["casal com filhos", "casal sem filhos"]:
                erros_coerencia.append(f"Synth {i}: solteiro com {cf['tipo']}")
            if cf["tipo"] == "unipessoal" and cf["numero_pessoas"] != 1:
                erros_coerencia.append(f"Synth {i}: unipessoal com {cf['numero_pessoas']} pessoas")
            if cf["tipo"] in ["casal com filhos", "casal sem filhos"] and cf["numero_pessoas"] < 2:
                erros_coerencia.append(f"Synth {i}: casal com {cf['numero_pessoas']} pessoa(s)")

        assert len(erros_coerencia) == 0, f"Erros de coerencia em batch: {erros_coerencia}"
        print(f"Teste 10: Batch de 10 synths todos coerentes")
    except Exception as e:
        all_failures.append(f"Teste 10 (batch coerencia): {str(e)}")

    # Resultado final
    print(f"\n{'='*60}")
    if all_failures:
        print(
            f"VALIDACAO FALHOU - {len(all_failures)} de {total_tests} testes falharam:"
        )
        for failure in all_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"VALIDACAO PASSOU - Todos os {total_tests} testes produziram resultados esperados"
        )
        print("Funcao validada e pronta para uso!")
        sys.exit(0)
