import type { ReactNode } from "react";

import { Button, Spinner } from "@/components/ui/button";

export function Badge({ className = "", children }: { className?: string; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${className}`}
    >
      {children}
    </span>
  );
}

export function PageLoading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex h-48 flex-col items-center justify-center gap-3 text-slate-400 dark:text-slate-500">
      <Spinner className="h-6 w-6" />
      <p className="text-small">{label}...</p>
    </div>
  );
}

export function LoadingSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="p-5">
      {/* Header line */}
      <div className="skeleton mb-4 h-7 w-44 rounded-lg" />
      {/* Table-ish rows */}
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex items-center gap-3" style={{ opacity: 1 - i * 0.12 }}>
            <div className="skeleton h-9 w-9 shrink-0 rounded-lg" />
            <div className="skeleton h-9 flex-1 rounded-lg" style={{ maxWidth: `${90 - i * 8}%` }} />
            <div className="skeleton hidden h-9 w-24 rounded-lg sm:block" />
          </div>
        ))}
      </div>
    </div>
  );
}

function EmptyIllustration() {
  return (
    <svg viewBox="0 0 160 120" fill="none" aria-hidden className="h-auto w-40">
      <rect x="24" y="28" width="112" height="76" rx="10" className="fill-slate-100 dark:fill-slate-800/60" />
      <rect x="38" y="46" width="52" height="7" rx="3.5" className="fill-slate-200 dark:fill-slate-700" />
      <rect x="38" y="60" width="84" height="7" rx="3.5" className="fill-slate-200 dark:fill-slate-700" />
      <rect x="38" y="74" width="66" height="7" rx="3.5" className="fill-slate-200 dark:fill-slate-700" />
      <circle cx="118" cy="34" r="18" className="fill-indigo-100 dark:fill-indigo-500/15" />
      <path
        d="M111 34l5 5 9-10"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="stroke-indigo-500 dark:stroke-indigo-400"
      />
    </svg>
  );
}

export function EmptyState({
  title = "Nothing here yet",
  description = "Get started by creating your first item.",
  icon,
  action,
}: {
  title?: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="animate-fade-up flex flex-col items-center justify-center gap-4 px-6 py-16 text-center">
      {icon ?? <EmptyIllustration />}
      <div>
        <p className="text-base font-semibold text-slate-800 dark:text-slate-100">{title}</p>
        <p className="mx-auto mt-1 max-w-sm text-small leading-relaxed text-slate-500 dark:text-slate-400">{description}</p>
      </div>
      {action}
    </div>
  );
}

export function ErrorState({
  message = "Something went wrong",
  onRetry,
  error,
}: {
  message?: string;
  onRetry?: () => void;
  error?: unknown;
}) {
  const detail =
    error && typeof error === "object" && "message" in error
      ? String((error as { message: unknown }).message)
      : null;
  return (
    <div className="flex flex-col items-center justify-center gap-4 px-6 py-16 text-center">
      <svg viewBox="0 0 160 120" fill="none" aria-hidden className="h-auto w-36">
        <circle cx="80" cy="56" r="42" className="fill-red-50 dark:fill-red-950/30" />
        <circle cx="80" cy="56" r="27" className="fill-red-100 dark:fill-red-900/40" />
        <path
          d="M80 44v14m0 8h.01"
          strokeWidth="4"
          strokeLinecap="round"
          className="stroke-red-500 dark:stroke-red-400"
        />
        <path d="M32 104h96" strokeWidth="3" strokeLinecap="round" className="stroke-red-100 dark:stroke-red-950" />
      </svg>
      <div>
        <p className="text-base font-semibold text-slate-800 dark:text-slate-100">{message}</p>
        {detail && detail !== message && (
          <p className="mx-auto mt-1 max-w-sm text-small leading-relaxed text-slate-500 dark:text-slate-400">{detail}</p>
        )}
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
