"""
Sensitivity deriver service.

Derives 4 user sensitivities from synth demographic data using
configurable YAML rules. Each sensitivity starts at a base value
and is adjusted by rules that match the synth's demographics.

References:
    - Spec: specs/040-mechanism-sensitivity-update/spec.md (US1)
    - YAML rules: src/synth_lab/config/sensitivity_rules.yaml
    - PyYAML docs: https://pyyaml.org/wiki/PyYAMLDocumentation

Sample usage:
    from synth_lab.services.sensitivity_deriver import derive_sensitivities

    synth_data = {
        "demografia": {"idade": 25, "escolaridade": "ensino superior completo"},
    }
    result = derive_sensitivities(synth_data)

Expected output:
    {
        "risk_aversion": 0.50,
        "social_dependency": 0.60,
        ...,
        "_meta": {
            "derivation_version": "1.0",
            "config_name": "default",
            "applied_rules": ["Jovens sao mais aventureiros", ...]
        }
    }
"""

from pathlib import Path
from typing import Any

import numpy as np
import yaml
from loguru import logger

# Default Beta distribution concentration parameter.
# Higher values produce tighter distributions around the mean.
# Individual sensitivities can override via 'strength' in YAML.
BETA_STRENGTH_DEFAULT: int = 15

# 4 expected sensitivity keys
SENSITIVITY_KEYS = [
    "risk_aversion",
    "institutional_trust_level",
    "friction_tolerance",
    "digital_capability",
]

# Supported numeric operators
_NUMERIC_OPS: dict[str, Any] = {
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    "==": lambda a, b: a == b,
}


def _config_dir() -> Path:
    """Return the path to the config directory."""
    return Path(__file__).parent.parent / "config"


