"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

const ACTIONS = [
  { href: "/dashboard", label: "Dashboard", type: "Overview", icon: "M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" },
  { href: "/dashboard/reports", label: "Reports", type: "Overview", icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" },
  { href: "/dashboard/products", label: "Products", type: "Commerce", icon: "M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zM6 8h12M6 12h12M6 16h8" },
  { href: "/dashboard/categories", label: "Categories", type: "Commerce", icon: "M4 6h7v7H4zM13 6h7v4h-7zM13 13h7v5h-7zM4 16h7v2H4z" },
  { href: "/dashboard/orders", label: "Orders", type: "Commerce", icon: "M12 2 2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" },
  { href: "/dashboard/customers", label: "Customers", type: "Commerce", icon: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm14 10v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" },
  { href: "/dashboard/inventory", label: "Inventory", type: "Commerce", icon: "M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16zM3.27 6.96 12 12.01l8.73-5.05M12 22.08V12" },
  { href: "/dashboard/sellers", label: "Sellers", type: "Operations", icon: "M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0zM12 14a7 7 0 0 0-7 7h14a7 7 0 0 0-7-7z" },
  { href: "/dashboard/suppliers", label: "Suppliers", type: "Operations", icon: "M17 8v3a4 4 0 0 1-8 0V8a2 2 0 1 1 4 0v3a6 6 0 0 1-12 0V8a2 2 0 1 1 4 0v3a2 2 0 1 0 4 0V8a4 4 0 1 0-8 0v3a8 8 0 0 0 16 0V8a4 4 0 1 0-8 0m-2 0v5" },
  { href: "/dashboard/purchase-orders", label: "Purchase Orders", type: "Operations", icon: "M3 3v18h18M7 9h10M7 13h6" },
  { href: "/dashboard/shipping", label: "Shipping", type: "Operations", icon: "M1 3h15v13H1zM16 8h4l3 4v4h-7M5.5 21a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zm13 0a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z" },
  { href: "/dashboard/refunds", label: "Refunds", type: "Operations", icon: "M4 4h16v6a4 4 0 0 1-4 4h-8a4 4 0 0 1-4-4V4zm8 10v7m-4-3 4 3 4-3" },
  { href: "/dashboard/marketing", label: "Coupons", type: "Marketing", icon: "M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" },
  { href: "/dashboard/users", label: "Members", type: "Team", icon: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm14 10v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" },
  { href: "/dashboard/audit", label: "Audit log", type: "Team", icon: "M12 8v4l3 3m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" },
  { href: "/dashboard/webhooks", label: "Webhooks", type: "Developer", icon: "M6 3v18M4 7l4 4-4 4M18 3v18M14 9l4 4-4 4" },
  { href: "/dashboard/api-keys", label: "API Keys", type: "Developer", icon: "M15 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0zm-4 4h8v3a2 2 0 0 1-2 2h-2v2h-2v2H9m-2-2v.01" },
  { href: "/dashboard/billing", label: "Billing", type: "Settings", icon: "M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7zm2 0h2v2h4V7h8v10H7v-2h2v-2H7V7zm4 0v2h6V7h-6z" },
  { href: "/dashboard/settings", label: "Organization settings", type: "Settings", icon: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm7.4-3a7.4 7.4 0 0 0-.1-1.2l2-1.5-2-3.5-2.4 1a7.4 7.4 0 0 0-2-1.2L14.5 3h-5l-.4 2.6a7.4 7.4 0 0 0-2 1.2l-2.4-1-2 3.5 2 1.5a7.4 7.4 0 0 0 0 2.4l-2 1.5 2 3.5 2.4-1a7.4 7.4 0 0 0 2 1.2l.4 2.6h5l.4-2.6a7.4 7.4 0 0 0 2-1.2l2.4 1 2-3.5-2-1.5c.07-.4.1-.8.1-1.2z" },
  { href: "/storefront", label: "Storefront", type: "Public", icon: "M2.5 7h19l-2 12H4.5l-2-12zM6 7a6 6 0 0 1 12 0" },
];

export function CommandSearchModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null;
  // Remounting per open resets query/selection without state effects.
  return <Palette onClose={onClose} />;
}

function Palette({ onClose }: { onClose: () => void }) {
  const [query, setQuery] = useState("");
  const [rawIndex, setRawIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return ACTIONS;
    return ACTIONS.filter(
      (a) => a.label.toLowerCase().includes(q) || a.type.toLowerCase().includes(q),
    );
  }, [query]);

  const activeIndex = Math.min(rawIndex, results.length - 1);

  const move = (delta: number) =>
    setRawIndex((i) => Math.max(0, Math.min(i + delta, results.length - 1)));

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      onClose();
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      move(1);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      move(-1);
    } else if (e.key === "Enter") {
      e.preventDefault();
      const item = results[activeIndex];
      if (item) {
        onClose();
        window.location.assign(item.href);
      }
    }
  };

  // Keep the active row in view during keyboard navigation.
  useEffect(() => {
    const el = listRef.current?.querySelector<HTMLElement>(`[data-index="${activeIndex}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [activeIndex]);

  let lastType = "";

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center px-4 pt-[12vh]" role="dialog" aria-modal="true" aria-label="Command palette">
      <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm animate-fade-in dark:bg-slate-950/70" onClick={onClose} />
      <div className="relative z-10 w-full max-w-xl animate-scale-in overflow-hidden rounded-xl border border-slate-200/80 bg-white shadow-[var(--shadow-overlay)] dark:border-slate-800/80 dark:bg-slate-900">
        <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-3 dark:border-slate-800/80">
          <svg className="h-4 w-4 shrink-0 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKey}
            placeholder="Search pages and actions…"
            role="combobox"
            aria-expanded="true"
            aria-controls="command-palette-list"
            aria-activedescendant={results[activeIndex] ? `cmd-${activeIndex}` : undefined}
            className="flex-1 bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none dark:text-slate-100"
          />
          <kbd className="rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 font-mono text-[10px] font-medium text-slate-400 dark:border-slate-700 dark:bg-slate-800">ESC</kbd>
        </div>
        <div ref={listRef} id="command-palette-list" role="listbox" className="max-h-80 overflow-y-auto p-1.5">
          {results.length === 0 ? (
            <p className="px-3 py-10 text-center text-sm text-slate-500">No results for “{query}”</p>
          ) : (
            results.map((a, i) => {
              const showGroup = a.type !== lastType;
              lastType = a.type;
              const isActive = i === activeIndex;
              return (
                <div key={a.href}>
                  {showGroup && (
                    <p className="px-3 pb-1 pt-2 text-label text-slate-400 first:pt-1 dark:text-slate-600">
                      {a.type}
                    </p>
                  )}
                  <Link
                    id={`cmd-${i}`}
                    data-index={i}
                    role="option"
                    aria-selected={isActive}
                    href={a.href}
                    onMouseEnter={() => setRawIndex(i)}
                    onClick={onClose}
                    className={`group flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm transition-[background-color,color] duration-100 ${
                      isActive
                        ? "bg-indigo-50/80 dark:bg-indigo-500/15"
                        : "hover:bg-slate-50 dark:hover:bg-slate-800/40"
                    }`}
                  >
                    <span
                      className={`flex h-7 w-7 items-center justify-center rounded-md transition-colors ${
                        isActive
                          ? "bg-indigo-100 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300"
                          : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400"
                      }`}
                    >
                      <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
                        <path d={a.icon} />
                      </svg>
                    </span>
                    <span className={`flex-1 font-medium ${isActive ? "text-indigo-900 dark:text-indigo-100" : "text-slate-700 dark:text-slate-200"}`}>
                      {a.label}
                    </span>
                    {isActive && (
                      <kbd className="rounded border border-indigo-200/80 bg-white px-1.5 py-0.5 font-mono text-[10px] text-indigo-600 dark:border-indigo-800 dark:bg-slate-800 dark:text-indigo-300">↵</kbd>
                    )}
                  </Link>
                </div>
              );
            })
          )}
        </div>
        <div className="flex items-center gap-4 border-t border-slate-100 px-4 py-2 text-[11px] text-slate-400 dark:border-slate-800/80 dark:text-slate-500">
          <span className="flex items-center gap-1.5">
            <kbd className="rounded border border-slate-200 bg-slate-50 px-1 font-mono text-[10px] dark:border-slate-700 dark:bg-slate-800">↑↓</kbd> navigate
          </span>
          <span className="flex items-center gap-1.5">
            <kbd className="rounded border border-slate-200 bg-slate-50 px-1 font-mono text-[10px] dark:border-slate-700 dark:bg-slate-800">↵</kbd> open
          </span>
          <span className="flex items-center gap-1.5">
            <kbd className="rounded border border-slate-200 bg-slate-50 px-1 font-mono text-[10px] dark:border-slate-700 dark:bg-slate-800">esc</kbd> close
          </span>
        </div>
      </div>
    </div>
  );
}
