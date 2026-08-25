"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { formatRelative } from "@/lib/format";
import { api } from "@/lib/api-client";
import { useAuth } from "@/lib/auth";
import type { Notification } from "@/lib/types";

interface UnreadCount {
  count: number;
}

const POLL_MS = 30_000;

export function NotificationBell() {
  const { can } = useAuth();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Notification[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  const refresh = useCallback(async () => {
    if (!can("notifications.read")) return;
    try {
      const [page, count] = await Promise.all([
        api.get<{ items: Notification[] }>("/notifications", { page: 1, page_size: 8 }),
        api.get<UnreadCount>("/notifications/unread-count"),
      ]);
      setItems(page.items);
      setUnread(count.count);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load notifications");
    } finally {
      setLoading(false);
    }
  }, [can]);

  useEffect(() => {
    const t = window.setTimeout(() => void refresh(), 0);
    const timer = window.setInterval(() => void refresh(), POLL_MS);
    return () => {
      window.clearTimeout(t);
      window.clearInterval(timer);
    };
  }, [refresh]);

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  async function markRead(n: Notification) {
    if (n.read) return;
    try {
      await api.patch(`/notifications/${n.id}/read`);
      setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, read: true } : x)));
      setUnread((u) => Math.max(0, u - 1));
    } catch {
      // ignore transient errors
    }
  }

  async function markAllRead() {
    try {
      await api.patch<UnreadCount>("/notifications/read-all");
      setItems((prev) => prev.map((x) => ({ ...x, read: true })));
      setUnread(0);
    } catch {
      // ignore transient errors
    }
  }

  if (!can("notifications.read")) return null;

  return (
    <div className="relative" ref={rootRef}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="dialog"
        className="relative rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 active:scale-[0.95] dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
        aria-label="Notifications"
      >
        <svg className="h-4.5 w-4.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {unread > 0 && (
          <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white shadow-xs animate-dot-pulse">
            {unread > 99 ? "99+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Notifications"
          className="absolute right-0 z-30 mt-2 w-80 origin-top-right animate-scale-in overflow-hidden rounded-xl border border-slate-200/80 bg-white shadow-[var(--shadow-overlay)] dark:border-slate-800/80 dark:bg-slate-900 sm:w-96"
        >
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3 dark:border-slate-800/80">
            <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Notifications</p>
            {unread > 0 && (
              <button
                onClick={() => void markAllRead()}
                className="text-xs font-medium text-indigo-600 hover:text-indigo-500 active:scale-95 transition dark:text-indigo-400"
              >
                Mark all read
              </button>
            )}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {loading && items.length === 0 && (
              <div className="space-y-2.5 px-4 py-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="skeleton h-12 rounded-lg" style={{ opacity: Math.max(1 - i * 0.2, 0.4) }} />
                ))}
              </div>
            )}

            {!loading && error && (
              <div className="flex flex-col items-center gap-2 px-4 py-8 text-center">
                <p className="text-sm text-slate-500 dark:text-slate-400">{error}</p>
                <button
                  onClick={() => void refresh()}
                  className="text-xs font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                >
                  Retry
                </button>
              </div>
            )}

            {!loading && !error && items.length === 0 && (
              <div className="px-4 py-10 text-center">
                <p className="text-sm text-slate-500 dark:text-slate-400">You are all caught up</p>
              </div>
            )}

            {items.map((n) => (
              <button
                key={n.id}
                onClick={() => void markRead(n)}
                className={`block w-full border-b border-slate-100/80 px-4 py-3 text-left transition duration-150 last:border-0 hover:bg-slate-50 dark:border-slate-800/60 dark:hover:bg-slate-800/50 ${
                  !n.read ? "bg-indigo-50/40 dark:bg-indigo-950/20" : ""
                }`}
              >
                <div className="flex items-start gap-2.5">
                  <span
                    className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                      n.read ? "bg-slate-200 dark:bg-slate-700" : "bg-indigo-500"
                    }`}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100">{n.title}</p>
                    <p className="mt-0.5 line-clamp-2 text-xs text-slate-500 dark:text-slate-400">{n.message}</p>
                    <p className="mt-1 text-[10px] font-medium uppercase tracking-wider text-slate-400 dark:text-slate-500">
                      {formatRelative(n.created_at)}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}