/**
 * T032 Synths page - Synth Catalog.
 *
 * Synth catalog page with Research Observatory aesthetic.
 *
 * References:
 *   - Spec: specs/018-experiment-hub/spec.md (US8)
 */

import { useState, useEffect } from 'react';
import { SynthList } from '@/components/synths/SynthList';
import { Users, Filter } from 'lucide-react';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import { useSynthGroups } from '@/hooks/use-synth-groups';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

// =============================================================================
// Animated Section Component
// =============================================================================

interface AnimatedSectionProps {
  children: React.ReactNode;
  delay?: number;
}

function AnimatedSection({ children, delay = 0 }: AnimatedSectionProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      className={`transition-all duration-500 ease-out ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
      }`}
    >
      {children}
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function Synths() {
  const [selectedGroupId, setSelectedGroupId] = useState<string | undefined>(undefined);
  const { data: groupsData, isLoading: groupsLoading } = useSynthGroups({ limit: 100 });

  const handleGroupChange = (value: string) => {
    if (value === 'all') {
      setSelectedGroupId(undefined);
    } else {
      setSelectedGroupId(value);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader subtitle="Catálogo de Synths" backTo="/" />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header with Filter */}
        <AnimatedSection delay={0}>
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-indigo-500 to-violet-500 rounded-xl text-white shadow-lg shadow-indigo-200/50">
                <Users className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Synths</h2>
                <p className="text-sm text-slate-500">
                  Cada synth representa um perfil demográfico e comportamental único
                </p>
              </div>
            </div>

            {/* Filter */}
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-slate-400" />
              <Select
                value={selectedGroupId || 'all'}
                onValueChange={handleGroupChange}
                disabled={groupsLoading}
              >
                <SelectTrigger className="w-[220px] bg-white border-slate-200 hover:border-slate-300 transition-colors">
                  <SelectValue placeholder="Todos os grupos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os grupos</SelectItem>
                  {groupsData?.data.map((group) => (
                    <SelectItem key={group.id} value={group.id}>
                      {group.name} ({group.synth_count})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </AnimatedSection>

        {/* Synth List */}
        <AnimatedSection delay={100}>
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <SynthList selectedGroupId={selectedGroupId} />
          </div>
        </AnimatedSection>
      </main>
    </div>
  );
}
