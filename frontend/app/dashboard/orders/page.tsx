"use client";

import { useCallback, useState } from "react";

import { Badge } from "@/components/ui/states";
import { PageHeader } from "@/components/page-header";
import { Toolbar } from "@/components/page-header";
import { DataTable, MobileCard } from "@/components/ui/table";
import { Pagination } from "@/components/ui/table";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Field, Input, Select } from "@/components/ui/input";
import { Modal, Toast } from "@/components/ui/modal";
import { useAuth } from "@/lib/auth";
import { useList } from "@/lib/use-list";
import { api } from "@/lib/api-client";
import { badgeClass, formatDate, formatMoney, ORDER_STATUS_COLORS, PAYMENT_STATUS_COLORS } from "@/lib/format";
import type { Order, OrderCreate, OrderHistoryEntry, OrderStatus, PaymentStatus, Product } from "@/lib/types";

const STATUSES: OrderStatus[] = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"];
const PAYMENT_STATUSES: PaymentStatus[] = ["pending", "paid", "partially_paid", "refunded"];

interface NewOrderState {
  customer_id: string;
  seller_id: string;
  discount: string;
  tax: string;
  shipping_fee: string;
  payment_status: PaymentStatus;
  items: { product_id: string; quantity: string }[];
}

const EMPTY_ORDER: NewOrderState = {
  customer_id: "",
  seller_id: "",
  discount: "0",
  tax: "0",
  shipping_fee: "0",
  payment_status: "pending",
  items: [{ product_id: "", quantity: "1" }],
};

function printInvoice(order: Order, orgName: string) {
  const win = window.open("", "_blank", "width=800,height=900");
  if (!win) return;
  const rows = order.items
    .map(
      (item) => `<tr>
          <td>${item.product_name}</td>
          <td class="num">${item.quantity}</td>
          <td class="num">${formatMoney(item.unit_price)}</td>
          <td class="num">${formatMoney(item.subtotal)}</td>
        </tr>`,
    )
    .join("");
  win.document.write(`<!DOCTYPE html><html><head><title>Invoice ${order.order_number}</title><style>
    * { box-sizing: border-box; }
    body { margin: 32px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; color: #0f172a; background: #fff; }
    .sheet { max-width: 640px; margin: 0 auto; }
    h1 { font-size: 22px; letter-spacing: 3px; margin: 0 0 2px; }
    .org { font-size: 13px; margin: 0 0 24px; color: #334155; }
    .meta { display: flex; justify-content: space-between; margin-bottom: 24px; color: #334155; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
    th { text-align: left; padding: 6px 8px; border-bottom: 2px solid #0f172a; }
    td { padding: 6px 8px; border-bottom: 1px solid #cbd5e1; }
    .num { text-align: right; }
    .totals { margin-left: auto; width: 260px; }
    .totals .row { display: flex; justify-content: space-between; padding: 3px 0; }
    .totals .total { border-top: 2px solid #0f172a; margin-top: 4px; padding-top: 6px; font-weight: 700; font-size: 14px; }
    .footer { margin-top: 32px; color: #64748b; }
    @media print { body { margin: 0; } }
  </style></head><body>
    <div class="sheet">
      <h1>INVOICE</h1>
      <p class="org">${orgName}</p>
      <div class="meta">
        <div>
          <div><strong>Order:</strong> ${order.order_number}</div>
          <div><strong>Date:</strong> ${formatDate(order.created_at)}</div>
        </div>
        <div>
          <div><strong>Customer:</strong> ${order.customer_name}</div>
          <div><strong>Seller:</strong> ${order.seller_name ?? "—"}</div>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Product</th>
            <th class="num">Qty</th>
            <th class="num">Price</th>
            <th class="num">Subtotal</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
      <div class="totals">
        <div class="row"><span>Subtotal</span><span>${formatMoney(order.subtotal)}</span></div>
        <div class="row"><span>Discount</span><span>-${formatMoney(order.discount)}</span></div>
        <div class="row"><span>Tax</span><span>${formatMoney(order.tax)}</span></div>
        <div class="row"><span>Shipping</span><span>${formatMoney(order.shipping_fee)}</span></div>
        <div class="row total"><span>Total</span><span>${formatMoney(order.total)}</span></div>
      </div>
      <p class="footer">Generated on ${formatDate(new Date().toISOString())}</p>
    </div>
  </body></html>`);
  win.document.close();
  win.focus();
  win.print();
}

