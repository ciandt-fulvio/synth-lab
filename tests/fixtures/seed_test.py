"""
Test database seeding for synth-lab.

Provides realistic test data for integration and E2E tests.
Creates a complete experiment scenario matching production usage patterns.

Seed includes:
- 1 primary experiment: "App de Delivery - Feature de Agendamento de Pedidos"
- Interview guide (required for "Nova Entrevista" button)
- 6 completed interviews (ResearchExecution + Transcripts)
- Documents: summary + PR-FAQ
- Synth groups and synths for interviews

Usage:
    from tests.fixtures.seed_test import seed_database

    engine = create_engine(DATABASE_URL)  # Set by Makefile to test container
    seed_database(engine)
"""

from datetime import datetime, timedelta

from loguru import logger
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from synth_lab.models.orm import (
    Experiment,
    ExperimentDocument,
    ResearchExecution,
    Synth,
    SynthGroup,
    Transcript,
)
from synth_lab.models.orm.experiment import InterviewGuide
from synth_lab.models.orm.user import User

# Test user constants - must match tests/conftest.py
TEST_USER_ID = "00000001-0000-0000-0000-000000000001"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_GOOGLE_ID = "google-test-user-001"


def seed_database(engine: Engine) -> None:
    """
    Seed test database with realistic sample data.

    Creates:
    - 1 test user (for authentication tests)
    - 1 primary experiment (delivery app scheduling feature)
    - 6 research executions with transcripts
    - 3 documents (research summary, executive summary, PR-FAQ)
    - Synth groups and synths for realistic data

    Args:
        engine: SQLAlchemy engine connected to test database
    """
    logger.info("Seeding test database...")

    session = Session(engine)

    try:
        # Clear existing data (in correct order due to FK constraints)
        _clear_existing_data(session)

        # Seed in dependency order:
        # 1. User MUST come first (owner FK dependency)
        # 2. SynthGroups MUST come before experiment due to FK
        _seed_test_user(session)
        synth_groups = _seed_synth_groups(session)
        experiment = _seed_primary_experiment(session)
        synths = _seed_synths(session, synth_groups)
        _seed_research_executions(session, experiment, synths)
        _seed_interview_guide(session, experiment)
        _seed_documents(session, experiment)

        session.commit()
        logger.success("Test database seeded successfully")

    except Exception as e:
        session.rollback()
        logger.error(f"Failed to seed database: {e}")
        raise
    finally:
        session.close()


def _clear_existing_data(session: Session) -> None:
    """Clear existing test data."""
    logger.debug("Clearing existing data...")

    # Delete in reverse dependency order (children before parents)
    session.query(Transcript).delete()
    session.query(ResearchExecution).delete()
    session.query(ExperimentDocument).delete()
    session.query(Synth).delete()
    session.query(InterviewGuide).delete()  # Must delete before Experiment (FK dependency)
    session.query(Experiment).delete()  # Must delete before SynthGroup (FK dependency)
    session.query(SynthGroup).delete()
    session.query(User).delete()  # Clear users last (they own experiments/groups)

    session.commit()


def _seed_test_user(session: Session) -> User:
    """Seed test user for authentication tests.

    Creates a single test user that matches the TEST_USER_ID in conftest.py.
    This user is the owner of all seeded experiments and synth groups.
    """
    logger.debug("Seeding test user...")

    base_time = datetime.now()

    user = User(
        id=TEST_USER_ID,
        google_user_id=TEST_USER_GOOGLE_ID,
        email=TEST_USER_EMAIL,
        display_name="Test User",
        profile_picture_url=None,
        created_at=(base_time - timedelta(days=100)).isoformat(),
        updated_at=(base_time - timedelta(days=1)).isoformat(),
    )

    session.add(user)
    session.commit()

    logger.debug(f"Created test user: {user.id}")
    return user


