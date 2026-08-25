import type { ReactNode } from "react";
import Link from "next/link";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export const metadata = { title: "Welcome" };

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="relative flex min-h-screen flex-col justify-between bg-slate-50 text-slate-900 selection:bg-indigo-500 selection:text-white dark:bg-[#0a0f1d] dark:text-slate-100">
      {/* Background ambient lighting */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden opacity-30 dark:opacity-20" aria-hidden="true">
        <div className="absolute left-1/2 -top-40 h-[500px] w-[600px] -translate-x-1/2 rounded-full bg-indigo-500/25 blur-[140px]" />
        <div className="absolute -right-40 bottom-10 h-[400px] w-[400px] rounded-full bg-sky-500/15 blur-[120px]" />
      </div>

      {/* Top Bar with brand and theme toggle */}
      <header className="relative z-10 mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-5">
        <Link href="/" className="group flex items-center gap-2.5 transition">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-600 to-sky-400 text-sm font-bold text-white shadow-sm shadow-indigo-500/25 transition-transform duration-200 group-hover:scale-105">
            S
          </div>
          <span className="text-base font-bold tracking-tight text-slate-900 dark:text-white">
            Seller<span className="text-indigo-600 dark:text-indigo-400">Flow</span>
          </span>
        </Link>
        <ThemeToggle className="rounded-lg border border-slate-200/80 p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:border-slate-800 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100" />
      </header>

      {/* Main Form Center */}
      <main className="relative z-10 flex flex-1 items-center justify-center px-4 py-8 sm:px-6">
        <div className="w-full max-w-[420px] animate-fade-up">
          {children}
        </div>
      </main>

      {/* Subtle Footer */}
      <footer className="relative z-10 mx-auto w-full max-w-7xl px-6 py-5 text-center text-xs text-slate-400 dark:text-slate-600">
        © {new Date().getFullYear()} SellerFlow Inc. Protected by enterprise-grade security.
      </footer>
    </div>
  );
}