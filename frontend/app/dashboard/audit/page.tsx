"use client";

import { useState } from "react";

import { PageHeader, Toolbar } from "@/components/page-header";
import { DataTable, Pagination } from "@/components/ui/table";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/input";
import { badgeClass, formatDate } from "@/lib/format";
import { useList } from "@/lib/use-list";
import type { AuditLogEntry } from "@/lib/types";

const ACTION_COLORS: Record<string, string> = {
  "auth.login": "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
  "auth.logout": "bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-800",
  "auth.register": "bg-indigo-100 text-indigo-800 border-indigo-200 dark:bg-indigo-950/40 dark:text-indigo-300 dark:border-indigo-800",
  "auth.password_changed": "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800",
  "user.created": "bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-800",
  "product.created": "bg-sky-100 text-sky-800 border-sky-200 dark:bg-sky-950/40 dark:text-sky-300 dark:border-sky-800",
  "order.created": "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800",
  "order.status_changed": "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800",
  "inventory.adjusted": "bg-cyan-100 text-cyan-800 border-cyan-200 dark:bg-cyan-950/40 dark:text-cyan-300 dark:border-cyan-800",
};

export default function AuditPage() {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const { data, loading, error, query, setFilter, setPage, refetch } = useList<AuditLogEntry>("/audit-logs", {
    pageSize: 15,
    sortBy: "created_at",
    sortOrder: "desc",
  });

  const exportCsv = () => {
    if (!data || data.items.length === 0) return;
    const lines: string[] = ["ID,When,User,Action,Entity,EntityID,Metadata"];
    for (const log of data.items) {
      const metaStr = log.meta ? JSON.stringify(log.meta).replace(/"/g, '""') : "";
      lines.push(
        `"${log.id}","${log.created_at}","${(log.user_name ?? "System").replace(/"/g, '""')}","${log.action}","${log.entity_type ?? ""}","${log.entity_id ?? ""}","${metaStr}"`
      );
    }
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit-logs-page-${data.page}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const columns = [
    { key: "created_at", header: "When" },
    { key: "user_name", header: "User" },
    { key: "action", header: "Action" },
    { key: "entity_type", header: "Entity" },
  ];

  return (
    <div>
      <PageHeader
        title="Audit Log"
        description="Full trail of actions taken across the workspace."
        actions={
          <Button variant="outline" size="sm" onClick={exportCsv} disabled={!data || data.items.length === 0}>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            Export CSV
          </Button>
        }
      />

      <Card>
        <div className="border-b border-slate-100 p-4 dark:border-slate-800">
          <div className="flex flex-wrap gap-3">
            <Select
              value={(query.action as string) ?? ""}
              onChange={(e) => setFilter("action", e.target.value || undefined)}
              className="w-48"
            >
              <option value="">All Actions</option>
              <option value="auth.login">auth.login</option>
              <option value="auth.logout">auth.logout</option>
              <option value="auth.register">auth.register</option>
              <option value="auth.password_changed">auth.password_changed</option>
              <option value="user.created">user.created</option>
              <option value="product.created">product.created</option>
              <option value="order.created">order.created</option>
              <option value="order.status_changed">order.status_changed</option>
              <option value="inventory.adjusted">inventory.adjusted</option>
            </Select>

            <Select
              value={(query.entity_type as string) ?? ""}
              onChange={(e) => setFilter("entity_type", e.target.value || undefined)}
              className="w-44"
            >
              <option value="">All Entities</option>
              <option value="user">User</option>
              <option value="product">Product</option>
              <option value="order">Order</option>
              <option value="inventory">Inventory</option>
              <option value="customer">Customer</option>
              <option value="seller">Seller</option>
            </Select>
          </div>
        </div>
        <DataTable
          columns={columns}
          rows={data?.items ?? []}
          loading={loading}
          error={error}
          onRetry={refetch}
          renderRow={(log) => {
            const expanded = expandedId === log.id;
            const hasMeta = log.meta !== null && Object.keys(log.meta).length > 0;
            const cells = [
              <span key="when" className="text-xs text-slate-500 dark:text-slate-400">{formatDate(log.created_at)}</span>,
              <span key="user" className="font-medium text-slate-900 dark:text-slate-100">{log.user_name ?? "System"}</span>,
              <span
                key="action"
                className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${badgeClass(ACTION_COLORS, log.action)}`}
              >
                {log.action}
              </span>,
              <span key="entity" className="text-slate-600 dark:text-slate-300">
                {log.entity_type ?? "—"}
                {log.entity_id ? <span className="ml-1 font-mono text-xs text-slate-400 dark:text-slate-500">{log.entity_id.slice(0, 8)}</span> : null}
              </span>,
              <button
                key="chevron"
                type="button"
                aria-expanded={expanded}
                aria-label={expanded ? "Hide details" : "Show details"}
                onClick={() => setExpandedId(expanded ? null : log.id)}
                className="inline-flex h-7 w-7 items-center justify-center rounded-lg text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
              >
                <svg
                  className={`h-4 w-4 transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 9l6 6 6-6" />
                </svg>
              </button>,
            ];
            if (expanded) {
              cells.push(
                <tr key="expanded" className="border-t border-slate-100 dark:border-slate-800">
                  <td colSpan={columns.length + 1} className="px-4 py-3">
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-800/50">
                      <div className="grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
                        <div>
                          <p className="font-medium text-slate-500 dark:text-slate-400">Actor</p>
                          <p className="mt-0.5 text-slate-700 dark:text-slate-200">{log.user_name ?? "System"}</p>
                        </div>
                        <div>
                          <p className="font-medium text-slate-500 dark:text-slate-400">Entity</p>
                          <p className="mt-0.5 text-slate-700 dark:text-slate-200">{log.entity_type ?? "—"}</p>
                        </div>
                        <div>
                          <p className="font-medium text-slate-500 dark:text-slate-400">Entity ID</p>
                          <p className="mt-0.5 font-mono text-slate-700 dark:text-slate-200">{log.entity_id ?? "—"}</p>
                        </div>
                        <div>
                          <p className="font-medium text-slate-500 dark:text-slate-400">When</p>
                          <p className="mt-0.5 text-slate-700 dark:text-slate-200">{formatDate(log.created_at)}</p>
                        </div>
                      </div>
                      <p className="mt-3 font-medium text-slate-500 dark:text-slate-400">Metadata</p>
                      {hasMeta ? (
                        <pre className="mt-1.5 overflow-x-auto rounded bg-slate-50 p-3 font-mono text-xs text-slate-700 dark:bg-slate-950/50 dark:text-slate-300">
                          {JSON.stringify(log.meta, null, 2)}
                        </pre>
                      ) : (
                        <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">No metadata</p>
                      )}
                    </div>
                  </td>
                </tr>
              );
            }
            return cells;
          }}
        />
        {data && (
          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            totalPages={data.total_pages}
            onChange={setPage}
          />
        )}
      </Card>
    </div>
  );
}