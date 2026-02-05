/**
 * MechanismDropdown component.
 *
 * Inline dropdown for selecting a mechanism option within narrative text.
 * Displays as a clickable span that opens a dropdown with mechanism options.
 * Includes tooltip with mechanism description (US3).
 *
 * References:
 *   - Spec: specs/039-narrative-mechanism-config/spec.md
 *   - Types: types/mechanisms.ts
 */

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import type { MechanismDefinition } from '@/types/mechanisms';
import { cn } from '@/lib/utils';

interface MechanismDropdownProps {
  /** The mechanism definition with options */
  mechanism: MechanismDefinition;
  /** Currently selected option ID */
  selectedOptionId: string;
  /** Callback when selection changes */
  onSelect: (optionId: string) => void;
  /** Whether the dropdown is disabled */
  disabled?: boolean;
}

/**
 * Inline dropdown for mechanism selection.
 *
 * Renders as a styled span that fits within narrative text and opens
 * a dropdown with available options on click. Includes tooltip with
 * mechanism label and description on hover.
 *
 * Usage:
 *   <MechanismDropdown
 *     mechanism={irreversibilityMechanism}
 *     selectedOptionId="uuid-of-option"
 *     onSelect={(id) => setSelection(id)}
 *   />
 */
export function MechanismDropdown({
  mechanism,
  selectedOptionId,
  onSelect,
  disabled = false,
}: MechanismDropdownProps) {
  // Find the currently selected option for display
  const selectedOption = mechanism.options.find(
    (opt) => opt.id === selectedOptionId
  );

  // Sort options by display_order for consistent ordering
  const sortedOptions = [...mechanism.options].sort(
    (a, b) => a.display_order - b.display_order
  );

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="inline-block">
          <Select
            value={selectedOptionId}
            onValueChange={onSelect}
            disabled={disabled}
          >
            <SelectTrigger
              className={cn(
                // Inline styling to fit within text flow
                'inline-flex h-auto min-h-0 w-auto min-w-0 py-0.5 px-2',
                'border-0 border-b-2 border-dashed border-indigo-400',
                'rounded-none bg-indigo-50/50',
                'text-sm font-medium text-indigo-700',
                'hover:bg-indigo-100/70 hover:border-indigo-500',
                'focus:ring-1 focus:ring-indigo-400 focus:ring-offset-0',
                'transition-colors duration-150',
                // Remove default select styling
                '[&>span]:line-clamp-none [&>svg]:hidden'
              )}
            >
              <SelectValue>
                {selectedOption?.label || 'Selecione...'}
              </SelectValue>
            </SelectTrigger>
            <SelectContent
              position="popper"
              sideOffset={4}
              className="max-w-[300px]"
            >
              {sortedOptions.map((option) => (
                <SelectItem
                  key={option.id}
                  value={option.id}
                  className={cn(
                    'cursor-pointer',
                    option.id === selectedOptionId && 'bg-indigo-50'
                  )}
                >
                  <div className="flex items-center justify-between gap-4">
                    <span>{option.label}</span>
                    <span className="text-xs text-slate-400">
                      {(option.value * 100).toFixed(0)}%
                    </span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </span>
      </TooltipTrigger>
      <TooltipContent
        side="top"
        className="max-w-[280px] text-left"
      >
        <p className="font-medium text-slate-900">{mechanism.label_pt}</p>
        <p className="mt-1 text-xs text-slate-500">{mechanism.description}</p>
      </TooltipContent>
    </Tooltip>
  );
}

export default MechanismDropdown;
