"""
Derivations module for Synth Lab.

This module generates derived attributes from existing synth data,
including archetype classification, lifestyle inference, description generation,
and photo link creation.

Functions:
- derive_archetype(): Derive archetype from demographics and personality
- derive_lifestyle(): Derive lifestyle from Big Five traits
- derive_description(): Generate textual description of synth
- generate_photo_link(): Generate avatar link

Sample Input:
    demographics = {"idade": 32, "localizacao": {"regiao": "Sudeste"}, ...}
    big_five = {"abertura": 75, "extroversao": 65, ...}
    archetype = derive_archetype(demographics, big_five)

Expected Output:
    archetype = "Adulto Sudeste Criativo"
    lifestyle = "Criativo e explorador"
    description = "Mulher de 32 anos, analista de sistemas, mora em São Paulo, SP..."
    photo_link = "https://ui-avatars.com/api/?name=Maria+Silva&size=256&background=random"

Third-party packages:
- None (uses standard library only)
"""

from typing import Any


def derive_archetype(demographics: dict[str, Any], big_five: dict[str, int]) -> str:
    """
    Gera arquétipo automaticamente: {Faixa Etária} {Região} {Perfil Psicográfico}.

    Archetypes are human-readable classifications combining:
    - Age group (Adolescente, Jovem Adulto, Adulto, Meia-Idade, Idoso)
    - Region (Norte, Nordeste, Centro-Oeste, Sudeste, Sul)
    - Dominant personality trait (Criativo, Organizado, Social, Empático, Ansioso)

    Args:
        demographics: Dictionary with demographic data (idade, localizacao)
        big_five: Dictionary with Big Five personality traits

    Returns:
        str: Archetype string (e.g., "Adulto Sudeste Criativo")
    """
    idade = demographics["idade"]
    if idade < 18:
        faixa = "Adolescente"
    elif idade < 30:
        faixa = "Jovem Adulto"
    elif idade < 45:
        faixa = "Adulto"
    elif idade < 60:
        faixa = "Meia-Idade"
    else:
        faixa = "Idoso"

    regiao = demographics["localizacao"]["regiao"]

    # Traço dominante do Big Five
    tracos = {
        "Criativo": big_five["abertura"],
        "Organizado": big_five["conscienciosidade"],
        "Social": big_five["extroversao"],
        "Empático": big_five["amabilidade"],
        "Ansioso": big_five["neuroticismo"],
    }
    perfil = max(tracos, key=tracos.get)  # type: ignore

    return f"{faixa} {regiao} {perfil}"


def derive_lifestyle(big_five: dict[str, int]) -> str:
    """
    Deriva estilo de vida dos traços Big Five.

    Lifestyle is inferred from personality traits:
    - High extraversion + low neuroticism = "Ativo e social"
    - Low extraversion + high neuroticism = "Reservado e cauteloso"
    - High openness = "Criativo e explorador"
    - High conscientiousness = "Disciplinado e focado"
    - Otherwise = "Equilibrado e moderado"

    Args:
        big_five: Dictionary with Big Five personality traits

    Returns:
        str: Lifestyle description
    """
    extroversao = big_five["extroversao"]
    neuroticismo = big_five["neuroticismo"]
    abertura = big_five["abertura"]

    if extroversao > 60 and neuroticismo < 40:
        return "Ativo e social"
    elif extroversao < 40 and neuroticismo > 60:
        return "Reservado e cauteloso"
    elif abertura > 70:
        return "Criativo e explorador"
    elif big_five["conscienciosidade"] > 70:
        return "Disciplinado e focado"
    else:
        return "Equilibrado e moderado"


def derive_description(synth_data: dict[str, Any]) -> str:
    """
    Gera descrição textual do Synth (mínimo 50 caracteres).

    Creates a human-readable description combining:
    - Gender, age, occupation, location
    - Notable personality traits
    - Interests (if description is still short)

    Args:
        synth_data: Complete synth dictionary with all attributes

    Returns:
        str: Textual description (minimum 50 characters)
    """
    demo = synth_data["demografia"]
    psico = synth_data["psicografia"]

    # Usar identidade de gênero para artigo
    identidade = demo["identidade_genero"]
    if identidade in ["mulher cis", "mulher trans"]:
        genero_artigo = "Mulher"
    elif identidade in ["homem cis", "homem trans"]:
        genero_artigo = "Homem"
    else:
        genero_artigo = "Pessoa"

    desc = f"{genero_artigo} de {demo['idade']} anos, {demo['ocupacao'].lower()}, "
    desc += f"mora em {demo['localizacao']['cidade']}, {demo['localizacao']['estado']}. "

    big_five = psico["personalidade_big_five"]
    tracos_altos = [k.capitalize() for k, v in big_five.items() if v > 60]
    if tracos_altos:
        desc += f"Possui traços marcantes de {', '.join(tracos_altos[:2])}. "

    # Adicionar informação sobre interesses se descrição ainda curta
    if len(desc) < 50 and psico["interesses"]:
        desc += f"Interesses: {', '.join(psico['interesses'][:3])}."

    return desc


