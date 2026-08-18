"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api-client";

function VerifyEmailContent() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") ?? "";

  const [state, setState] = useState<"verifying" | "success" | "error">("verifying");
  const [message, setMessage] = useState("");

  const verify = useCallback(async () => {
    if (!token) {
      setState("error");
      setMessage("This link is invalid or incomplete. Use the link from your verification email.");
      return;
    }
    setState("verifying");
    try {
      await api.post("/auth/verify-email", { token });
      setState("success");
    } catch (err) {
      setState("error");
      setMessage(err instanceof Error ? err.message : "Verification failed");
    }
  }, [token]);

  useEffect(() => {
    const t = setTimeout(() => void verify(), 0);
    return () => clearTimeout(t);
  }, [verify]);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-2xl dark:border-slate-800 dark:bg-slate-900">
      {state === "verifying" && (
        <>
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
          <h2 className="mt-4 text-lg font-semibold text-slate-900 dark:text-slate-100">Verifying your email...</h2>
        </>
      )}

      {state === "success" && (
        <>
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-950/40">
            <svg className="h-6 w-6 text-emerald-600 dark:text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 6 9 17l-5-5" />
            </svg>
          </div>
          <h2 className="mt-4 text-lg font-semibold text-slate-900 dark:text-slate-100">Email verified</h2>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Your account is fully activated.</p>
          <Button className="mt-6" onClick={() => router.push("/dashboard")}>
            Go to dashboard
          </Button>
        </>
      )}

      {state === "error" && (
        <>
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-950/40">
            <svg className="h-6 w-6 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" />
            </svg>
          </div>
          <h2 className="mt-4 text-lg font-semibold text-slate-900 dark:text-slate-100">Verification failed</h2>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{message}</p>
          <Link href="/login" className="mt-6 inline-block text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400">
            Back to sign in
          </Link>
        </>
      )}
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500 shadow-2xl dark:border-slate-800 dark:bg-slate-900">Loading...</div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}