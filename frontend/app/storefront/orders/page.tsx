"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useCustomerAuth, customerRequest } from "@/lib/customer-auth";
import { sfPath } from "@/lib/storefront-slug";
import { formatMoney } from "@/lib/format";
import { ThemeToggle } from "@/components/ui/theme-toggle";

interface OrderItem {
  id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: string | number;
  subtotal: string | number;
}

interface OrderRecord {
  id: string;
  order_number: string;
  status: "pending" | "processing" | "shipped" | "delivered" | "cancelled";
  payment_status: "pending" | "paid" | "failed" | "refunded";
  total: string | number;
  subtotal?: string | number;
  discount?: string | number;
  shipping_fee?: string | number;
  items: OrderItem[];
  created_at: string;
}

const STATUS_STEPS = ["pending", "processing", "shipped", "delivered"] as const;

const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string; stepIndex: number }> = {
  pending: { label: "Pending", bg: "bg-amber-50 dark:bg-amber-950/40", text: "text-amber-700 dark:text-amber-400", stepIndex: 0 },
  processing: { label: "Processing", bg: "bg-blue-50 dark:bg-blue-950/40", text: "text-blue-700 dark:text-blue-400", stepIndex: 1 },
  shipped: { label: "Shipped", bg: "bg-indigo-50 dark:bg-indigo-950/40", text: "text-indigo-700 dark:text-indigo-400", stepIndex: 2 },
  delivered: { label: "Delivered", bg: "bg-emerald-50 dark:bg-emerald-950/40", text: "text-emerald-700 dark:text-emerald-400", stepIndex: 3 },
  cancelled: { label: "Cancelled", bg: "bg-rose-50 dark:bg-rose-950/40", text: "text-rose-700 dark:text-rose-400", stepIndex: -1 },
};

