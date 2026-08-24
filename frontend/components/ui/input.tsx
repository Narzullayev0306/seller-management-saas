import { forwardRef, type InputHTMLAttributes, type SelectHTMLAttributes, type TextareaHTMLAttributes } from "react";

function stateClasses(error?: boolean, success?: boolean): string {
  if (error) {
    return "border-red-400 focus:border-red-500 focus:ring-2 focus:ring-red-500/25 aria-invalid:text-red-600 dark:border-red-500/60 dark:focus:border-red-500";
  }
  if (success) {
    return "border-emerald-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/25 dark:border-emerald-500/60";
  }
  return "border-slate-300 hover:border-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/30 dark:border-slate-700 dark:hover:border-slate-600 dark:focus:border-indigo-500";
}

const base =
  "w-full rounded-xl border bg-white px-3 py-2 text-sm text-slate-900 shadow-xs transition-[border-color,box-shadow] duration-150 placeholder:text-slate-400 focus:outline-none disabled:cursor-not-allowed disabled:bg-slate-50 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500 dark:disabled:bg-slate-800";

export const Input = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement> & { error?: boolean; success?: boolean }
>(function Input({ className = "", error, success, ...props }, ref) {
  return (
    <input
      ref={ref}
      aria-invalid={error || undefined}
      className={`${base} ${stateClasses(error, success)} ${className}`}
      {...props}
    />
  );
});

export const Select = forwardRef<
  HTMLSelectElement,
  SelectHTMLAttributes<HTMLSelectElement> & { error?: boolean; success?: boolean }
>(function Select({ className = "", children, error, success, ...props }, ref) {
  return (
    <select
      ref={ref}
      aria-invalid={error || undefined}
      className={`${base} cursor-pointer appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2216%22%20height%3D%2216%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%2394a3b8%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M6%209l6%206%206-6%22%2F%3E%3C%2Fsvg%3E')] bg-[position:right_0.6rem_center] bg-no-repeat pr-9 ${stateClasses(error, success)} ${className}`}
      {...props}
    >
      {children}
    </select>
  );
});

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement> & { error?: boolean; success?: boolean }
>(function Textarea({ className = "", error, success, rows = 3, ...props }, ref) {
  return (
    <textarea
      ref={ref}
      rows={rows}
      aria-invalid={error || undefined}
      className={`${base} resize-y ${stateClasses(error, success)} ${className}`}
      {...props}
    />
  );
});

export function Field({
  label,
  htmlFor,
  error,
  hint,
  success,
  required,
  children,
}: {
  label: string;
  htmlFor?: string;
  error?: string;
  hint?: string;
  success?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="block text-sm font-medium text-slate-700 dark:text-slate-300">
        {label}
        {required && (
          <span className="ml-0.5 text-red-500" aria-hidden>
            *
          </span>
        )}
      </label>
      {children}
      {hint && !error && !success && <p className="text-xs text-slate-400 dark:text-slate-500">{hint}</p>}
      {success && !error && <p className="text-xs font-medium text-emerald-600">{success}</p>}
      {error && (
        <p className="flex items-center gap-1 text-xs font-medium text-red-600 dark:text-red-400" role="alert">
          <svg className="h-3 w-3 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9.303 3.376c.866 1.5-.217 3.374-1.948 3.374H4.645c-1.73 0-2.813-1.874-1.948-3.374L10.05 3.378c.866-1.5 3.032-1.5 3.898 0l7.355 12.748zM12 15.75h.007v.008H12v-.008z" />
          </svg>
          {error}
        </p>
      )}
    </div>
  );
}
