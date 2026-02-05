/**
 * NarrativeStep component.
 *
 * Wizard Step 2 for mechanism configuration via LLM-generated narrative.
 * Replaces the old scorecard sliders with inline mechanism dropdowns.
 *
 * Features:
 *   - Auto-generates narrative on mount using feature info
 *   - Displays loading skeleton during generation
 *   - Renders narrative with inline mechanism dropdowns
 *   - "Regenerar" button for new narrative (US2)
 *   - Edge case handling: short description warning, no mechanisms, errors (Phase 7)
 *
 * References:
 *   - Spec: specs/039-narrative-mechanism-config/spec.md
 *   - Task: T025, T029-T032, T041-T044
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Loader2, RefreshCw, AlertTriangle, Info, Sparkles, ArrowLeft } from 'lucide-react';
import { useGenerateNarrative, useMechanisms } from '@/hooks/use-mechanisms';
import { NarrativeMechanismEditor, getMechanismValues } from './NarrativeMechanismEditor';
import type {
  GenerateNarrativeResponse,
  MechanismSelections,
  MechanismValues,
} from '@/types/mechanisms';

interface NarrativeStepProps {
  /** Feature name from Step 1 */
  name: string;
  /** Hypothesis from Step 1 */
  hypothesis: string;
  /** Description from Step 1 (optional) */
  description?: string;
  /** Called when user clicks "Continue" with mechanism values */
  onContinue: (values: MechanismValues, inferredTypes: string[]) => void;
  /** Called when user clicks "Back" */
  onBack: () => void;
  /** Whether the parent is submitting */
  isSubmitting?: boolean;
}

const MIN_DESCRIPTION_WORDS = 20;

/**
 * Check if description is too short (less than MIN_DESCRIPTION_WORDS words).
 */
function isDescriptionTooShort(name: string, hypothesis: string, description?: string): boolean {
  const combinedText = [name, hypothesis, description].filter(Boolean).join(' ');
  const wordCount = combinedText.trim().split(/\s+/).length;
  return wordCount < MIN_DESCRIPTION_WORDS;
}

/**
 * NarrativeStep renders the mechanism configuration via LLM-generated narrative.
 *
 * Usage:
 *   <NarrativeStep
 *     name="Pix via WhatsApp"
 *     hypothesis="Usuários preferem pagar pelo app"
 *     description="Permite enviar dinheiro"
 *     onContinue={(values) => saveAndProceed(values)}
 *     onBack={() => setStep(1)}
 *   />
 */
