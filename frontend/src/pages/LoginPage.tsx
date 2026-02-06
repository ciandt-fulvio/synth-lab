/**
 * Login Page component.
 *
 * Displays Google OAuth login button for user authentication.
 */

import { GoogleLoginButton } from "../components/auth/GoogleLoginButton";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";

export default function LoginPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">
            Welcome to Synth-Lab
          </CardTitle>
          <CardDescription className="text-center">
            Sign in with your Google account to continue
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center space-y-4">
          <GoogleLoginButton className="w-full" />
          <p className="text-sm text-gray-500 text-center">
            By signing in, you agree to our Terms of Service and Privacy Policy
          </p>
        </CardContent>
      </Card>
      {import.meta.env.VITE_COMMIT_SHA && (
        <p className="mt-3 text-[10px] text-gray-300 font-mono">
          v.{import.meta.env.VITE_COMMIT_SHA.slice(0, 7)}
        </p>
      )}
    </div>
  );
}