def load_sensitivity_rules(config_name: str = "default") -> dict:
    """Load sensitivity rules from YAML config.

    Args:
        config_name: Config name (maps to sensitivity_rules.yaml).

    Returns:
        Parsed dict with version, description, and sensitivities.

    Raises:
        FileNotFoundError: If YAML file does not exist.
        ValueError: If YAML is malformed or missing required fields.
    """
    yaml_path = _config_dir() / "sensitivity_rules.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"Sensitivity rules file not found: {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Malformed YAML: expected dict, got {type(data).__name__}")

    if "version" not in data:
        raise ValueError("Sensitivity rules YAML missing required 'version' field")

    if "sensitivities" not in data or not isinstance(data.get("sensitivities"), dict):
        raise ValueError("Sensitivity rules YAML missing or invalid 'sensitivities' field")

    logger.debug(f"Loaded sensitivity rules v{data['version']} ({config_name})")
    return data


def get_nested_value(data: dict, field_path: str, default: Any = None) -> Any:
    """Get value from nested dict using dot notation.

    Args:
        data: Source dictionary (possibly nested).
        field_path: Dot-separated path (e.g. "demografia.idade").
        default: Value to return if path is not found.

    Returns:
        The value at the given path, or default if not found.
    """
    current = data
    for key in field_path.split("."):
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def evaluate_condition(condition: dict, synth_data: dict) -> bool:
    """Evaluate a single condition against synth data.

    Supported operators:
        Numeric: >=, <=, >, <, ==
        String: contains (substring), contains_any (any of list), in (value in list)

    Args:
        condition: Dict with field, operator, and value keys.
        synth_data: Synth demographic data.

    Returns:
        True if condition matches, False otherwise (including missing fields).
    """
    field_path = condition.get("field", "")
    operator = condition.get("operator", "")
    expected = condition.get("value")

    actual = get_nested_value(synth_data, field_path)
    if actual is None:
        return False

    # Numeric operators
    if operator in _NUMERIC_OPS:
        try:
            return _NUMERIC_OPS[operator](float(actual), float(expected))
        except (TypeError, ValueError):
            return False

    # String: contains (substring match)
    if operator == "contains":
        try:
            return str(expected) in str(actual)
        except (TypeError, ValueError):
            return False

    # String: contains_any (any item from list is substring)
    if operator == "contains_any":
        if not isinstance(expected, list):
            return False
        actual_str = str(actual)
        return any(str(item) in actual_str for item in expected)

    # String: in (actual value is in expected list)
    if operator == "in":
        if not isinstance(expected, list):
            return False
        return actual in expected

    logger.warning(f"Unknown operator '{operator}' in condition for field '{field_path}'")
    return False


def derive_sensitivities(
    synth_data: dict,
    config_name: str = "default",
    seed: int | None = None,
) -> dict:
    """Derive 4 sensitivities from synth demographic data using YAML rules.

    For each sensitivity:
        1. Start with base value from YAML.
        2. Apply all matching rule adjustments.
        3. Clamp mean to [0.01, 0.99].
        4. Sample from Beta(mean * strength, (1-mean) * strength).

    The strength parameter defaults to BETA_STRENGTH_DEFAULT (15) but can
    be overridden per-sensitivity in YAML (e.g. subject_domain uses 6
    for a wider Beta(3,3) spread).

    Args:
        synth_data: Full synth data dict (with demografia, composicao_familiar, etc.).
        config_name: Which YAML config to load.
        seed: Random seed for reproducibility (None for random).

    Returns:
        Dict with 4 sensitivity float values and a _meta dict containing
        derivation_version, config_name, and applied_rules.
    """
    rng = np.random.default_rng(seed)
    rules_data = load_sensitivity_rules(config_name)
    sensitivities_config = rules_data.get("sensitivities", {})
    version = rules_data.get("version", "unknown")
    global_strength = int(rules_data.get("strength_default", BETA_STRENGTH_DEFAULT))

    result: dict[str, Any] = {}
    applied_rules: list[str] = []

    for key in SENSITIVITY_KEYS:
        sens_config = sensitivities_config.get(key, {})
        base = float(sens_config.get("base", 0.5))
        mean = base

        for rule in sens_config.get("rules", []):
            condition = rule.get("condition", {})
            if evaluate_condition(condition, synth_data):
                adjustment = float(rule.get("adjustment", 0.0))
                reason = rule.get("reason", "no reason")
                mean += adjustment
                applied_rules.append(reason)
                logger.debug(f"{key}: +{adjustment} ({reason})")

        # Clamp mean, then sample from Beta distribution
        mean = max(0.01, min(0.99, mean))
        strength = int(sens_config.get("strength", global_strength))
        alpha = mean * strength
        beta_param = (1.0 - mean) * strength
        result[key] = round(float(rng.beta(alpha, beta_param)), 4)

    result["_meta"] = {
        "derivation_version": str(version),
        "config_name": config_name,
        "applied_rules": applied_rules,
    }

    logger.info(
        f"Derived sensitivities (v{version}, {config_name}): {len(applied_rules)} rules applied"
    )
    return result


if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # ---- Test 1: Load config successfully ----
    total_tests += 1
    try:
        config = load_sensitivity_rules("default")
        if "version" not in config:
            all_validation_failures.append("Test 1: Config missing 'version'")
        if "sensitivities" not in config:
            all_validation_failures.append("Test 1: Config missing 'sensitivities'")
        if len(config["sensitivities"]) != 4:
            all_validation_failures.append(
                f"Test 1: Expected 4 sensitivities, got {len(config['sensitivities'])}"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 1 (load config): {e}")

    # ---- Test 2: get_nested_value with deep paths ----
    total_tests += 1
    try:
        nested = {"a": {"b": {"c": 42}}, "x": "hello"}
        assert get_nested_value(nested, "a.b.c") == 42, "deep path failed"
        assert get_nested_value(nested, "x") == "hello", "top-level failed"
        assert get_nested_value(nested, "a.b.missing", "default") == "default", "default failed"
        assert get_nested_value(nested, "z.y.x", None) is None, "missing branch failed"
        assert get_nested_value({}, "a.b", 0) == 0, "empty dict failed"
    except AssertionError as e:
        all_validation_failures.append(f"Test 2 (get_nested_value): {e}")
    except Exception as e:
        all_validation_failures.append(f"Test 2 (get_nested_value): {e}")

    # ---- Test 3: evaluate_condition for all operators ----
    total_tests += 1
    try:
        data = {
            "demografia": {"idade": 30, "escolaridade": "ensino superior completo"},
            "composicao_familiar": {"tipo": "casal monoparental com filhos"},
            "deficiencias": {"motora": {"tipo": "moderada"}},
        }

        # Numeric operators
        assert evaluate_condition(
            {"field": "demografia.idade", "operator": ">=", "value": 25}, data
        ), ">= failed"
        assert evaluate_condition(
            {"field": "demografia.idade", "operator": "<=", "value": 30}, data
        ), "<= failed"
        assert evaluate_condition(
            {"field": "demografia.idade", "operator": "==", "value": 30}, data
        ), "== failed"
        assert not evaluate_condition(
            {"field": "demografia.idade", "operator": ">", "value": 30}, data
        ), "> should be false"
        assert not evaluate_condition(
            {"field": "demografia.idade", "operator": "<", "value": 30}, data
        ), "< should be false"

        # String: contains
        assert evaluate_condition(
            {"field": "composicao_familiar.tipo", "operator": "contains", "value": "monoparental"},
            data,
        ), "contains failed"
        assert not evaluate_condition(
            {"field": "composicao_familiar.tipo", "operator": "contains", "value": "biparental"},
            data,
        ), "contains negative failed"

        # String: contains_any
        assert evaluate_condition(
            {
                "field": "composicao_familiar.tipo",
                "operator": "contains_any",
                "value": ["nuclear", "monoparental"],
            },
            data,
        ), "contains_any failed"

        # String: in
        assert evaluate_condition(
            {
                "field": "demografia.escolaridade",
                "operator": "in",
                "value": ["ensino superior completo", "pos-graduacao"],
            },
            data,
        ), "in failed"
        assert not evaluate_condition(
            {
                "field": "demografia.escolaridade",
                "operator": "in",
                "value": ["ensino medio", "fundamental"],
            },
            data,
        ), "in negative failed"

        # Missing field returns False
        assert not evaluate_condition(
            {"field": "missing.field", "operator": ">=", "value": 10}, data
        ), "missing field should return False"

    except AssertionError as e:
        all_validation_failures.append(f"Test 3 (evaluate_condition): {e}")
    except Exception as e:
        all_validation_failures.append(f"Test 3 (evaluate_condition): {e}")

    # ---- Test 4: Derive sensitivities with seed=42 for young tech ----
    total_tests += 1
    try:
        young_tech = {
            "demografia": {"idade": 25, "escolaridade": "ensino superior completo"},
        }
        result = derive_sensitivities(young_tech, seed=42)

        # All 7 keys present and in valid range
        for key in SENSITIVITY_KEYS:
            if key not in result:
                all_validation_failures.append(f"Test 4: Missing key '{key}'")
            elif not (0.0 <= result[key] <= 1.0):
                all_validation_failures.append(f"Test 4: {key}={result[key]} out of [0,1]")
    except Exception as e:
        all_validation_failures.append(f"Test 4 (young tech): {e}")

    # ---- Test 5: Same seed produces same results (deterministic) ----
    total_tests += 1
    try:
        synth = {"demografia": {"idade": 40, "escolaridade": "ensino superior completo"}}
        r1 = derive_sensitivities(synth, seed=42)
        r2 = derive_sensitivities(synth, seed=42)
        for key in SENSITIVITY_KEYS:
            if r1[key] != r2[key]:
                all_validation_failures.append(
                    f"Test 5: Same seed not deterministic for {key}: {r1[key]} != {r2[key]}"
                )
    except Exception as e:
        all_validation_failures.append(f"Test 5 (determinism): {e}")

    # ---- Test 6: Averages converge to base means (no demographics) ----
    total_tests += 1
    try:
        n = 100
        avgs = {k: 0.0 for k in SENSITIVITY_KEYS}
        for i in range(n):
            res = derive_sensitivities({}, seed=i)
            for k in SENSITIVITY_KEYS:
                avgs[k] += res[k]
        for k in SENSITIVITY_KEYS:
            avgs[k] /= n

        if len(derive_sensitivities({}, seed=0)["_meta"]["applied_rules"]) != 0:
            all_validation_failures.append("Test 6: Empty synth should have 0 applied rules")

        # Check averages are close to base means
        expected_bases = {
            "risk_aversion": 0.60,
            "institutional_trust_level": 0.50,
            "friction_tolerance": 0.50,
            "digital_capability": 0.50,
        }
        for k, base in expected_bases.items():
            tol = 0.05
            if abs(avgs[k] - base) > tol:
                all_validation_failures.append(
                    f"Test 6: avg {k}={avgs[k]:.4f} too far from base {base}"
                )
    except Exception as e:
        all_validation_failures.append(f"Test 6 (averages): {e}")

    # ---- Test 7: Values clamped to [0, 1] ----
    total_tests += 1
    try:
        # Use results from tests 4/5 and verify all are in range
        for test_data in [
            {"demografia": {"idade": 25, "escolaridade": "ensino superior completo"}},
            {"demografia": {"idade": 65, "escolaridade": "ensino fundamental"}},
            {},
        ]:
            res = derive_sensitivities(test_data)
            for key in SENSITIVITY_KEYS:
                val = res[key]
                if not (0.0 <= val <= 1.0):
                    all_validation_failures.append(
                        f"Test 7: {key}={val} out of [0,1] for data={test_data}"
                    )
    except Exception as e:
        all_validation_failures.append(f"Test 7 (clamping): {e}")

    # ---- Test 8: Metadata present with version, config, applied rules ----
    total_tests += 1
    try:
        result = derive_sensitivities(
            {"demografia": {"idade": 25, "escolaridade": "ensino superior completo"}}
        )
        meta = result.get("_meta")
        if meta is None:
            all_validation_failures.append("Test 8: _meta is missing")
        else:
            if meta.get("derivation_version") != "1.1":
                all_validation_failures.append(
                    f"Test 8: version expected '1.1', got '{meta.get('derivation_version')}'"
                )
            if meta.get("config_name") != "default":
                all_validation_failures.append(
                    f"Test 8: config_name expected 'default', got '{meta.get('config_name')}'"
                )
            if not isinstance(meta.get("applied_rules"), list):
                all_validation_failures.append("Test 8: applied_rules should be a list")
            elif len(meta["applied_rules"]) == 0:
                all_validation_failures.append(
                    "Test 8: 25yo tech should have at least 1 applied rule"
                )
    except Exception as e:
        all_validation_failures.append(f"Test 8 (metadata): {e}")

    # ---- Final report ----
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
