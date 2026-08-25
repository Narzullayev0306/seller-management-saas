"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string; form?: string }>({});
  const [loading, setLoading] = useState(false);

  function validate(): boolean {
    const next: typeof errors = {};
    if (!email.trim()) next.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) next.email = "Enter a valid email address";
    if (!password) next.password = "Password is required";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setErrors({});
    try {
      const me = await login(email.trim(), password);
      if (me.permissions.length === 0) {
        router.push("/storefront");
      } else {
        router.push("/dashboard");
      }
      router.refresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Login failed";
      setErrors({ form: message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white/95 p-7 shadow-xl shadow-slate-200/50 backdrop-blur-xl dark:border-white/[0.08] dark:bg-slate-900/90 dark:shadow-2xl dark:shadow-black/50">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">Welcome back</h2>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Enter your credentials to access your dashboard.
        </p>
      </div>

      {/* Demo Credentials Pill */}
      <div
        onClick={() => {
          setEmail("owner@techmart.uz");
          setPassword("DemoPass123!");
        }}
        className="group mt-4 flex cursor-pointer items-center justify-between rounded-lg border border-indigo-100 bg-indigo-50/70 px-3 py-2 text-xs transition duration-150 hover:border-indigo-300 hover:bg-indigo-50 dark:border-indigo-900/50 dark:bg-indigo-950/40 dark:hover:border-indigo-700"
        title="Click to fill credentials"
      >
        <div className="flex items-center gap-2">
          <span className="flex h-2 w-2 rounded-full bg-indigo-600 animate-pulse dark:bg-indigo-400" />
          <span className="font-medium text-indigo-900 dark:text-indigo-200">
            Demo: <span className="font-mono text-[11px] text-indigo-700 dark:text-indigo-300">owner@techmart.uz</span>
          </span>
        </div>
        <span className="font-medium text-[11px] text-indigo-600 transition group-hover:translate-x-0.5 dark:text-indigo-400">
          Autofill →
        </span>
      </div>

      {errors.form && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50/80 px-3.5 py-2.5 text-xs font-medium text-red-700 animate-shake dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
          {errors.form}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-5 space-y-4" noValidate>
        <Field label="Work email" error={errors.email}>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            autoComplete="email"
          />
        </Field>
        <Field label="Password" error={errors.password}>
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            autoComplete="current-password"
          />
        </Field>
        <div className="flex items-center justify-between pt-0.5 text-xs">
          <span />
          <Link
            href="/forgot-password"
            className="font-medium text-indigo-600 transition hover:text-indigo-500 dark:text-indigo-400"
          >
            Forgot password?
          </Link>
        </div>
        <Button type="submit" className="w-full" size="md" loading={loading}>
          {loading ? "Signing in..." : "Sign in to account"}
        </Button>
      </form>

      <div className="mt-6 border-t border-slate-100 pt-4 text-center text-xs text-slate-500 dark:border-slate-800 dark:text-slate-400">
        Don&apos;t have an account yet?{" "}
        <Link href="/register" className="font-semibold text-indigo-600 transition hover:text-indigo-500 dark:text-indigo-400">
          Create account
        </Link>
      </div>
    </div>
  );
}