"use client";

import type { ReactNode } from "react";

import { Button, Spinner } from "@/components/ui/button";
import { downloadCsv, type CsvValue } from "@/lib/csv";
import { useLocalValue } from "@/lib/local-store";

interface Column {
  key: string;
  header: string;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column[];
  rows: T[];
  renderRow: (row: T) => ReactNode[];
  /** Rendered instead of the table on <md screens. Falls back to horizontal scroll. */
  renderMobileCard?: (row: T) => ReactNode;
  loading?: boolean;
  error?: unknown;
  emptyTitle?: string;
  emptyDescription?: string;
  onRetry?: () => void;
  onSort?: (key: string) => void;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
  /** Extra controls (filters, export buttons…) rendered above the table. */
  toolbar?: ReactNode;
  /** When provided, an Export CSV button appears in the header row. */
  csv?: {
    filename: string;
    headers?: Record<string, string>;
    row: (row: T) => Record<string, CsvValue>;
  };
}

const DENSITY_KEY = "sms_table_density";

type Density = "comfortable" | "compact";

function useDensity(): [Density, (d: Density) => void] {
  const [stored, setValue] = useLocalValue(DENSITY_KEY);
  const density: Density = stored === "compact" ? "compact" : "comfortable";
  const update = (d: Density) => setValue(d);
  return [density, update];
}

function SortIcon({ active, order }: { active: boolean; order?: "asc" | "desc" }) {
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
      className={`h-3 w-3 transition-transform duration-150 ${active ? "text-indigo-600 dark:text-indigo-400" : "text-slate-300 group-hover:text-slate-400 dark:text-slate-600"} ${active && order === "asc" ? "" : ""}`}
    >
      {/* up chevron */}
      <path d="M4.5 9.5 8 6l3.5 3.5" transform={active && order === "desc" ? "rotate(180 8 8)" : undefined} />
    </svg>
  );
}

function SkeletonRows() {
  return (
    <div className="space-y-2.5 p-5">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="skeleton h-10 rounded-lg" style={{ opacity: Math.max(1 - i * 0.13, 0.3) }} />
      ))}
    </div>
  );
}

