"use client";

import { useState } from "react";

import { BagIcon, CheckIcon, LockIcon, XIcon } from "@/components/storefront/icons";
import { api } from "@/lib/api-client";
import { cartHeaders } from "@/lib/customer-auth";
import { formatMoney } from "@/lib/format";
import { useStorefront } from "@/lib/storefront-context";
import { sfPath } from "@/lib/storefront-slug";
import type { StorefrontCheckoutResult } from "@/lib/types";

interface CheckoutModalProps {
  open: boolean;
  onClose: () => void;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const FIELD_CLASS =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-indigo-500";
const LABEL_CLASS = "mb-1 block text-xs font-medium text-slate-600 dark:text-slate-300";

export function CheckoutModal({ open, onClose }: CheckoutModalProps) {
  const { cart, cartTotal, cartDiscount, clearCart } = useStorefront();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    address: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [result, setResult] = useState<StorefrontCheckoutResult | null>(null);

  if (!open) return null;

  const validate = (): boolean => {
    const next: Record<string, string> = {};
    if (form.first_name.trim().length < 2) next.first_name = "First name must be at least 2 characters";
    if (form.last_name.trim().length < 2) next.last_name = "Last name must be at least 2 characters";
    if (!EMAIL_RE.test(form.email.trim())) next.email = "Enter a valid email address";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const setField = (key: keyof typeof form, value: string) => {
    setForm((f) => ({ ...f, [key]: value }));
    setErrors((e) => ({ ...e, [key]: "" }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError("");
    if (!validate()) return;
    setLoading(true);
    try {
      const payload: Record<string, unknown> = {
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim() || undefined,
        address: form.address.trim() || undefined,
        discount: cartDiscount > 0 ? cartDiscount : undefined,
        items: cart.map((i) => ({ product_id: i.product.id, quantity: i.quantity })),
      };
      const key =
        window.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      const path = await sfPath("/checkout");
      const res = await api.post<StorefrontCheckoutResult>(
        path,
        payload,
        { "Idempotency-Key": key, ...cartHeaders() },
      );
      setResult(res);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Checkout failed — please try again");
    } finally {
      setLoading(false);
    }
  };

  const handleContinue = () => {
    clearCart();
    setResult(null);
    setForm({ first_name: "", last_name: "", email: "", phone: "", address: "" });
    setErrors({});
    onClose();
  };

  const itemCount = cart.reduce((sum, i) => sum + i.quantity, 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto p-4 sm:p-6">
      <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={result ? handleContinue : onClose} />

      <div className="relative z-10 my-auto w-full max-w-lg animate-in fade-in zoom-in-95 duration-200 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-6 py-4 dark:border-slate-800 dark:bg-slate-900/80">
          <div className="flex items-center gap-2">
            <LockIcon className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            <h2 className="font-semibold text-slate-900 dark:text-slate-100">
              {result ? "Order confirmed" : "Checkout"}
            </h2>
          </div>
          <button
            type="button"
            onClick={result ? handleContinue : onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-200 hover:text-slate-900 active:scale-[0.98] dark:hover:bg-slate-800 dark:hover:text-slate-100"
            aria-label="Close checkout"
          >
            <XIcon className="h-5 w-5" />
          </button>
        </div>

        <div className="max-h-[80vh] overflow-y-auto p-6">
          {result ? (
            <div className="flex flex-col items-center gap-4 py-6 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400">
                <CheckIcon className="h-9 w-9" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white">Order confirmed!</h3>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                  Order number:{" "}
                  <span className="font-mono font-bold text-slate-900 dark:text-indigo-400">{result.order_number}</span>
                </p>
              </div>
              <div className="w-full space-y-2 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-800 dark:bg-slate-800/50">
                <div className="flex justify-between text-slate-500 dark:text-slate-400">
                  <span>Items</span>
                  <span className="font-medium text-slate-900 dark:text-slate-200">{result.items_count}</span>
                </div>
                <div className="flex justify-between border-t border-slate-200 pt-2 dark:border-slate-700">
                  <span className="font-semibold text-slate-800 dark:text-slate-200">Total</span>
                  <span className="font-bold text-emerald-700 dark:text-emerald-400">{formatMoney(result.total)}</span>
                </div>
              </div>
              <button
                type="button"
                onClick={handleContinue}
                className="mt-1 w-full rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 active:scale-[0.98] dark:bg-indigo-600 dark:hover:bg-indigo-500"
              >
                Continue shopping
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-800 dark:bg-slate-800/50">
                <div className="flex items-center gap-2 text-sm">
                  <BagIcon className="h-4 w-4 text-slate-500 dark:text-slate-400" />
                  <span className="text-slate-600 dark:text-slate-300">{itemCount} {itemCount === 1 ? "item" : "items"}</span>
                </div>
                <span className="text-base font-bold text-slate-900 dark:text-white">{formatMoney(cartTotal)}</span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={LABEL_CLASS} htmlFor="co-first">First name</label>
                  <input
                    id="co-first"
                    type="text"
                    value={form.first_name}
                    onChange={(e) => setField("first_name", e.target.value)}
                    placeholder="Jane"
                    className={FIELD_CLASS}
                  />
                  {errors.first_name && <p className="mt-1 text-[11px] text-red-600 dark:text-red-400">{errors.first_name}</p>}
                </div>
                <div>
                  <label className={LABEL_CLASS} htmlFor="co-last">Last name</label>
                  <input
                    id="co-last"
                    type="text"
                    value={form.last_name}
                    onChange={(e) => setField("last_name", e.target.value)}
                    placeholder="Doe"
                    className={FIELD_CLASS}
                  />
                  {errors.last_name && <p className="mt-1 text-[11px] text-red-600 dark:text-red-400">{errors.last_name}</p>}
                </div>
              </div>

              <div>
                <label className={LABEL_CLASS} htmlFor="co-email">Email</label>
                <input
                  id="co-email"
                  type="email"
                  value={form.email}
                  onChange={(e) => setField("email", e.target.value)}
                  placeholder="jane@example.com"
                  className={FIELD_CLASS}
                />
                {errors.email && <p className="mt-1 text-[11px] text-red-600 dark:text-red-400">{errors.email}</p>}
              </div>

              <div>
                <label className={LABEL_CLASS} htmlFor="co-phone">Phone (optional)</label>
                <input
                  id="co-phone"
                  type="tel"
                  value={form.phone}
                  onChange={(e) => setField("phone", e.target.value)}
                  placeholder="+1 555 000 0000"
                  className={FIELD_CLASS}
                />
              </div>

              <div>
                <label className={LABEL_CLASS} htmlFor="co-address">Address (optional)</label>
                <input
                  id="co-address"
                  type="text"
                  value={form.address}
                  onChange={(e) => setField("address", e.target.value)}
                  placeholder="123 Market St"
                  className={FIELD_CLASS}
                />
              </div>

              {submitError && (
                <p className="rounded-xl bg-red-50 px-3 py-2.5 text-xs font-medium text-red-700 dark:bg-red-950/50 dark:text-red-400">
                  {submitError}
                </p>
              )}

              <button
                type="submit"
                disabled={loading || cart.length === 0}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500 dark:bg-indigo-600 dark:hover:bg-indigo-500 dark:disabled:bg-slate-800 dark:disabled:text-slate-600"
              >
                {loading ? (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                ) : (
                  <>
                    <LockIcon className="h-4 w-4" />
                    Place order • {formatMoney(cartTotal)}
                  </>
                )}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}