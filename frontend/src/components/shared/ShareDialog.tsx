/**
 * ShareDialog component.
 *
 * Modal for sharing experiments or synth groups by email.
 * Shows active shares and pending invites with ability to revoke.
 */

import { useState } from 'react';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  useExperimentShares,
  useShareExperiment,
  useRevokeExperimentShare,
} from '@/hooks/use-sharing';
import { Mail, X, Clock, UserCheck, Loader2 } from 'lucide-react';

interface ShareDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  experimentId: string;
  experimentName: string;
}

export function ShareDialog({
  open,
  onOpenChange,
  experimentId,
  experimentName,
}: ShareDialogProps) {
  const [email, setEmail] = useState('');

  const { data: sharesData, isLoading } = useExperimentShares(experimentId, open);
  const shareMutation = useShareExperiment();
  const revokeMutation = useRevokeExperimentShare();

  const handleShare = () => {
    const trimmed = email.trim().toLowerCase();
    if (!trimmed || !trimmed.includes('@')) {
      toast.error('Email invalido');
      return;
    }

    shareMutation.mutate(
      { experimentId, email: trimmed },
      {
        onSuccess: (result) => {
          setEmail('');
          if (result.status === 'shared') {
            toast.success(`Compartilhado com ${trimmed}`);
          } else {
            toast.success(`Convite pendente criado para ${trimmed}`, {
              description: 'O acesso sera concedido quando a pessoa se cadastrar.',
            });
          }
        },
        onError: (error) => {
          const message = error instanceof Error ? error.message : 'Erro ao compartilhar';
          toast.error(message);
        },
      },
    );
  };

  const handleRevoke = (targetEmail: string) => {
    revokeMutation.mutate(
      { experimentId, email: targetEmail },
      {
        onSuccess: () => {
          toast.success(`Acesso revogado para ${targetEmail}`);
        },
        onError: (error) => {
          const message = error instanceof Error ? error.message : 'Erro ao revogar';
          toast.error(message);
        },
      },
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleShare();
    }
  };

  const activeShares = sharesData?.shares ?? [];
  const pendingInvites = sharesData?.pending ?? [];
  const hasAccess = activeShares.length > 0 || pendingInvites.length > 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-lg">
            Compartilhar "{experimentName}"
          </DialogTitle>
        </DialogHeader>

        {/* Email input */}
        <div className="flex gap-2">
          <Input
            type="email"
            placeholder="email@exemplo.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={shareMutation.isPending}
          />
          <Button
            onClick={handleShare}
            disabled={shareMutation.isPending || !email.trim()}
            size="default"
          >
            {shareMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Mail className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Access list */}
        <div className="mt-2">
          {isLoading ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
            </div>
          ) : !hasAccess ? (
            <p className="text-sm text-slate-400 text-center py-4">
              Nenhum compartilhamento ainda.
            </p>
          ) : (
            <div className="space-y-1 max-h-60 overflow-y-auto">
              {/* Active shares */}
              {activeShares.map((share) => (
                <div
                  key={share.share_id}
                  className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-50 group"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <UserCheck className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm text-slate-700 truncate">
                        {share.display_name || share.email}
                      </p>
                      {share.display_name && (
                        <p className="text-xs text-slate-400 truncate">{share.email}</p>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity text-slate-400 hover:text-red-500"
                    onClick={() => handleRevoke(share.email)}
                    disabled={revokeMutation.isPending}
                  >
                    <X className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}

              {/* Pending invites */}
              {pendingInvites.map((invite) => (
                <div
                  key={invite.invite_id}
                  className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-50 group"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <Clock className="h-4 w-4 text-amber-500 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm text-slate-700 truncate">{invite.email}</p>
                      <p className="text-xs text-amber-600">pendente</p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity text-slate-400 hover:text-red-500"
                    onClick={() => handleRevoke(invite.email)}
                    disabled={revokeMutation.isPending}
                  >
                    <X className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
