"use client";

import type { ReactNode } from "react";

import { CheckIcon, ImageIcon, LayersIcon, XIcon } from "@/components/storefront/icons";
import { formatMoney } from "@/lib/format";
import type { StorefrontProduct } from "@/lib/types";

interface ProductComparisonModalProps {
  open: boolean;
  onClose: () => void;
  products: StorefrontProduct[];
  onClearAll: () => void;
}

const STOCK_LABELS: Record<string, string> = {
  in_stock: "In stock",
  low_stock: "Low stock",
  out_of_stock: "Out of stock",
};

export function ProductComparisonModal({
  open,
  onClose,
  products,
  onClearAll,
}: ProductComparisonModalProps) {
  if (!open || products.length === 0) return null;

  const rows: { label: string; render: (p: StorefrontProduct) => ReactNode }[] = [
    {
      label: "Name",
      render: (p) => p.name,
    },
    {
      label: "Brand",
      render: (p) => p.brand_name ?? "—",
    },
    {
      label: "Price",
      render: (p) => formatMoney(p.price),
    },
    {
      label: "Rating",
      render: (p) => (p.rating !== null ? `${Number(p.rating).toFixed(1)} (${p.review_count})` : "No reviews"),
    },
    {
      label: "Stock",
      render: (p) => STOCK_LABELS[p.stock_status] ?? p.stock_status,
    },
    {
      label: "Description",
      render: (p) => (p as Partial<StorefrontProduct> & { description?: string | null }).description ?? "—",
    },
  ];

  const isDifferent = (row: (typeof rows)[number]): boolean => {
    const values = new Set(products.map((p) => String(row.render(p))));
    return values.size > 1;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
      <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={onClose} />

      <div className="relative z-10 flex max-h-[90vh] w-full max-w-5xl animate-in fade-in zoom-in-95 duration-200 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-6 py-4 dark:border-slate-800 dark:bg-slate-900/80">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400">
              <LayersIcon className="h-4.5 w-4.5" />
            </span>
            <div>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Compare products</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {products.length} {products.length === 1 ? "product" : "products"} side-by-side
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClearAll}
              className="rounded-xl px-3 py-2 text-xs font-semibold text-slate-500 transition hover:bg-slate-200 hover:text-slate-900 active:scale-[0.98] dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
            >
              Clear all
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-200 hover:text-slate-900 active:scale-[0.98] dark:hover:bg-slate-800 dark:hover:text-slate-100"
              aria-label="Close comparison"
            >
              <XIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-auto p-6">
          <div className="min-w-[560px]">
            <div className="grid grid-cols-[140px_repeat(auto-fit,minmax(180px,1fr))] gap-3 border-b border-slate-100 pb-4 dark:border-slate-800">
              <div />
              {products.map((p) => (
                <div key={p.id} className="flex flex-col items-center gap-2 text-center">
                  {p.image_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={p.image_url}
                      alt={p.name}
                      className="h-24 w-24 rounded-xl border border-slate-100 object-cover shadow-sm dark:border-slate-700"
                    />
                  ) : (
                    <div className="flex h-24 w-24 items-center justify-center rounded-xl bg-slate-100 text-slate-300 dark:bg-slate-800 dark:text-slate-600">
                      <ImageIcon className="h-8 w-8" />
                    </div>
                  )}
                  <span className="text-xs font-bold text-slate-900 dark:text-slate-100">{p.name}</span>
                  <span className="text-lg font-bold text-indigo-700 dark:text-indigo-400">{formatMoney(p.price)}</span>
                </div>
              ))}
            </div>

            <div className="divide-y divide-slate-100 text-sm dark:divide-slate-800">
              {rows.map((row) => {
                const different = isDifferent(row);
                return (
                  <div
                    key={row.label}
                    className={`grid grid-cols-[140px_repeat(auto-fit,minmax(180px,1fr))] gap-3 py-3.5 ${
                      different ? "bg-indigo-50/50 dark:bg-indigo-950/30" : ""
                    }`}
                  >
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                      {row.label}
                    </span>
                    {products.map((p) => (
                      <span
                        key={p.id}
                        className={`flex items-center gap-1 text-xs leading-relaxed ${
                          different
                            ? "font-semibold text-indigo-800 dark:text-indigo-300"
                            : "text-slate-700 dark:text-slate-300"
                        }`}
                      >
                        {different && <CheckIcon className="h-3 w-3 shrink-0 text-indigo-400" />}
                        {String(row.render(p)) || "—"}
                      </span>
                    ))}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50 px-6 py-4 dark:border-slate-800 dark:bg-slate-900/80">
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Compare up to 4 products. Highlighted rows show differences.
          </span>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white transition hover:bg-slate-800 active:scale-[0.98] dark:bg-slate-700 dark:hover:bg-slate-600"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}