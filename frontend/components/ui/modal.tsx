"use client";

import { useEffect, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/button";

const SIZES = {
  sm: "max-w-sm",
  md: "max-w-lg",
  lg: "max-w-2xl",
  xl: "max-w-4xl",
} as const;

export function Modal({
  open,
  title,
  description,
  onClose,
  children,
  footer,
  loading,
  size = "md",
}: {
  open: boolean;
  title: string;
  description?: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  loading?: boolean;
  size?: keyof typeof SIZES;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm animate-fade-in dark:bg-slate-950/70"
        onClick={onClose}
        aria-hidden
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`relative z-10 max-h-[90vh] w-full ${SIZES[size]} animate-scale-in overflow-y-auto rounded-xl border border-slate-200/70 bg-white shadow-[var(--shadow-overlay)] dark:border-slate-800/80 dark:bg-slate-900`}
      >
        <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-4 dark:border-slate-800/80">
          <div>
            <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">{title}</h3>
            {description && <p className="mt-0.5 text-small text-slate-500 dark:text-slate-400">{description}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="-mr-2 -mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-400 transition-colors duration-100 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
            aria-label="Close"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="px-6 py-4">{children}</div>
        {footer && (
          <div className="flex justify-end gap-2 border-t border-slate-100 px-6 py-4 dark:border-slate-800/80">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            {footer}
            {loading && <Spinner className="h-4 w-4 self-center text-indigo-600" />}
          </div>
        )}
      </div>
    </div>
  );
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Confirm",
  variant = "danger",
  loading,
  onConfirm,
  onClose,
}: {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  variant?: "danger" | "primary" | "outline";
  loading?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}) {
  return (
    <Modal
      open={open}
      title={title}
      onClose={onClose}
      size="sm"
      loading={loading}
      footer={
        <Button variant={variant} onClick={onConfirm} disabled={loading}>
          {loading ? "Processing..." : confirmLabel}
        </Button>
      }
    >
      <p className="text-small leading-relaxed text-slate-600 dark:text-slate-300">{description}</p>
    </Modal>
  );
}

const TOAST_VARIANTS = {
  default: null,
  success: (
    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-500 text-white">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" className="h-3 w-3" aria-hidden>
        <path d="M20 6L9 17l-5-5" />
      </svg>
    </span>
  ),
  error: (
    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-500 text-white">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3} strokeLinecap="round" className="h-3 w-3" aria-hidden>
        <path d="M18 6L6 18M6 6l12 12" />
      </svg>
    </span>
  ),
  info: (
    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-indigo-500 text-white">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" className="h-3 w-3" aria-hidden>
        <path d="M12 8h.01M12 12v4" />
        <circle cx="12" cy="12" r="9" strokeWidth={2} />
      </svg>
    </span>
  ),
  warning: (
    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-500 text-white">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" className="h-3 w-3" aria-hidden>
        <path d="M12 8v5m0 3.5h.01M10.3 4.1 2.9 17a2 2 0 0 0 1.7 3h14.8a2 2 0 0 0 1.7-3L13.7 4.1a2 2 0 0 0-3.4 0z" strokeWidth={2} />
      </svg>
    </span>
  ),
} as const;

export function Toast({
  message,
  variant = "default",
}: {
  message: string | null;
  variant?: keyof typeof TOAST_VARIANTS;
}) {
  if (!message) return null;
  return (
    <div
      className="fixed bottom-6 left-1/2 z-[60] -translate-x-1/2 animate-slide-in-bottom"
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center gap-2.5 rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-small font-medium text-white shadow-[var(--shadow-overlay)] dark:bg-slate-100 dark:text-slate-900">
        {TOAST_VARIANTS[variant]}
        <span>{message}</span>
      </div>
    </div>
  );
}
