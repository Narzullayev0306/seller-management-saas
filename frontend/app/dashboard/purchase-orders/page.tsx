"use client";

import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { Modal, Toast } from "@/components/ui/modal";
import { Badge } from "@/components/ui/states";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api-client";
import { formatDate, formatMoney } from "@/lib/format";
import type { Product, PurchaseOrder, PurchaseOrderCreate, Supplier } from "@/lib/types";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
  ordered: "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800",
  received: "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
  cancelled: "bg-red-100 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800",
};

interface ItemRow {
  product_id: string;
  quantity: string;
  unit_cost: string;
}

interface FormState {
  supplier_id: string;
  expected_date: string;
  notes: string;
  items: ItemRow[];
}

const EMPTY_FORM: FormState = { supplier_id: "", expected_date: "", notes: "", items: [{ product_id: "", quantity: "1", unit_cost: "" }] };

export default function PurchaseOrdersPage() {
  const { can } = useAuth();
  const canUpdate = can("inventory.update");

  const [pos, setPos] = useState<PurchaseOrder[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState<{ supplier_id?: string; items?: string }>({});
  const [saving, setSaving] = useState(false);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<string>("");

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 3000);
  }, []);

  const load = useCallback(() => {
    setError(null);
    api
      .get<PurchaseOrder[]>("/purchase-orders")
      .then(setPos)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load purchase orders"));
  }, []);

  useEffect(() => {
    const t = setTimeout(() => void load(), 0);
    return () => clearTimeout(t);
  }, [load]);

  function openCreate() {
    setForm(EMPTY_FORM);
    setFormErrors({});
    setSelectedProduct("");
    setModalOpen(true);
    Promise.all([
      api.get<{ items: Supplier[] }>("/suppliers", { page: 1, page_size: 100 }),
      api.get<{ items: Product[] }>("/products", { page: 1, page_size: 100 }),
    ])
      .then(([s, p]) => {
        setSuppliers(s.items);
        setProducts(p.items);
      })
      .catch(() => {
        setSuppliers([]);
        setProducts([]);
      });
  }

  function validate(): boolean {
    const next: { supplier_id?: string; items?: string } = {};
    if (form.items.length === 0 || form.items.some((i) => !i.product_id)) {
      next.items = "Add at least one product";
    }
    if (form.items.some((i) => i.product_id && (!i.quantity || Number(i.quantity) < 1))) {
      next.items = "Each item needs a valid quantity";
    }
    if (form.items.some((i) => i.product_id && (i.unit_cost === "" || Number(i.unit_cost) < 0))) {
      next.items = "Each item needs a valid unit cost";
    }
    setFormErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleCreate() {
    if (!validate()) return;
    setSaving(true);
    try {
      const payload: PurchaseOrderCreate = {
        supplier_id: form.supplier_id || undefined,
        expected_date: form.expected_date || undefined,
        notes: form.notes.trim() || undefined,
        items: form.items.map((i) => ({
          product_id: i.product_id,
          quantity: Number(i.quantity),
          unit_cost: Number(i.unit_cost),
        })),
      };
      await api.post("/purchase-orders", payload);
      showToast("Purchase order created");
      setModalOpen(false);
      load();
    } catch (err) {
      setFormErrors({ items: err instanceof Error ? err.message : "Failed to create purchase order" });
    } finally {
      setSaving(false);
    }
  }

  function addItem() {
    if (!selectedProduct) {
      showToast("Select a product first");
      return;
    }
    const product = products.find((p) => p.id === selectedProduct);
    if (!product) return;
    setForm((f) => ({
      ...f,
      items: [...f.items, { product_id: product.id, quantity: "1", unit_cost: product.cost_price || product.price }],
    }));
    setSelectedProduct("");
  }

  function removeItem(index: number) {
    setForm((f) => ({ ...f, items: f.items.filter((_, i) => i !== index) }));
  }

  async function changeStatus(po: PurchaseOrder, status: string) {
    setActionLoading(`${po.id}:${status}`);
    try {
      await api.patch(`/purchase-orders/${po.id}`, { status });
      showToast(`Purchase order ${status}`);
      load();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to update purchase order");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleDelete(po: PurchaseOrder) {
    if (!window.confirm(`Delete purchase order ${po.po_number}?`)) return;
    setActionLoading(`${po.id}:delete`);
    try {
      await api.delete(`/purchase-orders/${po.id}`);
      showToast("Purchase order deleted");
      load();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to delete purchase order");
    } finally {
      setActionLoading(null);
    }
  }

  return (
    <div>
      <PageHeader
        title="Purchase Orders"
        description="Order stock from suppliers and receive it into inventory."
        actions={
          canUpdate && (
            <Button onClick={openCreate}>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              New purchase order
            </Button>
          )
        }
      />

      <Card>
        <div className="overflow-x-auto">
          {!error && !pos ? (
            <div className="space-y-3 p-5">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-10 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
              ))}
            </div>
          ) : error ? (
            <div className="flex flex-col items-center gap-3 px-6 py-14 text-center">
              <p className="text-sm font-semibold text-slate-700">{error}</p>
              <Button variant="outline" size="sm" onClick={load}>
                Try again
              </Button>
            </div>
          ) : pos!.length === 0 ? (
            <div className="flex flex-col items-center gap-2 px-6 py-14 text-center">
              <p className="text-sm font-semibold text-slate-700">No purchase orders</p>
              <p className="text-sm text-slate-500">Create a purchase order to restock from suppliers.</p>
            </div>
          ) : (
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/60 dark:border-slate-800 dark:bg-slate-800/40">
                  {["PO number", "Supplier", "Items", "Total", "Status", "Created", "Received", ""].map((h) => (
                    <th key={h} className="px-4 py-3 font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {pos!.map((po) => (
                  <tr key={po.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{po.po_number}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{po.supplier_name ?? "—"}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{po.items.reduce((s, i) => s + i.quantity, 0)} units</td>
                    <td className="px-4 py-3 font-semibold text-slate-900 dark:text-slate-100">{formatMoney(po.total)}</td>
                    <td className="px-4 py-3">
                      <Badge className={STATUS_COLORS[po.status]}>{po.status}</Badge>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">{formatDate(po.created_at)}</td>
                    <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">{po.received_at ? formatDate(po.received_at) : "—"}</td>
                    <td className="px-4 py-3">
                      {canUpdate && (
                        <div className="flex justify-end gap-1">
                          {po.status === "draft" && (
                            <Button
                              variant="outline"
                              size="sm"
                              loading={actionLoading === `${po.id}:ordered`}
                              onClick={() => void changeStatus(po, "ordered")}
                            >
                              Order
                            </Button>
                          )}
                          {po.status === "ordered" && (
                            <Button
                              variant="outline"
                              size="sm"
                              loading={actionLoading === `${po.id}:received`}
                              onClick={() => void changeStatus(po, "received")}
                            >
                              Receive
                            </Button>
                          )}
                          {(po.status === "draft" || po.status === "ordered") && (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40"
                                loading={actionLoading === `${po.id}:cancelled`}
                                onClick={() => void changeStatus(po, "cancelled")}
                              >
                                Cancel
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40"
                                loading={actionLoading === `${po.id}:delete`}
                                onClick={() => void handleDelete(po)}
                              >
                                Delete
                              </Button>
                            </>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>

      <Modal
        open={modalOpen}
        title="New purchase order"
        description="Draft an order for stock from a supplier"
        onClose={() => setModalOpen(false)}
        loading={saving}
        footer={
          <Button onClick={handleCreate} loading={saving}>
            Create purchase order
          </Button>
        }
      >
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Supplier">
              <Select value={form.supplier_id} onChange={(e) => setForm((f) => ({ ...f, supplier_id: e.target.value }))}>
                <option value="">No supplier</option>
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Expected date">
              <Input
                type="date"
                value={form.expected_date}
                onChange={(e) => setForm((f) => ({ ...f, expected_date: e.target.value }))}
              />
            </Field>
          </div>

          <div>
            <div className="mb-2 flex items-center gap-2">
              <Select value={selectedProduct} onChange={(e) => setSelectedProduct(e.target.value)}>
                <option value="">Add product...</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.sku})
                  </option>
                ))}
              </Select>
              <Button variant="outline" size="sm" onClick={addItem}>
                Add
              </Button>
            </div>
            <div className="space-y-2">
              {form.items.map((item, index) => {
                const product = products.find((p) => p.id === item.product_id);
                return (
                  <div key={index} className="flex items-center gap-2 rounded-lg border border-slate-200 p-2 dark:border-slate-700">
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">
                        {product ? product.name : "Removed product"}
                      </p>
                      <p className="text-xs text-slate-500">{product?.sku ?? "—"}</p>
                    </div>
                    <Input
                      type="number"
                      min="1"
                      className="w-20"
                      value={item.quantity}
                      onChange={(e) =>
                        setForm((f) => ({
                          ...f,
                          items: f.items.map((it, i) => (i === index ? { ...it, quantity: e.target.value } : it)),
                        }))
                      }
                    />
                    <Input
                      type="number"
                      min="0"
                      step="0.01"
                      className="w-24"
                      placeholder="Cost"
                      value={item.unit_cost}
                      onChange={(e) =>
                        setForm((f) => ({
                          ...f,
                          items: f.items.map((it, i) => (i === index ? { ...it, unit_cost: e.target.value } : it)),
                        }))
                      }
                    />
                    <button
                      type="button"
                      onClick={() => removeItem(index)}
                      className="rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
                      aria-label="Remove item"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                );
              })}
            </div>
            {formErrors.items && <p className="mt-1.5 text-xs font-medium text-red-600">{formErrors.items}</p>}
          </div>

          <Field label="Notes">
            <Textarea rows={2} value={form.notes} onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} />
          </Field>
        </div>
      </Modal>

      <Toast message={toast} />
    </div>
  );
}