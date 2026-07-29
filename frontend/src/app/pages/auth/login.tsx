import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { AnimatedLogo } from "@/components/animated-logo";

export function LoginPage() {
  const { login, isDemoMode, enterDemoMode } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      navigate("/");
    } catch (err: unknown) {
      const apiErr = err as { message?: string };
      setError(apiErr.message || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoMode = () => {
    enterDemoMode();
    navigate("/");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <Card className="w-full max-w-md">
          <CardHeader className="space-y-1 text-center">
            <CardTitle className="text-2xl font-bold">
              <AnimatedLogo />
            </CardTitle>
            <CardDescription>Sign in to your account</CardDescription>
          </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {isDemoMode && (
              <div className="rounded-md bg-amber-500/15 p-3 text-sm text-amber-600 dark:text-amber-400">
                <p className="font-medium">Backend unavailable</p>
                <p className="mt-1">
                  You can browse the UI in demo mode. AI features require a running backend.
                </p>
              </div>
            )}
            {error && (
              <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="username">Username or Email</Label>
              <Input
                id="username"
                placeholder="Enter your username or email"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-4">
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Signing in..." : "Sign In"}
            </Button>
            {isDemoMode && (
              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={handleDemoMode}
              >
                Browse in Demo Mode
              </Button>
            )}
            <p className="text-sm text-muted-foreground">
              Don't have an account?{" "}
              <Link to="/register" className="text-primary hover:underline">
                Sign up
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
