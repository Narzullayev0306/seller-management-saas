import type { ReactNode } from "react";

import { Button, Spinner } from "@/components/ui/button";

export function Badge({ className = "", children }: { className?: string; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${className}`}
    >
      {children}
    </span>
  );
}

export function PageLoading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex h-48 animate-fade-in flex-col items-center justify-center gap-3 text-slate-400 dark:text-slate-500">
      <div className="relative">
        <Spinner className="h-6 w-6 text-indigo-500" />
      </div>
      <p className="text-small">{label}…</p>
    </div>
  );
}

export function LoadingSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-5 p-5">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div className="skeleton h-6 w-36 rounded-md" />
        <div className="skeleton h-8 w-24 rounded-lg" />
      </div>
      {/* Table rows */}
      <div className="space-y-2.5">
        {Array.from({ length: rows }).map((_, i) => (
          <div
            key={i}
            className="flex items-center gap-3"
            style={{ opacity: Math.max(1 - i * 0.15, 0.3) }}
          >
            <div className="skeleton h-8 w-8 shrink-0 rounded-lg" />
            <div className="skeleton h-8 flex-1 rounded-lg" style={{ maxWidth: `${88 - i * 7}%` }} />
            <div className="skeleton hidden h-8 w-20 rounded-lg sm:block" />
            <div className="skeleton hidden h-8 w-16 rounded-md md:block" />
          </div>
        ))}
      </div>
    </div>
  );
}

function EmptyIllustration() {
  return (
    <svg viewBox="0 0 160 120" fill="none" aria-hidden className="h-auto w-36">
      {/* Background circle */}
      <circle cx="80" cy="60" r="46" className="fill-slate-100 dark:fill-slate-800/50" />
      {/* Document */}
      <rect x="50" y="30" width="60" height="76" rx="8" className="fill-white stroke-slate-200 dark:fill-slate-800 dark:stroke-slate-700" strokeWidth="1.5" />
      {/* Lines */}
      <rect x="62" y="48" width="36" height="5" rx="2.5" className="fill-slate-200 dark:fill-slate-700" />
      <rect x="62" y="60" width="28" height="5" rx="2.5" className="fill-slate-200 dark:fill-slate-700" />
      <rect x="62" y="72" width="32" height="5" rx="2.5" className="fill-slate-200 dark:fill-slate-700" />
      {/* Badge */}
      <circle cx="112" cy="36" r="16" className="fill-indigo-100 dark:fill-indigo-500/15" />
      <path
        d="M106 36l4 4 8-8"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="stroke-indigo-600 dark:stroke-indigo-400"
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
    <div className="animate-fade-up flex flex-col items-center justify-center gap-5 px-6 py-16 text-center">
      {icon ?? <EmptyIllustration />}
      <div className="max-w-xs">
        <p className="text-h4 text-slate-800 dark:text-slate-100">{title}</p>
        <p className="mt-1.5 text-small leading-relaxed text-slate-500 dark:text-slate-400">
          {description}
        </p>
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
    <div className="animate-fade-up flex flex-col items-center justify-center gap-5 px-6 py-16 text-center">
      <div className="relative">
        <svg viewBox="0 0 80 80" fill="none" aria-hidden className="h-20 w-20">
          <circle cx="40" cy="40" r="36" className="fill-red-50 dark:fill-red-950/40" />
          <circle cx="40" cy="40" r="24" className="fill-red-100 dark:fill-red-900/50" />
          <path
            d="M40 30v12"
            strokeWidth="3"
            strokeLinecap="round"
            className="stroke-red-500 dark:stroke-red-400"
          />
          <circle cx="40" cy="48" r="1.5" className="fill-red-500 dark:fill-red-400" />
        </svg>
      </div>
      <div className="max-w-xs">
        <p className="text-h4 text-slate-800 dark:text-slate-100">{message}</p>
        {detail && detail !== message && (
          <p className="mt-1.5 text-small leading-relaxed text-slate-500 dark:text-slate-400">
            {detail}
          </p>
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
