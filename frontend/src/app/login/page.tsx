"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { LogIn, AlertCircle, Loader2 } from "lucide-react";
import BNGLogo from "@/components/BNGLogo";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (res.ok && data.authenticated) {
        router.push("/");
        router.refresh();
      } else {
        setError(data.error || "Login failed");
      }
    } catch {
      setError("Connection failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="mx-auto mb-4 flex justify-center">
            <BNGLogo size={56} />
          </div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">OBD SuperStar Agent</h1>
          <p className="text-xs text-[var(--accent)] font-medium mt-1">by Black &amp; Green</p>
          <p className="text-sm text-[var(--muted)] mt-2">
            Sign in to access the platform
          </p>
        </div>

        {/* Login Form */}
        <form
          onSubmit={handleSubmit}
          className="p-6 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] space-y-5"
        >
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-[var(--error)]/10 border border-[var(--error)]/20">
              <AlertCircle className="w-4 h-4 text-[var(--error)] shrink-0" />
              <p className="text-sm text-[var(--error)]">{error}</p>
            </div>
          )}

          <div>
            <label
              htmlFor="username"
              className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5"
            >
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              autoComplete="username"
              className="w-full px-4 py-2.5 rounded-xl bg-[var(--input-bg)] border border-[var(--card-border)] text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent)]/50 focus:ring-1 focus:ring-[var(--accent)]/30 transition-colors"
              placeholder="Enter username"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="w-full px-4 py-2.5 rounded-xl bg-[var(--input-bg)] border border-[var(--card-border)] text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent)]/50 focus:ring-1 focus:ring-[var(--accent)]/30 transition-colors"
              placeholder="Enter password"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !username || !password}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-white font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            style={{ background: `linear-gradient(135deg, var(--gradient-from), var(--gradient-to))` }}
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <LogIn className="w-4 h-4" />
            )}
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <p className="text-center text-xs text-[var(--muted)] mt-6">
          Powered by BNG &middot; Touching Billions of Lives
        </p>
      </div>
    </div>
  );
}
