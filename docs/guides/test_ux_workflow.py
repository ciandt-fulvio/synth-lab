"""
Workflow completo de análise UX - Seguindo as 6 fases do plan.md.

Execute com: uv run python docs/guides/test_ux_workflow.py

Pode usar uma simulação existente:
  export SIM_ID=sim_xxx
  uv run python docs/guides/test_ux_workflow.py

Ou criar uma nova (comportamento padrão se SIM_ID não estiver definido)

Fases:
  1. Visão Geral (Overview)
  2. Localização (Localization)
  3. Segmentação (Clustering/Personas)
  4. Casos Especiais (Outliers/Extreme Cases)
  5. Explicabilidade (SHAP/PDP)
  6. Insights LLM
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

BASE_URL = "http://localhost:8000/simulation"
DEBUG = False  # Ativa prints detalhados

# Simulação existente (via env var) ou None para criar nova
EXISTING_SIM_ID = os.getenv("SIM_ID")

# Lista global para coletar todas as falhas
ALL_FAILURES: list[dict[str, Any]] = []


def debug(label: str, data: Any, indent: int = 2) -> None:
    """Print debug information if DEBUG is enabled."""
    if DEBUG:
        print(f"\n{'=' * 60}")
        print(f"DEBUG [{label}]")
        print(f"{'=' * 60}")
        if isinstance(data, dict):
            print(json.dumps(data, indent=indent, default=str))
        elif isinstance(data, list):
            print(json.dumps(data, indent=indent, default=str))
        else:
            print(data)
        print(f"{'=' * 60}\n")


def request_with_debug(
    method: str,
    url: str,
    json_data: dict | None = None,
    params: dict | None = None,
    endpoint_name: str = "",
) -> dict:
    """Make a request with detailed debug output and failure tracking."""
    full_url = url
    if params:
        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        full_url = f"{url}?{param_str}"

    print(f"\n>>> {method.upper()} {full_url}")
    if json_data:
        debug("Request Body", json_data)

    start_time = time.time()

    try:
        if method.lower() == "get":
            response = requests.get(url, params=params, timeout=30)
        elif method.lower() == "post":
            response = requests.post(url, json=json_data, params=params, timeout=30)
        elif method.lower() == "delete":
            response = requests.delete(url, params=params, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")

        elapsed_ms = (time.time() - start_time) * 1000

        print(f"<<< Status: {response.status_code} ({elapsed_ms:.1f}ms)")

        # Handle 204 No Content (e.g., DELETE operations)
        if response.status_code == 204:
            return {"status": "success", "status_code": 204}

        if response.status_code >= 400:
            error_text = response.text
            print(f"ERROR: {error_text}")
            debug("Error Response", error_text)

            # Registrar falha
            ALL_FAILURES.append(
                {
                    "endpoint": endpoint_name or full_url,
                    "method": method.upper(),
                    "status_code": response.status_code,
                    "error": error_text,
                    "url": full_url,
                }
            )

            return {"error": error_text, "status_code": response.status_code}

        try:
            result = response.json()
            debug("Response", result)
            return result
        except json.JSONDecodeError:
            print(f"WARNING: Response is not JSON: {response.text[:200]}")
            return {"raw": response.text}

    except requests.exceptions.RequestException as e:
        print(f"REQUEST ERROR: {e}")
        # Registrar falha de conexão
        ALL_FAILURES.append(
            {
                "endpoint": endpoint_name or full_url,
                "method": method.upper(),
                "status_code": 0,
                "error": str(e),
                "url": full_url,
            }
        )
        return {"error": str(e), "status_code": 0}


def separator(title: str) -> None:
    """Print a section separator."""
    print("\n")
    print("#" * 80)
    print(f"# {title}")
    print("#" * 80)


# =============================================================================
# SETUP - Criar scorecard e simulação
# =============================================================================


def setup_simulation() -> tuple[str, dict]:
    """
    Setup simulation for testing.

    If EXISTING_SIM_ID is set, uses that simulation.
    Otherwise, creates a new scorecard and simulation.
    """
    if EXISTING_SIM_ID:
        separator("SETUP - Usando Simulação Existente")
        print(f"\n📌 Usando simulação: {EXISTING_SIM_ID}")
        print("   (fornecida via variável de ambiente SIM_ID)")

        # Buscar dados da simulação existente
        print("\n[1/1] Buscando dados da simulação...")
        simulation = request_with_debug(
            "get",
            f"{BASE_URL}/simulations/{EXISTING_SIM_ID}",
            endpoint_name="GET /simulations/{id}",
        )

        if "error" in simulation:
            print(f"FATAL: Simulação {EXISTING_SIM_ID} não encontrada!")
            print("   Verifique se o ID está correto ou remova a variável SIM_ID")
            sys.exit(1)

        outcomes = simulation.get("aggregated_outcomes", {})
        print(f"\n✓ Simulação encontrada: {EXISTING_SIM_ID}")
        print(f"  - Scorecard: {simulation.get('scorecard_id', 'N/A')}")
        print(f"  - Scenario: {simulation.get('scenario_id', 'N/A')}")
        print(f"  - Total synths: {simulation.get('total_synths', 'N/A')}")
        print(f"  - Success rate: {outcomes.get('success', 0):.1%}")
        print(f"  - Failed rate: {outcomes.get('failed', 0):.1%}")
        print(f"  - Did not try rate: {outcomes.get('did_not_try', 0):.1%}")

        return EXISTING_SIM_ID, simulation

    else:
        separator("SETUP - Criando Nova Simulação")
        print("\n💡 Para usar uma simulação existente, defina: export SIM_ID=sim_xxx")

        # 1. Criar Scorecard
        print("\n[1/2] Criando Scorecard...")
        scorecard = request_with_debug(
            "post",
            f"{BASE_URL}/scorecards",
            json_data={
                "feature_name": "Análise UX Completa - Teste de Workflow",
                "use_scenario": "Workflow de pesquisa UX com todas as fases",
                "description_text": "Feature para demonstração completa do sistema de análise UX",
                "complexity": {"score": 0.5},
                "initial_effort": {"score": 0.4},
                "perceived_risk": {"score": 0.3},
                "time_to_value": {"score": 0.6},
            },
            endpoint_name="POST /scorecards",
        )

        if "error" in scorecard:
            print("FATAL: Falha ao criar scorecard")
            sys.exit(1)

        scorecard_id = scorecard["id"]
        print(f"✓ Scorecard criado: {scorecard_id}")

        # 2. Executar Simulação
        print("\n[2/2] Executando Simulação...")
        simulation = request_with_debug(
            "post",
            f"{BASE_URL}/simulations",
            json_data={
                "scorecard_id": scorecard_id,
                "scenario_id": "baseline",
                "n_executions": 100,
                "seed": 42,
            },
            endpoint_name="POST /simulations",
        )

        if "error" in simulation:
            print("FATAL: Falha ao executar simulação")
            sys.exit(1)

        sim_id = simulation["id"]
        outcomes = simulation.get("aggregated_outcomes", {})

        print(f"\n✓ Simulação criada: {sim_id}")
        print(f"  - Total synths: {simulation.get('total_synths', 'N/A')}")
        print(f"  - Success rate: {outcomes.get('success', 0):.1%}")
        print(f"  - Failed rate: {outcomes.get('failed', 0):.1%}")
        print(f"  - Did not try rate: {outcomes.get('did_not_try', 0):.1%}")

        return sim_id, simulation


# =============================================================================
# FASE 1 - VISÃO GERAL (Overview)
# =============================================================================


def fase1_visao_geral(sim_id: str) -> dict:
    """
    Fase 1: Visão Geral - Entender o panorama da simulação.

    Endpoints:
    - GET /charts/try-vs-success
    - GET /charts/distribution
    - GET /charts/sankey
    """
    separator("FASE 1 - VISÃO GERAL (Overview)")
    results = {}

    # 1.1 Try vs Success Chart (Quadrant Analysis)
    print("\n[1.1] Try vs Success Chart - Análise de Quadrantes")
    print("     Mostra a distribuição de synths por intenção (try) vs resultado (success)")
    try_success = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/charts/try-vs-success",
        params={"attempt_rate_threshold": 0.65, "success_rate_threshold": 0.5},
    )
    results["try_success"] = try_success

    if "quadrant_counts" in try_success:
        qc = try_success["quadrant_counts"]
        print("\n  Quadrantes:")
        print(f"    Q1 (High Try, High Success) 'ok':            {qc.get('ok', 0)}")
        print(f"    Q2 (Low Try, High Success) 'discovery_issue': {qc.get('discovery_issue', 0)}")
        print(f"    Q3 (Low Try, Low Success) 'low_value':       {qc.get('low_value', 0)}")
        print(f"    Q4 (High Try, Low Success) 'usability_issue': {qc.get('usability_issue', 0)}")

    # 1.2 Distribution Chart
    print("\n[1.2] Distribution Chart - Distribuição de Outcomes")
    print("     Mostra como os outcomes estão distribuídos entre os synths")
    distribution = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/charts/distribution",
        params={"mode": "by_synth", "sort_by": "success_rate", "order": "desc", "limit": 50},
    )
    results["distribution"] = distribution

    if "summary" in distribution:
        s = distribution["summary"]
        print("\n  Summary:")
        print(f"    Avg Success:     {s.get('avg_success', 0):.1%}")
        print(f"    Avg Failed:      {s.get('avg_failed', 0):.1%}")
        print(f"    Avg Did Not Try: {s.get('avg_did_not_try', 0):.1%}")
        print(f"    Total Synths:    {s.get('total_synths', 'N/A')}")

    # 1.3 Sankey Chart
    print("\n[1.3] Sankey Chart - Fluxo de Decisões")
    print("     Visualiza o fluxo: Traits → Decision → Outcome")
    sankey = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/charts/sankey",
    )
    results["sankey"] = sankey

    if "nodes" in sankey and "links" in sankey:
        total = sankey.get("total_synths", 0)
        print(f"\n  📊 Fluxo de Decisões (Total: {total} synths):")

        # Extrair valores para análise
        links = {(link["source"], link["target"]): link for link in sankey.get("links", [])}

        # Camada 1: Tentativa
        attempted_link = links.get(("all", "attempted"))
        not_attempted_link = links.get(("all", "not_attempted"))

        print("\n     CAMADA 1 - Engajamento:")
        if attempted_link:
            val = attempted_link["value"]
            pct = attempted_link["percentage"]
            print(f"       ✓ {val:3} synths TENTARAM usar ({pct:5.1f}%)")
        if not_attempted_link:
            val = not_attempted_link["value"]
            pct = not_attempted_link["percentage"]
            print(f"       ✗ {val:3} synths NÃO tentaram ({pct:5.1f}%)")

        # Camada 2: Resultado (dos que tentaram)
        success_link = links.get(("attempted", "success"))
        failed_link = links.get(("attempted", "failed"))

        print("\n     CAMADA 2 - Resultado (dos que tentaram):")
        if success_link:
            val = success_link["value"]
            pct = success_link["percentage"]
            print(f"       ✓ {val:3} synths tiveram SUCESSO ({pct:5.1f}%)")
        if failed_link:
            val = failed_link["value"]
            pct = failed_link["percentage"]
            print(f"       ✗ {val:3} synths FALHARAM ({pct:5.1f}%)")

        # Análise Final
        if success_link and total > 0:
            success_val = success_link["value"]
            rate = (success_val / total) * 100
            print(f"\n     📈 Taxa de sucesso GERAL: {success_val}/{total} = {rate:.1f}%")

    print("\n✓ Fase 1 completa!")
    return results


# =============================================================================
# FASE 2 - LOCALIZAÇÃO (Localization)
# =============================================================================


def fase2_localizacao(sim_id: str) -> dict:
    """
    Fase 2: Localização - Identificar onde estão os problemas.

    Endpoints:
    - GET /sensitivity (pré-requisito para tornado)
    - GET /charts/failure-heatmap
    - GET /charts/scatter
    - GET /charts/tornado
    """
    separator("FASE 2 - LOCALIZAÇÃO (Localization)")
    results = {}

    # 2.1 Sensitivity Analysis (pré-requisito para tornado)
    print("\n[2.1] Sensitivity Analysis - Análise de Sensibilidade (OAT)")
    print("     Pré-requisito para o Tornado Chart")
    sensitivity = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/sensitivity",
    )
    results["sensitivity"] = sensitivity

    if "dimensions" in sensitivity:
        print(f"\n  Dimensões analisadas: {len(sensitivity['dimensions'])}")
        for dim in sensitivity.get("dimensions", [])[:5]:
            dim_name = dim.get("dimension", "unknown")
            impact = dim.get("sensitivity_index", 0)
            print(f"    - {dim_name}: sensitivity_index={impact:.3f}")

    # 2.2 Failure Heatmap
    print("\n[2.2] Failure Heatmap - Mapa de Calor de Falhas")
    print("     Mostra concentração de falhas por combinação de dimensões")
    heatmap = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/charts/failure-heatmap",
        params={
            "x_axis": "capability_mean",
            "y_axis": "trust_mean",
            "bins": 5,
            "metric": "failed_rate",
        },
    )
    results["heatmap"] = heatmap

    if "cells" in heatmap:
        print(f"\n  Total cells: {len(heatmap['cells'])}")
        # Find cell with highest failure rate
        max_cell = max(heatmap["cells"], key=lambda c: c.get("value", 0), default={})
        if max_cell:
            print("  Highest failure cell:")
            print(f"    X: {max_cell.get('x_label', 'N/A')}")
            print(f"    Y: {max_cell.get('y_label', 'N/A')}")
            print(f"    Value: {max_cell.get('value', 0):.1%}")

    # 2.3 Scatter Plot with Correlation
    print("\n[2.3] Scatter Plot - Correlação entre Dimensões e Outcomes")
    print("     Mostra relação entre uma dimensão e a taxa de sucesso")
    scatter = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/charts/scatter",
        params={
            "x_axis": "trust_mean",
            "y_axis": "success_rate",
            "show_trendline": "true",
        },
    )
    results["scatter"] = scatter

    if "correlation" in scatter:
        corr = scatter["correlation"]
        print("\n  Correlation:")
        print(f"    Pearson R: {corr.get('pearson_r', 0):.4f}")
        print(f"    R²: {corr.get('r_squared', 0):.4f}")
        print(f"    P-value: {corr.get('p_value', 0):.4e}")
        print(f"    Significant: {corr.get('is_significant', False)}")

    if "trendline" in scatter and scatter["correlation"]:
        corr = scatter["correlation"]
        print("\n  Trendline:")
        print(f"    Slope: {corr.get('trend_slope', 0):.4f}")
        print(f"    Intercept: {corr.get('trend_intercept', 0):.4f}")
        print(f"    Points: {len(scatter['trendline'])} points")

    # 2.4 Tornado Chart
    print("\n[2.4] Tornado Chart - Impacto das Dimensões")
    print("     Mostra quais dimensões têm maior impacto no outcome")
    tornado = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/charts/tornado",
    )
    results["tornado"] = tornado

    if "bars" in tornado and tornado["bars"]:
        print(f"\n  Total dimensions: {len(tornado['bars'])}")
        print("  Top 3 mais impactantes:")
        for i, bar in enumerate(tornado["bars"][:3], 1):
            dim = bar.get("dimension", "unknown")
            low = bar.get("low_value", 0)
            high = bar.get("high_value", 0)
            impact = bar.get("impact", 0)
            print(f"    {i}. {dim}: low={low:.3f}, high={high:.3f}, impact={impact:.3f}")
    else:
        print("  WARNING: Tornado chart returned no bars!")
        debug("Tornado Full Response", tornado)

    print("\n✓ Fase 2 completa!")
    return results


# =============================================================================
# FASE 3 - SEGMENTAÇÃO (Clustering/Personas)
# =============================================================================


def fase3_segmentacao(sim_id: str) -> dict:
    """
    Fase 3: Segmentação - Agrupar synths em personas.

    Ordem correta:
    1. POST /clusters (kmeans) - cria clustering E calcula elbow automaticamente
    2. GET /elbow - retorna dados de elbow calculados no passo 1
    3. GET /clusters - lista clusters
    4. POST /clusters (hierarchical) - cria clustering hierárquico
    5. GET /dendrogram - visualização do clustering hierárquico
    6. GET /clusters/{cluster_id}/radar - perfil de um cluster
    7. GET /clusters/radar-comparison - comparar todos os clusters
    8. POST /clusters/cut - cortar dendrograma
    """
    separator("FASE 3 - SEGMENTAÇÃO (Clustering/Personas)")
    results = {}

    # 3.1 Create Clusters (K-Means) - calcula elbow automaticamente
    print("\n[3.1] Create K-Means Clusters")
    print("     Agrupa synths em 3 clusters e calcula dados de elbow automaticamente")
    clusters_kmeans = request_with_debug(
        "post",
        f"{BASE_URL}/simulations/{sim_id}/clusters",
        json_data={
            "method": "kmeans",
            "n_clusters": 3,
        },
        endpoint_name="POST /clusters (kmeans)",
    )
    results["clusters_kmeans"] = clusters_kmeans

    if "silhouette_score" in clusters_kmeans:
        print(f"\n  Silhouette Score: {clusters_kmeans['silhouette_score']:.3f}")
        print("  (Quanto mais próximo de 1, melhor a separação)")

    if "clusters" in clusters_kmeans:
        print(f"\n  Clusters criados: {len(clusters_kmeans['clusters'])}")
        for cluster in clusters_kmeans["clusters"]:
            cid = cluster.get("cluster_id", "?")
            label = cluster.get("suggested_label", "Unknown")
            size = cluster.get("size", 0)
            pct = cluster.get("percentage", 0)
            success = cluster.get("avg_success_rate", 0)
            high_traits = cluster.get("high_traits", [])
            low_traits = cluster.get("low_traits", [])
            print(f"\n    Cluster {cid}: {label}")
            print(f"      Size: {size} synths ({pct:.1f}%)")
            print(f"      Avg Success Rate: {success:.1%}")
            print(f"      High Traits: {high_traits}")
            print(f"      Low Traits: {low_traits}")

    # 3.2 Elbow Method - obtém dados calculados no passo anterior
    print("\n[3.2] Elbow Method - Dados de Inércia por K")
    print("     Retorna dados calculados durante o K-Means")
    elbow = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/clusters/elbow",
        endpoint_name="GET /clusters/elbow",
    )
    results["elbow"] = elbow

    if isinstance(elbow, list) and elbow:
        print(f"\n  K values tested: {len(elbow)}")
        for point in elbow[:5]:
            k = point.get("k", 0)
            inertia = point.get("inertia", 0)
            silhouette = point.get("silhouette", 0)
            print(f"    K={k}: inertia={inertia:.2f}, silhouette={silhouette:.3f}")

    # 3.3 List Clusters
    print("\n[3.3] List Clusters - Listar clusters existentes")
    clusters_list = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/clusters",
    )
    results["clusters_list"] = clusters_list

    # 3.4 Create Hierarchical Clustering
    print("\n[3.4] Create Hierarchical Clustering")
    print("     Clustering hierárquico para dendrograma e análise de estrutura")
    clusters_hierarchical = request_with_debug(
        "post",
        f"{BASE_URL}/simulations/{sim_id}/clusters",
        json_data={
            "method": "hierarchical",
            "n_clusters": 4,
        },
        endpoint_name="POST /clusters (hierarchical)",
    )
    results["clusters_hierarchical"] = clusters_hierarchical

    if "linkage_matrix" in clusters_hierarchical:
        lm = clusters_hierarchical["linkage_matrix"]
        print(f"\n  Linkage matrix shape: {len(lm)} x {len(lm[0]) if lm else 0}")
    if "clusters" in clusters_hierarchical:
        print(f"  Clusters criados: {len(clusters_hierarchical['clusters'])}")

    # 3.5 Dendrogram - visualização do clustering hierárquico
    print("\n[3.5] Dendrogram - Visualização do Clustering Hierárquico")
    print("     Retorna dados do dendrogram calculado no passo anterior")
    dendrogram = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/clusters/dendrogram",
        params={"max_depth": 5, "color_threshold": 2.5},
        endpoint_name="GET /clusters/dendrogram",
    )
    results["dendrogram"] = dendrogram

    if "linkage_matrix" in dendrogram:
        lm = dendrogram["linkage_matrix"]
        print(f"\n  Linkage matrix shape: {len(lm)} x {len(lm[0]) if lm else 0}")
    if "dendrogram_data" in dendrogram:
        dd = dendrogram["dendrogram_data"]
        print(f"  Dendrogram leaves: {len(dd.get('ivl', []))}")
        print(f"  Dendrogram colors: {len(set(dd.get('color_list', [])))}")

    # 3.6 Radar Chart for Single Cluster
    print("\n[3.6] Radar Chart - Perfil de um Cluster (K-Means)")
    if clusters_kmeans.get("clusters"):
        first_cluster_id = clusters_kmeans["clusters"][0].get("cluster_id", 0)
        radar_single = request_with_debug(
            "get",
            f"{BASE_URL}/simulations/{sim_id}/clusters/{first_cluster_id}/radar",
            endpoint_name="GET /clusters/{id}/radar",
        )
        results["radar_single"] = radar_single

        if "dimensions" in radar_single:
            print(f"\n  Dimensões no radar: {len(radar_single['dimensions'])}")
            for dim in radar_single.get("dimensions", [])[:5]:
                name = dim.get("name", "unknown")
                value = dim.get("value", 0)
                print(f"    - {name}: {value:.3f}")
    else:
        print("  SKIP: Nenhum cluster disponível")

    # 3.7 Radar Comparison
    print("\n[3.7] Radar Comparison - Comparar todos os clusters")
    radar_comparison = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/clusters/radar-comparison",
        endpoint_name="GET /clusters/radar-comparison",
    )
    results["radar_comparison"] = radar_comparison

    if "clusters" in radar_comparison:
        print(f"\n  Clusters no comparison: {len(radar_comparison['clusters'])}")
        for cluster in radar_comparison.get("clusters", []):
            cid = cluster.get("cluster_id", "?")
            label = cluster.get("label", "Unknown")
            dims = cluster.get("dimensions", [])
            print(f"    Cluster {cid} ({label}): {len(dims)} dimensions")

    # 3.8 Cut Dendrogram
    print("\n[3.8] Cut Dendrogram - Cortar dendrograma em N clusters")
    print("     Re-corta o clustering hierárquico com número diferente de clusters")
    cut_result = request_with_debug(
        "post",
        f"{BASE_URL}/simulations/{sim_id}/clusters/cut",
        json_data={"n_clusters": 5},
        endpoint_name="POST /clusters/cut",
    )
    results["cut"] = cut_result

    if "clusters" in cut_result:
        print(f"\n  Clusters após corte: {len(cut_result['clusters'])}")

    print("\n✓ Fase 3 completa!")
    return results


# =============================================================================
# FASE 4 - CASOS ESPECIAIS (Outliers/Extreme Cases)
# =============================================================================


def fase4_casos_especiais(sim_id: str) -> dict:
    """
    Fase 4: Casos Especiais - Identificar synths para entrevistas.

    Endpoints:
    - GET /extreme-cases (piores falhas, casos inesperados)
    - GET /outliers (detecção via Isolation Forest)
    """
    separator("FASE 4 - CASOS ESPECIAIS (Outliers/Extreme Cases)")
    results = {}

    # 4.1 Extreme Cases
    print("\n[4.1] Extreme Cases - Casos Extremos para Entrevistas")
    print("     Identifica synths com comportamentos extremos")
    extreme = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/extreme-cases",
        params={
            "n_per_category": 5,
        },
    )
    results["extreme_cases"] = extreme

    # Best Successes
    if "best_successes" in extreme:
        print(f"\n  Best Successes: {len(extreme['best_successes'])}")
        for synth in extreme["best_successes"][:3]:
            sid = synth.get("synth_id", "?")
            rate = synth.get("success_rate", 0)
            summary = synth.get("profile_summary", "")[:60]
            print(f"    - {sid}: {rate:.1%} success")
            print(f"      {summary}...")

    # Worst Failures
    if "worst_failures" in extreme:
        print(f"\n  Worst Failures: {len(extreme['worst_failures'])}")
        for synth in extreme["worst_failures"][:3]:
            sid = synth.get("synth_id", "?")
            rate = synth.get("failed_rate", 0)
            summary = synth.get("profile_summary", "")[:60]
            print(f"    - {sid}: {rate:.1%} failed")
            print(f"      {summary}...")

    # Unexpected Cases
    if "unexpected_cases" in extreme:
        print(f"\n  Unexpected Cases: {len(extreme['unexpected_cases'])}")
        for synth in extreme["unexpected_cases"][:3]:
            sid = synth.get("synth_id", "?")
            category = synth.get("category", "unknown")
            explanation = synth.get("explanation", "")[:60]
            print(f"    - {sid}: {category}")
            print(f"      {explanation}...")

    # 4.2 Outliers (Isolation Forest)
    print("\n[4.2] Outliers - Detecção via Isolation Forest")
    print("     Identifica synths estatisticamente anômalos")
    outliers = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/outliers",
        params={
            "contamination": 0.1,
        },
    )
    results["outliers"] = outliers

    if "n_outliers" in outliers:
        print(f"\n  Total outliers detectados: {outliers['n_outliers']}")
        print(f"  Contamination rate: {outliers.get('contamination', 0.1):.1%}")

    if "outliers" in outliers:
        print("\n  Detalhes dos outliers:")
        for outlier in outliers["outliers"][:5]:
            sid = outlier.get("synth_id", "?")
            otype = outlier.get("outlier_type", "unknown")
            score = outlier.get("anomaly_score", 0)
            explanation = outlier.get("explanation", "")[:60]
            print(f"    - {sid}: {otype} (score={score:.3f})")
            print(f"      {explanation}...")

    print("\n✓ Fase 4 completa!")
    return results


# =============================================================================
# FASE 5 - EXPLICABILIDADE (SHAP/PDP)
# =============================================================================


def fase5_explicabilidade(sim_id: str, fase4_results: dict) -> dict:
    """
    Fase 5: Explicabilidade - Entender por que cada synth teve seu resultado.

    Endpoints:
    - GET /shap/summary - SHAP global mostrando importância de features
    - GET /shap/{synth_id} - SHAP para um synth específico
    - GET /pdp?feature=xxx - Partial Dependence Plot para uma feature
    - GET /pdp/comparison?features=xxx,yyy - Comparar PDPs de múltiplas features
    """
    separator("FASE 5 - EXPLICABILIDADE (SHAP/PDP)")
    results = {}

    # 5.1 SHAP Summary - Global Feature Importance
    print("\n[5.1] SHAP Summary - Importância Global de Features")
    print("     Mostra quais features têm maior impacto nas previsões")
    shap_summary = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/shap/summary",
        endpoint_name="GET /shap/summary",
    )
    results["shap_summary"] = shap_summary

    if "feature_importances" in shap_summary:
        print(f"\n  Model R² Score: {shap_summary.get('model_score', 0):.3f}")
        print(f"  Total Synths: {shap_summary.get('total_synths', 'N/A')}")
        print("\n  Top Features by SHAP Importance:")
        top_features = shap_summary.get("top_features", [])
        importances = shap_summary.get("feature_importances", {})
        for i, feat in enumerate(top_features[:5], 1):
            importance = importances.get(feat, 0)
            print(f"    {i}. {feat}: {importance:.4f}")

    # 5.2 SHAP Explanation for a specific synth
    print("\n[5.2] SHAP Explanation - Explicação Individual")
    print("     Explica por que um synth específico teve seu resultado")

    # Get a synth ID from extreme cases (worst failure for interesting explanation)
    synth_id_to_explain = None
    worst_failures = fase4_results.get("extreme_cases", {}).get("worst_failures", [])
    if worst_failures:
        synth_id_to_explain = worst_failures[0].get("synth_id")

    if synth_id_to_explain:
        shap_explanation = request_with_debug(
            "get",
            f"{BASE_URL}/simulations/{sim_id}/shap/{synth_id_to_explain}",
            endpoint_name="GET /shap/{synth_id}",
        )
        results["shap_explanation"] = shap_explanation

        if "contributions" in shap_explanation:
            print(f"\n  Synth: {synth_id_to_explain}")
            pred_rate = shap_explanation.get("predicted_success_rate", 0)
            actual_rate = shap_explanation.get("actual_success_rate", 0)
            baseline = shap_explanation.get("baseline_prediction", 0)
            print(f"  Predicted Success Rate: {pred_rate:.3f}")
            print(f"  Actual Success Rate: {actual_rate:.3f}")
            print(f"  Baseline Prediction: {baseline:.3f}")
            print("\n  Top Contributing Features:")
            for contrib in shap_explanation.get("contributions", [])[:5]:
                feat = contrib.get("feature_name", "unknown")
                shap_val = contrib.get("shap_value", 0)
                impact = contrib.get("impact", "unknown")
                print(f"    - {feat}: SHAP={shap_val:+.4f} ({impact})")
            print(f"\n  Explanation: {shap_explanation.get('explanation_text', 'N/A')[:200]}...")
    else:
        print("  SKIP: Nenhum synth disponível dos extreme cases")
        results["shap_explanation"] = {}

    # 5.3 PDP - Partial Dependence Plot
    print("\n[5.3] PDP - Partial Dependence Plot")
    print("     Mostra como uma feature afeta a taxa de sucesso")
    pdp_result = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/pdp",
        params={"feature": "trust_mean", "grid_resolution": 20},
        endpoint_name="GET /pdp",
    )
    results["pdp"] = pdp_result

    if "pdp_values" in pdp_result:
        print(f"\n  Feature: {pdp_result.get('feature_display_name', 'N/A')}")
        print(f"  Effect Type: {pdp_result.get('effect_type', 'N/A')}")
        print(f"  Effect Strength: {pdp_result.get('effect_strength', 0):.4f}")
        print(f"  Baseline Value: {pdp_result.get('baseline_value', 0):.3f}")
        print(f"  PDP Points: {len(pdp_result.get('pdp_values', []))}")

        # Show first and last points to illustrate the effect
        pdp_values = pdp_result.get("pdp_values", [])
        if len(pdp_values) >= 2:
            first = pdp_values[0]
            last = pdp_values[-1]
            print("\n  Effect Range:")
            first_feat = first.get("feature_value", 0)
            first_pred = first.get("predicted_success", 0)
            last_feat = last.get("feature_value", 0)
            last_pred = last.get("predicted_success", 0)
            print(f"    Min ({first_feat:.2f}): {first_pred:.3f} success rate")
            print(f"    Max ({last_feat:.2f}): {last_pred:.3f} success rate")

    # 5.4 PDP Comparison - Compare multiple features
    print("\n[5.4] PDP Comparison - Comparar Múltiplas Features")
    print("     Compara o efeito de diferentes features na taxa de sucesso")
    pdp_comparison = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/pdp/comparison",
        params={
            "features": "trust_mean,capability_mean,initial_effort_score,perceived_risk_score",
            "grid_resolution": 15,
        },
        endpoint_name="GET /pdp/comparison",
    )
    results["pdp_comparison"] = pdp_comparison

    if "pdp_results" in pdp_comparison:
        print(f"\n  Features Compared: {len(pdp_comparison.get('pdp_results', []))}")
        print(f"  Total Synths: {pdp_comparison.get('total_synths', 'N/A')}")
        print("\n  Feature Ranking by Effect Strength:")
        for i, feat in enumerate(pdp_comparison.get("feature_ranking", []), 1):
            # Find the effect strength for this feature
            for pdp in pdp_comparison.get("pdp_results", []):
                if pdp.get("feature_name") == feat:
                    effect = pdp.get("effect_strength", 0)
                    effect_type = pdp.get("effect_type", "unknown")
                    print(f"    {i}. {feat}: {effect:.4f} ({effect_type})")
                    break

    print("\n✓ Fase 5 completa!")
    return results


# =============================================================================
# FASE 6 - INSIGHTS LLM
# =============================================================================


def _generate_insight(
    sim_id: str,
    chart_type: str,
    chart_data: dict,
    label: str,
) -> tuple[str, dict]:
    """Helper function to generate insight for a chart type (for parallel execution)."""
    result = request_with_debug(
        "post",
        f"{BASE_URL}/simulations/{sim_id}/insights/{chart_type}",
        json_data={"chart_data": chart_data},
        endpoint_name=f"POST /insights/{chart_type}",
    )
    return label, result


def fase6_insights_llm(
    sim_id: str,
    fase1_results: dict,
    fase2_results: dict,
    fase3_results: dict,
) -> dict:
    """
    Fase 6: Insights LLM - Gerar insights automáticos via IA.

    Endpoints:
    - DELETE /insights - Limpar cache de insights
    - POST /insights/{chart_type} - Gerar insight para um tipo de gráfico
    - GET /insights - Listar todos os insights cacheados
    - POST /insights/executive-summary - Gerar resumo executivo

    Note: Steps 6.2-6.5 are executed in parallel for better performance.
    """
    separator("FASE 6 - INSIGHTS LLM")
    results = {}

    # 6.1 Clear any existing insights (start fresh)
    print("\n[6.1] Limpar insights cacheados (se existirem)")
    request_with_debug(
        "delete",
        f"{BASE_URL}/simulations/{sim_id}/insights",
        endpoint_name="DELETE /insights",
    )
    # Note: This returns 204 No Content on success

    # 6.2-6.5 Generate insights in PARALLEL
    print("\n[6.2-6.5] Gerando insights em PARALELO...")
    print("     - Try vs Success Chart")
    print("     - Sankey Chart")
    print("     - Tornado Chart")
    print("     - Clustering")

    # Prepare insight generation tasks
    insight_tasks = [
        ("try_vs_success", fase1_results.get("try_success", {}), "insight_try_success"),
        ("sankey", fase1_results.get("sankey", {}), "insight_sankey"),
        ("tornado", fase2_results.get("tornado", {}), "insight_tornado"),
        ("clustering", fase3_results.get("clusters_kmeans", {}), "insight_clustering"),
    ]

    # Execute in parallel using ThreadPoolExecutor
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_generate_insight, sim_id, chart_type, chart_data, result_key): (
                chart_type,
                result_key,
            )
            for chart_type, chart_data, result_key in insight_tasks
        }

        for future in as_completed(futures):
            chart_type, result_key = futures[future]
            try:
                label, insight_result = future.result()
                results[label] = insight_result
                print(f"\n  ✓ {chart_type} concluído")
                if "caption" in insight_result:
                    print(f"    Caption: {insight_result.get('caption', 'N/A')}")
            except Exception as e:
                print(f"\n  ✗ {chart_type} falhou: {e}")
                results[result_key] = {"error": str(e)}

    elapsed = time.time() - start_time
    print(f"\n  ⏱ Tempo total (paralelo): {elapsed:.1f}s")

    # Show detailed results for each insight
    print("\n  --- Detalhes dos Insights Gerados ---")

    # Try vs Success
    if "insight_try_success" in results and "caption" in results["insight_try_success"]:
        insight = results["insight_try_success"]
        print("\n  [6.2] Try vs Success:")
        print(f"    Explanation: {insight.get('explanation', 'N/A')[:150]}...")
        evidence = insight.get("evidence", [])
        if evidence:
            print("    Evidence:")
            for e in evidence[:2]:
                print(f"      - {e}")

    # Sankey
    if "insight_sankey" in results and "caption" in results["insight_sankey"]:
        insight = results["insight_sankey"]
        print("\n  [6.3] Sankey:")
        print(f"    Explanation: {insight.get('explanation', 'N/A')[:150]}...")

    # Tornado
    if "insight_tornado" in results and "caption" in results["insight_tornado"]:
        insight = results["insight_tornado"]
        print("\n  [6.4] Tornado:")
        print(f"    Explanation: {insight.get('explanation', 'N/A')[:150]}...")

    # Clustering
    if "insight_clustering" in results and "caption" in results["insight_clustering"]:
        insight = results["insight_clustering"]
        print("\n  [6.5] Clustering:")
        print(f"    Explanation: {insight.get('explanation', 'N/A')[:150]}...")

    # 6.6 Get all cached insights
    print("\n[6.6] Listar Todos os Insights Gerados")
    all_insights = request_with_debug(
        "get",
        f"{BASE_URL}/simulations/{sim_id}/insights",
        endpoint_name="GET /insights",
    )
    results["all_insights"] = all_insights

    if "insights" in all_insights:
        insights_dict = all_insights.get("insights", {})
        print(f"\n  Total Insights: {len(insights_dict)}")
        print(f"  Chart Types Covered: {list(insights_dict.keys())}")
        print(f"  Generated At: {all_insights.get('generated_at', 'N/A')}")

    # 6.7 Generate Executive Summary
    print("\n[6.7] Gerar Resumo Executivo")
    print("     Síntese de todos os insights em um resumo consolidado")
    executive_summary = request_with_debug(
        "post",
        f"{BASE_URL}/simulations/{sim_id}/insights/executive-summary",
        endpoint_name="POST /insights/executive-summary",
    )
    results["executive_summary"] = executive_summary

    if "executive_summary" in executive_summary:
        print(f"\n  Total Insights Analyzed: {executive_summary.get('total_insights', 0)}")
        print("\n  Executive Summary:")
        summary_text = executive_summary.get("executive_summary", "N/A")
        # Print summary in chunks for readability
        words = summary_text.split()
        line = "    "
        for word in words:
            if len(line) + len(word) > 80:
                print(line)
                line = "    " + word + " "
            else:
                line += word + " "
        if line.strip():
            print(line)

    print("\n✓ Fase 6 completa!")
    return results


# =============================================================================
# RESUMO E RECOMENDAÇÕES
# =============================================================================


def gerar_resumo(
    sim_id: str,
    simulation: dict,
    fase1: dict,
    fase2: dict,
    fase3: dict,
    fase4: dict,
    fase5: dict,
    fase6: dict,
) -> None:
    """Generate a summary with recommendations based on all phases."""
    separator("RESUMO E RECOMENDAÇÕES")

    print(f"\n🔬 SIMULAÇÃO: {sim_id}")
    print("-" * 40)

    # Use fase1 to show quadrant summary
    try_success = fase1.get("try_success", {})
    if try_success.get("quadrant_counts"):
        qc = try_success["quadrant_counts"]
        print(f"  Quadrante 'OK' (alta tentativa, alto sucesso): {qc.get('ok', 0)}")
        print(f"  Quadrante 'Usability Issue': {qc.get('usability_issue', 0)}")
        print(f"  Quadrante 'Discovery Issue': {qc.get('discovery_issue', 0)}")
        print(f"  Quadrante 'Low Value': {qc.get('low_value', 0)}")

    print("\n📊 MÉTRICAS PRINCIPAIS")
    print("-" * 40)
    outcomes = simulation.get("aggregated_outcomes", {})
    print(f"  Success Rate: {outcomes.get('success', 0):.1%}")
    print(f"  Failure Rate: {outcomes.get('failed', 0):.1%}")
    print(f"  Did Not Try Rate: {outcomes.get('did_not_try', 0):.1%}")

    print("\n🎯 DIMENSÃO MAIS IMPACTANTE")
    print("-" * 40)
    tornado = fase2.get("tornado", {})
    if tornado.get("bars"):
        top_dim = tornado["bars"][0]
        print(f"  {top_dim.get('dimension', 'N/A')}")
        print(f"  Impact: {top_dim.get('impact', 0):.3f}")
        print(f"  Range: {top_dim.get('low_value', 0):.3f} → {top_dim.get('high_value', 0):.3f}")
    else:
        print("  Não disponível")

    print("\n🧠 EXPLICABILIDADE (SHAP)")
    print("-" * 40)
    shap_summary = fase5.get("shap_summary", {})
    if shap_summary.get("top_features"):
        print(f"  Model R² Score: {shap_summary.get('model_score', 0):.3f}")
        print("  Top 3 Features:")
        importances = shap_summary.get("feature_importances", {})
        for i, feat in enumerate(shap_summary.get("top_features", [])[:3], 1):
            imp = importances.get(feat, 0)
            print(f"    {i}. {feat}: {imp:.4f}")
    else:
        print("  Não disponível")

    print("\n👥 PERSONAS IDENTIFICADAS (K-Means)")
    print("-" * 40)
    clusters = fase3.get("clusters_kmeans", {}).get("clusters", [])
    for cluster in clusters:
        label = cluster.get("suggested_label", "Unknown")
        pct = cluster.get("percentage", 0)
        success = cluster.get("avg_success_rate", 0)
        print(f"  • {label}: {pct:.0f}% dos synths, {success:.0%} success")

    print("\n🔍 CASOS PARA ENTREVISTA")
    print("-" * 40)
    extreme = fase4.get("extreme_cases", {})
    n_worst = len(extreme.get("worst_failures", []))
    n_unexpected = len(extreme.get("unexpected_cases", []))
    n_outliers = fase4.get("outliers", {}).get("n_outliers", 0)
    print(f"  • Piores falhas: {n_worst} synths")
    print(f"  • Casos inesperados: {n_unexpected} synths")
    print(f"  • Outliers detectados: {n_outliers} synths")

    print("\n💡 INSIGHTS LLM")
    print("-" * 40)
    all_insights = fase6.get("all_insights", {})
    if all_insights.get("insights"):
        insights_dict = all_insights.get("insights", {})
        print(f"  Total Insights Gerados: {len(insights_dict)}")
        print(f"  Charts Analisados: {', '.join(insights_dict.keys())}")
        # Show executive summary if available
        exec_summary = fase6.get("executive_summary", {})
        if exec_summary.get("executive_summary"):
            summary_text = exec_summary.get("executive_summary", "")
            # Show first 200 chars
            print(f"  Resumo: {summary_text[:200]}...")
    else:
        print("  Nenhum insight gerado")

    print("\n📋 PRÓXIMOS PASSOS RECOMENDADOS")
    print("-" * 40)
    print("  1. Entrevistar synths dos 'Worst Failures' para entender barreiras")
    print("  2. Analisar 'Unexpected Cases' para descobrir padrões ocultos")
    if tornado.get("bars"):
        top_dim = tornado["bars"][0].get("dimension", "N/A")
        print(f"  3. Focar em melhorar '{top_dim}' (maior impacto)")
    print("  4. Criar materiais específicos para cada persona/cluster")
    print("  5. Validar hipóteses com dados qualitativos")
    print("  6. Usar insights LLM para comunicar findings aos stakeholders")


# =============================================================================
# MAIN
# =============================================================================


def gerar_relatorio_falhas() -> None:
    """Gera relatório consolidado de todas as falhas encontradas."""
    separator("RELATÓRIO DE FALHAS")

    if not ALL_FAILURES:
        print("\n🎉 NENHUMA FALHA DETECTADA! Todos os endpoints funcionaram corretamente.")
        return

    print(f"\n❌ TOTAL DE FALHAS: {len(ALL_FAILURES)}")
    print("\nDetalhamento por status code:")

    # Agrupar por status code
    by_status: dict[int, list[dict]] = {}
    for failure in ALL_FAILURES:
        status = failure["status_code"]
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(failure)

    for status_code in sorted(by_status.keys()):
        failures = by_status[status_code]
        status_name = {
            0: "CONNECTION ERROR",
            400: "BAD REQUEST",
            404: "NOT FOUND",
            500: "INTERNAL SERVER ERROR",
        }.get(status_code, f"HTTP {status_code}")

        print(f"\n  {status_name} ({len(failures)} falhas):")
        print("  " + "-" * 76)

        for i, failure in enumerate(failures, 1):
            print(f"\n  {i}. {failure['method']} {failure['endpoint']}")
            print(f"     URL: {failure['url']}")
            error_text = failure["error"][:150]
            if len(failure["error"]) > 150:
                error_text += "..."
            print(f"     Error: {error_text}")

    # Resumo por fase
    print("\n" + "=" * 80)
    print("RESUMO POR ENDPOINT:")
    print("=" * 80)

    endpoints_with_issues = set(f["endpoint"] for f in ALL_FAILURES)
    for endpoint in sorted(endpoints_with_issues):
        failures_for_endpoint = [f for f in ALL_FAILURES if f["endpoint"] == endpoint]
        print(f"\n  ❌ {endpoint}")
        for f in failures_for_endpoint:
            print(f"     → {f['status_code']}: {f['error'][:80]}")


def main():
    """Execute the complete UX Research workflow."""
    print("\n" + "=" * 80)
    print("  WORKFLOW COMPLETO DE ANÁLISE UX")
    print("  Seguindo as 6 fases do plan.md")
    print("=" * 80)

    start_time = time.time()

    try:
        # Setup
        sim_id, simulation = setup_simulation()

        # Execute all phases
        fase1_results = fase1_visao_geral(sim_id)
        fase2_results = fase2_localizacao(sim_id)
        fase3_results = fase3_segmentacao(sim_id)
        fase4_results = fase4_casos_especiais(sim_id)
        fase5_results = fase5_explicabilidade(sim_id, fase4_results)
        fase6_results = fase6_insights_llm(sim_id, fase1_results, fase2_results, fase3_results)

        # Summary
        gerar_resumo(
            sim_id,
            simulation,
            fase1_results,
            fase2_results,
            fase3_results,
            fase4_results,
            fase5_results,
            fase6_results,
        )

        # Final stats
        elapsed = time.time() - start_time
        separator("CONCLUÍDO")
        print(f"\n✅ Workflow completo executado em {elapsed:.1f}s")
        print(f"   Simulation ID: {sim_id}")
        print(f"   Base URL: {BASE_URL}")
        print("\n   Para explorar mais:")
        print("   - OpenAPI docs: http://localhost:8000/docs")
        print(f"   - Simulation detail: GET {BASE_URL}/simulations/{sim_id}")

    finally:
        # SEMPRE gera o relatório de falhas, mesmo se houver exceção
        gerar_relatorio_falhas()


if __name__ == "__main__":
    main()
