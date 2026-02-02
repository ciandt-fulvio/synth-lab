/**
 * ClarificationQuestionsStep - Step for answering clarification questions.
 *
 * Displays 3-5 clarification questions for critical variables and allows users
 * to provide qualitative responses ("more", "less", "equal", "don't know").
 *
 * References:
 * - Spec: specs/036-simplified-hypothesis-wizard/spec.md
 * - Research: specs/036-simplified-hypothesis-wizard/research.md
 */

import { useState } from 'react';
import type { ClarificationQuestion, ResponseType } from '@/services/hypothesis-wizard-api';

export interface ClarificationResponse {
  variable_name: string;
  response: ResponseType;
}

interface ClarificationQuestionsStepProps {
  questions: ClarificationQuestion[];
  onSubmit: (responses: ClarificationResponse[]) => void;
  onSkip: () => void;
  disabled?: boolean;
}

/**
 * Clarification questions step for hypothesis wizard.
 */
export function ClarificationQuestionsStep({
  questions,
  onSubmit,
  onSkip,
  disabled = false,
}: ClarificationQuestionsStepProps) {
  const [responses, setResponses] = useState<Record<string, ResponseType>>({});

  const handleResponseChange = (variableName: string, response: ResponseType) => {
    setResponses((prev) => ({
      ...prev,
      [variableName]: response,
    }));
  };

  const handleSubmit = () => {
    // Convert responses object to array
    const responsesArray: ClarificationResponse[] = Object.entries(responses).map(
      ([variable_name, response]) => ({
        variable_name,
        response,
      })
    );

    onSubmit(responsesArray);
  };

  const isAnswered = (variableName: string) => !!responses[variableName];
  const allAnswered = questions.every((q) => isAnswered(q.variable_name));

  return (
    <div className="space-y-6">
      {/* Instructions */}
      <div className="card bg-blue-50/50 border-blue-200/60">
        <div className="flex items-start gap-3">
          <div className="icon-box-primary">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-blue-900 mb-1">
              Refine Critical Variables
            </h3>
            <p className="text-sm text-blue-800">
              Answer these questions to improve the accuracy of your simulation. You can skip any
              question if you're unsure.
            </p>
          </div>
        </div>
      </div>

      {/* Questions */}
      <div className="space-y-4">
        {questions.map((question, index) => (
          <div key={question.variable_name} className="card card-hover">
            {/* Question header */}
            <div className="flex items-start gap-3 mb-4">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 text-sm font-semibold flex-shrink-0">
                {index + 1}
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-slate-900 mb-1">
                  {question.variable_name}
                </h4>
                <p className="text-sm text-slate-600">{question.question_text}</p>
              </div>
            </div>

            {/* Response options */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {(['more', 'less', 'equal', 'dont_know'] as const).map((responseType) => {
                const labels: Record<ResponseType, string> = {
                  more: 'Mais',
                  less: 'Menos',
                  equal: 'Na Média',
                  dont_know: 'Não Sei',
                };

                const colors: Record<ResponseType, string> = {
                  more: 'bg-emerald-50 border-emerald-300 text-emerald-900',
                  less: 'bg-orange-50 border-orange-300 text-orange-900',
                  equal: 'bg-slate-50 border-slate-300 text-slate-900',
                  dont_know: 'bg-amber-50 border-amber-300 text-amber-900',
                };

                const activeColors: Record<ResponseType, string> = {
                  more: 'bg-emerald-600 border-emerald-600 text-white',
                  less: 'bg-orange-600 border-orange-600 text-white',
                  equal: 'bg-slate-600 border-slate-600 text-white',
                  dont_know: 'bg-amber-600 border-amber-600 text-white',
                };

                const isActive = responses[question.variable_name] === responseType;

                return (
                  <button
                    key={responseType}
                    type="button"
                    onClick={() => handleResponseChange(question.variable_name, responseType)}
                    disabled={disabled}
                    className={cn(
                      'px-4 py-2.5 rounded-lg border-2 text-sm font-medium transition-all',
                      'hover:scale-105 active:scale-95',
                      'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100',
                      isActive ? activeColors[responseType] : colors[responseType]
                    )}
                  >
                    {labels[responseType]}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-2">
        <button
          type="button"
          onClick={onSkip}
          disabled={disabled}
          className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors disabled:opacity-50"
        >
          Pular perguntas →
        </button>

        <div className="flex items-center gap-3">
          {/* Progress indicator */}
          <span className="text-sm text-slate-600">
            {Object.keys(responses).length} de {questions.length} respondidas
          </span>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={disabled || Object.keys(responses).length === 0}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {allAnswered ? 'Continuar' : 'Continuar com respostas parciais'}
          </button>
        </div>
      </div>
    </div>
  );
}

// Helper for className composition
function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ');
}
