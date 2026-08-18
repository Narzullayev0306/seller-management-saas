"use client";

import { useState } from "react";

import {
  BagIcon,
  CheckIcon,
  MinusIcon,
  PlusIcon,
  TagIcon,
  TrashIcon,
  TruckIcon,
  XIcon,
} from "@/components/storefront/icons";
import { formatMoney } from "@/lib/format";
import { useStorefront } from "@/lib/storefront-context";

interface CartDrawerProps {
  open: boolean;
  onClose: () => void;
  onCheckout: () => void;
}

export function CartDrawer({ open, onClose, onCheckout }: CartDrawerProps) {
  const {
    cart,
    removeFromCart,
    setQuantity,
    cartCount,
    cartSubtotal,
    cartDiscount,
    freeShippingThreshold,
    shippingCost,
    cartTotal,
    promo,
    applyPromo,
  } = useStorefront();
  const [promoInput, setPromoInput] = useState("");
  const [promoError, setPromoError] = useState("");

  if (!open) return null;

  const afterDiscount = cartSubtotal - cartDiscount;
  const progressPercent = Math.min(100, (afterDiscount / freeShippingThreshold) * 100);
  const remaining = Math.max(0, freeShippingThreshold - afterDiscount);

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault();
    if (!promoInput.trim()) return;
    try {
      applyPromo(promoInput);
      setPromoError("");
      setPromoInput("");
    } catch (err) {
      setPromoError(err instanceof Error ? err.message : "Invalid promo code");
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={onClose} />

      <div className="fixed inset-y-0 right-0 flex max-w-full pl-10">
        <div className="flex w-screen max-w-md animate-in slide-in-from-right duration-300 flex-col bg-white shadow-2xl dark:bg-slate-900 dark:border-l dark:border-slate-800">
          <div className="flex items-center justify-between border-b border-slate-100 p-5 dark:border-slate-800">
            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400">
                <BagIcon className="h-4.5 w-4.5" />
              </span>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                Your cart
                <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                  {cartCount}
                </span>
              </h2>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-100 hover:text-slate-900 active:scale-[0.98] dark:hover:bg-slate-800 dark:hover:text-slate-100"
              aria-label="Close cart"
            >
              <XIcon className="h-5 w-5" />
            </button>
          </div>

          <div className="border-b border-slate-100 bg-slate-50 px-5 py-3.5 dark:border-slate-800 dark:bg-slate-900/80">
            <div className="mb-1.5 flex items-center justify-between text-xs">
              {remaining > 0 ? (
                <span className="font-medium text-slate-600 dark:text-slate-300">
                  Add <span className="font-bold text-indigo-700 dark:text-indigo-400">{formatMoney(remaining)}</span> more for{" "}
                  <span className="font-semibold text-slate-900 dark:text-white">free shipping</span>
                </span>
              ) : (
                <span className="flex items-center gap-1 font-bold text-emerald-700 dark:text-emerald-400">
                  <CheckIcon className="h-3.5 w-3.5" />
                  Free shipping unlocked!
                </span>
              )}
              <span className="font-bold text-slate-500 dark:text-slate-400">{Math.round(progressPercent)}%</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
              <div
                className="h-full rounded-full bg-indigo-600 transition-all duration-300 dark:bg-indigo-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto p-5">
            {cart.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500">
                  <BagIcon className="h-8 w-8" />
                </div>
                <h3 className="font-semibold text-slate-900 dark:text-slate-100">Your cart is empty</h3>
                <p className="max-w-xs text-xs text-slate-500 dark:text-slate-400">
                  Discover something worth owning from our catalog.
                </p>
                <button
                  type="button"
                  onClick={onClose}
                  className="mt-1 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-indigo-700 active:scale-[0.98] dark:bg-indigo-600 dark:hover:bg-indigo-500"
                >
                  Continue shopping
                </button>
              </div>
            ) : (
              cart.map((item) => (
                <div key={item.product.id} className="flex gap-3 rounded-2xl border border-slate-200 p-3 dark:border-slate-800 dark:bg-slate-800/50">
                  {item.product.image_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={item.product.image_url}
                      alt={item.product.name}
                      className="h-16 w-16 shrink-0 rounded-xl border border-slate-100 object-cover dark:border-slate-700"
                    />
                  ) : (
                    <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-300 dark:bg-slate-800 dark:text-slate-600">
                      <BagIcon className="h-6 w-6" />
                    </div>
                  )}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        {item.product.brand_name && (
                          <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                            {item.product.brand_name}
                          </span>
                        )}
                        <h4 className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">{item.product.name}</h4>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeFromCart(item.product.id)}
                        className="shrink-0 rounded-lg p-1.5 text-slate-400 transition hover:bg-red-50 hover:text-red-500 active:scale-[0.98] dark:hover:bg-red-950/50"
                        aria-label={`Remove ${item.product.name}`}
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="mt-2 flex items-center justify-between">
                      <div className="flex items-center overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700">
                        <button
                          type="button"
                          onClick={() => setQuantity(item.product.id, item.quantity - 1)}
                          className="px-2 py-1 text-slate-600 transition hover:bg-slate-100 active:scale-[0.98] dark:text-slate-300 dark:hover:bg-slate-700"
                          aria-label="Decrease quantity"
                        >
                          <MinusIcon className="h-3 w-3" />
                        </button>
                        <span className="min-w-7 text-center text-xs font-bold text-slate-900 dark:text-white">
                          {item.quantity}
                        </span>
                        <button
                          type="button"
                          onClick={() => setQuantity(item.product.id, item.quantity + 1)}
                          className="px-2 py-1 text-slate-600 transition hover:bg-slate-100 active:scale-[0.98] dark:text-slate-300 dark:hover:bg-slate-700"
                          aria-label="Increase quantity"
                        >
                          <PlusIcon className="h-3 w-3" />
                        </button>
                      </div>
                      <span className="text-sm font-semibold text-slate-900 dark:text-white">
                        {formatMoney(item.product.price)}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {cart.length > 0 && (
            <div className="space-y-4 border-t border-slate-100 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900/90">
              <form onSubmit={handleApply} className="space-y-1.5">
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <TagIcon className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
                    <input
                      type="text"
                      value={promoInput}
                      onChange={(e) => setPromoInput(e.target.value)}
                      placeholder="Promo code (try SAVE10)"
                      className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-9 pr-3 text-xs font-medium uppercase text-slate-900 placeholder:normal-case placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500"
                    />
                  </div>
                  <button
                    type="submit"
                    className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white transition hover:bg-slate-800 active:scale-[0.98] dark:bg-slate-700 dark:hover:bg-slate-600"
                  >
                    Apply
                  </button>
                </div>
                {promo && (
                  <p className="flex items-center gap-1 text-[11px] font-medium text-emerald-700 dark:text-emerald-400">
                    <CheckIcon className="h-3 w-3" />
                    {promo} applied — 10% off
                  </p>
                )}
                {promoError && <p className="text-[11px] font-medium text-red-600 dark:text-red-400">{promoError}</p>}
              </form>

              <div className="space-y-1.5 text-sm">
                <div className="flex justify-between text-slate-500 dark:text-slate-400">
                  <span>Subtotal</span>
                  <span className="font-medium text-slate-900 dark:text-slate-100">{formatMoney(cartSubtotal)}</span>
                </div>
                {cartDiscount > 0 && (
                  <div className="flex justify-between text-emerald-700 dark:text-emerald-400">
                    <span>Discount (SAVE10)</span>
                    <span className="font-medium">−{formatMoney(cartDiscount)}</span>
                  </div>
                )}
                <div className="flex justify-between text-slate-500 dark:text-slate-400">
                  <span className="flex items-center gap-1">
                    <TruckIcon className="h-3.5 w-3.5" />
                    Shipping
                  </span>
                  <span className={`font-medium ${shippingCost === 0 ? "text-emerald-700 dark:text-emerald-400" : "text-slate-900 dark:text-slate-100"}`}>
                    {shippingCost === 0 ? "Free" : formatMoney(shippingCost)}
                  </span>
                </div>
                <div className="flex justify-between border-t border-slate-200 pt-2 text-base font-bold text-slate-900 dark:border-slate-800 dark:text-white">
                  <span>Total</span>
                  <span>{formatMoney(cartTotal)}</span>
                </div>
              </div>

              <div className="space-y-2">
                <button
                  type="button"
                  onClick={onCheckout}
                  className="w-full rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 active:scale-[0.98] dark:bg-indigo-600 dark:hover:bg-indigo-500"
                >
                  Checkout • {formatMoney(cartTotal)}
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="w-full rounded-xl py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-100 active:scale-[0.98] dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
                >
                  Continue shopping
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}