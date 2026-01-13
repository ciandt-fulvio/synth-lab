"""
Synth Builder - Orchestrates synth assembly from all generation modules.

This module combines demographics, psychographics, disabilities,
derivations, and observable attributes to create complete synthetic personas.

Functions:
- assemble_synth(): Generate a complete synth by orchestrating all modules

Sample usage:
    from synth_lab.gen_synth.synth_builder import assemble_synth
    from synth_lab.gen_synth.config import load_config_data

    config = load_config_data()
    synth = assemble_synth(config)
    print(synth['nome'], synth['descricao'])

Expected output:
    Complete synth dict with all fields populated and validated,
    including observables (5 attributes). Latent traits are derived
    during simulation in simulation_service.py, not stored with synth.
"""

from datetime import datetime, timezone
from typing import Any

import numpy as np

from synth_lab.domain.constants.group_defaults import (
    expand_education_distribution,
    normalize_composicao_familiar_distribution,
)
from synth_lab.gen_synth import (
    demographics,
    derivations,
    disabilities,
    psychographics,
    validation,
)
from synth_lab.gen_synth.simulation_attributes import (
    generate_observables_correlated,
)
from synth_lab.gen_synth.utils import gerar_id


def assemble_synth(
    config: dict[str, Any],
    rng: np.random.Generator | None = None,
) -> dict[str, Any]:
    """
    Assemble a complete synth by orchestrating all generation modules.

    This function generates a coherent synthetic persona by:
    1. Generating demographics (age, gender, location, education, income, occupation)
    2. Generating name based on demographics
    3. Generating psychographics (interests, cognitive contract)
    4. Generating disabilities (if applicable)
    5. Generating observables (correlated with demographics)
    6. Generating photo link from name
    7. Assembling complete synth
    8. Deriving description from complete synth

    Note: Latent traits are NOT generated here. They are derived during
    simulation in simulation_service.py and stored in synth_outcomes.

    Args:
        config: Configuration dict with 'ibge', 'occupations', 'interests_hobbies'
        rng: Optional NumPy random generator for reproducibility

    Returns:
        dict: Complete synth with all fields populated, including observables.
              observables are stored directly (not nested under simulation_attributes).
    """
    # Generate unique ID
    synth_id = gerar_id(tamanho=6)

    # Create RNG if not provided (for observable generation)
    if rng is None:
        rng = np.random.default_rng()

    # 1. Generate demographics
    demografia = demographics.generate_demographics(config)

    # 2. Generate name based on demographics
    nome = demographics.generate_name(demografia)

    # 3. Generate psychographics (interests, cognitive contract)
    psicografia = psychographics.generate_psychographics(config)

    # 4. Generate disabilities
    deficiencias = disabilities.generate_disabilities(config["ibge"])

    # 5. Generate observables (correlated with demographics)
    # Extract demographic factors for correlation
    idade = demografia.get("idade")
    escolaridade = demografia.get("escolaridade")
    composicao_familiar = demografia.get("composicao_familiar")

    observables = generate_observables_correlated(
        rng=rng,
        deficiencias=deficiencias,
        escolaridade=escolaridade,
        composicao_familiar=composicao_familiar,
        idade=idade,
    )

    # 6. Generate photo link
    link_photo = derivations.generate_photo_link(nome)

    # 7. Assemble complete synth (needed for description)
    synth = {
        "id": synth_id,
        "nome": nome,
        "descricao": "",  # Placeholder, will be filled after
        "link_photo": link_photo,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "version": "2.3.0",  # Bumped version for observables-only model
        "demografia": demografia,
        "psicografia": psicografia,
        "deficiencias": deficiencias,
        "observables": observables.model_dump(),
    }

    # 8. Derive description (needs complete synth)
    descricao = derivations.derive_description(synth)
    synth["descricao"] = descricao

    return synth