export function DataTable<T extends { id: string }>({
  columns,
  rows,
  renderRow,
  renderMobileCard,
  loading,
  error,
  emptyTitle = "No results found",
  emptyDescription = "Try adjusting your search or filter to find what you're looking for.",
  onRetry,
  onSort,
  sortBy,
  sortOrder,
  toolbar,
  csv,
}: DataTableProps<T>) {
  const [density, setDensity] = useDensity();
  const cellPad = density === "compact" ? "px-4 py-2" : "px-4 py-3";

  if (loading) return <SkeletonRows />;

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-500 dark:bg-red-950/50 dark:text-red-400">
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
            />
          </svg>
        </div>
        <p className="text-small font-semibold text-slate-700">
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
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500">
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m8.25 3v6.75m0 0l-3-3m3 3l3-3M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z"
            />
          </svg>
        </div>
        <div>
          <p className="text-small font-semibold text-slate-700">{emptyTitle}</p>
          <p className="mt-1 text-small text-slate-500">{emptyDescription}</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {(toolbar || csv || onSort) && (
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 px-4 py-2.5 dark:border-slate-800">
          <div className="flex flex-wrap items-center gap-2">{toolbar}</div>
          <div className="flex items-center gap-2">
            {csv && (
              <Button variant="ghost" size="xs" onClick={() => downloadCsv(csv.filename, rows.map(csv.row), csv.headers)}>
                <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
                </svg>
                CSV
              </Button>
            )}
            <div
              className="flex overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700"
              role="group"
              aria-label="Table density"
            >
              {(["comfortable", "compact"] as Density[]).map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDensity(d)}
                  aria-pressed={density === d}
                  title={d === "comfortable" ? "Comfortable rows" : "Compact rows"}
                  className={`px-2 py-1 text-[11px] font-medium capitalize transition ${
                    density === d
                      ? "bg-slate-100 text-slate-900 dark:bg-slate-700 dark:text-white"
                      : "text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Desktop table first in DOM so text queries resolve to the visible copy
          on md+ screens; the mobile card list is hidden at those breakpoints. */}
      {renderMobileCard ? (
        <>
          <div className="hidden max-h-[calc(100vh-22rem)] overflow-auto md:block">
            <DesktopTable
              columns={columns}
              rows={rows}
              renderRow={renderRow}
              cellPad={cellPad}
              onSort={onSort}
              sortBy={sortBy}
              sortOrder={sortOrder}
            />
          </div>
          <ul className="divide-y divide-slate-100 md:hidden dark:divide-slate-800">
            {rows.map((row) => (
              <li key={row.id} className="animate-fade-up">
                {renderMobileCard(row)}
              </li>
            ))}
          </ul>
        </>
      ) : (
        <div className="max-h-[calc(100vh-22rem)] overflow-auto">
          <DesktopTable
            columns={columns}
            rows={rows}
            renderRow={renderRow}
            cellPad={cellPad}
            onSort={onSort}
            sortBy={sortBy}
            sortOrder={sortOrder}
          />
        </div>
      )}
    </div>
  );
}

function DesktopTable<T extends { id: string }>({
  columns,
  rows,
  renderRow,
  cellPad,
  onSort,
  sortBy,
  sortOrder,
}: {
  columns: Column[];
  rows: T[];
  renderRow: (row: T) => ReactNode[];
  cellPad: string;
  onSort?: (key: string) => void;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}) {
  return (
    <table className="w-full min-w-[640px] text-left text-sm">
      <thead className="sticky top-0 z-10">
        <tr className="border-b border-slate-200/80 bg-slate-50/90 backdrop-blur-md dark:border-white/[0.06] dark:bg-slate-900/80">
          {columns.map((col) => {
            const active = sortBy === col.key;
            return (
              <th
                key={col.key}
                scope="col"
                aria-sort={active ? (sortOrder === "asc" ? "ascending" : "descending") : undefined}
                className={`px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 ${col.className ?? ""}`}
              >
                {onSort ? (
                  <button
                    type="button"
                    onClick={() => onSort(col.key)}
                    className={`group inline-flex items-center gap-1.5 transition-colors hover:text-slate-800 dark:hover:text-slate-100 ${active ? "text-indigo-600 dark:text-indigo-400" : ""}`}
                  >
                    {col.header}
                    <SortIcon active={!!active} order={sortOrder} />
                  </button>
                ) : (
                  <span>{col.header}</span>
                )}
              </th>
            );
          })}
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100/80 dark:divide-slate-800/60">
        {rows.map((row) => (
          <tr
            key={row.id}
            className="group transition-colors duration-[80ms] hover:bg-indigo-50/30 dark:hover:bg-slate-800/60"
          >
            {renderRow(row).map((cell, i) => (
              <td key={i} className={`${cellPad} text-slate-700 dark:text-slate-300`}>
                {cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Compact row card used by DataTable's `renderMobileCard` on small screens. */
export function MobileCard({
  title,
  subtitle,
  children,
  actions,
}: {
  title: string;
  subtitle?: string;
  /** Meta row under the title: price, badges, key numbers. */
  children?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-3 px-4 py-4">
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">{title}</p>
        {subtitle && (
          <p className="mt-0.5 truncate text-xs text-slate-500 dark:text-slate-400">{subtitle}</p>
        )}
        {children && (
          <div className="mt-2.5 flex flex-wrap items-center gap-2">{children}</div>
        )}
      </div>
      {actions && (
        <div className="flex shrink-0 items-center gap-1.5">{actions}</div>
      )}
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
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-5 py-3 dark:border-slate-800/80">
      <p className="text-small tabular-nums text-slate-500 dark:text-slate-400">
        Showing{" "}
        <span className="font-medium text-slate-700 dark:text-slate-200">
          {from}–{to}
        </span>{" "}
        of{" "}
        <span className="font-medium text-slate-700 dark:text-slate-200">{total}</span>
      </p>
      <div className="flex items-center gap-1.5">
        <Button
          variant="outline"
          size="xs"
          disabled={page <= 1}
          onClick={() => onChange(page - 1, pageSize)}
          aria-label="Previous page"
        >
          ← Prev
        </Button>
        <span className="tabular-nums rounded-lg border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-200">
          {page} / {Math.max(totalPages, 1)}
        </span>
        <Button
          variant="outline"
          size="xs"
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1, pageSize)}
          aria-label="Next page"
        >
          Next →
        </Button>
      </div>
    </div>
  );
}

export function PageLoader({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex h-48 flex-col items-center justify-center gap-3 text-slate-400">
      <Spinner className="h-6 w-6" />
      <p className="text-small">{label}...</p>
    </div>
  );
}