def _seed_primary_experiment(session: Session) -> Experiment:
    """Seed the primary test experiment."""
    logger.debug("Seeding primary experiment...")

    base_time = datetime.now()

    experiment = Experiment(
        id="exp_a1b2c3d4",  # Valid format: exp_[a-f0-9]{8}
        name="App de Delivery - Feature de Agendamento de Pedidos",
        hypothesis="Permitir agendamento de pedidos aumentara retencao em 25% e ticket medio em 15%",
        description=(
            "Funcionalidade de agendamento que permite usuarios programarem entregas "
            "para horarios especificos, com opcao de pedido recorrente para assinaturas. "
            "Inclui notificacoes e gestao de agenda no app."
        ),
        status="active",
        owner_id=TEST_USER_ID,  # Assign to test user
        created_at=(base_time - timedelta(days=14)).isoformat(),
        updated_at=(base_time - timedelta(days=1)).isoformat(),
    )

    session.add(experiment)
    session.commit()

    logger.debug(f"Created primary experiment: {experiment.id}")
    return experiment


def _seed_synth_groups(session: Session) -> list[SynthGroup]:
    """Seed synth groups representing user segments."""
    logger.debug("Seeding synth groups...")

    base_time = datetime.now()

    groups = [
        # Default group - MUST be created first as experiments use this by default
        SynthGroup(
            id="grp_00000001",  # Default group ID used by experiments
            name="Default",
            description="Grupo padrao para synths sem grupo especifico",
            owner_id=TEST_USER_ID,  # Assign to test user
            created_at=(base_time - timedelta(days=90)).isoformat(),
        ),
        SynthGroup(
            id="grp_a1b2c3d4",  # Valid format: grp_[a-f0-9]{8}
            name="Usuarios Frequentes",
            description="Usuarios que pedem 3+ vezes por semana, alta familiaridade com app",
            owner_id=TEST_USER_ID,  # Assign to test user
            created_at=(base_time - timedelta(days=60)).isoformat(),
        ),
        SynthGroup(
            id="grp_b2c3d4e5",  # Valid format: grp_[a-f0-9]{8}
            name="Profissionais Ocupados",
            description="Executivos e profissionais com rotina intensa, valorizam praticidade",
            owner_id=TEST_USER_ID,  # Assign to test user
            created_at=(base_time - timedelta(days=60)).isoformat(),
        ),
        SynthGroup(
            id="grp_c3d4e5f6",  # Valid format: grp_[a-f0-9]{8}
            name="Familias",
            description="Usuarios que pedem para familia, planejam refeicoes com antecedencia",
            owner_id=TEST_USER_ID,  # Assign to test user
            created_at=(base_time - timedelta(days=60)).isoformat(),
        ),
    ]

    session.add_all(groups)
    session.commit()

    logger.debug(f"Created {len(groups)} synth groups")
    return groups


def _seed_synths(session: Session, groups: list[SynthGroup]) -> list[Synth]:
    """Seed synths for research interviews."""
    logger.debug("Seeding synths...")

    base_time = datetime.now()

    synths = [
        # Frequent Users (index 1 = grp_a1b2c3d4)
        Synth(
            id="syn_maria_silva",
            nome="Maria Silva",
            synth_group_id=groups[1].id,
            data={
                "idade": 28,
                "ocupacao": "Designer",
                "frequencia_pedidos": "5x por semana",
                "ticket_medio": "R$ 45",
            },
            created_at=(base_time - timedelta(days=50)).isoformat(),
        ),
        Synth(
            id="syn_joao_santos",
            nome="Joao Santos",
            synth_group_id=groups[1].id,
            data={
                "idade": 32,
                "ocupacao": "Desenvolvedor",
                "frequencia_pedidos": "4x por semana",
                "ticket_medio": "R$ 38",
            },
            created_at=(base_time - timedelta(days=50)).isoformat(),
        ),
        # Busy Professionals (index 2 = grp_b2c3d4e5)
        Synth(
            id="syn_ana_rodrigues",
            nome="Ana Rodrigues",
            synth_group_id=groups[2].id,
            data={
                "idade": 42,
                "ocupacao": "Gerente de Marketing",
                "frequencia_pedidos": "3x por semana",
                "ticket_medio": "R$ 65",
            },
            created_at=(base_time - timedelta(days=50)).isoformat(),
        ),
        Synth(
            id="syn_carlos_lima",
            nome="Carlos Lima",
            synth_group_id=groups[2].id,
            data={
                "idade": 38,
                "ocupacao": "Diretor Comercial",
                "frequencia_pedidos": "4x por semana",
                "ticket_medio": "R$ 72",
            },
            created_at=(base_time - timedelta(days=50)).isoformat(),
        ),
        # Family Users (index 3 = grp_c3d4e5f6)
        Synth(
            id="syn_patricia_costa",
            nome="Patricia Costa",
            synth_group_id=groups[3].id,
            data={
                "idade": 35,
                "ocupacao": "Professora",
                "frequencia_pedidos": "2x por semana",
                "ticket_medio": "R$ 120",
                "tamanho_familia": 4,
            },
            created_at=(base_time - timedelta(days=50)).isoformat(),
        ),
        Synth(
            id="syn_roberto_alves",
            nome="Roberto Alves",
            synth_group_id=groups[3].id,
            data={
                "idade": 40,
                "ocupacao": "Contador",
                "frequencia_pedidos": "3x por semana",
                "ticket_medio": "R$ 95",
                "tamanho_familia": 3,
            },
            created_at=(base_time - timedelta(days=50)).isoformat(),
        ),
    ]

    session.add_all(synths)
    session.commit()

    logger.debug(f"Created {len(synths)} synths")
    return synths