export function NarrativeStep({
  name,
  hypothesis,
  description,
  onContinue,
  onBack,
  isSubmitting = false,
}: NarrativeStepProps) {
  // Fetch mechanisms from database
  const { data: mechanismsData, isLoading: isLoadingMechanisms } = useMechanisms();

  // Narrative generation mutation
  const generateMutation = useGenerateNarrative();

  // Current narrative response
  const [narrativeResponse, setNarrativeResponse] = useState<GenerateNarrativeResponse | null>(
    null
  );

  // Current mechanism selections (key -> optionId)
  const [selections, setSelections] = useState<MechanismSelections>({});

  // Warning state for short description
  const showShortDescriptionWarning = isDescriptionTooShort(name, hypothesis, description);

  // Ref to track if we've already triggered generation (prevents loops)
  const hasTriggeredGeneration = useRef(false);

  // Generate narrative on mount (only once)
  useEffect(() => {
    // Only generate if we have mechanisms loaded and haven't generated yet
    if (!mechanismsData?.mechanisms || narrativeResponse || hasTriggeredGeneration.current) {
      return;
    }

    hasTriggeredGeneration.current = true;

    generateMutation.mutate(
      { name, hypothesis, description: description || undefined },
      {
        onSuccess: (response) => {
          setNarrativeResponse(response);
          // Initialize selections from default options
          const initial = response.selected_mechanisms.reduce<MechanismSelections>(
            (acc, sm) => {
              acc[sm.key] = sm.default_option_id;
              return acc;
            },
            {}
          );
          setSelections(initial);
        },
      }
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mechanismsData?.mechanisms]);

  // Handle regeneration (T029, T030)
  const handleRegenerate = useCallback(() => {
    generateMutation.mutate(
      { name, hypothesis, description: description || undefined },
      {
        onSuccess: (response) => {
          setNarrativeResponse(response);
          // Reset selections with new defaults (T032)
          const initial = response.selected_mechanisms.reduce<MechanismSelections>(
            (acc, sm) => {
              acc[sm.key] = sm.default_option_id;
              return acc;
            },
            {}
          );
          setSelections(initial);
        },
      }
    );
  }, [name, hypothesis, description, generateMutation]);

  // Handle continue - extract values and pass to parent (T027, T028)
  const handleContinue = useCallback(() => {
    if (!mechanismsData?.mechanisms || !narrativeResponse) {
      return;
    }

    const values = getMechanismValues(selections, mechanismsData.mechanisms);
    onContinue(values, narrativeResponse.inferred_types);
  }, [selections, mechanismsData?.mechanisms, narrativeResponse, onContinue]);

  // Check for incomplete selections (T044)
  const getMissingMechanisms = useCallback((): string[] => {
    if (!narrativeResponse) return [];

    const missing: string[] = [];
    for (const sm of narrativeResponse.selected_mechanisms) {
      if (!selections[sm.key]) {
        // Find mechanism label
        const mech = mechanismsData?.mechanisms.find((m) => m.key === sm.key);
        missing.push(mech?.label_pt || sm.key);
      }
    }
    return missing;
  }, [narrativeResponse, selections, mechanismsData?.mechanisms]);

  const missingMechanisms = getMissingMechanisms();
  const hasIncompleteSelections = missingMechanisms.length > 0;

  // Loading state (T031)
  const isLoading = isLoadingMechanisms || generateMutation.isPending;

  // Error state (T042)
  const hasError = generateMutation.isError;

  return (
    <div className="space-y-4">
      <div className="text-center mb-2">
        <h3 className="font-medium text-gray-900 flex items-center justify-center gap-2">
          <Sparkles className="h-5 w-5 text-indigo-500" />
          Configuração de Mecanismos
        </h3>
        <p className="text-sm text-gray-500">
          Ajuste as características da feature selecionando as opções
        </p>
      </div>

      {/* Warning: Short description (T043) */}
      {showShortDescriptionWarning && !isLoading && (
        <Alert variant="default" className="border-amber-200 bg-amber-50">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertTitle className="text-amber-800">Descrição curta</AlertTitle>
          <AlertDescription className="text-amber-700">
            A descrição da feature tem menos de {MIN_DESCRIPTION_WORDS} palavras. Considere
            adicionar mais contexto para uma análise mais precisa.
          </AlertDescription>
        </Alert>
      )}

      {/* Loading skeleton (T031) */}
      {isLoading && (
        <div className="space-y-3 p-4 rounded-lg border border-slate-200 bg-slate-50/50">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            Analisando a funcionalidade...
          </div>
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-[90%]" />
          <Skeleton className="h-4 w-[95%]" />
          <Skeleton className="h-4 w-[85%]" />
        </div>
      )}

      {/* Error state (T042) */}
      {hasError && !isLoading && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Erro na geração</AlertTitle>
          <AlertDescription className="space-y-2">
            <p>Não foi possível gerar a narrativa. Tente novamente.</p>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRegenerate}
              className="mt-2"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar novamente
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* No relevant mechanisms (T041) */}
      {narrativeResponse &&
        narrativeResponse.selected_mechanisms.length === 0 &&
        !isLoading && (
          <Alert variant="default" className="border-blue-200 bg-blue-50">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertTitle className="text-blue-800">Nenhum mecanismo relevante</AlertTitle>
            <AlertDescription className="text-blue-700">
              A análise não identificou mecanismos relevantes para esta feature. Tente
              enriquecer a descrição com mais detalhes sobre o comportamento esperado.
            </AlertDescription>
          </Alert>
        )}

      {/* Narrative with dropdowns */}
      {narrativeResponse &&
        narrativeResponse.selected_mechanisms.length > 0 &&
        mechanismsData?.mechanisms &&
        !isLoading && (
          <div className="p-4 rounded-lg border border-slate-200 bg-white shadow-sm">
            {/* Inferred types badge */}
            {narrativeResponse.inferred_types.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {narrativeResponse.inferred_types.map((type) => (
                  <span
                    key={type}
                    className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700"
                  >
                    {type}
                  </span>
                ))}
              </div>
            )}

            <NarrativeMechanismEditor
              narrativeTemplate={narrativeResponse.narrative_template}
              selectedMechanisms={narrativeResponse.selected_mechanisms}
              mechanisms={mechanismsData.mechanisms}
              onSelectionsChange={setSelections}
              disabled={isSubmitting}
            />
          </div>
        )}

      {/* Incomplete selection warning (T044) */}
      {hasIncompleteSelections && !isLoading && (
        <Alert variant="default" className="border-amber-200 bg-amber-50">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertTitle className="text-amber-800">Seleção incompleta</AlertTitle>
          <AlertDescription className="text-amber-700">
            Selecione uma opção para: {missingMechanisms.join(', ')}
          </AlertDescription>
        </Alert>
      )}

      {/* Action buttons */}
      <div className="flex justify-between gap-2 pt-4">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onBack}
          disabled={isSubmitting || isLoading}
          className="btn-ghost-icon"
        >
          <ArrowLeft className="w-4 h-4" />
        </Button>

        <div className="flex gap-2">
          {/* Regenerate button (T029) */}
          {narrativeResponse && !isLoading && (
            <Button
              type="button"
              variant="outline"
              onClick={handleRegenerate}
              disabled={isSubmitting || generateMutation.isPending}
              className="btn-secondary"
            >
              {generateMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Regenerando...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Regenerar
                </>
              )}
            </Button>
          )}

          {/* Continue button */}
          <Button
            type="button"
            onClick={handleContinue}
            disabled={
              isSubmitting ||
              isLoading ||
              !narrativeResponse ||
              narrativeResponse.selected_mechanisms.length === 0 ||
              hasIncompleteSelections
            }
            className="btn-primary"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Salvando...
              </>
            ) : (
              'Continuar'
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

export default NarrativeStep;
