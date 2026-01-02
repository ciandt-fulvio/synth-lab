"""
Outlier detection service for UX Research analysis.

Identifies extreme cases and statistical outliers in simulation outcomes
to help researchers select interesting synths for qualitative interviews.

References:
    - Isolation Forest: scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html
    - Outlier Detection: scikit-learn.org/stable/modules/outlier_detection.html

Sample Input:
    outcomes: list[SynthOutcome] from simulation

Expected Output:
    ExtremeCasesTable: Top worst failures, best successes, unexpected cases
    OutlierResult: Statistical outliers via Isolation Forest
"""

import numpy as np
from sklearn.ensemble import IsolationForest

from synth_lab.domain.entities import (
    ExtremeCasesTable,
    ExtremeSynth,
    OutlierResult,
    OutlierSynth,
    SynthOutcome)


class OutlierService:
    """Service for identifying extreme cases and outliers in simulations."""

    def get_extreme_cases(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        n_per_category: int = 10) -> ExtremeCasesTable:
        """
        Identify extreme cases for qualitative research.

        Returns top N worst failures, best successes, and unexpected cases.

        Args:
            simulation_id: Simulation identifier.
            outcomes: List of synth outcomes.
            n_per_category: Number of synths per category (default: 10).

        Returns:
            ExtremeCasesTable with categorized extreme synths.

        Raises:
            ValueError: If outcomes list is empty or has < 10 synths.
        """
        if len(outcomes) < 10:
            raise ValueError(f"Extreme cases requires at least 10 synths, got {len(outcomes)}")

        # Sort by success rate (ascending) for worst failures
        sorted_by_failure = sorted(
            outcomes, key=lambda x: x.success_rate, reverse=False
        )

        # Sort by success rate (descending) for best successes
        sorted_by_success = sorted(outcomes, key=lambda x: x.success_rate, reverse=True)

        # Get top N from each category
        n_actual = min(n_per_category, len(outcomes))

        worst_failures = [
            self._create_extreme_synth(synth, "worst_failure")
            for synth in sorted_by_failure[:n_actual]
        ]

        best_successes = [
            self._create_extreme_synth(synth, "best_success")
            for synth in sorted_by_success[:n_actual]
        ]

        # Find unexpected cases (high capability but failed OR low capability but succeeded)
        unexpected = self._find_unexpected_cases(outcomes)

        return ExtremeCasesTable(
            simulation_id=simulation_id,
            worst_failures=worst_failures,
            best_successes=best_successes,
            unexpected_cases=unexpected,
            total_synths=len(outcomes))

    def detect_outliers(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        contamination: float = 0.1,
        features: list[str] | None = None) -> OutlierResult:
        """
        Detect statistical outliers using Isolation Forest.

        Args:
            simulation_id: Simulation identifier.
            outcomes: List of synth outcomes.
            contamination: Expected proportion of outliers (0-0.5, default: 0.1).
            features: Features to use (default: all latent traits + outcomes).

        Returns:
            OutlierResult with detected outliers and classifications.

        Raises:
            ValueError: If outcomes list has < 10 synths.
        """
        if len(outcomes) < 10:
            raise ValueError(f"Outlier detection requires at least 10 synths, got {len(outcomes)}")

        # Extract features
        X, synth_ids, features_used = self._extract_features(outcomes, features)

        # Train Isolation Forest
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100)

        # Fit and predict (-1 = outlier, 1 = inlier)
        predictions = iso_forest.fit_predict(X)
        anomaly_scores = iso_forest.score_samples(X)

        # Extract outliers
        outlier_indices = np.where(predictions == -1)[0]
        outlier_synths = []

        for idx in outlier_indices:
            synth_id = synth_ids[idx]
            synth = next(o for o in outcomes if o.synth_id == synth_id)

            outlier_type = self._classify_outlier_type(synth)
            explanation = self._generate_outlier_explanation(synth, outlier_type)

            outlier_synths.append(
                OutlierSynth(
                    synth_id=synth_id,
                    outlier_type=outlier_type,
                    anomaly_score=float(anomaly_scores[idx]),
                    success_rate=synth.success_rate,
                    failed_rate=synth.failed_rate,
                    did_not_try_rate=synth.did_not_try_rate,
                    explanation=explanation,
                    capability_mean=synth.synth_attributes.latent_traits.capability_mean,
                    trust_mean=synth.synth_attributes.latent_traits.trust_mean,
                    friction_tolerance_mean=synth.synth_attributes.latent_traits.friction_tolerance_mean,
                    digital_literacy=synth.synth_attributes.observables.digital_literacy,
                    similar_tool_experience=synth.synth_attributes.observables.similar_tool_experience)
            )

        return OutlierResult(
            simulation_id=simulation_id,
            method="isolation_forest",
            contamination=contamination,
            outliers=outlier_synths,
            total_synths=len(outcomes),
            n_outliers=len(outlier_synths),
            features_used=features_used)

    def _create_extreme_synth(self, outcome: SynthOutcome, category: str) -> ExtremeSynth:
        """Create ExtremeSynth entity with profile and questions."""
        profile_summary = self._generate_profile_summary(outcome)
        interview_questions = self._generate_interview_questions(outcome, category)

        return ExtremeSynth(
            synth_id=outcome.synth_id,
            category=category,
            success_rate=outcome.success_rate,
            failed_rate=outcome.failed_rate,
            did_not_try_rate=outcome.did_not_try_rate,
            profile_summary=profile_summary,
            interview_questions=interview_questions,
            capability_mean=outcome.synth_attributes.latent_traits.capability_mean,
            trust_mean=outcome.synth_attributes.latent_traits.trust_mean,
            friction_tolerance_mean=outcome.synth_attributes.latent_traits.friction_tolerance_mean)

    def _generate_profile_summary(self, outcome: SynthOutcome) -> str:
        """Generate human-readable profile summary."""
        traits = outcome.synth_attributes.latent_traits
        obs = outcome.synth_attributes.observables

        # Classify traits
        cap_level = (
            "high"
            if traits.capability_mean > 0.6
            else ("low" if traits.capability_mean < 0.4 else "medium")
        )
        trust_level = (
            "high" if traits.trust_mean > 0.6 else ("low" if traits.trust_mean < 0.4 else "medium")
        )
        lit_level = (
            "high"
            if obs.digital_literacy > 0.6
            else ("low" if obs.digital_literacy < 0.4 else "medium")
        )

        summary = f"Synth with {cap_level} capability ({traits.capability_mean:.2f}), "
        summary += f"{trust_level} trust ({traits.trust_mean:.2f}), "
        summary += f"and {lit_level} digital literacy ({obs.digital_literacy:.2f}). "
        summary += f"Success rate: {outcome.success_rate:.1%}, "
        summary += f"Failed rate: {outcome.failed_rate:.1%}."

        return summary

    def _generate_interview_questions(self, outcome: SynthOutcome, category: str) -> list[str]:
        """Generate suggested interview questions based on category."""
        questions = []

        if category == "worst_failure":
            questions = [
                "Quais foram os principais obstáculos que impediram seu sucesso?",
                "Pode descrever um momento específico em que se sentiu travado ou frustrado?",
                "O que teria ajudado você a superar esses desafios?",
            ]
        elif category == "best_success":
            questions = [
                "Quais estratégias você usou para alcançar o sucesso?",
                "Pode me guiar por uma interação típica sua com a funcionalidade?",
                "Quais aspectos da funcionalidade você achou mais úteis?",
            ]
        else:  # unexpected
            traits = outcome.synth_attributes.latent_traits
            if traits.capability_mean < 0.4 and outcome.success_rate > 0.7:
                questions = [
                    "Apesar de pontuação baixa de capacidade, você teve sucesso. O que fez a diferença?",
                    "Você achou a funcionalidade particularmente fácil de usar? Por quê?",
                ]
            elif traits.capability_mean > 0.6 and outcome.failed_rate > 0.5:
                questions = [
                    "Você tem alta capacidade mas experimentou falhas. O que deu errado?",
                    "Houve barreiras inesperadas ou aspectos confusos?",
                ]
            else:
                questions = [
                    "Seu perfil é incomum. Pode descrever sua experiência?",
                    "Quais fatores influenciaram seu resultado?",
                ]

        return questions

    def _find_unexpected_cases(self, outcomes: list[SynthOutcome]) -> list[ExtremeSynth]:
        """Find synths with unexpected outcomes given their attributes."""
        unexpected = []

        for outcome in outcomes:
            traits = outcome.synth_attributes.latent_traits

            # High capability but failed
            if traits.capability_mean > 0.6 and outcome.failed_rate > 0.5:
                unexpected.append(self._create_extreme_synth(outcome, "unexpected"))

            # Low capability but succeeded
            elif traits.capability_mean < 0.4 and outcome.success_rate > 0.7:
                unexpected.append(self._create_extreme_synth(outcome, "unexpected"))

        return unexpected[:10]  # Limit to 10

    def _classify_outlier_type(self, synth: SynthOutcome) -> str:
        """Classify outlier type based on outcome and attributes."""
        traits = synth.synth_attributes.latent_traits

        # High capability but failed unexpectedly
        if traits.capability_mean > 0.6 and synth.failed_rate > 0.5:
            return "unexpected_failure"

        # Low capability but succeeded unexpectedly
        if traits.capability_mean < 0.4 and synth.success_rate > 0.7:
            return "unexpected_success"

        # Otherwise it's an atypical profile
        return "atypical_profile"

    def _generate_outlier_explanation(self, synth: SynthOutcome, outlier_type: str) -> str:
        """Generate explanation for why synth is an outlier."""
        traits = synth.synth_attributes.latent_traits

        if outlier_type == "unexpected_failure":
            return (
                f"High capability ({traits.capability_mean:.2f}) but high failure rate "
                f"({synth.failed_rate:.1%}). This suggests unexpected barriers or friction points."
            )
        elif outlier_type == "unexpected_success":
            return (
                f"Low capability ({traits.capability_mean:.2f}) but high success rate "
                f"({synth.success_rate:.1%}). This indicates the feature may be easier than expected."
            )
        else:
            return (
                f"Atypical combination of attributes with capability={traits.capability_mean:.2f}, "
                f"trust={traits.trust_mean:.2f}, success={synth.success_rate:.1%}."
            )

    def _extract_features(
        self,
        outcomes: list[SynthOutcome],
        features: list[str] | None = None) -> tuple[np.ndarray, list[str], list[str]]:
        """Extract feature matrix for outlier detection."""
        if features is None:
            features = [
                "capability_mean",
                "trust_mean",
                "friction_tolerance_mean",
                "digital_literacy",
                "similar_tool_experience",
                "success_rate",
                "failed_rate",
            ]

        X_list = []
        synth_ids = []

        for outcome in outcomes:
            row = []
            traits = outcome.synth_attributes.latent_traits
            obs = outcome.synth_attributes.observables

            for feature in features:
                if feature == "capability_mean":
                    row.append(traits.capability_mean)
                elif feature == "trust_mean":
                    row.append(traits.trust_mean)
                elif feature == "friction_tolerance_mean":
                    row.append(traits.friction_tolerance_mean)
                elif feature == "digital_literacy":
                    row.append(obs.digital_literacy)
                elif feature == "similar_tool_experience":
                    row.append(obs.similar_tool_experience)
                elif feature == "success_rate":
                    row.append(outcome.success_rate)
                elif feature == "failed_rate":
                    row.append(outcome.failed_rate)

            X_list.append(row)
            synth_ids.append(outcome.synth_id)

        return np.array(X_list), synth_ids, features
