"use client";

import { useCallback, useState } from "react";

import { Badge } from "@/components/ui/states";
import { PageHeader, Toolbar } from "@/components/page-header";
import { DataTable, Pagination } from "@/components/ui/table";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { Modal, Toast } from "@/components/ui/modal";
import { useAuth } from "@/lib/auth";
import { useList } from "@/lib/use-list";
import { api } from "@/lib/api-client";
import { badgeClass, formatDate, SUPPLIER_STATUS_COLORS } from "@/lib/format";
import type { Supplier, SupplierCreate } from "@/lib/types";

interface FormState {
  name: string;
  email: string;
  phone: string;
  address: string;
  status: "active" | "inactive";
}

const EMPTY_FORM: FormState = { name: "", email: "", phone: "", address: "", status: "active" };

export default function SuppliersPage() {
  const { can } = useAuth();
  const { data, loading, error, query, setSearch, setPage, setFilter, refetch } =
    useList<Supplier>("/suppliers", { sortBy: "created_at", sortOrder: "desc" });

  const [search, setSearchInput] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Supplier | null>(null);
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

  const openEdit = (s: Supplier) => {
    setEditing(s);
    setForm({
      name: s.name,
      email: s.email ?? "",
      phone: s.phone ?? "",
      address: s.address ?? "",
      status: s.status,
    });
    setFormErrors({});
    setModalOpen(true);
  };

  function validate(): boolean {
    const next: Partial<Record<keyof FormState, string>> = {};
    if (!form.name.trim()) next.name = "Name is required";
    if (form.email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) next.email = "Enter a valid email";
    setFormErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSave() {
    if (!validate()) return;
    setSaving(true);
    try {
      const payload: SupplierCreate = {
        name: form.name.trim(),
        email: form.email.trim() || undefined,
        phone: form.phone.trim() || undefined,
        address: form.address.trim() || undefined,
        status: form.status,
      };
      if (editing) {
        await api.patch(`/suppliers/${editing.id}`, payload);
        showToast("Supplier updated");
      } else {
        await api.post("/suppliers", payload);
        showToast("Supplier created");
      }
      setModalOpen(false);
      refetch();
    } catch (err) {
      setFormErrors({ email: err instanceof Error ? err.message : "Failed to save supplier" });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(s: Supplier) {
    if (!window.confirm(`Delete supplier "${s.name}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/suppliers/${s.id}`);
      showToast("Supplier deleted");
      refetch();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to delete supplier");
    }
  }

  const columns = [
    { key: "name", header: "Supplier" },
    { key: "email", header: "Email" },
    { key: "phone", header: "Phone" },
    { key: "address", header: "Address" },
    { key: "status", header: "Status" },
    { key: "created_at", header: "Added" },
    { key: "actions", header: "" },
  ];

  return (
    <div>
      <PageHeader
        title="Suppliers"
        description="Manage the vendors you source products from."
        actions={
          can("suppliers.create") && (
            <Button onClick={openCreate}>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Add supplier
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
          placeholder="Search name, email or phone..."
          filters={
            <Select value={(query.status as string) ?? ""} onChange={(e) => setFilter("status", e.target.value || undefined)} className="w-36">
              <option value="">All statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </Select>
          }
        />

        <DataTable
          columns={columns}
          rows={data?.items ?? []}
          loading={loading}
          error={error}
          onRetry={refetch}
          renderRow={(s) => [
            <div key="name" className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                {s.name[0]?.toUpperCase() ?? "?"}
              </div>
              <p className="font-medium text-slate-900 dark:text-slate-100">{s.name}</p>
            </div>,
            <span key="email" className="text-slate-600 dark:text-slate-300">{s.email ?? "—"}</span>,
            <span key="phone" className="text-slate-600 dark:text-slate-300">{s.phone ?? "—"}</span>,
            <span key="address" className="max-w-56 truncate text-slate-600 dark:text-slate-300" title={s.address ?? undefined}>
              {s.address ?? "—"}
            </span>,
            <Badge key="status" className={badgeClass(SUPPLIER_STATUS_COLORS, s.status)}>
              {s.status}
            </Badge>,
            <span key="created" className="text-xs text-slate-500 dark:text-slate-400">{formatDate(s.created_at)}</span>,
            <div key="actions" className="flex justify-end gap-1">
              {can("suppliers.update") && (
                <Button variant="ghost" size="sm" onClick={() => openEdit(s)}>
                  Edit
                </Button>
              )}
              {can("suppliers.delete") && (
                <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40" onClick={() => void handleDelete(s)}>
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
            onChange={setPage}
          />
        )}
      </Card>

      <Modal
        open={modalOpen}
        title={editing ? "Edit supplier" : "Add supplier"}
        description={editing ? `Updating ${editing.name}` : "Create a new supplier record"}
        onClose={() => setModalOpen(false)}
        loading={saving}
        footer={
          <Button onClick={handleSave} loading={saving}>
            {editing ? "Save changes" : "Create supplier"}
          </Button>
        }
      >
        <div className="space-y-4">
          <Field label="Name" error={formErrors.name}>
            <Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder="Acme Distributors" />
          </Field>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Email" error={formErrors.email}>
              <Input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} placeholder="contact@acme.com" />
            </Field>
            <Field label="Phone">
              <Input value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} placeholder="+998 90 123 45 67" />
            </Field>
          </div>
          <Field label="Address">
            <Textarea rows={2} value={form.address} onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))} />
          </Field>
          <Field label="Status">
            <Select value={form.status} onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as "active" | "inactive" }))}>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </Select>
          </Field>
        </div>
      </Modal>

      <Toast message={toast} />
    </div>
  );
}