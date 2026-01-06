"""
Test database seeding for synth-lab.

Provides realistic test data for integration and E2E tests.
Creates a complete experiment scenario matching production usage patterns.

Seed includes:
- 1 primary experiment: "App de Delivery - Feature de Agendamento de Pedidos"
- Scorecard with detailed metrics
- 500 synths analyzed (AnalysisRun + SynthOutcomes)
- 6 completed interviews (ResearchExecution + Transcripts)
- Documents: summary + executive summary + PR-FAQ
- Exploration with 3 iterations (goal: 60% success)
- Synth groups and synths for interviews

Usage:
    from tests.fixtures.seed_test import seed_database

    engine = create_engine(DATABASE_TEST_URL)
    seed_database(engine)
"""

from datetime import datetime, timedelta
from typing import Any
import random

from loguru import logger
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from synth_lab.models.orm import (
    Experiment,
    SynthGroup,
    Synth,
    ResearchExecution,
    Transcript,
    Exploration,
    ScenarioNode,
    ExperimentDocument,
    AnalysisRun,
    SynthOutcome,
)


def seed_database(engine: Engine) -> None:
    """
    Seed test database with realistic sample data.

    Creates:
    - 1 primary experiment (delivery app scheduling feature)
    - 500 synth outcomes in analysis run
    - 6 research executions with transcripts
    - 1 exploration with 3 scenario nodes
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

        # Seed in dependency order
        experiment = _seed_primary_experiment(session)
        synth_groups = _seed_synth_groups(session)
        synths = _seed_synths(session, synth_groups)
        analysis_run = _seed_analysis_run(session, experiment, synth_count=500)
        _seed_synth_outcomes(session, analysis_run, synth_count=500)
        _seed_research_executions(session, experiment, synths)
        _seed_exploration(session, experiment, analysis_run)
        _seed_documents(session, experiment)

        session.commit()
        logger.success(f"Test database seeded successfully - {analysis_run.total_synths} synths analyzed")

    except Exception as e:
        session.rollback()
        logger.error(f"Failed to seed database: {e}")
        raise
    finally:
        session.close()


def _clear_existing_data(session: Session) -> None:
    """Clear existing test data."""
    logger.debug("Clearing existing data...")

    # Delete in reverse dependency order
    session.query(SynthOutcome).delete()
    session.query(Transcript).delete()
    session.query(ResearchExecution).delete()
    session.query(ScenarioNode).delete()
    session.query(Exploration).delete()
    session.query(ExperimentDocument).delete()
    session.query(AnalysisRun).delete()
    session.query(Synth).delete()
    session.query(SynthGroup).delete()
    session.query(Experiment).delete()

    session.commit()


def _seed_primary_experiment(session: Session) -> Experiment:
    """Seed the primary test experiment with complete scorecard."""
    logger.debug("Seeding primary experiment...")

    base_time = datetime.now()

    experiment = Experiment(
        id="exp_a1b2c3d4",  # Valid format: exp_[a-f0-9]{8}
        name="App de Delivery - Feature de Agendamento de Pedidos",
        hypothesis="Permitir agendamento de pedidos aumentará retenção em 25% e ticket médio em 15%",
        description=(
            "Funcionalidade de agendamento que permite usuários programarem entregas "
            "para horários específicos, com opção de pedido recorrente para assinaturas. "
            "Inclui notificações e gestão de agenda no app."
        ),
        status="active",
        created_at=(base_time - timedelta(days=14)).isoformat(),
        updated_at=(base_time - timedelta(days=1)).isoformat(),
        scorecard_data={
            "feature_name": "Agendamento de Pedidos",
            "scenario": "Usuário ativo do app de delivery que pede regularmente",
            "description_text": "Sistema de agendamento com calendário, horários disponíveis e pedidos recorrentes",
            "complexity": {
                "score": 0.65,
                "reasoning": "Requer integração com sistema de rotas, gestão de capacidade e notificações push"
            },
            "initial_effort": {
                "score": 0.70,
                "reasoning": "Usuário precisa aprender novo fluxo e confiar no sistema de agendamento"
            },
            "perceived_risk": {
                "score": 0.40,
                "reasoning": "Risco moderado - preocupação com atrasos e alterações de agenda"
            },
            "time_to_value": {
                "score": 0.75,
                "reasoning": "Valor percebido rapidamente na primeira entrega agendada com sucesso"
            },
        },
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
        SynthGroup(
            id="grp_a1b2c3d4",  # Valid format: grp_[a-f0-9]{8}
            name="Usuários Frequentes",
            description="Usuários que pedem 3+ vezes por semana, alta familiaridade com app",
            created_at=(base_time - timedelta(days=60)).isoformat(),
        ),
        SynthGroup(
            id="grp_b2c3d4e5",  # Valid format: grp_[a-f0-9]{8}
            name="Profissionais Ocupados",
            description="Executivos e profissionais com rotina intensa, valorizam praticidade",
            created_at=(base_time - timedelta(days=60)).isoformat(),
        ),
        SynthGroup(
            id="grp_c3d4e5f6",  # Valid format: grp_[a-f0-9]{8}
            name="Famílias",
            description="Usuários que pedem para família, planejam refeições com antecedência",
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
        # Frequent Users
        Synth(
            id="syn_maria_silva",
            nome="Maria Silva",
            synth_group_id=groups[0].id,
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
            nome="João Santos",
            synth_group_id=groups[0].id,
            data={
                "idade": 32,
                "ocupacao": "Desenvolvedor",
                "frequencia_pedidos": "4x por semana",
                "ticket_medio": "R$ 38",
            },
            created_at=(base_time - timedelta(days=50)).isoformat(),
        ),
        # Busy Professionals
        Synth(
            id="syn_ana_rodrigues",
            nome="Ana Rodrigues",
            synth_group_id=groups[1].id,
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
            synth_group_id=groups[1].id,
            data={
                "idade": 38,
                "ocupacao": "Diretor Comercial",
                "frequencia_pedidos": "4x por semana",
                "ticket_medio": "R$ 72",
            },
            created_at=(base_time - timedelta(days=50)).isoformat(),
        ),
        # Family Users
        Synth(
            id="syn_patricia_costa",
            nome="Patrícia Costa",
            synth_group_id=groups[2].id,
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
            synth_group_id=groups[2].id,
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


def _seed_analysis_run(session: Session, experiment: Experiment, synth_count: int) -> AnalysisRun:
    """Seed analysis run with specified synth count."""
    logger.debug(f"Seeding analysis run for {synth_count} synths...")

    base_time = datetime.now()

    analysis = AnalysisRun(
        id="ana_d4e5f6a7",  # Valid format: ana_[a-f0-9]{8}
        experiment_id=experiment.id,
        scenario_id="baseline",
        config={
            "model": "gpt-4",
            "temperature": 0.7,
            "synth_count": synth_count,
            "scenario_type": "baseline",
        },
        status="completed",
        started_at=(base_time - timedelta(hours=3)).isoformat(),
        completed_at=(base_time - timedelta(hours=2, minutes=15)).isoformat(),
        total_synths=synth_count,
        aggregated_outcomes={
            "success_rate": 0.62,
            "failed_rate": 0.25,
            "did_not_try_rate": 0.13,
        },
        execution_time_seconds=2700.0,
    )

    session.add(analysis)
    session.commit()

    logger.debug(f"Created analysis run: {analysis.id}")
    return analysis


def _seed_synth_outcomes(session: Session, analysis_run: AnalysisRun, synth_count: int) -> None:
    """Seed individual synth outcomes for the analysis run."""
    logger.debug(f"Seeding {synth_count} synth outcomes...")

    # Create realistic distribution of outcomes
    # Target: ~62% average success rate with variation
    outcomes = []

    for i in range(synth_count):
        # Generate realistic success rates with normal distribution around 62%
        base_success = 0.62
        variation = random.gauss(0, 0.18)  # Standard deviation of 0.18
        success_rate = max(0.0, min(1.0, base_success + variation))

        # Distribute remaining probability between failed and did_not_try
        remaining = 1.0 - success_rate
        failed_rate = remaining * random.uniform(0.6, 0.8)  # 60-80% of failures are actual failures
        did_not_try_rate = remaining - failed_rate

        outcome = SynthOutcome(
            id=f"out_{analysis_run.id}_{i+1:04d}",
            analysis_id=analysis_run.id,
            synth_id=f"syn_{i+1:04d}",
            success_rate=round(success_rate, 3),
            failed_rate=round(failed_rate, 3),
            did_not_try_rate=round(did_not_try_rate, 3),
            synth_attributes={
                "age_group": random.choice(["18-25", "26-35", "36-45", "46-55", "56+"]),
                "tech_savviness": random.choice(["low", "medium", "high"]),
                "order_frequency": random.choice(["weekly", "biweekly", "daily"]),
            },
        )
        outcomes.append(outcome)

    # Batch insert for performance
    session.bulk_save_objects(outcomes)
    session.commit()

    logger.debug(f"Created {len(outcomes)} synth outcomes")


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
            {"role": "interviewer", "content": "Como você usa o app de delivery atualmente?"},
            {"role": "synth", "content": "Eu uso praticamente todo dia, especialmente no almoço. É muito prático."},
            {"role": "interviewer", "content": "O que você acha da ideia de poder agendar pedidos com antecedência?"},
            {"role": "synth", "content": "Acho interessante! Às vezes eu já sei que vou querer pedir no dia seguinte."},
            {"role": "interviewer", "content": "Você vê alguma dificuldade em usar essa funcionalidade?"},
            {"role": "synth", "content": "Acho que teria que confiar que vai chegar no horário certo. Isso é crucial."},
            {"role": "interviewer", "content": "Em que situações você usaria agendamento?"},
            {"role": "synth", "content": "Principalmente para almoços de trabalho e jantares de fim de semana."},
        ],
        [
            {"role": "interviewer", "content": "Conte sobre sua experiência com delivery."},
            {"role": "synth", "content": "Uso bastante, mas às vezes é difícil planejar com antecedência."},
            {"role": "interviewer", "content": "Como funciona seu dia a dia com pedidos?"},
            {"role": "synth", "content": "Geralmente decido na hora, mas preferiria poder programar."},
            {"role": "interviewer", "content": "O agendamento faria diferença para você?"},
            {"role": "synth", "content": "Com certeza! Eu tenho reuniões o dia todo, seria ótimo já deixar programado."},
            {"role": "interviewer", "content": "Que horários você agendaria?"},
            {"role": "synth", "content": "Almoço às 12h30, todos os dias úteis."},
        ],
    ]

    return templates[idx % len(templates)]


def _seed_exploration(session: Session, experiment: Experiment, baseline_analysis: AnalysisRun) -> None:
    """Seed exploration with 3 scenario iterations targeting 60% success."""
    logger.debug("Seeding exploration with scenarios...")

    base_time = datetime.now()

    exploration = Exploration(
        id="expl_e5f6a7b8",  # Valid format: expl_[a-f0-9]{8}
        experiment_id=experiment.id,
        baseline_analysis_id=baseline_analysis.id,
        goal={
            "target_metric": "success_rate",
            "target_value": 0.60,
            "description": "Atingir 60% de success rate através de melhorias na UX e fluxo",
        },
        config={
            "max_depth": 3,
            "max_nodes": 10,
            "temperature": 0.7,
            "model": "gpt-4",
        },
        status="goal_achieved",
        current_depth=2,
        total_nodes=3,
        total_llm_calls=6,
        best_success_rate=0.63,
        started_at=(base_time - timedelta(days=5)).isoformat(),
        completed_at=(base_time - timedelta(days=1)).isoformat(),
    )

    session.add(exploration)
    session.commit()

    # Scenario 1: Baseline (starting point)
    node1 = ScenarioNode(
        id="node_f6a7b8c9",  # Valid format: node_[a-f0-9]{8}
        exploration_id=exploration.id,
        parent_id=None,
        depth=0,
        action_applied=None,
        action_category=None,
        rationale="Baseline scenario - starting point for exploration",
        short_action="Baseline",
        scorecard_params={
            "complexity": 0.65,
            "initial_effort": 0.70,
            "perceived_risk": 0.40,
            "time_to_value": 0.75,
        },
        simulation_results={
            "success_rate": 0.55,
            "synths_analyzed": 500,
            "avg_completion_time": 180,
        },
        execution_time_seconds=45.2,
        node_status="active",
        created_at=(base_time - timedelta(days=5)).isoformat(),
    )

    # Scenario 2: Simplified flow (iteration 1)
    node2 = ScenarioNode(
        id="node_a7b8c9d0",  # Valid format: node_[a-f0-9]{8}
        exploration_id=exploration.id,
        parent_id="node_f6a7b8c9",  # Reference to node1
        depth=1,
        action_applied="Reduzir passos de configuração de 5 para 3",
        action_category="simplification",
        rationale="Reduzir complexidade inicial para aumentar adoção",
        short_action="Simplificar fluxo",
        scorecard_params={
            "complexity": 0.50,
            "initial_effort": 0.60,
            "perceived_risk": 0.35,
            "time_to_value": 0.80,
        },
        simulation_results={
            "success_rate": 0.58,
            "synths_analyzed": 500,
            "avg_completion_time": 150,
        },
        execution_time_seconds=48.7,
        node_status="active",
        created_at=(base_time - timedelta(days=3)).isoformat(),
    )

    # Scenario 3: Tutorial + simplified flow (iteration 2 - goal achieved)
    node3 = ScenarioNode(
        id="node_b8c9d0e1",  # Valid format: node_[a-f0-9]{8}
        exploration_id=exploration.id,
        parent_id="node_a7b8c9d0",  # Reference to node2
        depth=2,
        action_applied="Adicionar tutorial interativo no primeiro uso e sugerir horários com base em histórico",
        action_category="onboarding",
        rationale="Tutorial ajuda a reduzir effort inicial e sugestões inteligentes aumentam valor percebido",
        short_action="Adicionar tutorial + sugestões",
        scorecard_params={
            "complexity": 0.45,
            "initial_effort": 0.40,
            "perceived_risk": 0.30,
            "time_to_value": 0.85,
        },
        simulation_results={
            "success_rate": 0.63,
            "synths_analyzed": 500,
            "avg_completion_time": 120,
        },
        execution_time_seconds=52.1,
        node_status="winner",
        created_at=(base_time - timedelta(days=1)).isoformat(),
    )

    session.add_all([node1, node2, node3])
    session.commit()

    logger.debug(f"Created exploration with 3 scenario nodes (goal: 60% → achieved: 63%)")


def _seed_documents(session: Session, experiment: Experiment) -> None:
    """Seed experiment documents: research summary, executive summary, and PR-FAQ."""
    logger.debug("Seeding documents...")

    base_time = datetime.now()

    documents = [
        ExperimentDocument(
            id="doc_c9d0e1f2",  # Valid format: doc_[a-f0-9]{8}
            experiment_id=experiment.id,
            document_type="research_summary",
            source_id=None,  # Research summary não tem source específico
            markdown_content="""# Research Summary: Agendamento de Pedidos

