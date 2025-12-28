/**
 * T032 Synths page - Synth Catalog.
 *
 * Synth catalog page with Research Observatory aesthetic.
 *
 * References:
 *   - Spec: specs/018-experiment-hub/spec.md (US8)
 */

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { SynthList } from '@/components/synths/SynthList';
import { Users, Sparkles } from 'lucide-react';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';

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
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader subtitle="Catálogo de Synths" backTo="/" />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <AnimatedSection delay={0}>
          <div className="flex items-center gap-3 mb-8">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl text-white shadow-lg shadow-blue-200">
              <Users className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-900">Synths</h2>
              <p className="text-sm text-slate-500">
                Personas sintéticas para pesquisa qualitativa
              </p>
            </div>
          </div>
        </AnimatedSection>

        {/* Info Banner */}
        <AnimatedSection delay={100}>
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-100 rounded-xl p-4 mb-8">
            <div className="flex items-start gap-3">
              <div className="p-1.5 bg-white rounded-lg shadow-sm">
                <Sparkles className="h-4 w-4 text-purple-500" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-700">
                  Synths são personas geradas por IA
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Cada synth representa um perfil demográfico e comportamental único,
                  usado para simular entrevistas qualitativas de pesquisa.
                </p>
              </div>
            </div>
          </div>
        </AnimatedSection>

        {/* Synth List */}
        <AnimatedSection delay={200}>
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <SynthList />
          </div>
        </AnimatedSection>
      </main>
    </div>
  );
}
