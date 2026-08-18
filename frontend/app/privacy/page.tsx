import Link from "next/link";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export default function PrivacyPage() {
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
          <h1 className="text-3xl font-black text-slate-900 dark:text-white">Privacy Policy</h1>
          <p className="mt-2 text-xs text-slate-400">Last updated: August 18, 2026</p>

          <div className="mt-8 space-y-6 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
            <section>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">1. Information We Collect</h2>
              <p className="mt-2">
                We collect personal information that you provide when registering an account, placing orders, or contacting support (e.g. name, email address, shipping details, and billing records).
              </p>
            </section>

            <section>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">2. How We Use Information</h2>
              <p className="mt-2">
                Your data is used solely to fulfill orders, process transactions securely, deliver product notifications, and provide customer support.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">3. Data Security & Encryption</h2>
              <p className="mt-2">
                We implement industry standard encryption (TLS/HTTPS and secure hashed storage) to protect your sensitive information from unauthorized access.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">4. Cookies & Preferences</h2>
              <p className="mt-2">
                We use localized storage cookies to save your user sessions, cart state, and theme preferences (Dark/Light mode).
              </p>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