## Principais Insights

### Alta Demanda por Planejamento
- 78% dos entrevistados planejam refeições com antecedência
- Profissionais ocupados são o segmento mais interessado
- Famílias valorizam muito a previsibilidade

### Barreiras Identificadas
1. **Confiança na entrega**: 65% expressaram preocupação com atrasos
2. **Complexidade inicial**: Fluxo precisa ser muito simples
3. **Flexibilidade**: Necessidade de poder cancelar/reagendar facilmente

### Oportunidades
- Pedidos recorrentes (assinaturas) têm alto potencial
- Notificações proativas aumentam confiança
- Sugestões baseadas em histórico são valorizadas

## Métricas de Adoção
- Success rate inicial: 55%
- Success rate pós-otimização: 63%
- Meta alcançada: ✅ 60%""",
            doc_metadata={"version": "1.0", "word_count": 142},
            generated_at=(base_time - timedelta(days=2)).isoformat(),
            model="gpt-4",
            status="completed",
        ),

        ExperimentDocument(
            id="doc_d0e1f2a3",  # Valid format: doc_[a-f0-9]{8}
            experiment_id=experiment.id,
            document_type="executive_summary",
            source_id=None,  # Executive summary é único por experimento
            markdown_content="""# Executive Summary

## Recomendação
✅ **APROVAR** implementação com otimizações identificadas