def _seed_research_executions(session: Session, experiment: Experiment, synths: list[Synth]) -> None:
    """Seed 6 completed research executions with transcripts."""
    logger.debug("Seeding research executions...")

    base_time = datetime.now()

    executions = []
    transcripts = []

    # Create 6 research executions, one for each synth
    for idx, synth in enumerate(synths):
        exec_id = f"rsrch_{experiment.id}_{idx+1}"

        execution = ResearchExecution(
            exec_id=exec_id,
            experiment_id=experiment.id,
            topic_name="Agendamento de Pedidos - User Research",
            status="completed",
            synth_count=1,
            successful_count=1,
            failed_count=0,
            model="gpt-4",
            max_turns=12,
            started_at=(base_time - timedelta(days=7-idx, hours=2)).isoformat(),
            completed_at=(base_time - timedelta(days=7-idx, hours=1, minutes=30)).isoformat(),
            additional_context="Pesquisa sobre feature de agendamento de pedidos em app de delivery",
        )
        executions.append(execution)

        # Create detailed transcript
        messages = _generate_transcript_messages(synth.nome, idx)

        transcript = Transcript(
            id=f"trans_{exec_id}",
            exec_id=exec_id,
            synth_id=synth.id,
            synth_name=synth.nome,
            status="completed",
            turn_count=len(messages),
            timestamp=execution.completed_at,
            messages=messages,
        )
        transcripts.append(transcript)

    session.add_all(executions)
    session.add_all(transcripts)
    session.commit()

    logger.debug(f"Created {len(executions)} research executions with transcripts")


def _generate_transcript_messages(synth_name: str, idx: int) -> list[dict[str, str]]:
    """Generate realistic transcript messages."""
    templates = [
        [
            {"role": "interviewer", "content": "Como voce usa o app de delivery atualmente?"},
            {"role": "synth", "content": "Eu uso praticamente todo dia, especialmente no almoco. E muito pratico."},
            {"role": "interviewer", "content": "O que voce acha da ideia de poder agendar pedidos com antecedencia?"},
            {"role": "synth", "content": "Acho interessante! As vezes eu ja sei que vou querer pedir no dia seguinte."},
            {"role": "interviewer", "content": "Voce ve alguma dificuldade em usar essa funcionalidade?"},
            {"role": "synth", "content": "Acho que teria que confiar que vai chegar no horario certo. Isso e crucial."},
            {"role": "interviewer", "content": "Em que situacoes voce usaria agendamento?"},
            {"role": "synth", "content": "Principalmente para almocos de trabalho e jantares de fim de semana."},
        ],
        [
            {"role": "interviewer", "content": "Conte sobre sua experiencia com delivery."},
            {"role": "synth", "content": "Uso bastante, mas as vezes e dificil planejar com antecedencia."},
            {"role": "interviewer", "content": "Como funciona seu dia a dia com pedidos?"},
            {"role": "synth", "content": "Geralmente decido na hora, mas preferiria poder programar."},
            {"role": "interviewer", "content": "O agendamento faria diferenca para voce?"},
            {"role": "synth", "content": "Com certeza! Eu tenho reunioes o dia todo, seria otimo ja deixar programado."},
            {"role": "interviewer", "content": "Que horarios voce agendaria?"},
            {"role": "synth", "content": "Almoco as 12h30, todos os dias uteis."},
        ],
    ]

    return templates[idx % len(templates)]


