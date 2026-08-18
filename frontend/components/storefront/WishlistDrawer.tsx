"use client";

import { BagIcon, HeartIcon, XIcon } from "@/components/storefront/icons";
import { formatMoney } from "@/lib/format";
import { useStorefront } from "@/lib/storefront-context";
import type { StorefrontProduct } from "@/lib/types";

interface WishlistDrawerProps {
  open: boolean;
  onClose: () => void;
  onOpenProduct: (product: StorefrontProduct) => void;
}

export function WishlistDrawer({ open, onClose, onOpenProduct }: WishlistDrawerProps) {
  const { wishlist, toggleWishlist, addToCart } = useStorefront();

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={onClose} />

      <div className="fixed inset-y-0 right-0 flex max-w-full pl-10">
        <div className="flex w-screen max-w-md animate-in slide-in-from-right duration-300 flex-col bg-white shadow-2xl dark:bg-slate-900 dark:border-l dark:border-slate-800">
          <div className="flex items-center justify-between border-b border-slate-100 p-5 dark:border-slate-800">
            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-red-50 text-red-500 dark:bg-red-950/60 dark:text-red-400">
                <HeartIcon className="h-4.5 w-4.5" />
              </span>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                Wishlist
                <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                  {wishlist.length}
                </span>
              </h2>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-100 hover:text-slate-900 active:scale-[0.98] dark:hover:bg-slate-800 dark:hover:text-slate-100"
              aria-label="Close wishlist"
            >
              <XIcon className="h-5 w-5" />
            </button>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto p-5">
            {wishlist.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500">
                  <HeartIcon className="h-8 w-8" />
                </div>
                <h3 className="font-semibold text-slate-900 dark:text-slate-100">Your wishlist is empty</h3>
                <p className="max-w-xs text-xs text-slate-500 dark:text-slate-400">
                  Tap the heart on any product to save it here for later.
                </p>
                <button
                  type="button"
                  onClick={onClose}
                  className="mt-1 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-indigo-700 active:scale-[0.98] dark:bg-indigo-600 dark:hover:bg-indigo-500"
                >
                  Browse products
                </button>
              </div>
            ) : (
              wishlist.map((product) => (
                <div key={product.id} className="flex gap-3 rounded-2xl border border-slate-200 p-3 dark:border-slate-800 dark:bg-slate-800/50">
                  <button type="button" onClick={() => onOpenProduct(product)} className="shrink-0">
                    {product.image_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={product.image_url}
                        alt={product.name}
                        className="h-20 w-20 rounded-xl border border-slate-100 object-cover dark:border-slate-700"
                      />
                    ) : (
                      <div className="flex h-20 w-20 items-center justify-center rounded-xl bg-slate-100 text-slate-300 dark:bg-slate-800 dark:text-slate-600">
                        <BagIcon className="h-6 w-6" />
                      </div>
                    )}
                  </button>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <button type="button" onClick={() => onOpenProduct(product)} className="min-w-0 text-left">
                        {product.brand_name && (
                          <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                            {product.brand_name}
                          </span>
                        )}
                        <h4 className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">{product.name}</h4>
                      </button>
                      <button
                        type="button"
                        onClick={() => toggleWishlist(product)}
                        className="shrink-0 rounded-lg p-1.5 text-red-500 transition hover:bg-red-50 active:scale-[0.98] dark:hover:bg-red-950/50"
                        aria-label={`Remove ${product.name} from wishlist`}
                      >
                        <HeartIcon className="h-4 w-4 fill-current" />
                      </button>
                    </div>
                    <div className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">
                      {formatMoney(product.price)}
                    </div>
                    {product.stock_status === "out_of_stock" && (
                      <span className="mt-0.5 inline-block rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-red-700 dark:bg-red-950/60 dark:text-red-300">
                        Out of stock
                      </span>
                    )}
                    <button
                      type="button"
                      onClick={() => addToCart(product)}
                      disabled={product.stock_status === "out_of_stock"}
                      className="mt-2 flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-indigo-700 active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500 dark:bg-indigo-600 dark:hover:bg-indigo-500 dark:disabled:bg-slate-800 dark:disabled:text-slate-600"
                    >
                      <BagIcon className="h-3.5 w-3.5" />
                      Add to cart
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}