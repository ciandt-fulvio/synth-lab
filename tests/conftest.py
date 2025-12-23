"""
Pytest configuration and shared fixtures for SynthLab tests.
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
    """Provide a minimal valid synth structure for testing (matches synth-schema v2.0.0)."""
    return {
        "id": "test01",
        "nome": "Test User",
        "descricao": "Pessoa de 25 anos para testes automatizados do sistema com descrição mais longa",
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
            "contrato_cognitivo": {
                "tipo": "factual",
                "perfil_cognitivo": "responde só ao que foi perguntado, evita abstrações",
                "regras": [
                    "Proibido dar opinião geral",
                    "Sempre relatar um evento específico"
                ],
                "efeito_esperado": "respostas secas, muito factuais"
            }
        },
        "deficiencias": {
            "visual": {"tipo": "nenhuma"},
            "auditiva": {"tipo": "nenhuma"},
            "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": False},
            "cognitiva": {"tipo": "nenhuma"}
        },
        "capacidades_tecnologicas": {
            "alfabetizacao_digital": 90
        }
    }


@pytest.fixture
def temp_output_dir():
    """Provide a temporary directory for test output, cleaned up after test."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)
