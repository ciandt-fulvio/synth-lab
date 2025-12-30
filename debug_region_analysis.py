"""
Debug script para investigar análise de regiões.
Execute: uv run python debug_region_analysis.py SIMULATION_ID
"""

import sys

import numpy as np

from synth_lab.infrastructure.database import DatabaseManager
from synth_lab.services.simulation.analyzer import RegionAnalyzer
from synth_lab.services.simulation.simulation_service import SimulationService

if len(sys.argv) < 2:
    print("Usage: uv run python debug_region_analysis.py SIMULATION_ID")
    sys.exit(1)

simulation_id = sys.argv[1]

print(f"=== Debug Region Analysis for {simulation_id} ===\n")

# Initialize
db = DatabaseManager("output/synthlab.db")
service = SimulationService(db)
analyzer = RegionAnalyzer()

# Get simulation
run = service.get_simulation(simulation_id)
if not run:
    print(f"❌ Simulation {simulation_id} not found")
    sys.exit(1)

print(f"✅ Simulation found: {run.id}")
print(f"   Status: {run.status}")
print(f"   Total synths: {run.total_synths}")
print(f"   Aggregated outcomes: {run.aggregated_outcomes}\n")

# Get outcomes
outcomes_result = service.get_simulation_outcomes(
    run_id=simulation_id,
    limit=1000,
    offset=0,
)

outcomes = outcomes_result["items"]
print(f"✅ Retrieved {len(outcomes)} outcomes\n")

# Check outcome structure
if len(outcomes) > 0:
    print("=== Sample Outcome ===")
    sample = outcomes[0]
    print(f"Synth ID: {sample['synth_id']}")
    print(f"Failed rate: {sample['failed_rate']:.3f}")
    print(f"Success rate: {sample['success_rate']:.3f}")
    print(f"Did not try rate: {sample['did_not_try_rate']:.3f}")

    if "synth_attributes" in sample:
        attrs = sample["synth_attributes"]
        print(f"\nSimulation attributes present: {bool(attrs)}")
        if attrs and "latent_traits" in attrs:
            latent = attrs["latent_traits"]
            print("Latent traits:")
            for key, value in latent.items():
                print(f"  - {key}: {value}")
    else:
        print("⚠️  No synth_attributes in outcome!")
    print()

# Extract features
print("=== Feature Extraction ===")
X, feature_names = analyzer._extract_features(outcomes)
print(f"Feature matrix shape: {X.shape}")
print(f"Feature names: {feature_names}")

# Check feature statistics
print("\nFeature statistics:")
for i, name in enumerate(feature_names):
    values = X[:, i]
    print(f"  {name}:")
    print(
        f"    min={values.min():.3f}, max={values.max():.3f}, "
        f"mean={values.mean():.3f}, std={values.std():.3f}"
    )

# Check if features have variation
has_variation = any(X[:, i].std() > 0.001 for i in range(X.shape[1]))
if not has_variation:
    print("\n⚠️  WARNING: Features have no variation! All synths have same attributes.")
    print("   This will prevent the decision tree from finding patterns.\n")
else:
    print("\n✅ Features have variation\n")

# Extract labels
print("=== Label Extraction ===")
y = analyzer._extract_labels(outcomes)
print(f"Label array shape: {y.shape}")
print("Label distribution:")
print(f"  Class 0 (low failure): {(y == 0).sum()} ({(y == 0).sum() / len(y) * 100:.1f}%)")
print(f"  Class 1 (high failure): {(y == 1).sum()} ({(y == 1).sum() / len(y) * 100:.1f}%)")

if (y == 0).sum() == 0:
    print("\n⚠️  WARNING: All samples are high failure (class 1)")
    print("   No contrast for decision tree to learn from.\n")
elif (y == 1).sum() == 0:
    print("\n⚠️  WARNING: All samples are low failure (class 0)")
    print("   No high-failure regions to identify.\n")
else:
    print("\n✅ Both classes present\n")

# Check failure rate distribution
print("=== Failure Rate Distribution ===")
failure_rates = [o["failed_rate"] for o in outcomes]
print("Failure rates:")
print(f"  min={min(failure_rates):.3f}, max={max(failure_rates):.3f}")
print(f"  mean={np.mean(failure_rates):.3f}, std={np.std(failure_rates):.3f}")

# Histogram
bins = [0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]
hist, _ = np.histogram(failure_rates, bins=bins)
print("\nHistogram of failure rates:")
for i in range(len(bins) - 1):
    pct = hist[i] / len(failure_rates) * 100
    print(f"  {bins[i]:.1f}-{bins[i + 1]:.1f}: {hist[i]:4d} ({pct:5.1f}%)")

# Try running the analysis with debug
print("\n=== Running Analysis (min_failure_rate=0.5) ===")
try:
    regions = analyzer.analyze_regions(
        outcomes=outcomes,
        simulation_id=simulation_id,
        min_failure_rate=0.5,
    )
    print(f"✅ Analysis completed: {len(regions)} regions found")

    if len(regions) == 0:
        print("\n⚠️  No regions found. This could mean:")
        print("   1. No leaf nodes have failure_rate >= 0.5")
        print("   2. Decision tree couldn't find meaningful splits")
        print("   3. All samples are too similar")
    else:
        print("\nTop regions:")
        for i, region in enumerate(regions[:3], 1):
            print(f"\n  Region {i}:")
            print(f"    Rule: {region.rule_text}")
            print(f"    Synth count: {region.synth_count}")
            print(f"    Failed rate: {region.failed_rate:.3f}")

except Exception as e:
    print(f"❌ Analysis failed: {e}")
    import traceback

    traceback.print_exc()

print("\n=== Debug Complete ===")
