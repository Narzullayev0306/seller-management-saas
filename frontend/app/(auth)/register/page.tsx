"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth";

interface FormErrors {
  full_name?: string;
  email?: string;
  password?: string;
  confirm?: string;
  form?: string;
}

const PASSWORD_RULES = [
  { id: "length", label: "At least 8 characters", test: (v: string) => v.length >= 8 },
  { id: "upper", label: "One uppercase letter", test: (v: string) => /[A-Z]/.test(v) },
  { id: "lower", label: "One lowercase letter", test: (v: string) => /[a-z]/.test(v) },
  { id: "digit", label: "One number", test: (v: string) => /\d/.test(v) },
];

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", confirm: "" });
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);

  function set<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function validate(): boolean {
    const next: FormErrors = {};
    if (!form.full_name.trim()) next.full_name = "Your full name is required";
    if (!form.email.trim()) next.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) next.email = "Enter a valid email address";
    if (!form.password) next.password = "Password is required";
    else if (!PASSWORD_RULES.every((r) => r.test(form.password))) next.password = "Password does not meet the requirements below";
    if (form.confirm !== form.password) next.confirm = "Passwords do not match";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setErrors({});
    try {
      const me = await register({
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        password: form.password,
      });
      if (me.permissions.length === 0) {
        router.push("/storefront");
      } else {
        router.push("/dashboard");
      }
      router.refresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Registration failed";
      setErrors({ form: message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white/95 p-7 shadow-xl shadow-slate-200/50 backdrop-blur-xl dark:border-white/[0.08] dark:bg-slate-900/90 dark:shadow-2xl dark:shadow-black/50">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">Create your account</h2>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Get started with your seller management workspace.
        </p>
      </div>

      {errors.form && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50/80 px-3.5 py-2.5 text-xs font-medium text-red-700 animate-shake dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
          {errors.form}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-5 space-y-3.5" noValidate>
        <Field label="Full name" error={errors.full_name}>
          <Input
            value={form.full_name}
            onChange={(e) => set("full_name", e.target.value)}
            placeholder="John Doe"
            autoComplete="name"
          />
        </Field>
        <Field label="Work email" error={errors.email}>
          <Input
            type="email"
            value={form.email}
            onChange={(e) => set("email", e.target.value)}
            placeholder="you@company.com"
            autoComplete="email"
          />
        </Field>
        <Field label="Password" error={errors.password}>
          <Input
            type="password"
            value={form.password}
            onChange={(e) => set("password", e.target.value)}
            placeholder="Create a strong password"
            autoComplete="new-password"
          />
        </Field>

        {/* Password Strength Checklist */}
        <div className="rounded-lg border border-slate-100 bg-slate-50/80 p-3 dark:border-slate-800/80 dark:bg-slate-800/40">
          <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">Password requirements:</p>
          <ul className="mt-2 grid grid-cols-2 gap-1.5 text-[11px]">
            {PASSWORD_RULES.map((rule) => {
              const ok = form.password.length > 0 && rule.test(form.password);
              return (
                <li
                  key={rule.id}
                  className={`flex items-center gap-1.5 transition-colors duration-150 ${
                    ok
                      ? "text-emerald-600 dark:text-emerald-400 font-medium"
                      : "text-slate-400 dark:text-slate-500"
                  }`}
                >
                  <span className={`flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full text-[9px] ${
                    ok ? "bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-300 font-bold" : "bg-slate-200 dark:bg-slate-700"
                  }`}>
                    {ok ? "✓" : "•"}
                  </span>
                  <span>{rule.label}</span>
                </li>
              );
            })}
          </ul>
        </div>

        <Field label="Confirm password" error={errors.confirm}>
          <Input
            type="password"
            value={form.confirm}
            onChange={(e) => set("confirm", e.target.value)}
            placeholder="Repeat password"
            autoComplete="new-password"
          />
        </Field>

        <div className="pt-2">
          <Button type="submit" className="w-full" size="md" loading={loading}>
            {loading ? "Creating account..." : "Create account"}
          </Button>
        </div>
      </form>

      <div className="mt-6 border-t border-slate-100 pt-4 text-center text-xs text-slate-500 dark:border-slate-800 dark:text-slate-400">
        Already have an account?{" "}
        <Link href="/login" className="font-semibold text-indigo-600 transition hover:text-indigo-500 dark:text-indigo-400">
          Sign in
        </Link>
      </div>
    </div>
  );
}
