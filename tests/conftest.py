"""
Pytest configuration and shared fixtures for Synth Lab tests.
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def config_data() -> dict[str, Any]:
    """Load actual config data from data/config/."""
    data_dir = Path(__file__).parent.parent / "data"
    config_dir = data_dir / "config"

    config = {}
    config_files = {
        "ibge": config_dir / "ibge_distributions.json",
        "occupations": config_dir / "occupations_structured.json",
        "interests_hobbies": config_dir / "interests_hobbies.json",
    }

    for key, path in config_files.items():
        with open(path, "r", encoding="utf-8") as f:
            config[key] = json.load(f)

    return config


@pytest.fixture
def sample_synth() -> dict[str, Any]:
    """Provide a minimal valid synth structure for testing."""
    return {
        "id": "test01",
        "nome": "Test User",
        "arquetipo": "Jovem Adulto Sudeste Criativo",
        "descricao": "Pessoa de 25 anos para testes automatizados do sistema",
        "link_photo": "https://ui-avatars.com/api/?name=Test+User&size=256&background=random",
        "created_at": "2025-12-15T10:00:00Z",
        "version": "2.0.0",
        "demografia": {
            "idade": 25,
            "genero_biologico": "masculino",
            "identidade_genero": "homem cis",
            "raca_etnia": "pardo",
            "localizacao": {
                "pais": "Brasil",
                "regiao": "Sudeste",
                "estado": "SP",
                "cidade": "São Paulo"
            },
            "escolaridade": "Superior completo",
            "renda_mensal": 5000.0,
            "ocupacao": "Desenvolvedor",
            "estado_civil": "solteiro",
            "composicao_familiar": {
                "tipo": "unipessoal",
                "numero_pessoas": 1
            }
        },
        "psicografia": {
            "personalidade_big_five": {
                "abertura": 70,
                "conscienciosidade": 60,
                "extroversao": 50,
                "amabilidade": 65,
                "neuroticismo": 40
            },
            "interesses": ["Tecnologia", "Leitura", "Música"],
            "inclinacao_politica": 10,
            "inclinacao_religiosa": "ateu/agnóstico"
        },
        "comportamento": {
            "habitos_consumo": {
                "frequencia_compras": "semanal",
                "preferencia_canal": "e-commerce",
                "categorias_preferidas": ["Eletrônicos", "Livros"]
            },
            "padroes_midia": {
                "tv_aberta": 5,
                "streaming": 20,
                "redes_sociais": 15
            },
            "fonte_noticias": ["Portais online", "Redes sociais"],
            "lealdade_marca": 60,
            "engajamento_redes_sociais": {
                "plataformas": ["Instagram", "Twitter", "LinkedIn"],
                "frequencia_posts": "ocasional"
            }
        },
        "deficiencias": {
            "visual": {"tipo": "nenhuma"},
            "auditiva": {"tipo": "nenhuma"},
            "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": False},
            "cognitiva": {"tipo": "nenhuma"}
        },
        "capacidades_tecnologicas": {
            "alfabetizacao_digital": 90,
            "dispositivos": {
                "principal": "computador",
                "qualidade": "novo"
            },
            "preferencias_acessibilidade": {
                "zoom_fonte": 100,
                "alto_contraste": False
            },
            "velocidade_digitacao": 80,
            "frequencia_internet": "diária",
            "familiaridade_plataformas": {
                "e_commerce": 90,
                "banco_digital": 85,
                "redes_sociais": 95
            }
        },
        "vieses": {
            "aversao_perda": 50,
            "desconto_hiperbolico": 45,
            "suscetibilidade_chamariz": 40,
            "ancoragem": 55,
            "vies_confirmacao": 60,
            "vies_status_quo": 50,
            "sobrecarga_informacao": 55
        }
    }


@pytest.fixture
def temp_output_dir():
    """Provide a temporary directory for test output, cleaned up after test."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)
