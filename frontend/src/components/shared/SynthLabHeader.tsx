/**
 * SynthLabHeader - Shared header component for all pages.
 *
 * Usage:
 *   <SynthLabHeader
 *     subtitle="Detalhe do Experimento"
 *     backTo="/"
 *     actions={<Button>Action</Button>}
 *   />
 *
 * Props:
 *   - subtitle: Text shown below "SynthLab" (optional)
 *   - backTo: URL to navigate when clicking back button (optional, shows back button if provided)
 *   - actions: React node for right-side actions (optional)
 */

import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface SynthLabHeaderProps {
  /** Subtitle text shown below "SynthLab" */
  subtitle?: string;
  /** URL to navigate back to (shows back button if provided) */
  backTo?: string;
  /** Action buttons/elements to show on the right side */
  actions?: React.ReactNode;
}

export function SynthLabHeader({ subtitle, backTo, actions }: SynthLabHeaderProps) {
  const navigate = useNavigate();

  return (
    <header className="header-sticky">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Back Button */}
            {backTo && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate(backTo)}
                className="btn-ghost-icon"
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
            )}

            {/* Logo - Link to homepage */}
            <Link to="/" className="relative hover:opacity-80 transition-opacity">
              <div className="logo-glow" />
              <img
                src="/synthlab-log.png"
                alt="SynthLab Logo"
                className="relative h-9 w-auto logo-pulse-loop"
              />
            </Link>

            {/* Title and subtitle */}
            <div>
              <div className="flex items-center gap-2">
                <Link to="/" className="hover:opacity-80 transition-opacity">
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-slate-900 via-slate-700 to-slate-900 bg-clip-text text-transparent">
                    SynthLab
                  </h1>
                </Link>
                <Badge variant="secondary" className="text-xs badge-primary">
                  Beta
                </Badge>
              </div>
              {subtitle ? (
                <p className="text-xs text-slate-500 font-medium tracking-wide">
                  {subtitle}
                </p>
              ) : (
                <p className="text-xs text-slate-500 font-medium tracking-wide">
                  Pesquisa sintética, insights reais
                </p>
              )}
            </div>
          </div>

          {/* Right-side actions */}
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      </div>
    </header>
  );
}

export default SynthLabHeader;
