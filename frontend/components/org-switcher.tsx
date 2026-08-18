"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api-client";
import { setTokens } from "@/lib/api-client";
import { useAuth } from "@/lib/auth";
import type { Membership } from "@/lib/types";

export function OrgSwitcher() {
  const { user } = useAuth();
  const [memberships, setMemberships] = useState<Membership[] | null>(null);
  const [open, setOpen] = useState(false);
  const [switching, setSwitching] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const t = setTimeout(() => {
      api
        .get<Membership[]>("/auth/memberships")
        .then((data) => {
          if (!cancelled) setMemberships(data);
        })
        .catch(() => {
          if (!cancelled) setMemberships([]);
        });
    }, 0);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [user?.organization_id]);

  async function switchOrg(orgId: string) {
    if (orgId === user?.organization_id) {
      setOpen(false);
      return;
    }
    setSwitching(true);
    try {
      const tokens = await api.post<{ access_token: string; refresh_token: string }>(
        "/auth/switch-org",
        { organization_id: orgId },
      );
      setTokens(tokens.access_token, tokens.refresh_token);
      window.location.reload();
    } catch {
      setSwitching(false);
      setOpen(false);
    }
  }

  if (!memberships || memberships.length < 2) return null;

  return (
    <div className="relative px-3">
      <button
        onClick={() => setOpen((o) => !o)}
        disabled={switching}
        className="flex w-full items-center gap-2 rounded-xl px-2 py-1.5 text-left text-sm transition hover:bg-slate-100 disabled:opacity-60 dark:hover:bg-slate-800"
      >
        <svg className="h-4 w-4 shrink-0 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="3" width="7" height="7" rx="1.5" />
          <rect x="3" y="14" width="7" height="7" rx="1.5" />
          <rect x="14" y="14" width="7" height="7" rx="1.5" />
        </svg>
        <span className="truncate text-xs font-medium text-slate-600 dark:text-slate-300">
          {user?.organization_name ?? "Workspace"}
        </span>
        <svg className="ml-auto h-3.5 w-3.5 shrink-0 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute left-0 right-0 z-20 mt-1 origin-top rounded-xl border border-slate-200 bg-white py-1 shadow-xl dark:border-slate-700 dark:bg-slate-900">
            <p className="px-3 pb-1 pt-2 text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              Switch workspace
            </p>
            {memberships.map((m) => {
              const active = m.organization_id === user?.organization_id;
              return (
                <button
                  key={m.organization_id}
                  onClick={() => void switchOrg(m.organization_id)}
                  disabled={switching || !m.is_active}
                  className={`flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm transition disabled:opacity-50 ${
                    active
                      ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300"
                      : "text-slate-700 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800"
                  }`}
                >
                  <span className="truncate">{m.name}</span>
                  {active && <span className="text-[10px] font-semibold uppercase text-indigo-500">Active</span>}
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}