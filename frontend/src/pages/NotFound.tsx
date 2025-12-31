import { useLocation, Link } from "react-router-dom";
import { useEffect } from "react";
import { Home, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error(
      "404 Error: User attempted to access non-existent route:",
      location.pathname,
    );
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-indigo-50/30 flex flex-col">
      {/* Decorative background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-indigo-100/40 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-violet-100/30 rounded-full blur-3xl" />
      </div>

      {/* Main content */}
      <main className="flex-1 flex items-center justify-center px-4 relative z-10">
        <div className="max-w-2xl w-full text-center">
          {/* Image */}
          <div className="mb-8 flex justify-center">
            <img
              src="/404.png"
              alt="Robôs confusos olhando para um erro"
              className="w-full max-w-xs sm:max-w-sm h-auto drop-shadow-lg"
            />
          </div>

          {/* Text content */}
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-indigo-100/80 text-indigo-700 rounded-full text-sm font-medium">
              <span className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse" />
              Erro 404
            </div>

            <h1 className="text-3xl sm:text-4xl font-bold text-slate-800">
              Página não encontrada
            </h1>

            <p className="text-slate-600 text-lg max-w-md mx-auto">
              Parece que nossos robôs também estão confusos.
              <br />
              <span className="text-slate-500">
                A página <code className="px-1.5 py-0.5 bg-slate-100 rounded text-sm font-mono text-indigo-600">{location.pathname}</code> não existe.
              </span>
            </p>
          </div>

          {/* Actions */}
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Button
              asChild
              className="bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white shadow-lg shadow-indigo-500/25 transition-all hover:shadow-xl hover:shadow-indigo-500/30"
            >
              <Link to="/">
                <Home className="w-4 h-4 mr-2" />
                Voltar ao início
              </Link>
            </Button>

            <Button
              variant="outline"
              onClick={() => window.history.back()}
              className="border-slate-300 text-slate-700 hover:bg-slate-50"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Página anterior
            </Button>
          </div>
        </div>
      </main>

      {/* Footer hint */}
      <footer className="pb-6 text-center relative z-10">
        <p className="text-sm text-slate-400">
          SynthLab — Pesquisa sintética, insights reais
        </p>
      </footer>
    </div>
  );
};

export default NotFound;