## Potencial de Negócio
- Aumento estimado de 25% na retenção
- Crescimento de 15% no ticket médio
- ROI projetado: 3.2x em 12 meses

## Riscos Mitigados
- Complexidade reduzida através de tutorial interativo
- Confiança aumentada com notificações proativas
- Flexibilidade garantida com cancelamento simplificado

## Próximos Passos
1. MVP com fluxo simplificado (3 passos)
2. Tutorial no primeiro uso
3. Sistema de sugestões inteligentes
4. Programa piloto com usuários frequentes""",
            doc_metadata={"version": "1.0", "word_count": 89},
            generated_at=(base_time - timedelta(days=1, hours=12)).isoformat(),
            model="gpt-4",
            status="completed",
        ),

        ExperimentDocument(
            id="doc_e1f2a3b4",  # Valid format: doc_[a-f0-9]{8}
            experiment_id=experiment.id,
            document_type="prfaq",
            source_id=None,
            markdown_content="""# Press Release: Novo Agendamento de Pedidos

**São Paulo, [DATA]** - Hoje anunciamos o lançamento do Agendamento de Pedidos, uma nova funcionalidade que permite aos usuários programarem suas entregas com antecedência, trazendo mais controle e praticidade para o dia a dia.

## Para Quem É

Perfeito para profissionais ocupados, famílias que planejam refeições e qualquer pessoa que valorize organização e previsibilidade.

## Como Funciona

1. Escolha o restaurante e monte seu pedido
2. Selecione data e horário desejado
3. Receba confirmação e notificações
4. Opção de tornar pedido recorrente

## Benefícios

- **Planejamento**: Programe com até 7 dias de antecedência
- **Economia de tempo**: Configure pedidos recorrentes
- **Confiança**: Notificações em cada etapa
- **Flexibilidade**: Cancele ou reagende facilmente

## FAQ

**P: Posso cancelar um pedido agendado?**
R: Sim, até 2 horas antes do horário programado, sem custo.

**P: Como sei que vai chegar no horário?**
R: Você recebe notificações quando o pedido sair para entrega e pode acompanhar em tempo real.

**P: Posso agendar pedidos recorrentes?**
R: Sim! Configure uma vez e receba automaticamente nos dias/horários escolhidos.""",
            doc_metadata={"version": "1.0", "word_count": 218},
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

    db_url = os.getenv("DATABASE_TEST_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_TEST_URL or DATABASE_URL not set")
        exit(1)

    engine = create_db_engine(db_url)
    seed_database(engine)
    engine.dispose()
    print("✅ Database seeded successfully!")
