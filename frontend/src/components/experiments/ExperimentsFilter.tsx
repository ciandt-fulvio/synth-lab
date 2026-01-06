/**
 * Search, tag filter, and sort controls for experiments list.
 *
 * Provides:
 * - Search input with 300ms debounce
 * - Tag filter dropdown
 * - Sort dropdown (Recent / Name A-Z)
 *
 * References:
 *   - Design System: globals.css
 *   - shadcn/ui: components/ui/*
 */

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Search, X } from 'lucide-react';
import { useTags } from '@/hooks/use-tags';

export type SortOption = 'recent' | 'name';

interface ExperimentsFilterProps {
  search: string;
  sortOption: SortOption;
  selectedTag: string | null;
  onSearchChange: (search: string) => void;
  onSortChange: (sort: SortOption) => void;
  onTagChange: (tag: string | null) => void;
}

export function ExperimentsFilter({
  search,
  sortOption,
  selectedTag,
  onSearchChange,
  onSortChange,
  onTagChange,
}: ExperimentsFilterProps) {
  // Local state for input value (before debounce)
  const [inputValue, setInputValue] = useState(search);

  // Fetch available tags
  const { data: tags = [] } = useTags();

  // Sync local state if external search changes
  useEffect(() => {
    setInputValue(search);
  }, [search]);

  // Debounce search input (300ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (inputValue !== search) {
        onSearchChange(inputValue);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [inputValue, search, onSearchChange]);

  return (
    <div className="flex items-center gap-3 mb-6">
      {/* Search Input */}
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <Input
          type="text"
          placeholder="Buscar por nome ou hipótese..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Tag Filter */}
      {tags.length > 0 && (
        <div className="flex items-center gap-2">
          <Select
            value={selectedTag || 'all'}
            onValueChange={(v) => onTagChange(v === 'all' ? null : v)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filtrar por tag" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas as tags</SelectItem>
              {tags.map((tag) => (
                <SelectItem key={tag.id} value={tag.name}>
                  {tag.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {selectedTag && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onTagChange(null)}
              className="h-9 px-2"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      )}

      {/* Sort Dropdown */}
      <Select value={sortOption} onValueChange={(v) => onSortChange(v as SortOption)}>
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="Ordenar por" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="recent">Recentes</SelectItem>
          <SelectItem value="name">Nome A-Z</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
