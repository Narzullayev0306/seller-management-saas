"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const router = useRouter();

  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center px-6 py-16 text-center">
      <svg viewBox="0 0 160 120" fill="none" aria-hidden className="h-auto w-36">
        <circle cx="80" cy="56" r="42" className="fill-red-50 dark:fill-red-950/30" />
        <circle cx="80" cy="56" r="27" className="fill-red-100 dark:fill-red-900/40" />
        <path d="M80 44v14m0 8h.01" strokeWidth="4" strokeLinecap="round" className="stroke-red-500 dark:stroke-red-400" />
        <path d="M32 104h96" strokeWidth="3" strokeLinecap="round" className="stroke-red-100 dark:stroke-red-950" />
      </svg>
      <h1 className="mt-6 text-2xl font-bold text-slate-900 dark:text-slate-100">Something went wrong</h1>
      <p className="mt-2 max-w-md text-small leading-relaxed text-slate-500 dark:text-slate-400">
        An unexpected error interrupted this page. Your data is safe — try again,
        and if the problem persists, return to the dashboard.
      </p>
      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        <button
          onClick={reset}
          className="rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-700 active:scale-[0.98] dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
        >
          Try again
        </button>
        <button
          onClick={() => router.push("/dashboard")}
          className="rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-medium text-slate-600 transition hover:border-slate-300 hover:text-slate-900 active:scale-[0.98] dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-slate-600 dark:hover:text-white"
        >
          Return to dashboard
        </button>
      </div>
    </div>
  );
}
