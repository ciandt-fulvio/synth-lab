/**
 * DistributionPicker component for selecting distribution types.
 *
 * Dropdown with distribution options and descriptions.
 *
 * References:
 *   - Types: types/hypothesis.ts
 */

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DISTRIBUTION_OPTIONS, type DistributionType } from '@/types/hypothesis';

interface DistributionPickerProps {
  /**
   * Current distribution type.
   */
  value: DistributionType;

  /**
   * Callback when distribution changes.
   */
  onChange: (value: DistributionType) => void;

  /**
   * Whether picker is disabled.
   */
  disabled?: boolean;
}

/**
 * DistributionPicker component.
 *
 * @example
 * <DistributionPicker
 *   value={distribution}
 *   onChange={setDistribution}
 * />
 */
export function DistributionPicker({
  value,
  onChange,
  disabled = false,
}: DistributionPickerProps) {
  return (
    <Select
      value={value}
      onValueChange={(v) => onChange(v as DistributionType)}
      disabled={disabled}
    >
      <SelectTrigger className="w-full">
        <SelectValue placeholder="Select distribution..." />
      </SelectTrigger>
      <SelectContent>
        {DISTRIBUTION_OPTIONS.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            <div className="flex flex-col">
              <span className="font-medium">{option.label}</span>
              <span className="text-xs text-slate-500">{option.description}</span>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

/**
 * Get required parameters for a distribution type.
 */
export function getDistributionParams(type: DistributionType): string[] {
  const option = DISTRIBUTION_OPTIONS.find((o) => o.value === type);
  return option?.params || [];
}

/**
 * Get label for a distribution type.
 */
export function getDistributionLabel(type: DistributionType): string {
  const option = DISTRIBUTION_OPTIONS.find((o) => o.value === type);
  return option?.label || type;
}