def assemble_synth_with_config(
    config: dict[str, Any],
    group_config: dict[str, Any],
    rng: np.random.Generator | None = None,
) -> dict[str, Any]:
    """
    Assemble a synth using custom group configuration distributions.

    This function generates a synthetic persona using custom distributions
    from the group_config instead of IBGE defaults.

    Args:
        config: Base configuration dict with 'ibge', 'occupations', 'interests_hobbies'
        group_config: Custom distributions with:
            - distributions.idade: Age distribution (4 buckets)
            - distributions.escolaridade: Education distribution (4 buckets)
            - distributions.deficiencias: Disability config (rate + severity dist)
            - distributions.composicao_familiar: Family composition distribution
            - distributions.domain_expertise: Beta params (alpha, beta)
        rng: Optional NumPy random generator for reproducibility

    Returns:
        dict: Complete synth with all fields populated using custom distributions.
    """
    # Generate unique ID
    synth_id = gerar_id(tamanho=6)

    # Create RNG if not provided
    if rng is None:
        rng = np.random.default_rng()

    # Extract custom distributions
    distributions = group_config.get("distributions", {})

    # Build custom_distributions for demographics module
    custom_distributions: dict[str, Any] = {}

    # Age distribution (convert alias keys if needed)
    idade_dist = distributions.get("idade", {})
    if idade_dist:
        custom_distributions["idade"] = {
            "15-29": idade_dist.get("15-29", idade_dist.get("faixa_15_29", 0.25)),
            "30-44": idade_dist.get("30-44", idade_dist.get("faixa_30_44", 0.25)),
            "45-59": idade_dist.get("45-59", idade_dist.get("faixa_45_59", 0.25)),
            "60+": idade_dist.get("60+", idade_dist.get("faixa_60_plus", 0.25)),
        }

    # Education distribution (expand from 4-level to 8-level)
    escolaridade_dist = distributions.get("escolaridade", {})
    if escolaridade_dist:
        custom_distributions["escolaridade"] = expand_education_distribution(escolaridade_dist)

    # Family composition distribution (convert internal keys to display names)
    composicao_dist = distributions.get("composicao_familiar", {})
    if composicao_dist:
        custom_distributions["composicao_familiar"] = normalize_composicao_familiar_distribution(
            composicao_dist
        )

    # 1. Generate demographics with custom distributions
    demografia = demographics.generate_demographics(config, custom_distributions)

    # 2. Generate name based on demographics
    nome = demographics.generate_name(demografia)

    # 3. Generate psychographics (interests, cognitive contract)
    psicografia = psychographics.generate_psychographics(config)

    # 4. Generate disabilities with custom rate and severity
    defic_config = distributions.get("deficiencias", {})
    custom_rate = defic_config.get("taxa_com_deficiencia")
    custom_severity = defic_config.get("distribuicao_severidade")

    deficiencias = disabilities.generate_disabilities(
        config["ibge"],
        custom_rate=custom_rate,
        custom_severity_dist=custom_severity,
    )

    # 5. Generate observables with custom domain expertise params
    idade = demografia.get("idade")
    escolaridade = demografia.get("escolaridade")
    composicao_familiar = demografia.get("composicao_familiar")

    domain_expertise_config = distributions.get("domain_expertise", {})
    expertise_alpha = domain_expertise_config.get("alpha", 3.0)
    expertise_beta = domain_expertise_config.get("beta", 3.0)

    observables = generate_observables_correlated(
        rng=rng,
        deficiencias=deficiencias,
        escolaridade=escolaridade,
        composicao_familiar=composicao_familiar,
        idade=idade,
        expertise_alpha=expertise_alpha,
        expertise_beta=expertise_beta,
    )

    # 6. Generate photo link
    link_photo = derivations.generate_photo_link(nome)

    # 7. Assemble complete synth
    synth = {
        "id": synth_id,
        "nome": nome,
        "descricao": "",
        "link_photo": link_photo,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "version": "2.3.0",
        "demografia": demografia,
        "psicografia": psicografia,
        "deficiencias": deficiencias,
        "observables": observables.model_dump(),
    }

    # 8. Derive description
    descricao = derivations.derive_description(synth)
    synth["descricao"] = descricao

    return synth


