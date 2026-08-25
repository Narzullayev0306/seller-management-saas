"use client";

import { useStorefront } from "@/lib/storefront-context";
import { formatMoney } from "@/lib/format";
import type { StorefrontProduct } from "@/lib/types";

import {
  BagIcon,
  HeartIcon,
  ImageIcon,
  StarIcon,
} from "@/components/storefront/icons";

interface ProductCardProps {
  product: StorefrontProduct;
  onOpen: (product: StorefrontProduct) => void;
  isCompared: boolean;
  onToggleCompare: (product: StorefrontProduct) => void;
}

const STOCK_BADGES: Record<string, { label: string; className: string }> = {
  low_stock: {
    label: "Low stock",
    className: "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300",
  },
  out_of_stock: {
    label: "Out of stock",
    className: "bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300",
  },
};

export function ProductCard({ product, onOpen, isCompared, onToggleCompare }: ProductCardProps) {
  const { addToCart, isWishlisted, toggleWishlist } = useStorefront();
  const wished = isWishlisted(product.id);
  const badge = STOCK_BADGES[product.stock_status];
  const rating = product.rating !== null ? Number(product.rating) : null;

  return (
    <div
      onClick={() => onOpen(product)}
      className="group flex cursor-pointer flex-col overflow-hidden rounded-2xl border border-slate-200/80 bg-white/90 shadow-xs backdrop-blur-md transition-all duration-200 ease-[cubic-bezier(0.16,1,0.3,1)] hover:-translate-y-1 hover:border-indigo-300 hover:shadow-lg hover:shadow-indigo-500/10 dark:border-white/[0.08] dark:bg-slate-900/80 dark:hover:border-indigo-500/40 dark:hover:shadow-2xl dark:hover:shadow-black/50"
    >
      <div className="relative aspect-square overflow-hidden bg-slate-100 dark:bg-slate-800/80">
        {product.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={product.image_url}
            alt={product.name}
            className="h-full w-full object-cover transition-transform duration-500 ease-out group-hover:scale-108"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-slate-300 dark:text-slate-600">
            <ImageIcon className="h-12 w-12" />
          </div>
        )}

        {badge && (
          <span
            className={`absolute left-3 top-3 rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider backdrop-blur-md ${badge.className}`}
          >
            {badge.label}
          </span>
        )}

        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            toggleWishlist(product);
          }}
          className={`absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full backdrop-blur-md shadow-xs transition duration-150 active:scale-90 ${
            wished
              ? "bg-rose-50/90 text-rose-500 dark:bg-rose-950/80 dark:text-rose-400"
              : "bg-white/80 text-slate-400 hover:text-rose-500 dark:bg-slate-900/80 dark:text-slate-400 dark:hover:text-rose-400"
          }`}
          aria-label={wished ? "Remove from wishlist" : "Add to wishlist"}
        >
          <HeartIcon className={`h-4 w-4 ${wished ? "fill-current" : ""}`} />
        </button>
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4">
        <div className="space-y-1">
          <div className="flex items-center justify-between gap-2">
            {product.brand_name ? (
              <span className="truncate text-[10px] font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                {product.brand_name}
              </span>
            ) : (
              <span />
            )}
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-400">
              {product.category}
            </span>
          </div>
          <h3 className="truncate text-sm font-semibold text-slate-900 transition-colors group-hover:text-indigo-600 dark:text-slate-100 dark:group-hover:text-indigo-400">
            {product.name}
          </h3>
          <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
            <span className="flex items-center gap-0.5">
              {[1, 2, 3, 4, 5].map((i) => (
                <StarIcon
                  key={i}
                  className={`h-3 w-3 ${
                    rating !== null && rating >= i - 0.25
                      ? "fill-amber-400 text-amber-400"
                      : "text-slate-200 dark:text-slate-700"
                  }`}
                />
              ))}
            </span>
            {rating !== null ? (
              <span className="font-semibold text-slate-700 dark:text-slate-300 text-[11px]">
                {rating.toFixed(1)}
                <span className="text-slate-400 dark:text-slate-500 font-normal"> ({product.review_count})</span>
              </span>
            ) : (
              <span className="text-[11px] text-slate-400 dark:text-slate-500">No reviews</span>
            )}
          </div>
        </div>

        <div className="mt-auto flex items-center justify-between gap-2 border-t border-slate-100/80 pt-3 dark:border-slate-800/80">
          <span className="text-base font-extrabold tracking-tight text-slate-900 dark:text-white">
            {formatMoney(product.price)}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onToggleCompare(product);
              }}
              className={`text-[11px] font-semibold transition active:scale-[0.98] ${
                isCompared
                  ? "text-indigo-600 dark:text-indigo-400"
                  : "text-slate-400 hover:text-indigo-600 dark:text-slate-500 dark:hover:text-indigo-400"
              }`}
            >
              {isCompared ? "✓ Compare" : "Compare"}
            </button>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                addToCart(product);
              }}
              disabled={product.stock_status === "out_of_stock"}
              className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white shadow-xs shadow-indigo-600/25 transition hover:bg-indigo-500 active:scale-[0.96] disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400 dark:bg-indigo-600 dark:hover:bg-indigo-500 dark:disabled:bg-slate-800 dark:disabled:text-slate-600"
            >
              <BagIcon className="h-3.5 w-3.5" />
              Add
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}