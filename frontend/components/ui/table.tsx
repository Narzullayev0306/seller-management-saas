import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/button";

interface TableProps<T> {
  columns: { key: string; header: string; className?: string }[];
  rows: T[];
  renderRow: (row: T) => ReactNode[];
  loading?: boolean;
  error?: unknown;
  emptyTitle?: string;
  emptyDescription?: string;
  onRetry?: () => void;
  onSort?: (key: string) => void;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

export function DataTable<T extends { id: string }>({
  columns,
  rows,
  renderRow,
  loading,
  error,
  emptyTitle = "No results found",
  emptyDescription = "Try adjusting your search or filter to find what you're looking for.",
  onRetry,
  onSort,
  sortBy,
  sortOrder,
}: TableProps<T>) {
  if (loading) {
    return (
      <div className="space-y-3 p-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-10 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-500">
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
            />
          </svg>
        </div>
        <p className="text-sm font-semibold text-slate-700">
          {error && typeof error === "object" && "message" in error
            ? String((error as { message: unknown }).message)
            : "Something went wrong"}
        </p>
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry}>
            Try again
          </Button>
        )}
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m8.25 3v6.75m0 0l-3-3m3 3l3-3M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z"
            />
          </svg>
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-700">{emptyTitle}</p>
          <p className="mt-1 text-sm text-slate-500">{emptyDescription}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50/60 dark:border-slate-800 dark:bg-slate-800/40">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-4 py-3 font-medium text-slate-500 dark:text-slate-400 ${col.className ?? ""}`}
              >
                {onSort ? (
                  <button
                    type="button"
                    onClick={() => onSort(col.key)}
                    className="inline-flex items-center gap-1 uppercase tracking-wide hover:text-slate-800"
                  >
                    {col.header}
                    {sortBy === col.key && (
                      <span className="text-indigo-600">{sortOrder === "asc" ? "▲" : "▼"}</span>
                    )}
                  </button>
                ) : (
                  <span className="uppercase tracking-wide">{col.header}</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
          {rows.map((row) => (
            <tr key={row.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
              {renderRow(row).map((cell, i) => (
                <td key={i} className="px-4 py-3 text-slate-700 dark:text-slate-300">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Pagination({
  page,
  pageSize,
  total,
  totalPages,
  onChange,
}: {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
  onChange: (page: number, pageSize: number) => void;
}) {
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-5 py-3 dark:border-slate-800">
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Showing <span className="font-medium text-slate-700 dark:text-slate-200">{from}</span>–
        <span className="font-medium text-slate-700 dark:text-slate-200">{to}</span> of{" "}
        <span className="font-medium text-slate-700 dark:text-slate-200">{total}</span>
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => onChange(page - 1, pageSize)}
        >
          Previous
        </Button>
        <span className="px-2 text-sm text-slate-600 dark:text-slate-400">
          Page {page} of {Math.max(totalPages, 1)}
        </span>
        <Button
          variant="outline"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1, pageSize)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}

export function PageLoader({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex h-48 flex-col items-center justify-center gap-3 text-slate-400">
      <Spinner className="h-6 w-6" />
      <p className="text-sm">{label}...</p>
    </div>
  );
}