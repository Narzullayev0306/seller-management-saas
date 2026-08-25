"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { api } from "@/lib/api-client";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [errors, setErrors] = useState<{ email?: string; form?: string }>({});
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  function validate(): boolean {
    const next: typeof errors = {};
    if (!email.trim()) next.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) next.email = "Enter a valid email address";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setErrors({});
    try {
      await api.post("/auth/forgot-password", { email: email.trim() });
      setSent(true);
    } catch (err) {
      setErrors({ form: err instanceof Error ? err.message : "Something went wrong" });
    } finally {
      setLoading(false);
    }
  }

  if (sent) {
    return (
      <div className="rounded-2xl border border-slate-200/80 bg-white/95 p-7 text-center shadow-xl shadow-slate-200/50 backdrop-blur-xl dark:border-white/[0.08] dark:bg-slate-900/90 dark:shadow-2xl dark:shadow-black/50">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100 dark:bg-emerald-950/60">
          <svg className="h-6 w-6 text-emerald-600 dark:text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z" />
          </svg>
        </div>
        <h2 className="mt-4 text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">Check your email</h2>
        <p className="mt-2 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
          If an account exists for <b className="text-slate-800 dark:text-slate-200">{email}</b>, a password reset link has been sent. The link expires in 1 hour.
        </p>
        <Link href="/login" className="mt-6 inline-block text-xs font-semibold text-indigo-600 transition hover:text-indigo-500 dark:text-indigo-400">
          ← Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white/95 p-7 shadow-xl shadow-slate-200/50 backdrop-blur-xl dark:border-white/[0.08] dark:bg-slate-900/90 dark:shadow-2xl dark:shadow-black/50">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">Reset your password</h2>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Enter your email and we will send you a secure reset link.
        </p>
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
        <Button type="submit" className="w-full" size="md" loading={loading}>
          {loading ? "Sending..." : "Send reset link"}
        </Button>
      </form>

      <div className="mt-6 border-t border-slate-100 pt-4 text-center text-xs text-slate-500 dark:border-slate-800 dark:text-slate-400">
        Remembered your password?{" "}
        <Link href="/login" className="font-semibold text-indigo-600 transition hover:text-indigo-500 dark:text-indigo-400">
          Sign in
        </Link>
      </div>
    </div>
  );
}