/**
 * NarrativeMechanismEditor component.
 *
 * Parses a narrative template with {mechanism_key} placeholders and renders
 * inline dropdowns for each selected mechanism. Manages local selection state
 * and provides getMechanismValues() to extract numeric values.
 *
 * References:
 *   - Spec: specs/039-narrative-mechanism-config/spec.md
 *   - Types: types/mechanisms.ts
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { MechanismDropdown } from './MechanismDropdown';
import type {
  MechanismDefinition,
  MechanismSelections,
  MechanismValues,
  SelectedMechanism,
} from '@/types/mechanisms';

interface NarrativeMechanismEditorProps {
  /** Narrative template with {mechanism_key} placeholders */
  narrativeTemplate: string;
  /** Mechanisms selected by LLM with default options */
  selectedMechanisms: SelectedMechanism[];
  /** All mechanism definitions (for rendering dropdowns) */
  mechanisms: MechanismDefinition[];
  /** Optional initial selections (key -> optionId) */
  initialSelections?: MechanismSelections;
  /** Callback when any selection changes */
  onSelectionsChange?: (selections: MechanismSelections) => void;
  /** Whether editing is disabled */
  disabled?: boolean;
}

/**
 * Token type for parsed narrative.
 */
type NarrativeToken =
  | { type: 'text'; content: string }
  | { type: 'mechanism'; key: string };

/**
 * Parse narrative template into tokens (text and mechanism placeholders).
 */
function parseTemplate(template: string): NarrativeToken[] {
  const tokens: NarrativeToken[] = [];
  // Regex to match {mechanism_key} placeholders
  const regex = /\{([a-z_]+)\}/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(template)) !== null) {
    // Add text before the placeholder
    if (match.index > lastIndex) {
      tokens.push({
        type: 'text',
        content: template.slice(lastIndex, match.index),
      });
    }
    // Add the mechanism placeholder
    tokens.push({
      type: 'mechanism',
      key: match[1],
    });
    lastIndex = regex.lastIndex;
  }

  // Add remaining text after last placeholder
  if (lastIndex < template.length) {
    tokens.push({
      type: 'text',
      content: template.slice(lastIndex),
    });
  }

  return tokens;
}

/**
 * NarrativeMechanismEditor renders narrative text with inline mechanism dropdowns.
 *
 * Usage:
 *   const editorRef = useRef<NarrativeMechanismEditorHandle>(null);
 *
 *   <NarrativeMechanismEditor
 *     narrativeTemplate="A transação é {irreversibility} após confirmada."
 *     selectedMechanisms={[{ key: 'irreversibility', default_option_id: 'uuid' }]}
 *     mechanisms={allMechanisms}
 *     onSelectionsChange={(sel) => setSelections(sel)}
 *   />
 *
 *   // Get values: getMechanismValues(selections, mechanisms)
 */
export function NarrativeMechanismEditor({
  narrativeTemplate,
  selectedMechanisms,
  mechanisms,
  initialSelections,
  onSelectionsChange,
  disabled = false,
}: NarrativeMechanismEditorProps) {
  // Local state for selections (key -> optionId)
  const [selections, setSelections] = useState<MechanismSelections>(() => {
    // Initialize from initialSelections or use LLM defaults
    if (initialSelections) {
      return initialSelections;
    }
    return selectedMechanisms.reduce<MechanismSelections>((acc, sm) => {
      acc[sm.key] = sm.default_option_id;
      return acc;
    }, {});
  });

  // Reset selections when template changes (T032 - regeneration support)
  useEffect(() => {
    const newSelections = selectedMechanisms.reduce<MechanismSelections>(
      (acc, sm) => {
        acc[sm.key] = sm.default_option_id;
        return acc;
      },
      {}
    );
    setSelections(newSelections);
    onSelectionsChange?.(newSelections);
  }, [narrativeTemplate, selectedMechanisms, onSelectionsChange]);

  // Create lookup for mechanisms by key
  const mechanismsByKey = useMemo(() => {
    return mechanisms.reduce<Record<string, MechanismDefinition>>(
      (acc, mech) => {
        acc[mech.key] = mech;
        return acc;
      },
      {}
    );
  }, [mechanisms]);

  // Set of selected mechanism keys for quick lookup
  const selectedKeys = useMemo(
    () => new Set(selectedMechanisms.map((sm) => sm.key)),
    [selectedMechanisms]
  );

  // Parse the template into tokens
  const tokens = useMemo(
    () => parseTemplate(narrativeTemplate),
    [narrativeTemplate]
  );

  // Handle selection change for a mechanism
  const handleSelect = useCallback(
    (key: string, optionId: string) => {
      setSelections((prev) => {
        const updated = { ...prev, [key]: optionId };
        onSelectionsChange?.(updated);
        return updated;
      });
    },
    [onSelectionsChange]
  );

  return (
    <TooltipProvider delayDuration={300}>
      <div className="prose prose-slate prose-sm max-w-none leading-relaxed">
        {tokens.map((token, idx) => {
          if (token.type === 'text') {
            return <span key={idx}>{token.content}</span>;
          }

          // Mechanism placeholder
          const { key } = token;
          const mechanism = mechanismsByKey[key];

          // Only render dropdown if this mechanism was selected and exists
          if (!mechanism || !selectedKeys.has(key)) {
            // Render as plain text if mechanism not found
            return (
              <span key={idx} className="text-amber-600">
                [{key}]
              </span>
            );
          }

          return (
            <MechanismDropdown
              key={idx}
              mechanism={mechanism}
              selectedOptionId={selections[key] || ''}
              onSelect={(optionId) => handleSelect(key, optionId)}
              disabled={disabled}
            />
          );
        })}
      </div>
    </TooltipProvider>
  );
}

/**
 * Extract numeric values from mechanism selections.
 *
 * T027: Converts selection IDs to numeric values for persistence.
 *
 * Usage:
 *   const values = getMechanismValues(selections, mechanisms);
 *   // { irreversibility: 0.75, institutional_trust: 0.5 }
 */
export function getMechanismValues(
  selections: MechanismSelections,
  mechanisms: MechanismDefinition[]
): MechanismValues {
  const values: MechanismValues = {};

  // Build lookup: optionId -> value
  const optionValues: Record<string, number> = {};
  for (const mech of mechanisms) {
    for (const opt of mech.options) {
      optionValues[opt.id] = opt.value;
    }
  }

  // Build lookup: optionId -> mechanismKey
  const optionToKey: Record<string, string> = {};
  for (const mech of mechanisms) {
    for (const opt of mech.options) {
      optionToKey[opt.id] = mech.key;
    }
  }

  // Convert selections to values
  for (const [key, optionId] of Object.entries(selections)) {
    if (optionId && optionValues[optionId] !== undefined) {
      values[key] = optionValues[optionId];
    }
  }

  return values;
}

export default NarrativeMechanismEditor;