def _seed_interview_guide(session: Session, experiment: Experiment) -> None:
    """Seed interview guide for the experiment (required for 'Nova Entrevista' button)."""
    logger.debug("Seeding interview guide...")

    base_time = datetime.now()

    interview_guide = InterviewGuide(
        experiment_id=experiment.id,
        context_definition="""Voce esta testando uma nova funcionalidade de agendamento de pedidos em um app de delivery.
O usuario pode programar entregas para horarios especificos, com opcao de pedido recorrente.
A funcionalidade inclui calendario, selecao de horarios disponiveis e notificacoes.""",
        questions="""1. Como voce normalmente decide quando pedir delivery?
2. O que voce acha da ideia de poder agendar pedidos com antecedencia?
3. Em quais situacoes voce usaria o agendamento de pedidos?
4. Quais preocupacoes voce teria ao usar essa funcionalidade?
5. Como voce gostaria de ser notificado sobre pedidos agendados?
6. Voce usaria a opcao de pedido recorrente? Em quais situacoes?""",
        context_examples="""Exemplo positivo: 'Adoro a ideia! Trabalho muito e seria otimo deixar o almoco programado.'
Exemplo negativo: 'Prefiro decidir na hora, nao gosto de me comprometer com antecedencia.'
Exemplo neutro: 'Interessante, mas teria que ver como funciona na pratica.'""",
        created_at=(base_time - timedelta(days=10)).isoformat(),
    )

    session.add(interview_guide)
    session.commit()

    logger.debug(f"Created interview guide for experiment: {experiment.id}")


def _seed_documents(session: Session, experiment: Experiment) -> None:
    """Seed experiment documents: research summary and PR-FAQ."""
    logger.debug("Seeding documents...")

    base_time = datetime.now()

    documents = [
        ExperimentDocument(
            id="doc_c9d0e1f2",  # Valid format: doc_[a-f0-9]{8}
            experiment_id=experiment.id,
            document_type="research_summary",
            source_id=None,
            markdown_content="""# Research Summary: Agendamento de Pedidos

## Principais Insights

### Alta Demanda por Planejamento
- 78% dos entrevistados planejam refeicoes com antecedencia
- Profissionais ocupados sao o segmento mais interessado
- Familias valorizam muito a previsibilidade

### Barreiras Identificadas
1. **Confianca na entrega**: 65% expressaram preocupacao com atrasos
2. **Complexidade inicial**: Fluxo precisa ser muito simples
3. **Flexibilidade**: Necessidade de poder cancelar/reagendar facilmente

### Oportunidades
- Pedidos recorrentes (assinaturas) tem alto potencial
- Notificacoes proativas aumentam confianca
- Sugestoes baseadas em historico sao valorizadas""",
            doc_metadata={"version": "1.0", "word_count": 100},
            generated_at=(base_time - timedelta(days=2)).isoformat(),
            model="gpt-4",
            status="completed",
        ),

        ExperimentDocument(
            id="doc_e1f2a3b4",  # Valid format: doc_[a-f0-9]{8}
            experiment_id=experiment.id,
            document_type="prfaq",
            source_id=None,
            markdown_content="""# Press Release: Novo Agendamento de Pedidos

Hoje anunciamos o lancamento do Agendamento de Pedidos, uma nova funcionalidade
que permite aos usuarios programarem suas entregas com antecedencia.

## Como Funciona

1. Escolha o restaurante e monte seu pedido
2. Selecione data e horario desejado
3. Receba confirmacao e notificacoes
4. Opcao de tornar pedido recorrente

## FAQ

**P: Posso cancelar um pedido agendado?**
R: Sim, ate 2 horas antes do horario programado, sem custo.""",
            doc_metadata={"version": "1.0", "word_count": 80},
            generated_at=(base_time - timedelta(days=1)).isoformat(),
            model="gpt-4",
            status="completed",
        ),
    ]

    session.add_all(documents)
    session.commit()

    logger.debug(f"Created {len(documents)} documents")


if __name__ == "__main__":
    """Allow running seed directly for testing."""
    import os

    from synth_lab.infrastructure.database_v2 import create_db_engine

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set - run via: make test")
        exit(1)

    engine = create_db_engine(db_url)
    seed_database(engine)
    engine.dispose()
    print("Database seeded successfully!")
