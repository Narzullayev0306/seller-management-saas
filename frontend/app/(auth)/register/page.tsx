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
    <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
      <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Create your account</h2>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
        You will be registered as a customer and can start shopping right away.
      </p>

      {errors.form && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800">
          {errors.form}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
        <Field label="Full name" error={errors.full_name}>
          <Input
            value={form.full_name}
            onChange={(e) => set("full_name", e.target.value)}
            placeholder="John Doe"
            autoComplete="name"
          />
        </Field>
        <Field label="Email" error={errors.email}>
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
            placeholder="••••••••"
            autoComplete="new-password"
          />
          <ul className="mt-2 space-y-1">
            {PASSWORD_RULES.map((rule) => {
              const ok = rule.test(form.password);
              return (
                <li
                  key={rule.id}
                  className={`flex items-center gap-1.5 text-xs ${ok ? "text-emerald-600" : "text-slate-400 dark:text-slate-500"}`}
                >
                  {ok ? "✓" : "○"} {rule.label}
                </li>
              );
            })}
          </ul>
        </Field>
        <Field label="Confirm password" error={errors.confirm}>
          <Input
            type="password"
            value={form.confirm}
            onChange={(e) => set("confirm", e.target.value)}
            placeholder="••••••••"
            autoComplete="new-password"
          />
        </Field>
        <Button type="submit" className="w-full" size="lg" loading={loading}>
          {loading ? "Creating account..." : "Create account"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400">
          Sign in
        </Link>
      </p>
    </div>
  );
}
