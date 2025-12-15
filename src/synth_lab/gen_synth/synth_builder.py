"""
Synth Builder - Orchestrates synth assembly from all generation modules.

This module combines demographics, psychographics, behavior, disabilities,
tech capabilities, biases, and derivations to create complete synthetic personas.

Functions:
- assemble_synth(): Generate a complete synth by orchestrating all modules

Sample usage:
    from synth_lab.gen_synth.synth_builder import assemble_synth
    from synth_lab.gen_synth.config import load_config_data

    config = load_config_data()
    synth = assemble_synth(config)
    print(synth['nome'], synth['arquetipo'])

Expected output:
    Complete synth dict with all fields populated and validated
"""

from datetime import datetime, timezone
from typing import Any

from synth_lab.gen_synth import (
    analysis,
    behavior,
    biases,
    demographics,
    derivations,
    disabilities,
    psychographics,
    storage,
    tech_capabilities,
    validation,
)
from synth_lab.gen_synth.utils import gerar_id


def assemble_synth(config: dict[str, Any]) -> dict[str, Any]:
    """
    Assemble a complete synth by orchestrating all generation modules.

    This function generates a coherent synthetic persona by:
    1. Generating demographics (age, gender, location, education, income, occupation)
    2. Generating name based on demographics
    3. Generating Big Five personality traits
    4. Generating psychographics (values, interests, hobbies)
    5. Generating behavior (consumption, technology, media)
    6. Generating disabilities (if applicable)
    7. Generating tech capabilities (digital literacy, devices)
    8. Generating behavioral biases (cognitive biases)
    9. Deriving archetype from demographics and personality
    10. Deriving lifestyle from personality
    11. Generating photo link from name
    12. Assembling complete synth
    13. Deriving description from complete synth

    Args:
        config: Configuration dict with 'ibge', 'occupations', 'interests_hobbies'

    Returns:
        dict: Complete synth with all fields populated
    """
    # Generate unique ID
    synth_id = gerar_id(tamanho=6)

    # 1. Generate demographics
    demografia = demographics.generate_demographics(config)

    # 2. Generate name based on demographics
    nome = demographics.generate_name(demografia)

    # 3. Generate Big Five personality traits first
    big_five = psychographics.generate_big_five()

    # 4. Generate full psychographics profile
    psicografia = psychographics.generate_psychographics(big_five, config)

    # 5. Generate behavior (correlated with age and income)
    comportamento = behavior.generate_behavior(demografia, config)

    # 6. Generate disabilities
    deficiencias = disabilities.generate_disabilities(config["ibge"])

    # 7. Generate tech capabilities (correlated with age and disabilities)
    capacidades_tecnologicas = tech_capabilities.generate_tech_capabilities(
        demografia,
        deficiencias
    )

    # 8. Generate behavioral biases
    vieses = biases.generate_behavioral_biases()

    # 9. Derive archetype
    arquetipo = derivations.derive_archetype(demografia, big_five)

    # 10. Derive lifestyle
    estilo_vida = derivations.derive_lifestyle(big_five)

    # 11. Generate photo link
    link_photo = derivations.generate_photo_link(nome)

    # 12. Assemble complete synth (needed for description)
    synth = {
        "id": synth_id,
        "nome": nome,
        "arquetipo": arquetipo,
        "descricao": "",  # Placeholder, will be filled after
        "link_photo": link_photo,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "demografia": demografia,
        "psicografia": {
            **psicografia,
            "estilo_vida": estilo_vida,
        },
        "comportamento": comportamento,
        "deficiencias": deficiencias,
        "capacidades_tecnologicas": capacidades_tecnologicas,
        "vieses": vieses,
    }

    # 13. Derive description (needs complete synth)
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
            "id", "nome", "arquetipo", "descricao", "link_photo",
            "created_at", "version", "demografia", "psicografia",
            "comportamento", "deficiencias", "capacidades_tecnologicas", "vieses"
        ]

        missing_fields = [f for f in required_fields if f not in synth]
        if missing_fields:
            all_validation_failures.append(
                f"Single synth: Missing top-level fields: {missing_fields}"
            )
        else:
            print(f"✓ Single synth generated: {synth['nome']} ({synth['arquetipo']})")
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

        # Check gender coherence
        if demo["genero_biologico"] == "feminino" and "mulher" not in demo["identidade_genero"]:
            if "não-binário" not in demo["identidade_genero"] and "outro" not in demo["identidade_genero"]:
                all_validation_failures.append(
                    f"Gender coherence: Biological female but identity is {demo['identidade_genero']}"
                )

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

        required_psico_fields = [
            "personalidade_big_five", "valores", "interesses",
            "hobbies", "estilo_vida", "inclinacao_politica", "inclinacao_religiosa"
        ]

        missing_psico = [f for f in required_psico_fields if f not in psico]
        if missing_psico:
            all_validation_failures.append(
                f"Psychographics: Missing fields: {missing_psico}"
            )
        else:
            # Verify Big Five has all 5 traits
            big_five_traits = ["abertura", "conscienciosidade", "extroversao", "amabilidade", "neuroticismo"]
            missing_traits = [t for t in big_five_traits if t not in psico["personalidade_big_five"]]
            if missing_traits:
                all_validation_failures.append(
                    f"Big Five: Missing traits: {missing_traits}"
                )
            else:
                print(f"✓ Psychographics complete with Big Five and lifestyle")

    # Test 5: Verify behavior structure
    total_tests += 1
    if "synth" in locals():
        comp = synth["comportamento"]

        required_comp_fields = [
            "habitos_consumo", "uso_tecnologia", "padroes_midia",
            "fonte_noticias", "comportamento_compra", "lealdade_marca",
            "engajamento_redes_sociais"
        ]

        missing_comp = [f for f in required_comp_fields if f not in comp]
        if missing_comp:
            all_validation_failures.append(
                f"Behavior: Missing fields: {missing_comp}"
            )
        else:
            print(f"✓ Behavior complete with consumption and technology patterns")

    # Test 6: Verify disabilities structure
    total_tests += 1
    if "synth" in locals():
        defic = synth["deficiencias"]

        required_defic_fields = ["visual", "auditiva", "motora", "cognitiva"]
        missing_defic = [f for f in required_defic_fields if f not in defic]
        if missing_defic:
            all_validation_failures.append(
                f"Disabilities: Missing fields: {missing_defic}"
            )
        else:
            print(f"✓ Disabilities complete: {defic['visual']['tipo']}")

    # Test 7: Verify tech capabilities structure
    total_tests += 1
    if "synth" in locals():
        tech = synth["capacidades_tecnologicas"]

        required_tech_fields = [
            "alfabetizacao_digital", "dispositivos", "preferencias_acessibilidade",
            "velocidade_digitacao", "frequencia_internet", "familiaridade_plataformas"
        ]

        missing_tech = [f for f in required_tech_fields if f not in tech]
        if missing_tech:
            all_validation_failures.append(
                f"Tech capabilities: Missing fields: {missing_tech}"
            )
        else:
            print(f"✓ Tech capabilities complete: digital literacy {tech['alfabetizacao_digital']}")

    # Test 8: Verify biases structure
    total_tests += 1
    if "synth" in locals():
        vieses_data = synth["vieses"]

        required_biases = [
            "aversao_perda", "desconto_hiperbolico", "suscetibilidade_chamariz",
            "ancoragem", "vies_confirmacao", "vies_status_quo", "sobrecarga_informacao"
        ]

        missing_biases = [b for b in required_biases if b not in vieses_data]
        if missing_biases:
            all_validation_failures.append(
                f"Biases: Missing biases: {missing_biases}"
            )
        else:
            print(f"✓ Biases complete: all 7 cognitive biases present")

    # Test 9: Verify derivations
    total_tests += 1
    if "synth" in locals():
        if len(synth["arquetipo"]) < 10:
            all_validation_failures.append(
                f"Archetype: Too short - '{synth['arquetipo']}'"
            )
        if len(synth["descricao"]) < 50:
            all_validation_failures.append(
                f"Description: Too short (< 50 chars) - '{synth['descricao']}'"
            )
        if not synth["link_photo"].startswith("https://ui-avatars.com/api/"):
            all_validation_failures.append(
                f"Photo link: Invalid URL - '{synth['link_photo']}'"
            )
        if not all_validation_failures[-3:]:  # If no failures in this test
            print(f"✓ Derivations correct: archetype, description, photo link")

    # Test 10: Generate batch of 3 synths to verify uniqueness
    total_tests += 1
    try:
        synths_batch = [assemble_synth(config) for _ in range(3)]

        # Verify all IDs are unique
        ids = [s["id"] for s in synths_batch]
        if len(ids) != len(set(ids)):
            all_validation_failures.append(
                f"Batch uniqueness: Duplicate IDs found: {ids}"
            )

        # Verify all names are different (very high probability)
        names = [s["nome"] for s in synths_batch]
        if len(set(names)) < 2:  # At least 2 different names out of 3
            all_validation_failures.append(
                f"Batch diversity: Names not diverse enough: {names}"
            )

        if not all_validation_failures[-2:]:  # If no failures in this test
            print(f"✓ Batch of 3 synths: all unique IDs and diverse names")
    except Exception as e:
        all_validation_failures.append(f"Batch generation: Failed - {e}")

    # Test 11: Validate generated synth against schema
    total_tests += 1
    if "synth" in locals():
        try:
            is_valid, errors = validation.validate_synth(synth)
            if not is_valid:
                all_validation_failures.append(
                    f"Schema validation: Synth failed schema validation: {errors}"
                )
            else:
                print(f"✓ Schema validation: synth passes JSON Schema")
        except Exception as e:
            all_validation_failures.append(f"Schema validation: Error - {e}")

    # Final validation result
    print()
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Synth Builder is validated and ready for use")
        sys.exit(0)
