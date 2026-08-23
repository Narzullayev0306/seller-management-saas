"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";

import { formatMoney } from "@/lib/format";
import { ThemeToggle } from "@/components/ui/theme-toggle";

function CheckoutSuccessContent() {
  const searchParams = useSearchParams();
  // Lazy initializer: generated once per mount instead of on every render.
  const [fallbackOrderNumber] = useState(
    () => "ORD-" + Math.floor(100000 + Math.random() * 900000),
  );
  const orderNumber = searchParams?.get("order") || fallbackOrderNumber;
  const total = searchParams?.get("total") || "149.00";

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 selection:bg-indigo-500 selection:text-white dark:bg-slate-950 dark:text-slate-100">
      {/* Sticky Header */}
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-900/95">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link
            href="/storefront"
            className="flex items-center gap-2.5"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-sm font-bold text-white shadow-sm">
              S
            </span>
            <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
              Tech<span className="text-indigo-600 dark:text-indigo-400">Mart</span>
            </span>
          </Link>
          <ThemeToggle />
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-4 py-16 text-center sm:px-6">
        {/* Animated Checkmark Icon */}
        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 shadow-xl shadow-emerald-500/10 dark:bg-emerald-950/60 dark:text-emerald-400">
          <svg className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
        </div>

        <h1 className="mt-6 text-3xl font-black tracking-tight text-slate-900 dark:text-white sm:text-4xl">
          Order Confirmed!
        </h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Thank you for your purchase. We have received your order and are preparing it for shipment.
        </p>

        {/* Order Details Card */}
        <div className="mt-8 overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-8 text-left">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Order Number
              </span>
              <p className="text-lg font-bold text-slate-900 dark:text-white">
                #{orderNumber}
              </p>
            </div>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
              Paid & Confirmed
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 py-4 text-xs">
            <div>
              <span className="text-slate-400">Estimated Delivery</span>
              <p className="font-semibold text-slate-700 dark:text-slate-300">2-4 Business Days</p>
            </div>
            <div>
              <span className="text-slate-400">Total Amount</span>
              <p className="font-black text-slate-900 dark:text-white">{formatMoney(total)}</p>
            </div>
          </div>

          <div className="rounded-2xl bg-indigo-50/60 p-4 dark:bg-indigo-950/40">
            <p className="text-xs font-medium text-indigo-900 dark:text-indigo-200">
              📦 A confirmation email and tracking link will be sent once your package is dispatched.
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            href="/storefront/orders"
            className="w-full sm:w-auto rounded-2xl bg-indigo-600 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-600/25 transition hover:bg-indigo-500 active:scale-[0.98]"
          >
            Track My Order
          </Link>
          <Link
            href="/storefront"
            className="w-full sm:w-auto rounded-2xl border border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Continue Shopping
          </Link>
        </div>
      </main>
    </div>
  );
}

export default function CheckoutSuccessPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">Loading confirmation…</div>}>
      <CheckoutSuccessContent />
    </Suspense>
  );
}
