"use client";

import { StoreIcon, XIcon } from "@/components/storefront/icons";
import type { StorefrontBrand } from "@/lib/types";

interface BrandHubModalProps {
  open: boolean;
  onClose: () => void;
  brands: StorefrontBrand[];
  onSelectBrand: (brand: StorefrontBrand) => void;
}

export function BrandHubModal({ open, onClose, brands, onSelectBrand }: BrandHubModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
      <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={onClose} />

      <div className="relative z-10 flex max-h-[85vh] w-full max-w-3xl animate-in fade-in zoom-in-95 duration-200 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-6 py-4 dark:border-slate-800 dark:bg-slate-900/80">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400">
              <StoreIcon className="h-4.5 w-4.5" />
            </span>
            <div>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Brand hub</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Pick a brand to browse its catalog
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-200 hover:text-slate-900 active:scale-[0.98] dark:hover:bg-slate-800 dark:hover:text-slate-100"
            aria-label="Close brand hub"
          >
            <XIcon className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {brands.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-10 text-center">
              <StoreIcon className="h-10 w-10 text-slate-300 dark:text-slate-600" />
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">No brands available yet</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {brands.map((brand) => (
                <button
                  key={brand.id}
                  type="button"
                  onClick={() => onSelectBrand(brand)}
                  className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-left transition hover:-translate-y-0.5 hover:border-indigo-300 hover:shadow-lg active:scale-[0.98] dark:border-slate-800 dark:bg-slate-800/60 dark:hover:border-indigo-500/50"
                >
                  {brand.logo_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={brand.logo_url}
                      alt={brand.name}
                      className="h-12 w-12 shrink-0 rounded-full border border-slate-100 object-cover dark:border-slate-700"
                    />
                  ) : (
                    <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-100 to-violet-100 text-base font-bold text-indigo-700 dark:from-indigo-950 dark:to-violet-950 dark:text-indigo-300">
                      {brand.name.charAt(0).toUpperCase()}
                    </span>
                  )}
                  <div className="min-w-0">
                    <h3 className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">{brand.name}</h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {brand.product_count} {brand.product_count === 1 ? "product" : "products"}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}