export default function OrdersPage() {
  const { can, user } = useAuth();
  const { data, loading, error, query, setSearch, setPage, setFilter, toggleSort, refetch } =
    useList<Order>("/orders", { sortBy: "created_at", sortOrder: "desc" });

  const [search, setSearchInput] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [detail, setDetail] = useState<Order | null>(null);
  const [history, setHistory] = useState<OrderHistoryEntry[] | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [form, setForm] = useState<NewOrderState>(EMPTY_ORDER);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 3000);
  }, []);

  const customers = useList<{ id: string; first_name: string; last_name: string }>("/customers", { pageSize: 100 });
  const sellers = useList<{ id: string; first_name: string; last_name: string }>("/sellers", { pageSize: 100 });
  const products = useList<Product>("/products", { pageSize: 100 });

  const openCreate = () => {
    setForm(EMPTY_ORDER);
    setFormErrors({});
    setCreateOpen(true);
  };

  const openDetail = (o: Order) => {
    setDetail(o);
    setHistory(null);
    setHistoryError(null);
    void api
      .get<OrderHistoryEntry[]>(`/orders/${o.id}/history`)
      .then(setHistory)
      .catch((err) => setHistoryError(err instanceof Error ? err.message : "Failed to load history"));
  };

  function validate(): boolean {
    const next: Record<string, string> = {};
    if (!form.customer_id) next.customer_id = "Select a customer";
    if (form.items.length === 0) next.items = "Add at least one item";
    form.items.forEach((item, i) => {
      if (!item.product_id) next[`item-${i}-product`] = "Select a product";
      if (!item.quantity || parseInt(item.quantity, 10) < 1) next[`item-${i}-qty`] = "Quantity must be ≥ 1";
    });
    if (form.discount && (parseFloat(form.discount) < 0)) next.discount = "Discount cannot be negative";
    setFormErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleCreate() {
    if (!validate()) return;
    setSaving(true);
    try {
      await api.post<Order>("/orders", {
        customer_id: form.customer_id,
        seller_id: form.seller_id || null,
        discount: parseFloat(form.discount) || 0,
        tax: parseFloat(form.tax) || 0,
        shipping_fee: parseFloat(form.shipping_fee) || 0,
        payment_status: form.payment_status,
        items: form.items
          .filter((i) => i.product_id)
          .map((i) => ({ product_id: i.product_id, quantity: parseInt(i.quantity, 10) })),
      } satisfies OrderCreate);
      showToast("Order created");
      setCreateOpen(false);
      refetch();
    } catch (err) {
      setFormErrors({ form: err instanceof Error ? err.message : "Failed to create order" });
    } finally {
      setSaving(false);
    }
  }

  async function updateStatus(order: Order, status: OrderStatus) {
    setUpdatingId(order.id);
    try {
      await api.patch(`/orders/${order.id}`, { status });
      showToast(`Order marked ${status}`);
      refetch();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to update order");
    } finally {
      setUpdatingId(null);
    }
  }

  async function updatePayment(order: Order, paymentStatus: PaymentStatus) {
    setUpdatingId(order.id);
    try {
      await api.patch(`/orders/${order.id}/payment`, { payment_status: paymentStatus });
      showToast(`Payment marked ${paymentStatus.replace("_", " ")}`);
      refetch();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to update payment");
    } finally {
      setUpdatingId(null);
    }
  }

  const nextStatuses = (order: Order): OrderStatus[] => {
    if (order.status === "cancelled" || order.status === "delivered") return [];
    if (order.status === "pending") return ["confirmed", "processing", "cancelled"];
    if (order.status === "confirmed") return ["processing", "cancelled"];
    if (order.status === "processing") return ["shipped", "cancelled"];
    return ["delivered", "cancelled"];
  };

  const columns = [
    { key: "order_number", header: "Order" },
    { key: "customer_name", header: "Customer" },
    { key: "total", header: "Total" },
    { key: "status", header: "Status" },
    { key: "payment_status", header: "Payment" },
    { key: "created_at", header: "Created" },
    { key: "actions", header: "" },
  ];

  return (
    <div>
      <PageHeader
        title="Orders"
        description="Track orders from creation to delivery."
        actions={
          can("orders.create") && (
            <Button onClick={openCreate}>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              New order
            </Button>
          )
        }
      />

      <Card>
        <Toolbar
          search={search}
          onSearch={(v) => {
            setSearchInput(v);
            const t = window.setTimeout(() => setSearch(v), 350);
            return () => window.clearTimeout(t);
          }}
          placeholder="Search order number or customer..."
          filters={
            <div className="flex items-center gap-2">
              <Select value={(query.status as string) ?? ""} onChange={(e) => setFilter("status", e.target.value || undefined)} className="w-40">
                <option value="">All statuses</option>
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </Select>
              <Select value={(query.payment_status as string) ?? ""} onChange={(e) => setFilter("payment_status", e.target.value || undefined)} className="w-40">
                <option value="">All payments</option>
                {PAYMENT_STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s.replace("_", " ")}
                  </option>
                ))}
              </Select>
            </div>
          }
        />

        <DataTable
          columns={columns}
          rows={data?.items ?? []}
          loading={loading}
          error={error}
          onRetry={refetch}
          onSort={toggleSort}
          sortBy={query.sort_by as string}
          sortOrder={query.sort_order as "asc" | "desc"}
          renderMobileCard={(o) => (
            <MobileCard
              title={o.customer_name}
              subtitle={`${o.order_number} · ${formatDate(o.created_at)}${o.seller_name ? ` · Seller: ${o.seller_name}` : ""}`}
              actions={
                <>
                  <Button variant="ghost" size="sm" onClick={() => openDetail(o)}>
                    View
                  </Button>
                  {can("orders.update") &&
                    nextStatuses(o).length > 0 && (
                      <Select
                        value=""
                        onChange={(e) => {
                          if (e.target.value) void updateStatus(o, e.target.value as OrderStatus);
                        }}
                        aria-label={`Change status for ${o.order_number}`}
                        className="h-8 w-auto rounded-lg border border-slate-200 px-2 py-0 text-xs dark:border-slate-800"
                      >
                        <option value="" disabled>
                          {updatingId === o.id ? "Updating..." : "Change"}
                        </option>
                        {nextStatuses(o).map((s) => (
                          <option key={s} value={s}>
                            Mark {s}
                          </option>
                        ))}
                      </Select>
                    )}
                </>
              }
            >
              <span className="text-sm font-semibold tabular-nums">{formatMoney(o.total)}</span>
              <Badge className={badgeClass(ORDER_STATUS_COLORS, o.status)}>{o.status}</Badge>
              <Badge className={badgeClass(PAYMENT_STATUS_COLORS, o.payment_status)}>
                {o.payment_status.replace("_", " ")}
              </Badge>
            </MobileCard>
          )}
          renderRow={(o) => [
            <div key="num" className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-50 dark:bg-indigo-950/60">
                <svg className="h-4 w-4 text-indigo-500 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
                </svg>
              </div>
              <div>
                <button type="button" className="font-mono text-xs font-bold text-indigo-600 hover:underline dark:text-indigo-400" onClick={() => openDetail(o)}>
                  {o.order_number}
                </button>
                <p className="text-[11px] text-slate-400 dark:text-slate-500">{o.items.reduce((acc, i) => acc + i.quantity, 0)} items</p>
              </div>
            </div>,
            <div key="cust" className="flex items-center gap-2">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-xs font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                {o.customer_name ? o.customer_name.slice(0, 1).toUpperCase() : "?"}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-900 dark:text-slate-100 truncate">{o.customer_name}</p>
                {o.seller_name && <p className="text-[11px] text-slate-400 dark:text-slate-500 truncate">via {o.seller_name}</p>}
              </div>
            </div>,
            <span key="total" className="text-sm font-bold tabular-nums text-slate-900 dark:text-slate-100">{formatMoney(o.total)}</span>,
            <Badge key="status" className={badgeClass(ORDER_STATUS_COLORS, o.status)}>{o.status}</Badge>,
            <Badge key="payment" className={badgeClass(PAYMENT_STATUS_COLORS, o.payment_status)}>
              {o.payment_status.replace(/_/g, " ")}
            </Badge>,
            <span key="created" className="text-[11px] tabular-nums text-slate-500 dark:text-slate-400">{formatDate(o.created_at)}</span>,
            <div key="actions" className="flex justify-end gap-1">
              <Button variant="ghost" size="sm" onClick={() => openDetail(o)}>
                View
              </Button>
              {can("orders.update") &&
                nextStatuses(o).length > 0 && (
                  <Select
                    value=""
                    onChange={(e) => {
                      if (e.target.value) void updateStatus(o, e.target.value as OrderStatus);
                    }}
                    className="h-8 w-auto rounded-lg border border-slate-200 px-2 py-0 text-xs dark:border-slate-800"
                  >
                    <option value="" disabled>
                      {updatingId === o.id ? "Updating..." : "Change"}
                    </option>
                    {nextStatuses(o).map((s) => (
                      <option key={s} value={s}>
                        Mark {s}
                      </option>
                    ))}
                  </Select>
                )}
            </div>,
          ]}
        />

        {data && (
          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            totalPages={data.total_pages}
            onChange={setPage}
          />
        )}
      </Card>

      <Modal
        open={createOpen}
        title="Create order"
        description="Select a customer and add items. Stock is reserved immediately."
        onClose={() => setCreateOpen(false)}
        loading={saving}
        footer={
          <Button onClick={handleCreate} loading={saving}>
            Create order
          </Button>
        }
      >
        {formErrors.form && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950/40 dark:text-red-300">
            {formErrors.form}
          </div>
        )}
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Customer" error={formErrors.customer_id}>
              <Select value={form.customer_id} onChange={(e) => setForm((f) => ({ ...f, customer_id: e.target.value }))}>
                <option value="">Select customer...</option>
                {customers.data?.items.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.first_name} {c.last_name}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Seller (optional)">
              <Select value={form.seller_id} onChange={(e) => setForm((f) => ({ ...f, seller_id: e.target.value }))}>
                <option value="">No seller</option>
                {sellers.data?.items.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.first_name} {s.last_name}
                  </option>
                ))}
              </Select>
            </Field>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-700 dark:text-slate-200">Items</p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setForm((f) => ({ ...f, items: [...f.items, { product_id: "", quantity: "1" }] }))}
              >
                + Add item
              </Button>
            </div>
            {form.items.map((item, i) => (
              <div key={i} className="flex items-start gap-2">
                <div className="flex-1">
                  <Select
                    value={item.product_id}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, items: f.items.map((it, j) => (j === i ? { ...it, product_id: e.target.value } : it)) }))
                    }
                  >
                    <option value="">Select product...</option>
                    {products.data?.items.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} — {formatMoney(p.price)} ({p.stock_quantity} left)
                      </option>
                    ))}
                  </Select>
                  {formErrors[`item-${i}-product`] && (
                    <p className="mt-1 text-xs font-medium text-red-600">{formErrors[`item-${i}-product`]}</p>
                  )}
                </div>
                <div className="w-20">
                  <Input
                    type="number"
                    min="1"
                    value={item.quantity}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, items: f.items.map((it, j) => (j === i ? { ...it, quantity: e.target.value } : it)) }))
                    }
                  />
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={form.items.length === 1}
                  onClick={() => setForm((f) => ({ ...f, items: f.items.filter((_, j) => j !== i) }))}
                >
                  Remove
                </Button>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Discount (USD)">
              <Input type="number" step="0.01" min="0" value={form.discount} onChange={(e) => setForm((f) => ({ ...f, discount: e.target.value }))} />
            </Field>
            <Field label="Tax (USD)">
              <Input type="number" step="0.01" min="0" value={form.tax} onChange={(e) => setForm((f) => ({ ...f, tax: e.target.value }))} />
            </Field>
            <Field label="Shipping fee (USD)">
              <Input type="number" step="0.01" min="0" value={form.shipping_fee} onChange={(e) => setForm((f) => ({ ...f, shipping_fee: e.target.value }))} />
            </Field>
            <Field label="Payment status">
              <Select value={form.payment_status} onChange={(e) => setForm((f) => ({ ...f, payment_status: e.target.value as PaymentStatus }))}>
                {PAYMENT_STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s.replace("_", " ")}
                  </option>
                ))}
              </Select>
            </Field>
          </div>
        </div>
      </Modal>

      <Modal
        open={detail !== null}
        title={detail?.order_number ?? "Order"}
        description={detail ? `Created ${formatDate(detail.created_at)}` : undefined}
        onClose={() => setDetail(null)}
        footer={
          detail && (
            <>
              <Button variant="outline" size="sm" onClick={() => printInvoice(detail, user?.organization_name ?? "")}>
                Print invoice
              </Button>
              {can("orders.update") &&
                nextStatuses(detail).length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {nextStatuses(detail).map((s) => (
                      <Button key={s} variant={s === "cancelled" ? "danger" : "primary"} onClick={() => void updateStatus(detail, s)}>
                        Mark {s}
                      </Button>
                    ))}
                  </div>
                )}
            </>
          )
        }
      >
        {detail && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400 dark:text-slate-500">Customer</p>
                <p className="mt-0.5 font-medium text-slate-900 dark:text-slate-100">{detail.customer_name}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400 dark:text-slate-500">Seller</p>
                <p className="mt-0.5 font-medium text-slate-900 dark:text-slate-100">{detail.seller_name ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400 dark:text-slate-500">Status</p>
                <div className="mt-1">
                  <Badge className={badgeClass(ORDER_STATUS_COLORS, detail.status)}>{detail.status}</Badge>
                </div>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400 dark:text-slate-500">Payment</p>
                <div className="mt-1 flex items-center gap-2">
                  <Badge className={badgeClass(PAYMENT_STATUS_COLORS, detail.payment_status)}>
                    {detail.payment_status.replace("_", " ")}
                  </Badge>
                  {can("orders.update") && (
                    <Select
                      value=""
                      onChange={(e) => {
                        if (e.target.value) void updatePayment(detail, e.target.value as PaymentStatus);
                      }}
                      className="h-7 w-auto rounded-lg border border-slate-200 px-1.5 py-0 text-xs dark:border-slate-800"
                    >
                      <option value="" disabled>
                        Change
                      </option>
                      {PAYMENT_STATUSES.filter((s) => s !== detail.payment_status).map((s) => (
                        <option key={s} value={s}>
                          Mark {s.replace("_", " ")}
                        </option>
                      ))}
                    </Select>
                  )}
                </div>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400 dark:text-slate-500">Created by</p>
                <p className="mt-0.5 font-medium text-slate-900 dark:text-slate-100">{detail.created_by_name ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400 dark:text-slate-500">Created</p>
                <p className="mt-0.5 font-medium text-slate-900 dark:text-slate-100">{formatDate(detail.created_at)}</p>
              </div>
            </div>

            <div className="overflow-hidden rounded-lg border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 dark:bg-slate-800/40">
                  <tr>
                    <th className="px-3 py-2 font-medium text-slate-500 dark:text-slate-400">Product</th>
                    <th className="px-3 py-2 text-right font-medium text-slate-500 dark:text-slate-400">Qty</th>
                    <th className="px-3 py-2 text-right font-medium text-slate-500 dark:text-slate-400">Price</th>
                    <th className="px-3 py-2 text-right font-medium text-slate-500 dark:text-slate-400">Subtotal</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {detail.items.map((item) => (
                    <tr key={item.id}>
                      <td className="px-3 py-2 text-slate-700 dark:text-slate-300">{item.product_name}</td>
                      <td className="px-3 py-2 text-right text-slate-600 dark:text-slate-300">{item.quantity}</td>
                      <td className="px-3 py-2 text-right text-slate-600 dark:text-slate-300">{formatMoney(item.unit_price)}</td>
                      <td className="px-3 py-2 text-right font-medium text-slate-900 dark:text-slate-100">{formatMoney(item.subtotal)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="space-y-1.5 text-sm">
              <div className="flex justify-between text-slate-500 dark:text-slate-400">
                <span>Subtotal</span>
                <span>{formatMoney(detail.subtotal)}</span>
              </div>
              <div className="flex justify-between text-slate-500 dark:text-slate-400">
                <span>Discount</span>
                <span>-{formatMoney(detail.discount)}</span>
              </div>
              <div className="flex justify-between text-slate-500 dark:text-slate-400">
                <span>Tax</span>
                <span>{formatMoney(detail.tax)}</span>
              </div>
              <div className="flex justify-between text-slate-500 dark:text-slate-400">
                <span>Shipping</span>
                <span>{formatMoney(detail.shipping_fee)}</span>
              </div>
              <div className="flex justify-between border-t border-slate-100 pt-2 text-base font-bold text-slate-900 dark:border-slate-800 dark:text-slate-100">
                <span>Total</span>
                <span>{formatMoney(detail.total)}</span>
              </div>
            </div>

            <div>
              <p className="mb-2 text-xs uppercase tracking-wide text-slate-400 dark:text-slate-500">History</p>
              {historyError ? (
                <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-800 dark:bg-red-950/40 dark:text-red-300">
                  {historyError}
                </p>
              ) : history === null ? (
                <div className="space-y-2">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="h-8 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
                  ))}
                </div>
              ) : history.length === 0 ? (
                <p className="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-xs text-slate-500 dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-400">
                  No events recorded yet.
                </p>
              ) : (
                <ol className="space-y-2.5">
                  {history.map((h) => (
                    <li key={h.id} className="flex items-start gap-2.5">
                      <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-indigo-500" />
                      <div className="min-w-0">
                        <p className="text-xs font-medium text-slate-700 dark:text-slate-200">
                          {h.action.replaceAll(".", " ")}
                        </p>
                        <p className="text-[11px] text-slate-400 dark:text-slate-500">
                          {h.user_name ?? "System"} · {formatDate(h.created_at)}
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </div>
        )}
      </Modal>

      <Toast message={toast} />
    </div>
  );
}