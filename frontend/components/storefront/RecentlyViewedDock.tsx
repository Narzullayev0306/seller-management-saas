"use client";

import { ClockIcon, XIcon } from "@/components/storefront/icons";
import { useStorefront } from "@/lib/storefront-context";
import type { StorefrontProduct } from "@/lib/types";

interface RecentlyViewedDockProps {
  visible: boolean;
  onOpenProduct: (product: StorefrontProduct) => void;
}

export function RecentlyViewedDock({ visible, onOpenProduct }: RecentlyViewedDockProps) {
  const { recentlyViewed, viewedProducts, clearRecentlyViewed } = useStorefront();

  if (!visible || recentlyViewed.length === 0) return null;

  const products = recentlyViewed
    .map((id) => viewedProducts[id])
    .filter((p): p is StorefrontProduct => Boolean(p));

  if (products.length === 0) return null;

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-4 z-30 flex justify-center px-4">
      <div className="pointer-events-auto flex max-w-full animate-in fade-in slide-in-from-bottom-3 duration-300 items-center gap-3 rounded-2xl border border-slate-200 bg-white/95 p-2.5 shadow-xl backdrop-blur dark:border-slate-800 dark:bg-slate-900/95">
        <span className="flex shrink-0 items-center gap-1.5 pl-2 pr-1 text-xs font-bold text-slate-600 dark:text-slate-300">
          <ClockIcon className="h-4 w-4 text-slate-400 dark:text-slate-500" />
          <span className="hidden sm:inline">Recently viewed</span>
        </span>
        <div className="flex items-center gap-2 overflow-x-auto">
          {products.slice(0, 6).map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => onOpenProduct(p)}
              title={p.name}
              className="group h-11 w-11 shrink-0 overflow-hidden rounded-xl border border-slate-200 bg-slate-50 transition hover:border-indigo-400 active:scale-[0.98] dark:border-slate-700 dark:bg-slate-800 dark:hover:border-indigo-500"
            >
              {p.image_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={p.image_url}
                  alt={p.name}
                  className="h-full w-full object-cover transition group-hover:scale-105"
                />
              ) : (
                <span className="flex h-full w-full items-center justify-center text-[10px] font-bold text-slate-400 dark:text-slate-500">
                  {p.name.slice(0, 2).toUpperCase()}
                </span>
              )}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={clearRecentlyViewed}
          className="shrink-0 rounded-full p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 active:scale-[0.98] dark:hover:bg-slate-800 dark:hover:text-slate-200"
          aria-label="Clear recently viewed"
        >
          <XIcon className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}