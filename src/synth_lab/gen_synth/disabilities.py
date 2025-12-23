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
        "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": False},
        "cognitiva": {"tipo": "nenhuma"}
    }

Third-party packages:
- None (uses standard library only)

Data source:
- IBGE PNS 2019: ~8.4% of population has at least one disability
"""

import random
from typing import Any


def generate_disabilities(ibge_data: dict[str, Any]) -> dict[str, Any]:
    """
    Gera deficiências usando distribuições IBGE PNS 2019 (8.4% pelo menos uma).

    According to IBGE PNS 2019, approximately 8.4% of the Brazilian population
    has at least one disability. This function generates realistic disability
    profiles based on these statistics.

    Args:
        ibge_data: IBGE configuration data including disability distributions

    Returns:
        dict[str, Any]: Disability profile with visual, auditory, motor, and cognitive attributes
    """
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
            all_validation_failures.append(
                f"Invalid visual tipo: {disabilities['visual']['tipo']}")

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
            all_validation_failures.append(
                f"Invalid motora tipo: {disabilities['motora']['tipo']}")

        if "usa_cadeira_rodas" not in disabilities["motora"]:
            all_validation_failures.append(
                "Missing usa_cadeira_rodas in motora")
        elif not isinstance(disabilities["motora"]["usa_cadeira_rodas"], bool):
            all_validation_failures.append(
                f"usa_cadeira_rodas must be bool: {disabilities['motora']['usa_cadeira_rodas']}"
            )

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
                f"motora={disabilities['motora']['tipo']}, "
                f"cadeira={disabilities['motora']['usa_cadeira_rodas']}"
            )
    except Exception as e:
        all_validation_failures.append(
            f"Test 1 (generate_disabilities): {str(e)}")

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
        all_validation_failures.append(
            f"Test 2 (disability distribution): {str(e)}")

    # Test 3: Verify wheelchair usage is rare
    total_tests += 1
    try:
        wheelchair_count = 0
        for _ in range(100):
            disabilities = generate_disabilities(config["ibge"])
            if disabilities["motora"]["usa_cadeira_rodas"]:
                wheelchair_count += 1

        # Wheelchair usage should be rare (< 2% overall considering ~8% have disabilities and 10% of those use wheelchair)
        wheelchair_pct = (wheelchair_count / 100) * 100
        if wheelchair_pct > 5:
            all_validation_failures.append(
                f"Wheelchair usage too high: {wheelchair_pct}% (expected < 5%)"
            )
        else:
            print(
                f"Test 3: Wheelchair usage -> {wheelchair_pct}% (expected < 2%)")
    except Exception as e:
        all_validation_failures.append(f"Test 3 (wheelchair usage): {str(e)}")

    # Test 4: Verify all disability types appear in sample
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
            all_validation_failures.append(
                f"Visual types too limited: {visual_types}")
        if len(auditiva_types) < 2:
            all_validation_failures.append(
                f"Auditiva types too limited: {auditiva_types}")
        if len(motora_types) < 2:
            all_validation_failures.append(
                f"Motora types too limited: {motora_types}")
        if len(cognitiva_types) < 2:
            all_validation_failures.append(
                f"Cognitiva types too limited: {cognitiva_types}")

        if not any(f.startswith("Test 4") for f in all_validation_failures):
            print(
                f"Test 4: Disability type variety -> visual={len(visual_types)}, "
                f"auditiva={len(auditiva_types)}, motora={len(motora_types)}, "
                f"cognitiva={len(cognitiva_types)}"
            )
    except Exception as e:
        all_validation_failures.append(
            f"Test 4 (disability type variety): {str(e)}")

    # Test 5: Verify structure of no-disability case
    total_tests += 1
    try:
        # Force many generations to get a no-disability case
        found_no_disability = False
        for _ in range(100):
            disabilities = generate_disabilities(config["ibge"])
            if disabilities["visual"]["tipo"] == "nenhuma" and disabilities["motora"]["usa_cadeira_rodas"] is False:
                found_no_disability = True
                # Verify structure
                if (
                    disabilities["visual"]["tipo"] != "nenhuma"
                    or disabilities["auditiva"]["tipo"] != "nenhuma"
                    or disabilities["motora"]["tipo"] != "nenhuma"
                    or disabilities["cognitiva"]["tipo"] != "nenhuma"
                    or disabilities["motora"]["usa_cadeira_rodas"] is not False
                ):
                    # This is actually someone with a disability, keep looking
                    found_no_disability = False
                    continue
                break

        if found_no_disability:
            print("Test 5: No-disability case structure valid")
        else:
            all_validation_failures.append(
                "Could not find no-disability case in 100 samples")
    except Exception as e:
        all_validation_failures.append(
            f"Test 5 (no-disability structure): {str(e)}")

    # Test 6: Batch consistency test
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
                    f"Batch {i}: Invalid visual tipo: {disabilities['visual']['tipo']}")
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
                    f"Batch {i}: Invalid motora tipo: {disabilities['motora']['tipo']}")
            if not isinstance(disabilities["motora"]["usa_cadeira_rodas"], bool):
                batch_errors.append(
                    f"Batch {i}: usa_cadeira_rodas not bool: "
                    f"{disabilities['motora']['usa_cadeira_rodas']}"
                )
            if disabilities["cognitiva"]["tipo"] not in ["nenhuma", "leve", "moderada", "severa"]:
                batch_errors.append(
                    f"Batch {i}: Invalid cognitiva tipo: {disabilities['cognitiva']['tipo']}"
                )

        if batch_errors:
            all_validation_failures.extend(batch_errors)
        else:
            print("Test 6: Batch of 20 disabilities all valid")
    except Exception as e:
        all_validation_failures.append(f"Test 6 (batch consistency): {str(e)}")

    # Final validation result
    print(f"\n{'='*60}")
    if all_validation_failures:
        print(
            f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)
