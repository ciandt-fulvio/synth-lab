/**
 * Observable label utilities for synth-lab frontend.
 *
 * Provides:
 * - Centralized labels for observable attributes (used across all charts)
 * - Color mapping for observable values based on their labels
 *
 * Reference: specs/022-observable-latent-traits/spec.md (US4)
 */

import type { ObservableWithLabel } from '@/types/synth';

/**
 * Centralized labels for observable attributes.
 * These are the ONLY labels that should be displayed to the PM.
 * (Latent traits are internal and should NOT be shown in UI)
 */
export const OBSERVABLE_LABELS: Record<string, string> = {
  digital_literacy: 'Familiaridade com tecnologia',
  similar_tool_experience: 'Experiência com ferramentas similares',
  motor_ability: 'Habilidade física',
  time_availability: 'Disponibilidade de Tempo',
  domain_expertise: 'Conhecimento do assunto',
};

/**
 * Format a feature name to its display label.
 * Falls back to title-case formatting if not found.
 *
 * @param feature - The feature key (e.g., 'digital_literacy')
 * @returns The display label (e.g., 'Familiaridade com tecnologia')
 */
export function formatFeatureName(feature: string): string {
  if (OBSERVABLE_LABELS[feature]) {
    return OBSERVABLE_LABELS[feature];
  }
  // Fallback: convert snake_case to Title Case
  return feature.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Label type for type safety.
 */
export type ObservableLabel = 'Muito Baixo' | 'Baixo' | 'Médio' | 'Alto' | 'Muito Alto';

/**
 * Color configuration for each label level.
 */
interface LabelColorConfig {
  bg: string;
  text: string;
  progressBg: string;
  progressFill: string;
}

/**
 * Color mapping for observable labels.
 * Uses Tailwind classes for consistent styling.
 */
const LABEL_COLORS: Record<ObservableLabel, LabelColorConfig> = {
  'Muito Baixo': {
    bg: 'bg-red-50',
    text: 'text-red-700',
    progressBg: 'bg-red-100',
    progressFill: 'bg-red-500',
  },
  'Baixo': {
    bg: 'bg-orange-50',
    text: 'text-orange-700',
    progressBg: 'bg-orange-100',
    progressFill: 'bg-orange-500',
  },
  'Médio': {
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    progressBg: 'bg-amber-100',
    progressFill: 'bg-amber-500',
  },
  'Alto': {
    bg: 'bg-emerald-50',
    text: 'text-emerald-700',
    progressBg: 'bg-emerald-100',
    progressFill: 'bg-emerald-500',
  },
  'Muito Alto': {
    bg: 'bg-green-50',
    text: 'text-green-700',
    progressBg: 'bg-green-100',
    progressFill: 'bg-green-600',
  },
};

/**
 * Get the color configuration for an observable label.
 *
 * @param label - The observable label
 * @returns Color configuration for styling
 */
export function getObservableColor(label: ObservableLabel): LabelColorConfig {
  return LABEL_COLORS[label] || LABEL_COLORS['Médio'];
}

/**
 * Get progress bar classes for an observable.
 *
 * @param observable - The observable with label
 * @returns Object with background and fill class names
 */
export function getProgressBarClasses(observable: ObservableWithLabel): {
  background: string;
  fill: string;
} {
  const colors = getObservableColor(observable.label);
  return {
    background: colors.progressBg,
    fill: colors.progressFill,
  };
}

/**
 * Get badge classes for an observable label.
 *
 * @param observable - The observable with label
 * @returns Class string for badge styling
 */
export function getLabelBadgeClasses(observable: ObservableWithLabel): string {
  const colors = getObservableColor(observable.label);
  return `${colors.bg} ${colors.text}`;
}

/**
 * Format observable value as percentage string.
 *
 * @param value - Observable value [0, 1]
 * @returns Formatted percentage (e.g., "42%")
 */
export function formatValueAsPercentage(value: number): string {
  return `${Math.round(value * 100)}%`;
}
