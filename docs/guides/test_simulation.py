"""
Teste completo do sistema de Feature Impact Simulation.

Execute com: uv run python docs/guides/test_simulation.py

Pré-requisitos:
1. Servidor API rodando: uv run uvicorn synth_lab.api.main:app --reload
2. Synths no banco de dados
"""

import sys

import requests

BASE_URL = "http://localhost:8000/simulation"


def check_server():
    """Verifica se o servidor está rodando."""
    try:
        requests.get(f"{BASE_URL}/scenarios", timeout=5)
        return True
    except requests.exceptions.ConnectionError:
        return False


def main():
    print("=" * 60)
    print("  TESTE DO SISTEMA DE FEATURE IMPACT SIMULATION")
    print("=" * 60)

    # Verificar servidor
    print("\n[0] Verificando conexão com servidor...")
    if not check_server():
        print("❌ ERRO: Servidor não está rodando!")
        print("   Execute: uv run uvicorn synth_lab.api.main:app --reload")
        sys.exit(1)
    print("   ✓ Servidor disponível")

    # 1. Listar cenários
    print("\n[1] Listando cenários disponíveis...")
    try:
        scenarios = requests.get(f"{BASE_URL}/scenarios").json()
        print(f"   ✓ {len(scenarios)} cenários encontrados:")
        for s in scenarios:
            print(f"     - {s['id']}: {s['name']}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        sys.exit(1)

    # 2. Criar scorecard
    print("\n[2] Criando scorecard de teste...")
    try:
        scorecard_data = {
            "feature_name": "Feature de Teste",
            "use_scenario": "Usuário quer testar o sistema",
            "description_text": "Feature criada automaticamente para validação do sistema de simulação",
            "complexity": {"score": 0.4},
            "initial_effort": {"score": 0.3},
            "perceived_risk": {"score": 0.2},
            "time_to_value": {"score": 0.5},
        }
        response = requests.post(f"{BASE_URL}/scorecards", json=scorecard_data)
        if response.status_code != 201:
            print(f"   ❌ Erro ao criar scorecard: {response.text}")
            sys.exit(1)

        scorecard = response.json()
        scorecard_id = scorecard["id"]
        print(f"   ✓ Scorecard criado: {scorecard_id}")
        print(f"     - Feature: {scorecard['feature_name']}")
        print(f"     - Complexity: {scorecard['complexity_score']}")
        print(f"     - Initial Effort: {scorecard['initial_effort_score']}")
        print(f"     - Perceived Risk: {scorecard['perceived_risk_score']}")
        print(f"     - Time to Value: {scorecard['time_to_value_score']}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        sys.exit(1)

    # 3. Executar simulação baseline
    print("\n[3] Executando simulação (cenário baseline)...")
    try:
        sim_data = {
            "scorecard_id": scorecard_id,
            "scenario_id": "baseline",
            "n_executions": 100,
            "sigma": 0.1,
            "seed": 42,
        }
        response = requests.post(f"{BASE_URL}/simulations", json=sim_data)
        if response.status_code == 404:
            print(f"   ❌ Erro: {response.json()['detail']}")
            print("   💡 Dica: Gere synths com: uv run python -m synth_lab gensynth -n 20")
            sys.exit(1)
        if response.status_code != 201:
            print(f"   ❌ Erro: {response.text}")
            sys.exit(1)

        simulation = response.json()
        sim_id = simulation["id"]
        print(f"   ✓ Simulação executada: {sim_id}")
        print(f"     - Status: {simulation['status']}")
        print(f"     - Total synths: {simulation['total_synths']}")
        print(f"     - Execuções: {simulation['config']['n_executions']}")
        print(f"     - Tempo: {simulation['execution_time_seconds']:.4f}s")
        print("     - Resultados agregados:")
        agg = simulation["aggregated_outcomes"]
        print(f"       • Did not try: {agg['did_not_try']:.1%}")
        print(f"       • Failed:      {agg['failed']:.1%}")
        print(f"       • Success:     {agg['success']:.1%}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        sys.exit(1)

    # 4. Obter outcomes detalhados
    print("\n[4] Obtendo outcomes por synth...")
    try:
        response = requests.get(f"{BASE_URL}/simulations/{sim_id}/outcomes?limit=5")
        outcomes = response.json()
        print(f"   ✓ {outcomes['total']} outcomes encontrados")
        print("     Primeiros 5 synths:")
        for o in outcomes["outcomes"][:5]:
            print(
                f"       • {o['synth_id']}: "
                f"success={o['success_rate']:.1%}, "
                f"failed={o['failed_rate']:.1%}, "
                f"did_not_try={o['did_not_try_rate']:.1%}"
            )
    except Exception as e:
        print(f"   ❌ Erro: {e}")

    # 5. Comparar cenários
    print("\n[5] Comparando cenários...")
    print("     (mesmo scorecard, mesma seed, cenários diferentes)")
    print()
    print(f"     {'Cenário':<12} {'Success':>10} {'Failed':>10} {'Did not try':>12}")
    print("     " + "-" * 46)

    for scenario_id in ["baseline", "crisis", "first-use"]:
        try:
            sim_data = {
                "scorecard_id": scorecard_id,
                "scenario_id": scenario_id,
                "n_executions": 100,
                "seed": 42,
            }
            response = requests.post(f"{BASE_URL}/simulations", json=sim_data)
            if response.status_code == 201:
                sim = response.json()
                agg = sim["aggregated_outcomes"]
                print(
                    f"     {scenario_id:<12} "
                    f"{agg['success']:>9.1%} "
                    f"{agg['failed']:>9.1%} "
                    f"{agg['did_not_try']:>11.1%}"
                )
        except Exception as e:
            print(f"     {scenario_id:<12} ❌ Erro: {e}")

    # 6. Listar todas as simulações
    print("\n[6] Listando simulações recentes...")
    try:
        response = requests.get(f"{BASE_URL}/simulations?limit=5")
        sims = response.json()
        print(f"   ✓ {sims['total']} simulações no total")
        print("     Últimas 5:")
        for s in sims["simulations"][:5]:
            status_icon = "✓" if s["status"] == "completed" else "✗"
            print(
                f"       {status_icon} {s['id']}: "
                f"scenario={s['scenario_id']}, "
                f"synths={s['total_synths']}"
            )
    except Exception as e:
        print(f"   ❌ Erro: {e}")

    # Resultado final
    print("\n" + "=" * 60)
    print("  ✅ TODOS OS TESTES COMPLETADOS COM SUCESSO!")
    print("=" * 60)
    print(f"\nScorecard criado: {scorecard_id}")
    print(f"Simulação criada: {sim_id}")
    print("\nPróximos passos:")
    print("  1. Explore a API via Swagger: http://localhost:8000/docs")
    print("  2. Filtre simulações: GET /simulation/simulations?scorecard_id=...")
    print("  3. Gere insights LLM: POST /simulation/scorecards/{id}/generate-insights")


if __name__ == "__main__":
    main()
