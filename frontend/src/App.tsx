import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { setQueryClient } from "./services/api";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import Index from "./pages/Index";
import OldHome from "./pages/OldHome";
import LoginPage from "./pages/LoginPage";
import OAuthCallback from "./pages/OAuthCallback";
import ExperimentDetail from "./pages/ExperimentDetail";
import InterviewDetail from "./pages/InterviewDetail";
import Synths from "./pages/Synths";
import SynthGroupDetail from "./pages/SynthGroupDetail";
import NewExperiment from "./pages/NewExperiment";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();
setQueryClient(queryClient);

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/auth/callback" element={<OAuthCallback />} />

          {/* Protected Routes */}
          <Route path="/" element={<ProtectedRoute><Index /></ProtectedRoute>} />
          <Route path="/old-home/" element={<ProtectedRoute><OldHome /></ProtectedRoute>} />
          <Route path="/new-experiment/" element={<ProtectedRoute><NewExperiment /></ProtectedRoute>} />
          <Route path="/experiments/:id" element={<ProtectedRoute><ExperimentDetail /></ProtectedRoute>} />
          <Route path="/old-experiments/:id" element={<ProtectedRoute><ExperimentDetail /></ProtectedRoute>} />
          <Route path="/interviews/:execId" element={<ProtectedRoute><InterviewDetail /></ProtectedRoute>} />
          <Route path="/experiments/:expId/interviews/:execId" element={<ProtectedRoute><InterviewDetail /></ProtectedRoute>} />
          <Route path="/synths" element={<ProtectedRoute><Synths /></ProtectedRoute>} />
          <Route path="/synths/groups/:groupId" element={<ProtectedRoute><SynthGroupDetail /></ProtectedRoute>} />

          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
