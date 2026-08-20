"use client";

import { useCallback, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { Modal, Toast } from "@/components/ui/modal";
import { DataTable, Pagination } from "@/components/ui/table";
import { Badge } from "@/components/ui/states";
import { useAuth } from "@/lib/auth";
import { useList } from "@/lib/use-list";
import { api } from "@/lib/api-client";
import { formatDate, formatMoney } from "@/lib/format";
import type { ShippingMethod, ShippingMethodCreate } from "@/lib/types";

interface FormState {
  name: string;
  description: string;
  price: string;
  min_order_amount: string;
  max_order_amount: string;
  estimated_delivery_days: string;
  is_active: boolean;
  sort_order: number;
}

const EMPTY_FORM: FormState = {
  name: "",
  description: "",
  price: "",
  min_order_amount: "",
  max_order_amount: "",
  estimated_delivery_days: "",
  is_active: true,
  sort_order: 0,
};

export default function ShippingPage() {
  const { can } = useAuth();
  const { data, loading, error, refetch } = useList<ShippingMethod>("/shipping-methods", { sortBy: "sort_order", sortOrder: "asc" });

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<ShippingMethod | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 3000);
  }, []);

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormErrors({});
    setModalOpen(true);
  };

  const openEdit = (m: ShippingMethod) => {
    setEditing(m);
    setForm({
      name: m.name,
      description: m.description ?? "",
      price: String(m.price),
      min_order_amount: m.min_order_amount !== null ? String(m.min_order_amount) : "",
      max_order_amount: m.max_order_amount !== null ? String(m.max_order_amount) : "",
      estimated_delivery_days: m.estimated_delivery_days !== null ? String(m.estimated_delivery_days) : "",
      is_active: m.is_active,
      sort_order: m.sort_order,
    });
    setFormErrors({});
    setModalOpen(true);
  };

  function validate(): boolean {
    const next: Partial<Record<keyof FormState, string>> = {};
    if (!form.name.trim()) next.name = "Name is required";
    if (!form.price.trim() || Number.isNaN(Number(form.price)) || Number(form.price) < 0) next.price = "Enter a valid price";
    if (form.estimated_delivery_days.trim() && (Number.isNaN(Number(form.estimated_delivery_days)) || Number(form.estimated_delivery_days) < 0)) {
      next.estimated_delivery_days = "Enter a valid number of days";
    }
    setFormErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSave() {
    if (!validate()) return;
    setSaving(true);
    try {
      const payload: ShippingMethodCreate = {
        name: form.name.trim(),
        description: form.description.trim() || undefined,
        price: Number(form.price),
        min_order_amount: form.min_order_amount ? Number(form.min_order_amount) : undefined,
        max_order_amount: form.max_order_amount ? Number(form.max_order_amount) : undefined,
        estimated_delivery_days: form.estimated_delivery_days ? Number(form.estimated_delivery_days) : undefined,
        is_active: form.is_active,
        sort_order: form.sort_order,
      };
      if (editing) {
        await api.patch(`/shipping-methods/${editing.id}`, payload);
        showToast("Shipping method updated");
      } else {
        await api.post("/shipping-methods", payload);
        showToast("Shipping method created");
      }
      setModalOpen(false);
      refetch();
    } catch (err) {
      setFormErrors({ name: err instanceof Error ? err.message : "Failed to save shipping method" });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(m: ShippingMethod) {
    if (!window.confirm(`Delete shipping method "${m.name}"?`)) return;
    try {
      await api.delete(`/shipping-methods/${m.id}`);
      showToast("Shipping method deleted");
      refetch();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to delete shipping method");
    }
  }

  const columns = [
    { key: "name", header: "Method" },
    { key: "price", header: "Price" },
    { key: "min_order_amount", header: "Order range" },
    { key: "estimated_delivery_days", header: "Delivery" },
    { key: "sort_order", header: "Order" },
    { key: "is_active", header: "Status" },
    { key: "created_at", header: "Added" },
    { key: "actions", header: "" },
  ];

  return (
    <div>
      <PageHeader
        title="Shipping"
        description="Configure shipping rates and delivery estimates offered at checkout."
        actions={
          can("settings.update") && (
            <Button onClick={openCreate}>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Add method
            </Button>
          )
        }
      />

      <Card>
        <DataTable
          columns={columns}
          rows={data?.items ?? []}
          loading={loading}
          error={error}
          onRetry={refetch}
          emptyTitle="No shipping methods"
          emptyDescription="Add a shipping method to offer delivery options at checkout."
          renderRow={(m) => [
            <div key="name">
              <p className="font-medium text-slate-900 dark:text-slate-100">{m.name}</p>
              {m.description && <p className="max-w-64 truncate text-xs text-slate-500" title={m.description}>{m.description}</p>}
            </div>,
            <span key="price" className="font-semibold text-slate-900 dark:text-slate-100">{formatMoney(m.price)}</span>,
            <span key="range" className="text-xs text-slate-500 dark:text-slate-400">
              {m.min_order_amount !== null ? `${formatMoney(m.min_order_amount)} min` : "No minimum"}
              {m.max_order_amount !== null ? ` · ${formatMoney(m.max_order_amount)} max` : ""}
            </span>,
            <span key="delivery" className="text-slate-600 dark:text-slate-300">{m.estimated_delivery_days !== null ? `${m.estimated_delivery_days} days` : "—"}</span>,
            <span key="sort" className="text-slate-600 dark:text-slate-300">{m.sort_order}</span>,
            <Badge key="status" className={m.is_active ? "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800" : "bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700"}>
              {m.is_active ? "active" : "inactive"}
            </Badge>,
            <span key="created" className="text-xs text-slate-500 dark:text-slate-400">{formatDate(m.created_at)}</span>,
            <div key="actions" className="flex justify-end gap-1">
              {can("settings.update") && (
                <Button variant="ghost" size="sm" onClick={() => openEdit(m)}>
                  Edit
                </Button>
              )}
              {can("settings.update") && (
                <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40" onClick={() => void handleDelete(m)}>
                  Delete
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
            onChange={() => undefined}
          />
        )}
      </Card>

      <Modal
        open={modalOpen}
        title={editing ? "Edit shipping method" : "Add shipping method"}
        description={editing ? `Updating ${editing.name}` : "Configure a new shipping option"}
        onClose={() => setModalOpen(false)}
        loading={saving}
        footer={
          <Button onClick={handleSave} loading={saving}>
            {editing ? "Save changes" : "Create method"}
          </Button>
        }
      >
        <div className="space-y-4">
          <Field label="Name" error={formErrors.name}>
            <Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder="Standard delivery" />
          </Field>
          <Field label="Description">
            <Textarea rows={2} value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
          </Field>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Field label="Price" error={formErrors.price}>
              <Input type="number" step="0.01" min="0" value={form.price} onChange={(e) => setForm((f) => ({ ...f, price: e.target.value }))} placeholder="9.99" />
            </Field>
            <Field label="Min order">
              <Input type="number" step="0.01" min="0" value={form.min_order_amount} onChange={(e) => setForm((f) => ({ ...f, min_order_amount: e.target.value }))} placeholder="0.00" />
            </Field>
            <Field label="Max order">
              <Input type="number" step="0.01" min="0" value={form.max_order_amount} onChange={(e) => setForm((f) => ({ ...f, max_order_amount: e.target.value }))} placeholder="999.00" />
            </Field>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Field label="Delivery days" error={formErrors.estimated_delivery_days}>
              <Input type="number" min="0" max="365" value={form.estimated_delivery_days} onChange={(e) => setForm((f) => ({ ...f, estimated_delivery_days: e.target.value }))} placeholder="3" />
            </Field>
            <Field label="Sort order">
              <Input type="number" min="0" value={form.sort_order} onChange={(e) => setForm((f) => ({ ...f, sort_order: Number(e.target.value) || 0 }))} />
            </Field>
            <Field label="Status">
              <Select value={form.is_active ? "active" : "inactive"} onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.value === "active" }))}>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </Select>
            </Field>
          </div>
        </div>
      </Modal>

      <Toast message={toast} />
    </div>
  );
}