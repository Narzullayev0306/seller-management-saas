"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { api } from "@/lib/api-client";

function AcceptInviteForm() {
  const params = useSearchParams();
  const token = params.get("token") ?? "";

  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<{ fullName?: string; password?: string; confirm?: string; form?: string }>({});
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  function validate(): boolean {
    const next: typeof errors = {};
    if (!token) next.form = "This invite link is invalid or incomplete. Ask your admin to resend the invite.";
    if (!fullName.trim()) next.fullName = "Full name is required";
    if (!password) next.password = "Password is required";
    else if (password.length < 8) next.password = "Password must be at least 8 characters";
    if (!confirm) next.confirm = "Please confirm your password";
    else if (confirm !== password) next.confirm = "Passwords do not match";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setErrors({});
    try {
      await api.post("/auth/invites/accept", {
        token,
        full_name: fullName.trim(),
        password,
      });
      setDone(true);
    } catch (err) {
      setErrors({ form: err instanceof Error ? err.message : "Failed to accept invite" });
    } finally {
      setLoading(false);
    }
  }

  if (done) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-2xl dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-950/40">
          <svg className="h-6 w-6 text-emerald-600 dark:text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 6 9 17l-5-5" />
          </svg>
        </div>
        <h2 className="mt-4 text-lg font-semibold text-slate-900 dark:text-slate-100">Welcome to the team!</h2>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Your account is ready. Sign in to get started.</p>
        <Link
          href="/login"
          className="mt-6 inline-flex rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-500"
        >
          Sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
      <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Join your team</h2>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
        You have been invited to a workspace. Set your name and password to activate your account.
      </p>

      {errors.form && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950/40 dark:text-red-300">
          {errors.form}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
        <Field label="Full name" error={errors.fullName}>
          <Input
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Jane Smith"
            autoComplete="name"
          />
        </Field>
        <Field label="Password" error={errors.password}>
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Min 8 characters"
            autoComplete="new-password"
          />
        </Field>
        <Field label="Confirm password" error={errors.confirm}>
          <Input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="Repeat password"
            autoComplete="new-password"
          />
        </Field>
        <Button type="submit" className="w-full" size="lg" loading={loading}>
          {loading ? "Activating..." : "Activate account"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
        <Link href="/login" className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}

export default function AcceptInvitePage() {
  return (
    <Suspense fallback={<div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500 shadow-2xl dark:border-slate-800 dark:bg-slate-900">Loading...</div>}>
      <AcceptInviteForm />
    </Suspense>
  );
}