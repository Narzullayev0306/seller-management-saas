import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "outline" | "ghost" | "danger" | "success";
type Size = "xs" | "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  children: ReactNode;
}

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:
    "bg-indigo-600 text-white shadow-xs shadow-indigo-600/20 hover:bg-indigo-500 hover:shadow-sm hover:shadow-indigo-600/25 active:bg-indigo-700 focus-visible:ring-indigo-500 disabled:bg-indigo-300 dark:disabled:bg-indigo-900",
  secondary:
    "bg-slate-800 text-white hover:bg-slate-700 active:bg-slate-900 focus-visible:ring-slate-500 disabled:bg-slate-400 dark:bg-slate-200 dark:text-slate-900 dark:hover:bg-white dark:disabled:bg-slate-700 dark:disabled:text-slate-400",
  outline:
    "border border-slate-300 bg-white text-slate-700 shadow-xs hover:border-slate-400 hover:bg-slate-50 hover:text-slate-900 active:bg-slate-100 focus-visible:ring-slate-400 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-slate-600 dark:hover:bg-slate-800 dark:hover:text-white",
  ghost:
    "text-slate-600 hover:bg-slate-100 hover:text-slate-900 active:bg-slate-200/70 focus-visible:ring-slate-400 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white",
  danger:
    "bg-red-600 text-white shadow-xs shadow-red-600/20 hover:bg-red-500 hover:shadow-sm hover:shadow-red-600/25 active:bg-red-700 focus-visible:ring-red-500 disabled:bg-red-300",
  success:
    "bg-emerald-600 text-white shadow-xs shadow-emerald-600/20 hover:bg-emerald-500 hover:shadow-sm hover:shadow-emerald-600/25 active:bg-emerald-700 focus-visible:ring-emerald-500 disabled:bg-emerald-300",
};

const SIZE_CLASSES: Record<Size, string> = {
  xs: "h-7 px-2.5 text-xs gap-1 rounded-md",
  sm: "h-8 px-3 text-xs gap-1.5 rounded-lg",
  md: "h-10 px-4 text-sm gap-2 rounded-xl",
  lg: "h-12 px-6 text-base gap-2 rounded-xl",
};

export function Spinner({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  children,
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex select-none items-center justify-center font-medium transition-[background-color,border-color,box-shadow,transform,color] duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-white active:scale-[0.98] disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100 dark:focus-visible:ring-offset-slate-950 ${VARIANT_CLASSES[variant]} ${SIZE_CLASSES[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Spinner />}
      {children}
    </button>
  );
}
