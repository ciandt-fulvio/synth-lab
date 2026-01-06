/**
 * TagSelector component.
 *
 * Component for managing experiment tags with autocomplete.
 * Allows adding and removing tags from an experiment.
 *
 * Usage:
 *   <TagSelector experimentId="exp_123" currentTags={['tag1', 'tag2']} />
 */

import { useState } from 'react';
import { X, Plus, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useTags, useAddTagToExperiment, useRemoveTagFromExperiment } from '@/hooks/use-tags';

interface TagSelectorProps {
  experimentId: string;
  currentTags: string[];
  readonly?: boolean;
}

export function TagSelector({ experimentId, currentTags, readonly = false }: TagSelectorProps) {
  const [inputValue, setInputValue] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);

  const { data: allTags = [], isLoading: isLoadingTags } = useTags();
  const addTagMutation = useAddTagToExperiment();
  const removeTagMutation = useRemoveTagFromExperiment();

  // Filter suggestions based on input and exclude already added tags
  const suggestions = allTags
    .filter((tag) => !currentTags.includes(tag.name))
    .filter((tag) => tag.name.toLowerCase().includes(inputValue.toLowerCase()))
    .slice(0, 5); // Limit to 5 suggestions

  const handleAddTag = async (tagName: string) => {
    const trimmedName = tagName.trim();
    if (!trimmedName) return;

    // Check if tag already exists
    if (currentTags.includes(trimmedName)) {
      toast.error('Tag já adicionada');
      return;
    }

    try {
      await addTagMutation.mutateAsync({
        experimentId,
        data: { tag_name: trimmedName },
      });
      toast.success(`Tag "${trimmedName}" adicionada`);
      setInputValue('');
      setShowSuggestions(false);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erro ao adicionar tag');
    }
  };

  const handleRemoveTag = async (tagName: string) => {
    try {
      await removeTagMutation.mutateAsync({
        experimentId,
        tagName,
      });
      toast.success(`Tag "${tagName}" removida`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erro ao remover tag');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag(inputValue);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  if (readonly && currentTags.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      {/* Current Tags */}
      {currentTags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {currentTags.map((tag) => (
            <Badge
              key={tag}
              variant="secondary"
              className="px-2 py-1 text-xs bg-indigo-50 text-indigo-700 border border-indigo-200 hover:bg-indigo-100 transition-colors"
            >
              {tag}
              {!readonly && (
                <button
                  onClick={() => handleRemoveTag(tag)}
                  className="ml-1.5 hover:text-indigo-900 focus:outline-none"
                  disabled={removeTagMutation.isPending}
                  aria-label={`Remove tag ${tag}`}
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </Badge>
          ))}
        </div>
      )}

      {/* Add Tag Input */}
      {!readonly && (
        <div className="relative">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Input
                type="text"
                placeholder="Adicionar tag..."
                value={inputValue}
                onChange={(e) => {
                  setInputValue(e.target.value);
                  setShowSuggestions(true);
                }}
                onKeyDown={handleKeyDown}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => {
                  // Delay to allow click on suggestion
                  setTimeout(() => setShowSuggestions(false), 200);
                }}
                disabled={isLoadingTags || addTagMutation.isPending}
                className="text-sm"
              />

              {/* Suggestions Dropdown */}
              {showSuggestions && suggestions.length > 0 && inputValue && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg max-h-40 overflow-y-auto">
                  {suggestions.map((tag) => (
                    <button
                      key={tag.id}
                      onClick={() => handleAddTag(tag.name)}
                      className="w-full px-3 py-2 text-left text-sm hover:bg-slate-50 transition-colors"
                    >
                      {tag.name}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <Button
              size="sm"
              onClick={() => handleAddTag(inputValue)}
              disabled={!inputValue.trim() || addTagMutation.isPending}
              className="btn-primary flex-shrink-0"
            >
              {addTagMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
