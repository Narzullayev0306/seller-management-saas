import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center px-6 py-16 text-center">
      <p className="text-caption font-semibold uppercase tracking-[0.2em] text-indigo-600 dark:text-indigo-400">404</p>
      <h1 className="mt-3 text-2xl font-bold text-slate-900 dark:text-slate-100">Page not found</h1>
      <p className="mt-2 max-w-md text-small leading-relaxed text-slate-500 dark:text-slate-400">
        The page you are looking for doesn&apos;t exist or may have been moved.
        Check the URL or head back to a known place.
      </p>
      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        <Link
          href="/"
          className="rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-700 active:scale-[0.98] dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
        >
          Back to home
        </Link>
        <Link
          href="/storefront"
          className="rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-medium text-slate-600 transition hover:border-slate-300 hover:text-slate-900 active:scale-[0.98] dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-slate-600 dark:hover:text-white"
        >
          Browse storefront
        </Link>
      </div>
    </div>
  );
}
