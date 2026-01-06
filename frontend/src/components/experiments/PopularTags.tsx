/**
 * Popular Tags - Quick filter buttons for experiments.
 *
 * Displays available tags as clickable badges for quick filtering.
 * Shows active state when a tag is selected.
 *
 * References:
 *   - Design System: globals.css
 *   - Tags API: services/tags-api.ts
 */

import { useTags } from '@/hooks/use-tags';
import { Tag as TagIcon } from 'lucide-react';

interface PopularTagsProps {
  selectedTag: string | null;
  onTagClick: (tag: string | null) => void;
}

export function PopularTags({ selectedTag, onTagClick }: PopularTagsProps) {
  const { data: tags = [], isLoading } = useTags();

  // Don't render if no tags or still loading
  if (isLoading || tags.length === 0) {
    return null;
  }

  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-3">
        <TagIcon className="h-4 w-4 text-slate-400" />
        <span className="text-sm font-medium text-slate-600">
          Filtros rápidos
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        {tags.map((tag) => {
          const isActive = selectedTag === tag.name;
          return (
            <button
              key={tag.id}
              onClick={() => onTagClick(isActive ? null : tag.name)}
              className={`
                px-3 py-1.5 rounded-full text-sm font-medium
                transition-all duration-200
                ${
                  isActive
                    ? 'bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow-md shadow-indigo-200'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200 hover:shadow-sm'
                }
              `}
            >
              {tag.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}
