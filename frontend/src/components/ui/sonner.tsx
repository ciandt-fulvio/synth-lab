import { Toaster as Sonner } from "sonner";

type ToasterProps = React.ComponentProps<typeof Sonner>;

/**
 * SynthLab Toast Notifications
 *
 * Styled Sonner toaster with SynthLab design system colors.
 * Uses top-right position with 5s auto-dismiss.
 *
 * Usage:
 *   import { toast } from 'sonner';
 *   toast.success('Operação realizada com sucesso');
 *   toast.error('Erro ao executar operação');
 *   toast.info('Informação importante');
 *   toast.warning('Atenção necessária');
 *
 * References:
 *   - Sonner docs: https://sonner.emilkowal.ski/
 *   - Design system: frontend/CLAUDE.md
 */
const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      position="top-right"
      expand={false}
      richColors
      closeButton
      duration={5000}
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-white group-[.toaster]:text-slate-900 group-[.toaster]:border group-[.toaster]:shadow-lg group-[.toaster]:rounded-xl",
          description: "group-[.toast]:text-slate-600",
          actionButton:
            "group-[.toast]:bg-indigo-600 group-[.toast]:text-white group-[.toast]:hover:bg-indigo-700",
          cancelButton:
            "group-[.toast]:bg-slate-100 group-[.toast]:text-slate-700 group-[.toast]:hover:bg-slate-200",
          closeButton:
            "group-[.toast]:bg-slate-100 group-[.toast]:text-slate-500 group-[.toast]:hover:bg-slate-200 group-[.toast]:border-slate-200",
          // Semantic colors matching SynthLab design system
          success:
            "group-[.toaster]:bg-green-50 group-[.toaster]:text-green-900 group-[.toaster]:border-green-200",
          error:
            "group-[.toaster]:bg-red-50 group-[.toaster]:text-red-900 group-[.toaster]:border-red-200",
          warning:
            "group-[.toaster]:bg-amber-50 group-[.toaster]:text-amber-900 group-[.toaster]:border-amber-200",
          info: "group-[.toaster]:bg-indigo-50 group-[.toaster]:text-indigo-900 group-[.toaster]:border-indigo-200",
        },
      }}
      {...props}
    />
  );
};

export { Toaster };