export default function StorefrontOrdersPage() {
  const { customer } = useCustomerAuth();
  const [orders, setOrders] = useState<OrderRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<OrderRecord | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    async function loadOrders() {
      setLoading(true);
      try {
        const localSaved = JSON.parse(localStorage.getItem("sms_storefront_orders") || "[]");
        if (customer) {
          try {
            const path = await sfPath("/auth/orders");
            const res = await customerRequest<OrderRecord[]>(path);
            if (Array.isArray(res)) {
              const combined = [...res];
              // Merge any local orders not yet on server
              localSaved.forEach((lo: OrderRecord) => {
                if (!combined.some((co) => co.id === lo.id || co.order_number === lo.order_number)) {
                  combined.push(lo);
                }
              });
              setOrders(combined);
              if (combined.length > 0) setSelectedOrder(combined[0]);
              setLoading(false);
              return;
            }
          } catch {
            // fallback to local
          }
        }
        setOrders(localSaved);
        if (localSaved.length > 0) setSelectedOrder(localSaved[0]);
      } catch {
        setOrders([]);
      } finally {
        setLoading(false);
      }
    }
    void loadOrders();
  }, [customer]);

  const filteredOrders = orders.filter((o) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      o.order_number.toLowerCase().includes(q) ||
      o.items?.some((i) => i.product_name.toLowerCase().includes(q))
    );
  });

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 selection:bg-indigo-500 selection:text-white dark:bg-slate-950 dark:text-slate-100">
      {/* Sticky Header */}
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-900/95">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4">
            <Link
              href="/storefront"
              className="flex items-center gap-2 text-sm font-semibold text-slate-600 transition hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
              Back to store
            </Link>
            <div className="h-4 w-px bg-slate-200 dark:bg-slate-800" />
            <h1 className="text-base font-bold text-slate-900 dark:text-white sm:text-lg">
              My Orders & Tracking
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link
              href="/storefront"
              className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-indigo-500"
            >
              Continue Shopping
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {loading ? (
          <div className="flex min-h-[400px] flex-col items-center justify-center gap-3">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
            <p className="text-sm text-slate-500 dark:text-slate-400">Loading your orders…</p>
          </div>
        ) : orders.length === 0 ? (
          <div className="flex min-h-[450px] flex-col items-center justify-center rounded-3xl border border-dashed border-slate-200 bg-white p-8 text-center dark:border-slate-800 dark:bg-slate-900">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400">
              <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
              </svg>
            </div>
            <h3 className="mt-4 text-lg font-bold text-slate-900 dark:text-white">No orders found</h3>
            <p className="mt-1 max-w-sm text-sm text-slate-500 dark:text-slate-400">
              You haven&apos;t placed any orders yet. Discover our latest curated items and make your first order!
            </p>
            <Link
              href="/storefront"
              className="mt-6 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 active:scale-[0.98]"
            >
              Start shopping
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            {/* Orders List Sidebar */}
            <div className="lg:col-span-5 space-y-3">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search by order # or product…"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-4 pr-10 text-sm text-slate-900 placeholder:text-slate-400 transition focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100"
                />
              </div>

              <div className="space-y-3">
                {filteredOrders.map((ord) => {
                  const cfg = STATUS_CONFIG[ord.status] || STATUS_CONFIG.pending;
                  const isSelected = selectedOrder?.id === ord.id;
                  return (
                    <button
                      key={ord.id}
                      type="button"
                      onClick={() => setSelectedOrder(ord)}
                      className={`w-full rounded-2xl border p-4 text-left transition-all ${
                        isSelected
                          ? "border-indigo-600 bg-indigo-50/50 shadow-md ring-2 ring-indigo-600/20 dark:border-indigo-500 dark:bg-indigo-950/40"
                          : "border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-900 dark:text-white">
                          #{ord.order_number}
                        </span>
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${cfg.bg} ${cfg.text}`}>
                          {cfg.label}
                        </span>
                      </div>

                      <div className="mt-2 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                        <span>{new Date(ord.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</span>
                        <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
                          {formatMoney(ord.total)}
                        </span>
                      </div>

                      <div className="mt-2 text-xs text-slate-600 dark:text-slate-300 line-clamp-1">
                        {ord.items?.map((i) => `${i.quantity}x ${i.product_name}`).join(", ") || "No item details"}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Selected Order Detailed View */}
            <div className="lg:col-span-7">
              {selectedOrder ? (
                <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-8">
                  {/* Order Header */}
                  <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 pb-6 dark:border-slate-800">
                    <div>
                      <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                        Order Details
                      </span>
                      <h2 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
                        #{selectedOrder.order_number}
                      </h2>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        Placed on {new Date(selectedOrder.created_at).toLocaleString("en-US", { dateStyle: "long", timeStyle: "short" })}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => window.print()}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M6.72 13.829c-.24-1.076-.672-2.13-1.28-3.093m0 0C4.38 9.176 3.6 7.425 3.6 5.4c0-2.43 1.97-4.4 4.4-4.4 1.84 0 3.42 1.13 4.08 2.74a4.402 4.402 0 014.08-2.74c2.43 0 4.4 1.97 4.4 4.4 0 2.025-.78 3.776-1.84 5.336m-7.04-4.24v12m0 0l-3-3m3 3l3-3" />
                        </svg>
                        Print Invoice
                      </button>
                    </div>
                  </div>

                  {/* Order Live Status Tracking Stepper */}
                  <div className="py-6 border-b border-slate-100 dark:border-slate-800">
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4">
                      Shipment Status Timeline
                    </h3>

                    {selectedOrder.status === "cancelled" ? (
                      <div className="rounded-2xl bg-rose-50 p-4 text-center text-sm font-semibold text-rose-700 dark:bg-rose-950/50 dark:text-rose-300">
                        This order was cancelled.
                      </div>
                    ) : (
                      <div className="grid grid-cols-4 gap-2 text-center">
                        {STATUS_STEPS.map((step, idx) => {
                          const currentIdx = STATUS_CONFIG[selectedOrder.status]?.stepIndex ?? 0;
                          const isPassed = idx <= currentIdx;
                          return (
                            <div key={step} className="flex flex-col items-center">
                              <div
                                className={`flex h-9 w-9 items-center justify-center rounded-full text-xs font-bold transition-all ${
                                  isPassed
                                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                                    : "bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500"
                                }`}
                              >
                                {isPassed ? "✓" : idx + 1}
                              </div>
                              <span className="mt-2 text-xs font-semibold capitalize text-slate-700 dark:text-slate-300">
                                {step}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Items list */}
                  <div className="py-6 border-b border-slate-100 dark:border-slate-800 space-y-4">
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                      Purchased Items ({selectedOrder.items?.length || 0})
                    </h3>
                    <div className="divide-y divide-slate-100 dark:divide-slate-800">
                      {selectedOrder.items?.map((item) => (
                        <div key={item.id} className="flex items-center justify-between py-3">
                          <div className="flex items-center gap-3">
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-xs font-bold text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                              {item.product_name.slice(0, 2).toUpperCase()}
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-slate-900 dark:text-white">
                                {item.product_name}
                              </p>
                              <p className="text-xs text-slate-500 dark:text-slate-400">
                                {item.quantity} x {formatMoney(item.unit_price)}
                              </p>
                            </div>
                          </div>
                          <span className="text-sm font-bold text-slate-900 dark:text-white">
                            {formatMoney(item.subtotal)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Total Breakdown */}
                  <div className="pt-6 space-y-2 text-sm">
                    <div className="flex justify-between text-slate-500 dark:text-slate-400">
                      <span>Subtotal</span>
                      <span>{formatMoney(selectedOrder.subtotal || selectedOrder.total)}</span>
                    </div>
                    {Number(selectedOrder.discount || 0) > 0 && (
                      <div className="flex justify-between text-emerald-600 dark:text-emerald-400">
                        <span>Discount</span>
                        <span>-{formatMoney(selectedOrder.discount || 0)}</span>
                      </div>
                    )}
                    <div className="flex justify-between text-slate-500 dark:text-slate-400">
                      <span>Shipping</span>
                      <span>{Number(selectedOrder.shipping_fee || 0) > 0 ? formatMoney(selectedOrder.shipping_fee || 0) : "Free"}</span>
                    </div>
                    <div className="flex justify-between border-t border-slate-100 pt-3 text-base font-black text-slate-900 dark:border-slate-800 dark:text-white">
                      <span>Total Paid</span>
                      <span>{formatMoney(selectedOrder.total)}</span>
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
