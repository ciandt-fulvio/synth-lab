/**
 * T032 Synths page (placeholder).
 *
 * Synth catalog page accessible from header.
 *
 * References:
 *   - Spec: specs/018-experiment-hub/spec.md (US8)
 */

import { useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { SynthList } from '@/components/synths/SynthList';
import { ArrowLeft } from 'lucide-react';

export default function Synths() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-slate-50 via-white to-blue-50/30 border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/')}
              className="text-muted-foreground hover:text-primary"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <img
              src="/synthlab-log.png"
              alt="SynthLab Logo"
              className="h-8 w-auto"
            />
            <h1 className="text-3xl font-bold text-primary">SynthLab</h1>
            <Badge variant="secondary">Beta</Badge>
          </div>
          <p className="mt-2 text-sm font-semibold text-gray-600 ml-12">
            Catálogo de Synths
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <SynthList />
      </main>
    </div>
  );
}
