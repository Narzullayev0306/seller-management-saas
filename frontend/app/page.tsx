"use client";

import Link from "next/link";
import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export default function LandingPage() {
  const { user } = useAuth();
  const [billingCycle, setBillingCycle] = useState<"monthly" | "annual">("annual");

  const [previewTab, setPreviewTab] = useState<"overview" | "orders" | "inventory">("overview");

  return (
    <div className="min-h-screen bg-slate-50/50 text-slate-900 selection:bg-indigo-500 selection:text-white dark:bg-[#090d16] dark:text-slate-100">
      {/* Background ambient glow */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden opacity-35 dark:opacity-25" aria-hidden="true">
        <div className="absolute left-1/2 -top-48 h-[600px] w-[800px] -translate-x-1/2 rounded-full bg-indigo-500/20 blur-[150px]" />
        <div className="absolute -right-40 top-1/3 h-[500px] w-[500px] rounded-full bg-purple-500/15 blur-[160px]" />
        <div className="absolute bottom-10 left-1/4 h-[400px] w-[500px] rounded-full bg-sky-500/15 blur-[140px]" />
      </div>

      {/* Navigation Header */}
      <header className="sticky top-0 z-40 border-b border-slate-200/70 bg-white/80 backdrop-blur-xl dark:border-white/[0.07] dark:bg-[#090d16]/80">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3.5 sm:px-6 lg:px-8">
          <Link href="/" className="group flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-600 to-sky-400 text-sm font-bold text-white shadow-sm shadow-indigo-500/25 transition-transform duration-200 group-hover:scale-105">
              S
            </div>
            <span className="text-base font-bold tracking-tight text-slate-900 dark:text-white">
              Seller<span className="text-indigo-600 dark:text-indigo-400">Flow</span>
            </span>
          </Link>

          <nav className="hidden items-center gap-7 md:flex">
            <a href="#features" className="text-xs font-medium text-slate-600 transition hover:text-indigo-600 dark:text-slate-400 dark:hover:text-slate-100">
              Features
            </a>
            <a href="#architecture" className="text-xs font-medium text-slate-600 transition hover:text-indigo-600 dark:text-slate-400 dark:hover:text-slate-100">
              Architecture
            </a>
            <a href="#pricing" className="text-xs font-medium text-slate-600 transition hover:text-indigo-600 dark:text-slate-400 dark:hover:text-slate-100">
              Pricing
            </a>
            <Link href="/storefront" className="flex items-center gap-1 text-xs font-medium text-indigo-600 transition hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300">
              <span>Storefront</span>
              <span className="rounded-md bg-indigo-50 px-1.5 py-0.5 text-[10px] font-bold dark:bg-indigo-950/60">Live</span>
            </Link>
          </nav>

          <div className="flex items-center gap-2.5">
            <ThemeToggle className="rounded-lg border border-slate-200/80 p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:border-slate-800 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100" />

            {user ? (
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm shadow-indigo-600/20 transition hover:bg-indigo-500 active:scale-[0.97]"
              >
                Dashboard
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                </svg>
              </Link>
            ) : (
              <>
                <Link
                  href="/login"
                  className="rounded-lg px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
                >
                  Sign in
                </Link>
                <Link
                  href="/register"
                  className="rounded-lg bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm shadow-indigo-600/20 transition hover:bg-indigo-500 active:scale-[0.97]"
                >
                  Get started
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 mx-auto max-w-7xl px-4 pt-16 pb-20 sm:px-6 sm:pt-24 lg:px-8">
        <div className="text-center animate-fade-up">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200/80 bg-indigo-50/70 px-3.5 py-1 text-xs font-semibold text-indigo-700 backdrop-blur-sm dark:border-indigo-900/60 dark:bg-indigo-950/40 dark:text-indigo-300">
            <span className="flex h-2 w-2 rounded-full bg-indigo-600 dark:bg-indigo-400 animate-pulse" />
            Enterprise Multi-Tenant SaaS Suite
          </div>

          <h1 className="mt-6 text-4xl font-extrabold tracking-tight sm:text-6xl sm:leading-[1.12]">
            Unified Multi-Seller & <br className="hidden sm:inline" />
            <span className="bg-gradient-to-r from-indigo-600 via-indigo-500 to-sky-500 bg-clip-text text-transparent">
              Operations Management
            </span>
          </h1>

          <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-slate-600 dark:text-slate-300">
            Streamline your multi-seller ecosystem. Manage roles, catalogs, live inventory movements, customer orders, and commission payouts in one high-performance dashboard.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              href={user ? "/dashboard" : "/register"}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm shadow-indigo-600/25 transition hover:bg-indigo-500 active:scale-[0.97]"
            >
              {user ? "Open Dashboard" : "Start Free Trial"}
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </Link>

            <Link
              href="/storefront"
              className="inline-flex items-center gap-2 rounded-lg border border-slate-300/80 bg-white/90 px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-xs backdrop-blur-sm transition hover:bg-slate-50 hover:text-slate-900 active:scale-[0.97] dark:border-slate-700 dark:bg-slate-900/90 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              <svg className="h-4 w-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 00-16.536-1.84M7.5 14.25L5.106 5.272M6 20.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm12.75 0a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" />
              </svg>
              View Public Storefront
            </Link>
          </div>
        </div>

        {/* Hero Interactive UI Preview */}
        <div className="mt-12 overflow-hidden rounded-2xl border border-slate-200/80 bg-slate-900/5 p-2 shadow-2xl backdrop-blur-xl dark:border-white/[0.08] dark:bg-slate-900/30">
          <div className="rounded-xl border border-slate-200/80 bg-white shadow-inner dark:border-slate-800 dark:bg-slate-900">
            {/* Window bar */}
            <div className="flex items-center justify-between border-b border-slate-100 px-4 py-2.5 dark:border-slate-800/80">
              <div className="flex items-center gap-1.5">
                <div className="h-2.5 w-2.5 rounded-full bg-rose-500/80" />
                <div className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
                <div className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
              </div>

              {/* Interactive preview tabs */}
              <div className="flex items-center gap-1 rounded-lg bg-slate-100 p-0.5 dark:bg-slate-800">
                {(["overview", "orders", "inventory"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setPreviewTab(tab)}
                    className={`rounded-md px-2.5 py-1 text-xs font-medium capitalize transition duration-150 ${
                      previewTab === tab
                        ? "bg-white text-indigo-700 shadow-xs dark:bg-slate-900 dark:text-indigo-300"
                        : "text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-1.5 font-mono text-[11px] text-slate-400">
                <span className="flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
                v2.0 Live
              </div>
            </div>

            {/* Dashboard Mockup Body based on selected tab */}
            {previewTab === "overview" && (
              <div className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-4 animate-fade-in">
                <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-4 dark:border-slate-800/80 dark:bg-slate-800/40">
                  <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">Monthly Revenue</p>
                  <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-white">$48,250.00</p>
                  <p className="mt-2 text-xs font-semibold text-emerald-600 dark:text-emerald-400">↑ 18.4% vs last period</p>
                </div>

                <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-4 dark:border-slate-800/80 dark:bg-slate-800/40">
                  <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">Completed Orders</p>
                  <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-white">1,429</p>
                  <p className="mt-2 text-xs font-semibold text-indigo-600 dark:text-indigo-400">99.4% Fulfillment Rate</p>
                </div>

                <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-4 dark:border-slate-800/80 dark:bg-slate-800/40">
                  <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">Active Sellers</p>
                  <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-white">38 Partners</p>
                  <p className="mt-2 text-xs font-semibold text-purple-600 dark:text-purple-400">$6,840 Commission</p>
                </div>

                <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-4 dark:border-slate-800/80 dark:bg-slate-800/40">
                  <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">Low Stock Alerts</p>
                  <p className="mt-1 text-2xl font-bold text-amber-600 dark:text-amber-400">3 SKUs</p>
                  <p className="mt-2 text-xs font-semibold text-slate-500 dark:text-slate-400">Auto-restock scheduled</p>
                </div>
              </div>
            )}

            {previewTab === "orders" && (
              <div className="p-5 animate-fade-in">
                <div className="space-y-2">
                  {[
                    { id: "ORD-9421", customer: "Amir Temur", amount: "$149.00", status: "Delivered", color: "text-emerald-700 bg-emerald-50 dark:bg-emerald-950/40 dark:text-emerald-300" },
                    { id: "ORD-9420", customer: "Malika Karimova", amount: "$89.50", status: "Shipped", color: "text-blue-700 bg-blue-50 dark:bg-blue-950/40 dark:text-blue-300" },
                    { id: "ORD-9419", customer: "Bobur Mirzo", amount: "$220.00", status: "Processing", color: "text-amber-700 bg-amber-50 dark:bg-amber-950/40 dark:text-amber-300" },
                  ].map((order) => (
                    <div key={order.id} className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800/60 dark:bg-slate-800/30">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-xs font-semibold text-indigo-600 dark:text-indigo-400">{order.id}</span>
                        <span className="text-xs font-medium text-slate-700 dark:text-slate-200">{order.customer}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-bold text-slate-900 dark:text-slate-100">{order.amount}</span>
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${order.color}`}>{order.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {previewTab === "inventory" && (
              <div className="p-5 animate-fade-in">
                <div className="space-y-2">
                  {[
                    { sku: "SKU-WL-01", name: "Wireless Headphones Pro", qty: 109, health: "Optimal", color: "text-emerald-600" },
                    { sku: "SKU-KB-04", name: "Mechanical Keyboard RGB", qty: 88, health: "Optimal", color: "text-emerald-600" },
                    { sku: "SKU-CM-09", name: "Instant Camera Mini V2", qty: 13, health: "Low stock", color: "text-amber-600" },
                  ].map((item) => (
                    <div key={item.sku} className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800/60 dark:bg-slate-800/30">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-xs font-medium text-slate-400">{item.sku}</span>
                        <span className="text-xs font-medium text-slate-800 dark:text-slate-200">{item.name}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">{item.qty} units</span>
                        <span className={`text-[11px] font-semibold ${item.color}`}>{item.health}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Metrics Bar */}
      <section className="border-y border-slate-200/80 bg-slate-50/60 py-10 dark:border-slate-800/80 dark:bg-slate-900/40">
        <div className="mx-auto grid max-w-7xl grid-cols-2 gap-8 px-4 text-center sm:grid-cols-4 sm:px-6 lg:px-8">
          <div>
            <div className="text-3xl font-extrabold text-indigo-600 dark:text-indigo-400">5 Roles</div>
            <p className="mt-1 text-xs font-medium text-slate-500 dark:text-slate-400">Owner, Admin, Manager, Seller, Viewer</p>
          </div>
          <div>
            <div className="text-3xl font-extrabold text-purple-600 dark:text-purple-400">32 Perms</div>
            <p className="mt-1 text-xs font-medium text-slate-500 dark:text-slate-400">Granular Role-Based Permissions</p>
          </div>
          <div>
            <div className="text-3xl font-extrabold text-blue-600 dark:text-blue-400">100%</div>
            <p className="mt-1 text-xs font-medium text-slate-500 dark:text-slate-400">Tenant Isolation by Organization ID</p>
          </div>
          <div>
            <div className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">&lt; 30ms</div>
            <p className="mt-1 text-xs font-medium text-slate-500 dark:text-slate-400">FastAPI & PostgreSQL Response Time</p>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">Built for scale</h2>
          <p className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">Everything required to operate a multi-seller ecosystem</p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
          {/* Card 1 */}
          <div className="group rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition hover:border-indigo-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-800">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z" />
              </svg>
            </div>
            <h3 className="mt-5 text-lg font-bold text-slate-900 dark:text-slate-100">Multi-Tenant Architecture</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
              Every query is filtered by company ID in the repository layer. Switch workspaces seamlessly with scoped JWT claims.
            </p>
          </div>

          {/* Card 2 */}
          <div className="group rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition hover:border-indigo-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-800">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-purple-50 text-purple-600 dark:bg-purple-950/60 dark:text-purple-400">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
            </div>
            <h3 className="mt-5 text-lg font-bold text-slate-900 dark:text-slate-100">5-Tier RBAC & Audit Trail</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
              Catalog of 32 distinct permissions. Immutable audit logging records actor, entity, timestamps, and metadata.
            </p>
          </div>

          {/* Card 3 */}
          <div className="group rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition hover:border-indigo-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-800">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-950/60 dark:text-blue-400">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
              </svg>
            </div>
            <h3 className="mt-5 text-lg font-bold text-slate-900 dark:text-slate-100">Automated Stock & Order Lifecycle</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
              Single-transaction inventory decrements on order creation, restore on cancellation, and commission calculation on delivery.
            </p>
          </div>

          {/* Card 4 */}
          <div className="group rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition hover:border-indigo-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-800">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007z" />
              </svg>
            </div>
            <h3 className="mt-5 text-lg font-bold text-slate-900 dark:text-slate-100">Customer Luxury Storefront</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
              Public storefront with responsive category browsing, instant cart calculations, product reviews, and inventory checks.
            </p>
          </div>

          {/* Card 5 */}
          <div className="group rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition hover:border-indigo-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-800">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-50 text-amber-600 dark:bg-amber-950/60 dark:text-amber-400">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            </div>
            <h3 className="mt-5 text-lg font-bold text-slate-900 dark:text-slate-100">Live Analytics & CSV Export</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
              Area and donut charts, sales velocity, top-performing sellers, low-stock threshold triggers, and 1-click CSV data export.
            </p>
          </div>

          {/* Card 6 */}
          <div className="group rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition hover:border-indigo-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-800">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-rose-50 text-rose-600 dark:bg-rose-950/60 dark:text-rose-400">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
              </svg>
            </div>
            <h3 className="mt-5 text-lg font-bold text-slate-900 dark:text-slate-100">Zero-Trust Authentication</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
              Short-lived access JWTs with rotating refresh tokens, rate limiting protection, and one-time password invitation tokens.
            </p>
          </div>
        </div>
      </section>

      {/* Architecture Section */}
      <section id="architecture" className="border-t border-slate-200/80 bg-slate-50/50 py-20 dark:border-slate-800/80 dark:bg-slate-900/30">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">Architecture & Stack</h2>
            <p className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">Engineered for clean separation & high throughput</p>
          </div>

          <div className="mt-12 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-10">
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-800/60">
                <div className="flex items-center gap-2 text-sm font-bold text-indigo-600 dark:text-indigo-400">
                  <span className="flex h-2.5 w-2.5 rounded-full bg-indigo-500" />
                  Frontend Layer
                </div>
                <h4 className="mt-2 text-lg font-semibold text-slate-900 dark:text-white">Next.js 16 & React 19</h4>
                <ul className="mt-3 space-y-2 text-xs text-slate-600 dark:text-slate-300">
                  <li>• App Router with optimized standalone build</li>
                  <li>• Tailwind CSS with dark mode tokens</li>
                  <li>• JWT rotation & route guard proxies</li>
                </ul>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-800/60">
                <div className="flex items-center gap-2 text-sm font-bold text-purple-600 dark:text-purple-400">
                  <span className="flex h-2.5 w-2.5 rounded-full bg-purple-500" />
                  Backend API Layer
                </div>
                <h4 className="mt-2 text-lg font-semibold text-slate-900 dark:text-white">FastAPI & Python 3.13</h4>
                <ul className="mt-3 space-y-2 text-xs text-slate-600 dark:text-slate-300">
                  <li>• SQLAlchemy 2.0 ORM with OrgRepository</li>
                  <li>• Alembic migrations + Pydantic v2 schemas</li>
                  <li>• Rate limiting & async background workers</li>
                </ul>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-800/60">
                <div className="flex items-center gap-2 text-sm font-bold text-emerald-600 dark:text-emerald-400">
                  <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
                  Data & Persistence
                </div>
                <h4 className="mt-2 text-lg font-semibold text-slate-900 dark:text-white">PostgreSQL + Redis</h4>
                <ul className="mt-3 space-y-2 text-xs text-slate-600 dark:text-slate-300">
                  <li>• Multi-tenant schema with UUID primary keys</li>
                  <li>• Redis token cache & rate limiter fallback</li>
                  <li>• Docker Compose orchestration for prod</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">Pricing plans</h2>
          <p className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">Transparent tiers for growing businesses</p>

          <div className="mt-6 inline-flex items-center rounded-xl border border-slate-200 bg-slate-100 p-1 dark:border-slate-800 dark:bg-slate-900">
            <button
              onClick={() => setBillingCycle("monthly")}
              className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition ${
                billingCycle === "monthly" ? "bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white" : "text-slate-500"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingCycle("annual")}
              className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition ${
                billingCycle === "annual" ? "bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white" : "text-slate-500"
              }`}
            >
              Annual (Save 20%)
            </button>
          </div>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Free Tier */}
          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Free Starter</h3>
            <p className="mt-1 text-xs text-slate-500">Perfect for individual sellers and small teams.</p>
            <div className="mt-6 flex items-baseline gap-1">
              <span className="text-4xl font-extrabold text-slate-900 dark:text-white">$0</span>
              <span className="text-sm text-slate-500">/ forever</span>
            </div>
            <ul className="mt-6 space-y-3 text-xs text-slate-600 dark:text-slate-300">
              <li>✓ Up to 3 Team Members</li>
              <li>✓ Up to 100 Products</li>
              <li>✓ Core Order & Inventory Management</li>
              <li>✓ Basic Sales Analytics</li>
            </ul>
            <Link
              href="/register"
              className="mt-8 block w-full rounded-xl border border-slate-300 bg-white py-2.5 text-center text-sm font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              Start for free
            </Link>
          </div>

          {/* Pro Tier */}
          <div className="relative rounded-2xl border-2 border-indigo-600 bg-white p-8 shadow-xl dark:border-indigo-500 dark:bg-slate-900">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-indigo-600 px-3 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white shadow-sm">
              Most Popular
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Professional</h3>
            <p className="mt-1 text-xs text-slate-500">Designed for established businesses & seller networks.</p>
            <div className="mt-6 flex items-baseline gap-1">
              <span className="text-4xl font-extrabold text-slate-900 dark:text-white">
                {billingCycle === "annual" ? "$39" : "$49"}
              </span>
              <span className="text-sm text-slate-500">/ month</span>
            </div>
            <ul className="mt-6 space-y-3 text-xs text-slate-600 dark:text-slate-300">
              <li>✓ Up to 25 Team Members</li>
              <li>✓ Unlimited Products & Categories</li>
              <li>✓ Automated Commission Tracking</li>
              <li>✓ Custom Public Storefront</li>
              <li>✓ Audit Trail & CSV Exports</li>
            </ul>
            <Link
              href="/register"
              className="mt-8 block w-full rounded-xl bg-indigo-600 py-2.5 text-center text-sm font-semibold text-white shadow-md shadow-indigo-500/20 transition hover:bg-indigo-500"
            >
              Upgrade to Pro
            </Link>
          </div>

          {/* Enterprise Tier */}
          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Enterprise</h3>
            <p className="mt-1 text-xs text-slate-500">For multi-brand organizations requiring dedicated SLAs.</p>
            <div className="mt-6 flex items-baseline gap-1">
              <span className="text-4xl font-extrabold text-slate-900 dark:text-white">
                {billingCycle === "annual" ? "$149" : "$189"}
              </span>
              <span className="text-sm text-slate-500">/ month</span>
            </div>
            <ul className="mt-6 space-y-3 text-xs text-slate-600 dark:text-slate-300">
              <li>✓ Unlimited Team Members & Sellers</li>
              <li>✓ Multi-Organization Workspace Switching</li>
              <li>✓ Custom Roles & Granular Permission Matrix</li>
              <li>✓ Priority 24/7 Dedicated Support</li>
              <li>✓ 99.99% Uptime Guarantee</li>
            </ul>
            <Link
              href="/register"
              className="mt-8 block w-full rounded-xl border border-slate-300 bg-white py-2.5 text-center text-sm font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              Contact Sales
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Footer Section */}
      <footer className="border-t border-slate-200/80 bg-slate-50 dark:border-slate-800/80 dark:bg-slate-950">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-white font-bold text-xs">
                SF
              </div>
              <span className="text-sm font-bold text-slate-900 dark:text-white">Seller Management SaaS</span>
            </div>

            <p className="text-xs text-slate-500">
              © {new Date().getFullYear()} SellerFlow Technologies. All rights reserved.
            </p>

            <div className="flex items-center gap-4 text-xs font-medium text-slate-600 dark:text-slate-400">
              <Link href="/dashboard" className="hover:text-indigo-600 dark:hover:text-white">Dashboard</Link>
              <Link href="/storefront" className="hover:text-indigo-600 dark:hover:text-white">Storefront</Link>
              <Link href="/login" className="hover:text-indigo-600 dark:hover:text-white">Login</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
