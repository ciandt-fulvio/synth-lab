/**
 * HypothesisValidationStep component for simulation wizard.
 *
 * Orchestrates a 4-step wizard for hypothesis configuration:
 *   1. Controllable Variables (Layer A)
 *   2. Critical Uncertainties (Layer B)
 *   3. Relationship Strength Editor
 *   4. Structural Assumptions Summary
 *
 * References:
 *   - Spec: specs/035-causal-simulation/spec.md
 */

import { useState, useMemo, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { ArrowLeft, ArrowRight, Loader2, AlertTriangle } from 'lucide-react';
import {
  HypothesisSubStepIndicator,
  HypothesisSubStep,
  ControllableVariablesStep,
  CriticalUncertaintiesStep,
  RelationshipStrengthEditor,
  RelationshipStrength,
  StructuralAssumptionsStep,
  TriangularParams,
} from './hypothesis';
import type { Hypothesis } from '@/types/hypothesis';
import type { CausalDAG, Variable, Edge } from '@/types/causal-dag';

interface HypothesisValidationStepProps {
  simulationId: string;
  hypotheses: Hypothesis[] | null;
  dag: CausalDAG | null;
  isLoading: boolean;
  onConfirm: () => void;
  isConfirming: boolean;
  /** When true, hides edit/confirm buttons for reviewing completed steps */
  readOnly?: boolean;
}

/**
 * Check if there are controllable variables in the DAG.
 */
function hasControllableVariables(variables: Variable[]): boolean {
  return variables.some(
    (v) =>
      v.controllability &&
      ['high', 'medium'].includes(v.controllability) &&
      !v.is_outcome
  );
}

/**
 * Check if there are critical uncertainties in the DAG.
 */
function hasCriticalUncertainties(variables: Variable[]): boolean {
  return variables.some((v) => v.is_critical_uncertainty && !v.is_outcome);
}

/**
 * Check if there are high-strength edges in the DAG.
 */
function hasHighStrengthEdges(edges: Edge[]): boolean {
  return edges.some((e) => e.strength_estimated === 'high');
}

/**
 * Step component for validating and configuring the generated hypotheses.
 */
export function HypothesisValidationStep({
  simulationId,
  hypotheses,
  dag,
  isLoading,
  onConfirm,
  isConfirming,
  readOnly = false,
}: HypothesisValidationStepProps) {
  // Sub-step state
  const [currentSubStep, setCurrentSubStep] = useState<HypothesisSubStep>(1);
  const [completedSubSteps, setCompletedSubSteps] = useState<HypothesisSubStep[]>([]);

  // Layer A: Scenario selections
  const [scenarioSelections, setScenarioSelections] = useState<Record<string, string>>({});

  // Layer B: Triangular parameters for critical uncertainties
  const [uncertaintyParams, setUncertaintyParams] = useState<Record<string, TriangularParams>>({});

  // Layer 3: Relationship strengths
  const [relationshipStrengths, setRelationshipStrengths] = useState<
    Record<string, RelationshipStrength>
  >({});

  // Extract variables and edges from DAG
  const variables = useMemo(() => dag?.nodes || [], [dag]);
  const edges = useMemo(() => dag?.edges || [], [dag]);

  // Determine which steps to show based on data
  const showControllables = useMemo(() => hasControllableVariables(variables), [variables]);
  const showUncertainties = useMemo(() => hasCriticalUncertainties(variables), [variables]);
  const showRelationships = useMemo(() => hasHighStrengthEdges(edges), [edges]);

  // Calculate effective steps (skip empty ones)
  const effectiveSteps = useMemo(() => {
    const steps: HypothesisSubStep[] = [];
    if (showControllables) steps.push(1);
    if (showUncertainties) steps.push(2);
    if (showRelationships) steps.push(3);
    steps.push(4); // Summary is always shown
    return steps;
  }, [showControllables, showUncertainties, showRelationships]);

  // Navigation handlers
  const handleNext = useCallback(() => {
    const currentIndex = effectiveSteps.indexOf(currentSubStep);
    if (currentIndex < effectiveSteps.length - 1) {
      // Mark current as completed
      if (!completedSubSteps.includes(currentSubStep)) {
        setCompletedSubSteps((prev) => [...prev, currentSubStep]);
      }
      setCurrentSubStep(effectiveSteps[currentIndex + 1]);
    }
  }, [currentSubStep, effectiveSteps, completedSubSteps]);

  const handleBack = useCallback(() => {
    const currentIndex = effectiveSteps.indexOf(currentSubStep);
    if (currentIndex > 0) {
      setCurrentSubStep(effectiveSteps[currentIndex - 1]);
    }
  }, [currentSubStep, effectiveSteps]);

  const handleStepClick = useCallback(
    (step: HypothesisSubStep) => {
      if (effectiveSteps.includes(step) && (completedSubSteps.includes(step) || step <= currentSubStep)) {
        setCurrentSubStep(step);
      }
    },
    [effectiveSteps, completedSubSteps, currentSubStep]
  );

  // Data handlers
  const handleScenarioChange = useCallback((variableName: string, scenario: string) => {
    setScenarioSelections((prev) => ({ ...prev, [variableName]: scenario }));
  }, []);

  const handleUncertaintyChange = useCallback((variableName: string, params: TriangularParams) => {
    setUncertaintyParams((prev) => ({ ...prev, [variableName]: params }));
  }, []);

  const handleRelationshipChange = useCallback(
    (source: string, target: string, strength: RelationshipStrength) => {
      const key = `${source}__${target}`;
      setRelationshipStrengths((prev) => ({ ...prev, [key]: strength }));
    },
    []
  );

  // Final confirmation handler
  const handleFinalConfirm = useCallback(() => {
    // TODO: In a full implementation, we would save the scenario selections,
    // uncertainty params, and relationship strengths to the backend before confirming.
    // For now, we just call the parent's onConfirm.
    onConfirm();
  }, [onConfirm]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  // No hypotheses state
  if (!hypotheses || hypotheses.length === 0) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 mx-auto text-amber-500 mb-4" />
        <h3 className="text-lg font-semibold text-slate-900 mb-2">Hipóteses não encontradas</h3>
        <p className="text-sm text-slate-600">
          As hipóteses ainda não foram geradas para esta simulação.
        </p>
      </div>
    );
  }

  const currentIndex = effectiveSteps.indexOf(currentSubStep);
  const isFirstStep = currentIndex === 0;
  const isLastStep = currentIndex === effectiveSteps.length - 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold text-slate-900">
          {readOnly ? 'Hipóteses' : 'Configurar Hipóteses'}
        </h2>
        {!readOnly && (
          <p className="text-sm text-slate-600 mt-1">
            Configure as variáveis e relacionamentos antes de executar a simulação.
          </p>
        )}
      </div>

      {/* Sub-step indicator */}
      <div className="py-4 border-y border-slate-100">
        <HypothesisSubStepIndicator
          currentStep={currentSubStep}
          completedSteps={completedSubSteps}
          onStepClick={readOnly ? undefined : handleStepClick}
        />
      </div>

      {/* Step content */}
      <div className="min-h-[400px]">
        {currentSubStep === 1 && (
          <ControllableVariablesStep
            variables={variables}
            hypotheses={hypotheses}
            selections={scenarioSelections}
            onChange={handleScenarioChange}
            readOnly={readOnly}
          />
        )}

        {currentSubStep === 2 && (
          <CriticalUncertaintiesStep
            variables={variables}
            hypotheses={hypotheses}
            params={uncertaintyParams}
            onChange={handleUncertaintyChange}
            readOnly={readOnly}
          />
        )}

        {currentSubStep === 3 && (
          <RelationshipStrengthEditor
            edges={edges}
            nodes={variables}
            strengths={relationshipStrengths}
            onChange={handleRelationshipChange}
            readOnly={readOnly}
          />
        )}

        {currentSubStep === 4 && (
          <StructuralAssumptionsStep
            variables={variables}
            hypotheses={hypotheses}
            onConfirm={handleFinalConfirm}
            isConfirming={isConfirming}
            readOnly={readOnly}
          />
        )}
      </div>

      {/* Navigation buttons (except on summary step which has its own confirm) */}
      {!readOnly && currentSubStep !== 4 && (
        <div className="flex justify-between pt-4 border-t">
          <Button
            variant="outline"
            onClick={handleBack}
            disabled={isFirstStep}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Anterior
          </Button>
          <Button onClick={handleNext}>
            Próximo
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
