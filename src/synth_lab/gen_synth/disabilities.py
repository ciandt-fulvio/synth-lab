"""
Disabilities generation module for SynthLab.

This module generates disability attributes based on IBGE PNS 2019 data,
including visual, auditory, motor, and cognitive disabilities.

Functions:
- generate_disabilities(): Generate disability profile

Sample Input:
    ibge_data = config["ibge"]
    disabilities = generate_disabilities(ibge_data)

Expected Output:
    {
        "visual": {"tipo": "leve"},
        "auditiva": {"tipo": "nenhuma"},
        "motora": {"tipo": "nenhuma"},
        "cognitiva": {"tipo": "nenhuma"}
    }

Third-party packages:
- None (uses standard library only)

Data source:
- IBGE PNS 2019: ~8.4% of population has at least one disability
"""

import random
from typing import Any


def generate_disabilities(
    ibge_data: dict[str, Any],
    custom_rate: float | None = None,
    custom_severity_dist: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Gera deficiências usando distribuições IBGE PNS 2019 (8.4% pelo menos uma).

    According to IBGE PNS 2019, approximately 8.4% of the Brazilian population
    has at least one disability. This function generates realistic disability
    profiles based on these statistics.

    Args:
        ibge_data: IBGE configuration data including disability distributions
        custom_rate: Custom disability rate (0.0 to 1.0). If None, uses IBGE rate.
        custom_severity_dist: Custom severity distribution dict with keys:
            nenhuma, leve, moderada, severa, total. Must sum to 1.0.
            If None, uses uniform distribution for severity.

    Returns:
        dict[str, Any]: Disability profile with visual, auditory, motor, and cognitive attributes
    """
    deficiencias_dist = ibge_data["deficiencias"]

    # Determine disability rate
    if custom_rate is not None:
        tem_deficiencia = random.random() < custom_rate
    else:
        tem_deficiencia = random.random() > deficiencias_dist["nenhuma"]

    if not tem_deficiencia:
        return {
            "visual": {"tipo": "nenhuma"},
            "auditiva": {"tipo": "nenhuma"},
            "motora": {"tipo": "nenhuma"},
            "cognitiva": {"tipo": "nenhuma"},
        }

    # Determine severity distribution
    if custom_severity_dist:
        # Use weighted choice based on custom severity distribution
        severity_weights = {
            "nenhuma": custom_severity_dist.get("nenhuma", 0.2),
            "leve": custom_severity_dist.get("leve", 0.2),
            "moderada": custom_severity_dist.get("moderada", 0.2),
            "severa": custom_severity_dist.get("severa", 0.2),
            "total": custom_severity_dist.get("total", 0.2),
        }

        def weighted_severity(options_for_total: str) -> str:
            """Choose severity based on weights, mapping 'total' to specific type."""
            severity = _weighted_choice(severity_weights)
            if severity == "total":
                return options_for_total
            return severity

        def _weighted_choice(weights: dict[str, float]) -> str:
            """Helper for weighted random choice."""
            items = list(weights.keys())
            probs = list(weights.values())
            return random.choices(items, weights=probs, k=1)[0]

        return {
            "visual": {"tipo": weighted_severity("cegueira")},
            "auditiva": {"tipo": weighted_severity("surdez")},
            "motora": {"tipo": weighted_severity("severa")},  # motora maps total to severa
            "cognitiva": {"tipo": weighted_severity("severa")},  # cognitiva maps total to severa
        }

    # Default: uniform random distribution for each disability type
    return {
        "visual": {"tipo": random.choice(["nenhuma", "leve", "moderada", "severa", "cegueira"])},
        "auditiva": {"tipo": random.choice(["nenhuma", "leve", "moderada", "severa", "surdez"])},
        "motora": {"tipo": random.choice(["nenhuma", "leve", "moderada", "severa"])},
        "cognitiva": {"tipo": random.choice(["nenhuma", "leve", "moderada", "severa"])},
    }


if __name__ == "__main__":
    """Validation block - test with real data."""
    import sys

    from .config import load_config_data

    print("=== Disabilities Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Load config
    try:
        config = load_config_data()
    except Exception as e:
        print(f"Failed to load config: {e}")
        sys.exit(1)

    # Test 1: Generate disabilities
    total_tests += 1
    try:
        disabilities = generate_disabilities(config["ibge"])

        required_fields = ["visual", "auditiva", "motora", "cognitiva"]
        for field in required_fields:
            if field not in disabilities:
                all_validation_failures.append(f"Missing field: {field}")

        if "tipo" not in disabilities["visual"]:
            all_validation_failures.append("Missing tipo in visual")
        elif disabilities["visual"]["tipo"] not in [
            "nenhuma",
            "leve",
            "moderada",
            "severa",
            "cegueira",
        ]:
            all_validation_failures.append(f"Invalid visual tipo: {disabilities['visual']['tipo']}")

        if "tipo" not in disabilities["auditiva"]:
            all_validation_failures.append("Missing tipo in auditiva")
        elif disabilities["auditiva"]["tipo"] not in [
            "nenhuma",
            "leve",
            "moderada",
            "severa",
            "surdez",
        ]:
            all_validation_failures.append(
                f"Invalid auditiva tipo: {disabilities['auditiva']['tipo']}"
            )

        if "tipo" not in disabilities["motora"]:
            all_validation_failures.append("Missing tipo in motora")
        elif disabilities["motora"]["tipo"] not in ["nenhuma", "leve", "moderada", "severa"]:
            all_validation_failures.append(f"Invalid motora tipo: {disabilities['motora']['tipo']}")

        if "tipo" not in disabilities["cognitiva"]:
            all_validation_failures.append("Missing tipo in cognitiva")
        elif disabilities["cognitiva"]["tipo"] not in ["nenhuma", "leve", "moderada", "severa"]:
            all_validation_failures.append(
                f"Invalid cognitiva tipo: {disabilities['cognitiva']['tipo']}"
            )

        if not any(f.startswith("Test 1") for f in all_validation_failures):
            print(
                f"Test 1: generate_disabilities() -> "
                f"visual={disabilities['visual']['tipo']}, "
                f"motora={disabilities['motora']['tipo']}"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 1 (generate_disabilities): {str(e)}")

    # Test 2: Verify disability distribution (most should have no disabilities)
    total_tests += 1
    try:
        disability_counts = {"has_disability": 0, "no_disability": 0}

        for _ in range(100):
            disabilities = generate_disabilities(config["ibge"])
            # Check if has any disability
            has_any = (
                disabilities["visual"]["tipo"] != "nenhuma"
                or disabilities["auditiva"]["tipo"] != "nenhuma"
                or disabilities["motora"]["tipo"] != "nenhuma"
                or disabilities["cognitiva"]["tipo"] != "nenhuma"
            )
            if has_any:
                disability_counts["has_disability"] += 1
            else:
                disability_counts["no_disability"] += 1

        # According to IBGE, ~8.4% have disabilities, so in 100 samples expect ~8-12
        # Allow some variance: 3-20%
        disability_pct = (disability_counts["has_disability"] / 100) * 100
        if disability_pct < 3 or disability_pct > 20:
            all_validation_failures.append(
                f"Disability percentage out of expected range: {disability_pct}% (expected 3-20%)"
            )
        else:
            print(
                f"Test 2: Disability distribution -> {disability_pct}% with disabilities "
                f"(expected ~8.4%)"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 2 (disability distribution): {str(e)}")

    # Test 3: Verify all disability types appear in sample
    total_tests += 1
    try:
        visual_types = set()
        auditiva_types = set()
        motora_types = set()
        cognitiva_types = set()

        for _ in range(200):
            disabilities = generate_disabilities(config["ibge"])
            visual_types.add(disabilities["visual"]["tipo"])
            auditiva_types.add(disabilities["auditiva"]["tipo"])
            motora_types.add(disabilities["motora"]["tipo"])
            cognitiva_types.add(disabilities["cognitiva"]["tipo"])

        # Should have at least "nenhuma" and one other type for each
        if len(visual_types) < 2:
            all_validation_failures.append(f"Visual types too limited: {visual_types}")
        if len(auditiva_types) < 2:
            all_validation_failures.append(f"Auditiva types too limited: {auditiva_types}")
        if len(motora_types) < 2:
            all_validation_failures.append(f"Motora types too limited: {motora_types}")
        if len(cognitiva_types) < 2:
            all_validation_failures.append(f"Cognitiva types too limited: {cognitiva_types}")

        if not any(f.startswith("Test 3") for f in all_validation_failures):
            print(
                f"Test 3: Disability type variety -> visual={len(visual_types)}, "
                f"auditiva={len(auditiva_types)}, motora={len(motora_types)}, "
                f"cognitiva={len(cognitiva_types)}"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 3 (disability type variety): {str(e)}")

    # Test 4: Verify structure of no-disability case
    total_tests += 1
    try:
        # Force many generations to get a no-disability case
        found_no_disability = False
        for _ in range(100):
            disabilities = generate_disabilities(config["ibge"])
            # Check if all disabilities are "nenhuma"
            if (
                disabilities["visual"]["tipo"] == "nenhuma"
                and disabilities["auditiva"]["tipo"] == "nenhuma"
                and disabilities["motora"]["tipo"] == "nenhuma"
                and disabilities["cognitiva"]["tipo"] == "nenhuma"
            ):
                found_no_disability = True
                break

        if found_no_disability:
            print("Test 4: No-disability case structure valid")
        else:
            all_validation_failures.append("Could not find no-disability case in 100 samples")
    except Exception as e:
        all_validation_failures.append(f"Test 4 (no-disability structure): {str(e)}")

    # Test 5: Batch consistency test
    total_tests += 1
    try:
        batch_errors = []
        for i in range(20):
            disabilities = generate_disabilities(config["ibge"])

            # Verify all fields exist and have valid values
            if disabilities["visual"]["tipo"] not in [
                "nenhuma",
                "leve",
                "moderada",
                "severa",
                "cegueira",
            ]:
                batch_errors.append(
                    f"Batch {i}: Invalid visual tipo: {disabilities['visual']['tipo']}"
                )
            if disabilities["auditiva"]["tipo"] not in [
                "nenhuma",
                "leve",
                "moderada",
                "severa",
                "surdez",
            ]:
                batch_errors.append(
                    f"Batch {i}: Invalid auditiva tipo: {disabilities['auditiva']['tipo']}"
                )
            if disabilities["motora"]["tipo"] not in ["nenhuma", "leve", "moderada", "severa"]:
                batch_errors.append(
                    f"Batch {i}: Invalid motora tipo: {disabilities['motora']['tipo']}"
                )
            if disabilities["cognitiva"]["tipo"] not in ["nenhuma", "leve", "moderada", "severa"]:
                batch_errors.append(
                    f"Batch {i}: Invalid cognitiva tipo: {disabilities['cognitiva']['tipo']}"
                )

        if batch_errors:
            all_validation_failures.extend(batch_errors)
        else:
            print("Test 5: Batch of 20 disabilities all valid")
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