def generate_photo_link(name: str) -> str:
    """
    Gera link para foto usando ui-avatars.com API.

    Creates a URL to generate an avatar image based on the person's name.
    The avatar is a simple colored square with initials.

    API documentation: https://ui-avatars.com/

    Args:
        name: Full name of the person

    Returns:
        str: URL to avatar image (256x256px, random background color)
    """
    name_encoded = name.replace(" ", "+")
    return f"https://ui-avatars.com/api/?name={name_encoded}&size=256&background=random"


if __name__ == "__main__":
    """Validation block - test with real data."""
    import sys

    print("=== Derivations Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Derive archetype for young adult
    total_tests += 1
    try:
        demo = {"idade": 25, "localizacao": {"regiao": "Sudeste"}}
        big_five = {
            "abertura": 75,
            "conscienciosidade": 50,
            "extroversao": 45,
            "amabilidade": 55,
            "neuroticismo": 40,
        }
        archetype = derive_archetype(demo, big_five)

        # Should contain age group, region, and personality
        if "Jovem Adulto" not in archetype:
            all_validation_failures.append(f"Archetype should contain 'Jovem Adulto': {archetype}")
        if "Sudeste" not in archetype:
            all_validation_failures.append(f"Archetype should contain 'Sudeste': {archetype}")
        if "Criativo" not in archetype:
            all_validation_failures.append(
                f"Archetype should contain 'Criativo' (highest trait): {archetype}"
            )

        if not any(f.startswith("Test 1") for f in all_validation_failures):
            print(f"Test 1: derive_archetype() -> {archetype}")
    except Exception as e:
        all_validation_failures.append(f"Test 1 (derive_archetype young): {str(e)}")

    # Test 2: Derive archetype for elderly
    total_tests += 1
    try:
        demo = {"idade": 70, "localizacao": {"regiao": "Sul"}}
        big_five = {
            "abertura": 40,
            "conscienciosidade": 80,
            "extroversao": 50,
            "amabilidade": 60,
            "neuroticismo": 45,
        }
        archetype = derive_archetype(demo, big_five)

        if "Idoso" not in archetype:
            all_validation_failures.append(f"Archetype should contain 'Idoso': {archetype}")
        if "Sul" not in archetype:
            all_validation_failures.append(f"Archetype should contain 'Sul': {archetype}")
        if "Organizado" not in archetype:
            all_validation_failures.append(
                f"Archetype should contain 'Organizado' (highest trait): {archetype}"
            )

        if not any(f.startswith("Test 2") for f in all_validation_failures):
            print(f"Test 2: derive_archetype(elderly) -> {archetype}")
    except Exception as e:
        all_validation_failures.append(f"Test 2 (derive_archetype elderly): {str(e)}")

    # Test 3: Derive lifestyle - active and social
    total_tests += 1
    try:
        big_five = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 75,
            "amabilidade": 60,
            "neuroticismo": 30,
        }
        lifestyle = derive_lifestyle(big_five)

        if lifestyle != "Ativo e social":
            all_validation_failures.append(
                f"Expected 'Ativo e social', got '{lifestyle}' "
                f"(extroversao=75, neuroticismo=30)"
            )
        else:
            print(f"Test 3: derive_lifestyle(high extraversion) -> {lifestyle}")
    except Exception as e:
        all_validation_failures.append(f"Test 3 (derive_lifestyle active): {str(e)}")

    # Test 4: Derive lifestyle - reserved and cautious
    total_tests += 1
    try:
        big_five = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 30,
            "amabilidade": 60,
            "neuroticismo": 70,
        }
        lifestyle = derive_lifestyle(big_five)

        if lifestyle != "Reservado e cauteloso":
            all_validation_failures.append(
                f"Expected 'Reservado e cauteloso', got '{lifestyle}' "
                f"(extroversao=30, neuroticismo=70)"
            )
        else:
            print(f"Test 4: derive_lifestyle(low extraversion) -> {lifestyle}")
    except Exception as e:
        all_validation_failures.append(f"Test 4 (derive_lifestyle reserved): {str(e)}")

    # Test 5: Derive lifestyle - creative and explorer
    total_tests += 1
    try:
        big_five = {
            "abertura": 85,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 55,
            "neuroticismo": 50,
        }
        lifestyle = derive_lifestyle(big_five)

        if lifestyle != "Criativo e explorador":
            all_validation_failures.append(
                f"Expected 'Criativo e explorador', got '{lifestyle}' (abertura=85)"
            )
        else:
            print(f"Test 5: derive_lifestyle(high openness) -> {lifestyle}")
    except Exception as e:
        all_validation_failures.append(f"Test 5 (derive_lifestyle creative): {str(e)}")

    # Test 6: Derive description
    total_tests += 1
    try:
        synth = {
            "demografia": {
                "idade": 32,
                "identidade_genero": "mulher cis",
                "ocupacao": "Analista de Sistemas",
                "localizacao": {"cidade": "São Paulo", "estado": "SP"},
            },
            "psicografia": {
                "personalidade_big_five": {
                    "abertura": 75,
                    "conscienciosidade": 65,
                    "extroversao": 45,
                    "amabilidade": 55,
                    "neuroticismo": 40,
                },
                "interesses": ["tecnologia", "cinema", "leitura"],
            },
        }
        description = derive_description(synth)

        # Verify minimum length
        if len(description) < 50:
            all_validation_failures.append(
                f"Description too short: {len(description)} chars (minimum 50)"
            )

        # Verify contains key information
        if "32 anos" not in description:
            all_validation_failures.append("Description should contain age")
        if "analista de sistemas" not in description.lower():
            all_validation_failures.append("Description should contain occupation")
        if "São Paulo" not in description:
            all_validation_failures.append("Description should contain city")

        if not any(f.startswith("Test 6") for f in all_validation_failures):
            print(f"Test 6: derive_description() -> {len(description)} chars")
            print(f"  Sample: {description[:80]}...")
    except Exception as e:
        all_validation_failures.append(f"Test 6 (derive_description): {str(e)}")

    # Test 7: Generate photo link
    total_tests += 1
    try:
        name = "Maria Silva Santos"
        photo_link = generate_photo_link(name)

        if not photo_link.startswith("https://ui-avatars.com/api/"):
            all_validation_failures.append(f"Invalid photo link URL: {photo_link}")
        if "name=Maria+Silva+Santos" not in photo_link:
            all_validation_failures.append(f"Photo link should contain encoded name: {photo_link}")
        if "size=256" not in photo_link:
            all_validation_failures.append(f"Photo link should have size=256: {photo_link}")
        if "background=random" not in photo_link:
            all_validation_failures.append(
                f"Photo link should have background=random: {photo_link}"
            )

        if not any(f.startswith("Test 7") for f in all_validation_failures):
            print(f"Test 7: generate_photo_link() -> {photo_link}")
    except Exception as e:
        all_validation_failures.append(f"Test 7 (generate_photo_link): {str(e)}")

    # Test 8: Test all age groups
    total_tests += 1
    try:
        age_groups = [
            (15, "Adolescente"),
            (25, "Jovem Adulto"),
            (35, "Adulto"),
            (55, "Meia-Idade"),
            (70, "Idoso"),
        ]
        big_five = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }

        for idade, expected_group in age_groups:
            demo = {"idade": idade, "localizacao": {"regiao": "Nordeste"}}
            archetype = derive_archetype(demo, big_five)
            if expected_group not in archetype:
                all_validation_failures.append(
                    f"Age {idade} should produce '{expected_group}', got: {archetype}"
                )

        if not any(f.startswith("Test 8") for f in all_validation_failures):
            print("Test 8: All age groups map correctly")
    except Exception as e:
        all_validation_failures.append(f"Test 8 (age groups): {str(e)}")

    # Test 9: Test all lifestyle patterns
    total_tests += 1
    try:
        lifestyle_tests = [
            ({"extroversao": 75, "neuroticismo": 30, "abertura": 50, "conscienciosidade": 50}, "Ativo e social"),
            ({"extroversao": 30, "neuroticismo": 70, "abertura": 50, "conscienciosidade": 50}, "Reservado e cauteloso"),
            ({"extroversao": 50, "neuroticismo": 50, "abertura": 80, "conscienciosidade": 50}, "Criativo e explorador"),
            ({"extroversao": 50, "neuroticismo": 50, "abertura": 50, "conscienciosidade": 80}, "Disciplinado e focado"),
            ({"extroversao": 50, "neuroticismo": 50, "abertura": 50, "conscienciosidade": 50}, "Equilibrado e moderado"),
        ]

        for traits, expected_lifestyle in lifestyle_tests:
            traits["amabilidade"] = 50
            lifestyle = derive_lifestyle(traits)
            if lifestyle != expected_lifestyle:
                all_validation_failures.append(
                    f"Expected '{expected_lifestyle}', got '{lifestyle}' for traits: {traits}"
                )

        if not any(f.startswith("Test 9") for f in all_validation_failures):
            print("Test 9: All lifestyle patterns work correctly")
    except Exception as e:
        all_validation_failures.append(f"Test 9 (lifestyle patterns): {str(e)}")

    # Final validation result
    print(f"\n{'='*60}")
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)