if __name__ == "__main__":
    """Validation with real data."""
    import sys

    from synth_lab.gen_synth.config import load_config_data

    print("=== Synth Builder Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Load config
    try:
        config = load_config_data()
        print("✓ Config loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        sys.exit(1)

    # Test 1: Generate single synth
    total_tests += 1
    try:
        import traceback

        synth = assemble_synth(config)

        # Verify all top-level fields exist
        required_fields = [
            "id",
            "nome",
            "descricao",
            "link_photo",
            "created_at",
            "version",
            "demografia",
            "psicografia",
            "deficiencias",
            "observables",
        ]

        missing_fields = [f for f in required_fields if f not in synth]
        if missing_fields:
            all_validation_failures.append(
                f"Single synth: Missing top-level fields: {missing_fields}"
            )
        else:
            print(f"✓ Single synth generated: {synth['nome']}")
    except Exception as e:
        traceback.print_exc()
        all_validation_failures.append(f"Single synth: Failed to generate - {e}")

    # Test 2: Verify ID format
    total_tests += 1
    if "synth" in locals():
        if len(synth["id"]) != 6 or not synth["id"].isalnum():
            all_validation_failures.append(
                f"ID format: Expected 6 alphanumeric chars, got '{synth['id']}'"
            )
        else:
            print(f"✓ ID format correct: {synth['id']}")

    # Test 3: Verify demographics coherence
    total_tests += 1
    if "synth" in locals():
        demo = synth["demografia"]

        # Verify identidade_genero is NOT present (removed)
        if "identidade_genero" in demo:
            all_validation_failures.append("Demographics: identidade_genero should not be present")

        # Check family coherence
        if demo["estado_civil"] == "solteiro":
            if demo["composicao_familiar"]["tipo"] == "casal com filhos":
                all_validation_failures.append(
                    "Family coherence: Single person cannot have 'casal com filhos'"
                )

        # Check occupation-education coherence
        if "escolaridade_minima" in str(config["occupations"]):
            # This is a simplified check - full validation happens in demographics module
            print(f"✓ Demographics coherent: {demo['ocupacao']}, {demo['escolaridade']}")

    # Test 4: Verify psychographics structure
    total_tests += 1
    if "synth" in locals():
        psico = synth["psicografia"]

        required_psico_fields = ["interesses", "contrato_cognitivo"]

        missing_psico = [f for f in required_psico_fields if f not in psico]
        if missing_psico:
            all_validation_failures.append(f"Psychographics: Missing fields: {missing_psico}")
        else:
            # Verify interests is 1-4 items
            if not (1 <= len(psico["interesses"]) <= 4):
                count = len(psico["interesses"])
                all_validation_failures.append(
                    f"Psychographics: interesses should be 1-4 items, got {count}"
                )
            # Verify cognitive contract structure
            cc = psico.get("contrato_cognitivo", {})
            if "tipo" not in cc or "perfil_cognitivo" not in cc or "regras" not in cc:
                all_validation_failures.append("Contrato cognitivo: Missing required fields")
            else:
                print(f"✓ Psychographics complete with contrato_cognitivo ({cc['tipo']})")

    # Test 5: Verify disabilities structure
    total_tests += 1
    if "synth" in locals():
        defic = synth["deficiencias"]

        required_defic_fields = ["visual", "auditiva", "motora", "cognitiva"]
        missing_defic = [f for f in required_defic_fields if f not in defic]
        if missing_defic:
            all_validation_failures.append(f"Disabilities: Missing fields: {missing_defic}")
        else:
            print(f"✓ Disabilities complete: {defic['visual']['tipo']}")

    # Test 6: Verify observables structure (latent_traits are derived during simulation)
    total_tests += 1
    if "synth" in locals():
        observables = synth.get("observables", {})
        observables_failures = []

        # Check all required observables
        required_observables = [
            "digital_literacy",
            "similar_tool_experience",
            "motor_ability",
            "time_availability",
            "domain_expertise",
        ]
        missing_obs = [f for f in required_observables if f not in observables]
        if missing_obs:
            observables_failures.append(f"Missing observables: {missing_obs}")

        # Verify all values in [0, 1]
        for field, value in observables.items():
            if not 0.0 <= value <= 1.0:
                observables_failures.append(f"Observable {field} out of range: {value}")

        # Verify latent_traits are NOT present (they're derived during simulation)
        if "latent_traits" in synth:
            observables_failures.append(
                "latent_traits should NOT be in synth (derived during simulation)"
            )
        if "simulation_attributes" in synth:
            observables_failures.append(
                "simulation_attributes should NOT be in synth (replaced by observables)"
            )

        dl = observables.get("digital_literacy", 0)
        if observables_failures:
            all_validation_failures.extend(observables_failures)
        else:
            print(f"✓ Observables complete: 5 attributes (dl={dl:.3f})")

    # Test 7: Verify derivations
    total_tests += 1
    if "synth" in locals():
        derivation_failures = []
        if len(synth["descricao"]) < 50:
            derivation_failures.append(
                f"Description: Too short (< 50 chars) - '{synth['descricao']}'"
            )
        if not synth["link_photo"].startswith("https://ui-avatars.com/api/"):
            derivation_failures.append(f"Photo link: Invalid URL - '{synth['link_photo']}'")
        if derivation_failures:
            all_validation_failures.extend(derivation_failures)
        else:
            print("✓ Derivations correct: description, photo link")

    # Test 8: Generate batch of 3 synths to verify uniqueness
    total_tests += 1
    try:
        synths_batch = [assemble_synth(config) for _ in range(3)]

        # Verify all IDs are unique
        ids = [s["id"] for s in synths_batch]
        if len(ids) != len(set(ids)):
            all_validation_failures.append(f"Batch uniqueness: Duplicate IDs found: {ids}")

        # Verify all names are different (very high probability)
        names = [s["nome"] for s in synths_batch]
        if len(set(names)) < 2:  # At least 2 different names out of 3
            all_validation_failures.append(f"Batch diversity: Names not diverse enough: {names}")

        if not all_validation_failures[-2:]:  # If no failures in this test
            print("✓ Batch of 3 synths: all unique IDs and diverse names")
    except Exception as e:
        all_validation_failures.append(f"Batch generation: Failed - {e}")

    # Test 9: Validate generated synth against schema
    total_tests += 1
    if "synth" in locals():
        try:
            is_valid, errors = validation.validate_synth(synth)
            if not is_valid:
                all_validation_failures.append(
                    f"Schema validation: Synth failed schema validation: {errors}"
                )
            else:
                print("✓ Schema validation: synth passes JSON Schema")
        except Exception as e:
            all_validation_failures.append(f"Schema validation: Error - {e}")

    # Final validation result
    print()
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Synth Builder is validated and ready for use")
        sys.exit(0)
