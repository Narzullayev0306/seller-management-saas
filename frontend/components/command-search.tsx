"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

const ACTIONS = [
  { href: "/dashboard", label: "Dashboard", type: "Page", icon: "M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" },
  { href: "/dashboard/products", label: "Products", type: "Page", icon: "M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zM6 8h12M6 12h12M6 16h8" },
  { href: "/dashboard/orders", label: "Orders", type: "Page", icon: "M12 2 2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" },
  { href: "/dashboard/customers", label: "Customers", type: "Page", icon: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm14 10v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" },
  { href: "/dashboard/sellers", label: "Sellers", type: "Page", icon: "M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0zM12 14a7 7 0 0 0-7 7h14a7 7 0 0 0-7-7z" },
  { href: "/dashboard/purchase-orders", label: "Purchase Orders", type: "Page", icon: "M3 3v18h18M7 9h10M7 13h6" },
  { href: "/dashboard/refunds", label: "Refunds", type: "Page", icon: "M4 4h16v6a4 4 0 0 1-4 4h-8a4 4 0 0 1-4-4V4zm8 10v7m-4-3 4 3 4-3" },
  { href: "/dashboard/webhooks", label: "Webhooks", type: "Page", icon: "M6 3v18M4 7l4 4-4 4M18 3v18M14 9l4 4-4 4" },
  { href: "/dashboard/api-keys", label: "API Keys", type: "Page", icon: "M15 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0zm-4 4h8v3a2 2 0 0 1-2 2h-2v2h-2v2H9m-2-2v.01" },
  { href: "/dashboard/billing", label: "Billing", type: "Page", icon: "M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7zm2 0h2v2h4V7h8v10H7v-2h2v-2H7V7zm4 0v2h6V7h-6z" },
  { href: "/dashboard/inventory", label: "Inventory", type: "Page", icon: "M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16zM3.27 6.96 12 12.01l8.73-5.05M12 22.08V12" },
  { href: "/dashboard/users", label: "Team", type: "Page", icon: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm14 10v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" },
  { href: "/dashboard/audit", label: "Audit log", type: "Page", icon: "M12 8v4l3 3m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" },
  { href: "/storefront", label: "Storefront", type: "Public", icon: "M2.5 7h19l-2 12H4.5l-2-12zM6 7a6 6 0 0 1 12 0" },
];

export function CommandSearchModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      const t = setTimeout(() => {
        setQuery("");
        inputRef.current?.focus();
      }, 10);
      return () => clearTimeout(t);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return ACTIONS;
    return ACTIONS.filter((a) => a.label.toLowerCase().includes(q) || a.type.toLowerCase().includes(q));
  }, [query]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center px-4 pt-20">
      <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-xs" onClick={onClose} />
      <div className="relative z-10 w-full max-w-xl animate-in fade-in zoom-in-95 duration-150 rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-3.5 dark:border-slate-800">
          <svg className="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search pages and actions…"
            className="flex-1 bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none dark:text-slate-100"
          />
          <kbd className="rounded-md border border-slate-200 px-1.5 py-0.5 text-[10px] font-medium text-slate-400 dark:border-slate-700">ESC</kbd>
        </div>
        <div className="max-h-80 overflow-y-auto p-2">
          <p className="px-3 pb-1.5 pt-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">Navigation</p>
          {results.length === 0 ? (
            <p className="px-3 py-8 text-center text-sm text-slate-500">No results found</p>
          ) : (
            results.map((a) => (
              <Link
                key={a.href}
                href={a.href}
                onClick={onClose}
                className="group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-500 group-hover:bg-indigo-100 group-hover:text-indigo-600 dark:bg-slate-800 dark:text-slate-400 dark:group-hover:bg-indigo-950 dark:group-hover:text-indigo-400">
                  <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
                    <path d={a.icon} />
                  </svg>
                </span>
                <span className="flex-1 font-medium text-slate-700 dark:text-slate-200">{a.label}</span>
                <span className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                  {a.type}
                </span>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  );
}