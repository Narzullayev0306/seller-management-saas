"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useCustomerAuth } from "@/lib/customer-auth";
import { ThemeToggle } from "@/components/ui/theme-toggle";

const FIELD_CLASS =
  "mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-100 dark:border-slate-800 dark:bg-slate-800 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-indigo-500";
const LABEL_CLASS = "text-xs font-semibold text-slate-700 dark:text-slate-300";

export default function StorefrontLoginPage() {
  const router = useRouter();
  const { login } = useCustomerAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email.trim(), password);
      router.push("/storefront");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-900/95">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/storefront" className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-sm font-bold text-white shadow-sm">
              S
            </span>
            <span className="text-lg font-bold tracking-tight">
              Tech<span className="text-indigo-600 dark:text-indigo-400">Mart</span>
            </span>
          </Link>
          <ThemeToggle />
        </div>
      </header>

      <main className="flex flex-1 items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Welcome back</h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Sign in to your account to track orders and check out faster.
            </p>

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <div>
                <label className={LABEL_CLASS} htmlFor="sf-login-email">
                  Email
                </label>
                <input
                  id="sf-login-email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className={FIELD_CLASS}
                />
              </div>

              <div>
                <label className={LABEL_CLASS} htmlFor="sf-login-password">
                  Password
                </label>
                <input
                  id="sf-login-password"
                  type="password"
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className={FIELD_CLASS}
                />
              </div>

              {error && (
                <p className="rounded-xl bg-red-50 px-3 py-2.5 text-xs font-medium text-red-700 dark:bg-red-950/50 dark:text-red-400">
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500 dark:bg-indigo-600 dark:hover:bg-indigo-500 dark:disabled:bg-slate-800 dark:disabled:text-slate-600"
              >
                {loading ? (
                  <span className="mx-auto block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                ) : (
                  "Sign in"
                )}
              </button>
            </form>

            <p className="mt-5 text-center text-xs text-slate-500 dark:text-slate-400">
              New here?{" "}
              <Link
                href="/storefront/auth/register"
                className="font-semibold text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
              >
                Create an account
              </Link>
            </p>
          </div>

          <p className="mt-4 text-center text-xs text-slate-400 dark:text-slate-500">
            No account needed — you can also shop as a guest.
          </p>
        </div>
      </main>
    </div>
  );
}