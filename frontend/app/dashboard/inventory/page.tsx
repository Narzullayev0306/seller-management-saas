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
import { badgeClass, formatDate, formatNumber, MOVEMENT_TYPE_COLORS, STOCK_STATUS_COLORS } from "@/lib/format";
import type { Movement, StockItem } from "@/lib/types";

export default function InventoryPage() {
  const { can } = useAuth();
  const { data, loading, error, query, setSearch, setPage, setFilter, toggleSort, refetch } =
    useList<StockItem>("/inventory", { sortBy: "stock_quantity", sortOrder: "asc" });
  const movements = useList<Movement>("/inventory/movements", { sortBy: "created_at", sortOrder: "desc" });

  const [search, setSearchInput] = useState("");
  const [tab, setTab] = useState<"stock" | "movements">("stock");
  const [adjustOpen, setAdjustOpen] = useState(false);
  const [form, setForm] = useState({ product_id: "", type: "purchase" as "purchase" | "adjustment", quantity: "", reason: "" });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 3000);
  }, []);

  const openAdjust = () => {
    setForm({ product_id: "", type: "purchase", quantity: "", reason: "" });
    setFormErrors({});
    setAdjustOpen(true);
  };

  async function handleAdjust() {
    const next: Record<string, string> = {};
    if (!form.product_id) next.product_id = "Select a product";
    if (!form.quantity || parseInt(form.quantity, 10) < 1) next.quantity = "Quantity must be ≥ 1";
    setFormErrors(next);
    if (Object.keys(next).length) return;

    setSaving(true);
    try {
      await api.post("/inventory/adjustments", {
        product_id: form.product_id,
        type: form.type,
        quantity: parseInt(form.quantity, 10),
        reason: form.reason.trim() || undefined,
      });
      showToast("Stock adjusted");
      setAdjustOpen(false);
      refetch();
      movements.refetch();
    } catch (err) {
      setFormErrors({ form: err instanceof Error ? err.message : "Failed to adjust stock" });
    } finally {
      setSaving(false);
    }
  }

  const stockColumns = [
    { key: "name", header: "Product" },
    { key: "sku", header: "SKU" },
    { key: "category", header: "Category" },
    { key: "stock_quantity", header: "In stock" },
    { key: "low_stock_threshold", header: "Threshold" },
    { key: "stock_status", header: "Status" },
    { key: "actions", header: "" },
  ];

  const movementColumns = [
    { key: "created_at", header: "Date" },
    { key: "product_name", header: "Product" },
    { key: "type", header: "Type" },
    { key: "quantity", header: "Change" },
    { key: "stock", header: "Stock" },
    { key: "reason", header: "Reason" },
    { key: "reference", header: "Reference" },
  ];

  const selectedProduct = (data?.items ?? []).find((p) => p.id === form.product_id);
  const previewQty = parseInt(form.quantity, 10);
  const showPreview = !!selectedProduct && !Number.isNaN(previewQty) && previewQty > 0;
  const projectedStock = showPreview
    ? selectedProduct.stock_quantity + (form.type === "adjustment" ? -previewQty : previewQty)
    : 0;

  const exportStockCsv = () => {
    if (!data || data.items.length === 0) return;
    const lines: string[] = ["Product,SKU,Category,InStock,Threshold,Status"];
    for (const item of data.items) {
      lines.push(
        `"${item.name.replace(/"/g, '""')}","${item.sku}","${item.category ?? ""}","${item.stock_quantity}","${item.low_stock_threshold}","${item.stock_status}"`
      );
    }
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `inventory-stock.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportMovementsCsv = () => {
    if (!movements.data || movements.data.items.length === 0) return;
    const lines: string[] = ["Date,Product,Type,Quantity,Reason,ReferenceID"];
    for (const m of movements.data.items) {
      lines.push(
        `"${m.created_at}","${(m.product_name ?? "").replace(/"/g, '""')}","${m.type}","${m.quantity}","${(m.reason ?? "").replace(/"/g, '""')}","${m.reference_id ?? ""}"`
      );
    }
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `inventory-movements.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <PageHeader
        title="Inventory"
        description="Stock levels and movement history."
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={tab === "stock" ? exportStockCsv : exportMovementsCsv}
              disabled={tab === "stock" ? (!data || data.items.length === 0) : (!movements.data || movements.data.items.length === 0)}
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              Export CSV
            </Button>
            {can("inventory.update") && (
              <Button onClick={openAdjust}>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                Adjust stock
              </Button>
            )}
          </div>
        }
      />

      <div className="mb-4 flex rounded-lg border border-slate-200 bg-white p-0.5 w-fit dark:border-slate-800 dark:bg-slate-900">
        <button
          type="button"
          onClick={() => setTab("stock")}
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${tab === "stock" ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"}`}
        >
          Stock levels
        </button>
        <button
          type="button"
          onClick={() => setTab("movements")}
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${tab === "movements" ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"}`}
        >
          Movements
        </button>
      </div>

      {tab === "stock" && (
        <Card>
          <Toolbar
            search={search}
            onSearch={(v) => {
              setSearchInput(v);
              const t = window.setTimeout(() => setSearch(v), 350);
              return () => window.clearTimeout(t);
            }}
            placeholder="Search product or SKU..."
            filters={
              <>
                <Select value={(query.stock_status as string) ?? ""} onChange={(e) => setFilter("stock_status", e.target.value || undefined)} className="w-36">
                  <option value="">All stock</option>
                  <option value="in_stock">In stock</option>
                  <option value="low_stock">Low stock</option>
                  <option value="out_of_stock">Out of stock</option>
                </Select>
              </>
            }
          />
          <DataTable
            columns={stockColumns}
            rows={data?.items ?? []}
            loading={loading}
            error={error}
            onRetry={refetch}
            onSort={toggleSort}
            sortBy={query.sort_by as string}
            sortOrder={query.sort_order as "asc" | "desc"}
            renderMobileCard={(p) => (
              <MobileCard
                title={p.name}
                subtitle={`${p.sku} · ${p.category}`}
                actions={
                  can("inventory.update") && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setForm((f) => ({ ...f, product_id: p.id, type: "purchase" }));
                        setFormErrors({});
                        setAdjustOpen(true);
                      }}
                    >
                      Restock
                    </Button>
                  )
                }
              >
                <span className={`text-sm font-semibold tabular-nums ${p.stock_quantity <= p.low_stock_threshold ? "text-amber-600 dark:text-amber-400" : "text-slate-900 dark:text-slate-100"}`}>
                  {formatNumber(p.stock_quantity)} in stock
                </span>
                <Badge className={badgeClass(STOCK_STATUS_COLORS, p.stock_status)}>{p.stock_status.replace("_", " ")}</Badge>
              </MobileCard>
            )}
            renderRow={(p) => [
              <div key="name">
                <p className="font-medium text-slate-900 dark:text-slate-100">{p.name}</p>
              </div>,
              <span key="sku" className="font-mono text-xs text-slate-500 dark:text-slate-400">{p.sku}</span>,
              <span key="cat" className="text-slate-600 dark:text-slate-300">{p.category}</span>,
              <span key="stock" className={`font-bold ${p.stock_quantity <= p.low_stock_threshold ? "text-amber-600 dark:text-amber-400" : "text-slate-900 dark:text-slate-100"}`}>
                {formatNumber(p.stock_quantity)}
              </span>,
              <span key="thr" className="text-slate-600 dark:text-slate-300">{p.low_stock_threshold}</span>,
              <Badge key="status" className={badgeClass(STOCK_STATUS_COLORS, p.stock_status)}>{p.stock_status.replace("_", " ")}</Badge>,
              <div key="actions" className="flex justify-end">
                {can("inventory.update") && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setForm((f) => ({ ...f, product_id: p.id, type: "purchase" }));
                      setFormErrors({});
                      setAdjustOpen(true);
                    }}
                  >
                    Restock
                  </Button>
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
      )}

      {tab === "movements" && (
        <Card>
          <DataTable
            columns={movementColumns}
            rows={movements.data?.items ?? []}
            loading={movements.loading}
            error={movements.error}
            onRetry={movements.refetch}
            renderMobileCard={(m) => (
              <MobileCard
                title={m.product_name}
                subtitle={formatDate(m.created_at)}
              >
                <Badge className={badgeClass(MOVEMENT_TYPE_COLORS, m.type)}>{m.type}</Badge>
                <span
                  className={`text-sm font-semibold tabular-nums ${m.quantity > 0 ? "text-emerald-600 dark:text-emerald-400" : m.quantity < 0 ? "text-red-600 dark:text-red-400" : "text-slate-500 dark:text-slate-400"}`}
                >
                  {m.quantity > 0 ? `+${formatNumber(m.quantity)}` : formatNumber(m.quantity)}
                </span>
                {m.previous_stock !== null && m.new_stock !== null && (
                  <span className="font-mono text-xs tabular-nums text-slate-500 dark:text-slate-400">
                    {formatNumber(m.previous_stock)} → {formatNumber(m.new_stock)}
                  </span>
                )}
              </MobileCard>
            )}
            renderRow={(m) => [
              <span key="date" className="text-xs text-slate-500 dark:text-slate-400">{formatDate(m.created_at)}</span>,
              <span key="product" className="font-medium text-slate-900 dark:text-slate-100">{m.product_name}</span>,
              <Badge key="type" className={badgeClass(MOVEMENT_TYPE_COLORS, m.type)}>{m.type}</Badge>,
              <span
                key="qty"
                className={`font-medium ${m.quantity > 0 ? "text-emerald-600 dark:text-emerald-400" : m.quantity < 0 ? "text-red-600 dark:text-red-400" : "text-slate-500 dark:text-slate-400"}`}
              >
                {m.quantity > 0 ? `+${formatNumber(m.quantity)}` : formatNumber(m.quantity)}
              </span>,
              <span key="stock" className="font-mono text-xs text-slate-500 dark:text-slate-400">
                {m.previous_stock !== null && m.new_stock !== null
                  ? `${formatNumber(m.previous_stock)} → ${formatNumber(m.new_stock)}`
                  : "—"}
              </span>,
              <span key="reason" className="text-slate-600 dark:text-slate-300">{m.reason ?? "—"}</span>,
              <span key="reference">
                {m.reference_id ? (
                  <span className="rounded border border-indigo-200 bg-indigo-50 px-1.5 py-0.5 font-mono text-xs font-medium text-indigo-600 dark:border-indigo-900/50 dark:bg-indigo-950/50 dark:text-indigo-400">
                    Order
                  </span>
                ) : (
                  <span className="text-slate-400 dark:text-slate-500">—</span>
                )}
              </span>,
            ]}
          />
          {movements.data && (
            <Pagination
              page={movements.data.page}
              pageSize={movements.data.page_size}
              total={movements.data.total}
              totalPages={movements.data.total_pages}
              onChange={movements.setPage}
            />
          )}
        </Card>
      )}

      <Modal
        open={adjustOpen}
        title="Adjust stock"
        description="Purchase restocks; adjustment can increase or decrease."
        onClose={() => setAdjustOpen(false)}
        loading={saving}
        footer={
          <Button onClick={handleAdjust} loading={saving}>
            Apply adjustment
          </Button>
        }
      >
        {formErrors.form && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {formErrors.form}
          </div>
        )}
        <div className="space-y-4">
          <Field label="Product" error={formErrors.product_id}>
            <Select
              value={form.product_id}
              onChange={(e) => {
                setForm((f) => ({ ...f, product_id: e.target.value }));
              }}
            >
              <option value="">Select product...</option>
              {(data?.items ?? []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.sku}) — {p.stock_quantity} in stock
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Type">
            <Select value={form.type} onChange={(e) => setForm((f) => ({ ...f, type: e.target.value as "purchase" | "adjustment" }))}>
              <option value="purchase">Purchase (restock)</option>
              <option value="adjustment">Adjustment</option>
            </Select>
          </Field>
          <Field label="Quantity" error={formErrors.quantity}>
            <Input type="number" min="1" value={form.quantity} onChange={(e) => setForm((f) => ({ ...f, quantity: e.target.value }))} />
          </Field>
          <Field label="Reason">
            <Input value={form.reason} onChange={(e) => setForm((f) => ({ ...f, reason: e.target.value }))} placeholder="Optional note" />
          </Field>
        </div>
        {selectedProduct && showPreview && (
          <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-800/50">
            <span className="text-slate-600 dark:text-slate-300">
              Current: <span className="font-bold text-slate-900 dark:text-slate-100">{formatNumber(selectedProduct.stock_quantity)}</span>
            </span>
            <span className="mx-2 text-slate-400 dark:text-slate-500">→</span>
            <span className="text-slate-600 dark:text-slate-300">
              After:{" "}
              <span className={`font-bold ${projectedStock < 0 ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"}`}>
                {formatNumber(projectedStock)}
              </span>
            </span>
            {projectedStock < 0 && (
              <span className="ml-2 text-xs font-medium text-red-600 dark:text-red-400">Stock cannot go below zero</span>
            )}
          </div>
        )}
      </Modal>

      <Toast message={toast} />
    </div>
  );
}