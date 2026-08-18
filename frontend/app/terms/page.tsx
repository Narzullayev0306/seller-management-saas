import Link from "next/link";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-900/95">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-sm font-bold text-white shadow-sm">
              S
            </span>
            <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
              Tech<span className="text-indigo-600 dark:text-indigo-400">Mart</span>
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link
              href="/storefront"
              className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-indigo-500"
            >
              Storefront
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-16 sm:px-6">
        <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-12">
          <h1 className="text-3xl font-black text-slate-900 dark:text-white">Terms of Service</h1>
          <p className="mt-2 text-xs text-slate-400">Last updated: August 18, 2026</p>

          <div className="mt-8 space-y-6 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
            <section>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">1. Acceptance of Terms</h2>
              <p className="mt-2">
                By accessing and using TechMart SaaS and Storefront platforms, you accept and agree to be bound by the terms and provision of this agreement.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">2. User & Seller Accounts</h2>
              <p className="mt-2">
                To access certain features of the platform, you must register for an account. You agree to provide accurate, current, and complete information and maintain the security of your credentials.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">3. Orders, Pricing & Payments</h2>
              <p className="mt-2">
                All prices displayed on the storefront are in US Dollars unless otherwise specified. We reserve the right to refuse or cancel any order for reasons including inventory limitations or pricing inaccuracies.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">4. Intellectual Property</h2>
              <p className="mt-2">
                All content, trademarks, logos, and software belong to TechMart SaaS and its respective licensors. Unauthorized copying or redistribution is strictly prohibited.
              </p>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
