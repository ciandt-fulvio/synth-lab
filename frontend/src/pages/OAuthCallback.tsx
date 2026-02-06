import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';

/**
 * OAuth Callback page - handles token from backend OAuth flow
 *
 * For staging/production:
 * 1. Backend redirects to /auth/callback?token=xxx
 * 2. This page extracts token from URL
 * 3. Sets auth_token cookie locally (same domain)
 * 4. Redirects to home page
 *
 * This solves the cross-domain cookie problem:
 * - Backend is at synth-lab-api-*.up.railway.app
 * - Frontend is at synth-lab-frontend-*.up.railway.app
 * - Cookies cannot be shared between different domains
 * - Solution: backend sends token in URL, frontend sets cookie locally
 */
export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const token = searchParams.get('token');

    if (!token) {
      toast.error('Authentication failed', {
        description: 'No token received from authentication server',
      });
      navigate('/login', { replace: true });
      return;
    }

    // Save token to localStorage (works across domains)
    localStorage.setItem('auth_token', token);

    // Redirect to home
    toast.success('Logged in successfully');
    navigate('/', { replace: true });
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
        <p className="text-slate-600">Completing authentication...</p>
      </div>
    </div>
  );
}
