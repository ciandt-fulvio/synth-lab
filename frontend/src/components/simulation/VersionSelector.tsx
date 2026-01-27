/**
 * VersionSelector component for selecting hypothesis versions.
 *
 * Dropdown with version history.
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
import type { HypothesisVersion } from '@/types/hypothesis';

interface VersionSelectorProps {
  /**
   * Available versions.
   */
  versions: HypothesisVersion[];

  /**
   * Currently selected version.
   */
  value?: number;

  /**
   * Callback when version changes.
   */
  onChange: (version: number) => void;

  /**
   * Whether selector is disabled.
   */
  disabled?: boolean;

  /**
   * Placeholder text.
   */
  placeholder?: string;
}

/**
 * VersionSelector component.
 *
 * @example
 * <VersionSelector
 *   versions={versions}
 *   value={selectedVersion}
 *   onChange={setSelectedVersion}
 * />
 */
export function VersionSelector({
  versions,
  value,
  onChange,
  disabled = false,
  placeholder = 'Select version...',
}: VersionSelectorProps) {
  return (
    <Select
      value={value?.toString()}
      onValueChange={(v) => onChange(parseInt(v, 10))}
      disabled={disabled}
    >
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {versions.map((version) => (
          <SelectItem key={version.version} value={version.version.toString()}>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="font-medium">v{version.version}</span>
                {version.name && (
                  <span className="text-xs text-slate-500">({version.name})</span>
                )}
              </div>
              <span className="text-xs text-slate-500">
                {new Date(version.created_at).toLocaleDateString()}
              </span>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
