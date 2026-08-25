"use client";

import { useCallback, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Toolbar } from "@/components/page-header";
import { DataTable, MobileCard } from "@/components/ui/table";
import { Pagination } from "@/components/ui/table";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Field, Input, Textarea } from "@/components/ui/input";
import { Modal, Toast } from "@/components/ui/modal";
import { useAuth } from "@/lib/auth";
import { useList } from "@/lib/use-list";
import { api } from "@/lib/api-client";
import { formatDate, formatMoney, fullName } from "@/lib/format";
import type { Customer } from "@/lib/types";

interface FormState {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  address: string;
}

const EMPTY_FORM: FormState = { first_name: "", last_name: "", email: "", phone: "", address: "" };

export default function CustomersPage() {
  const { can } = useAuth();
  const { data, loading, error, query, setSearch, setPage, toggleSort, refetch } =
    useList<Customer>("/customers", { sortBy: "created_at", sortOrder: "desc" });

  const [search, setSearchInput] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
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

  const openEdit = (c: Customer) => {
    setEditing(c);
    setForm({ first_name: c.first_name, last_name: c.last_name, email: c.email, phone: c.phone ?? "", address: c.address ?? "" });
    setFormErrors({});
    setModalOpen(true);
  };

  function validate(): boolean {
    const next: Partial<Record<keyof FormState, string>> = {};
    if (!form.first_name.trim()) next.first_name = "First name is required";
    if (!form.last_name.trim()) next.last_name = "Last name is required";
    if (!form.email.trim()) next.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) next.email = "Enter a valid email";
    setFormErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSave() {
    if (!validate()) return;
    setSaving(true);
    try {
      const payload = {
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim() || undefined,
        address: form.address.trim() || undefined,
      };
      if (editing) {
        await api.patch(`/customers/${editing.id}`, payload);
        showToast("Customer updated");
      } else {
        await api.post("/customers", payload);
        showToast("Customer created");
      }
      setModalOpen(false);
      refetch();
    } catch (err) {
      setFormErrors({ email: err instanceof Error ? err.message : "Failed to save" });
    } finally {
      setSaving(false);
    }
  }

  const columns = [
    { key: "name", header: "Name" },
    { key: "email", header: "Email" },
    { key: "phone", header: "Phone" },
    { key: "total_orders", header: "Orders" },
    { key: "total_spent", header: "Total spent" },
    { key: "created_at", header: "Customer since" },
    { key: "actions", header: "" },
  ];

  return (
    <div>
      <PageHeader
        title="Customers"
        description="Your customer base and their purchase history."
        actions={
          can("customers.create") && (
            <Button onClick={openCreate}>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Add customer
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
          placeholder="Search name or email..."
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
          renderMobileCard={(c) => (
            <MobileCard
              title={fullName(c.first_name, c.last_name)}
              subtitle={`${c.email}${c.phone ? ` · ${c.phone}` : ""}`}
              actions={
                can("customers.update") && (
                  <Button variant="ghost" size="sm" onClick={() => openEdit(c)}>
                    Edit
                  </Button>
                )
              }
            >
              <span className="text-sm font-semibold tabular-nums">{formatMoney(c.total_spent)}</span>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {c.total_orders} order{c.total_orders === 1 ? "" : "s"}
              </span>
              <span className="text-xs text-slate-400 dark:text-slate-500">since {formatDate(c.created_at)}</span>
            </MobileCard>
          )}
          renderRow={(c) => [
            <div key="name" className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-700">
                {c.first_name[0] ?? ""}
                {c.last_name[0] ?? ""}
              </div>
              <p className="font-medium text-slate-900 dark:text-slate-100">{fullName(c.first_name, c.last_name)}</p>
            </div>,
            <span key="email" className="text-slate-600 dark:text-slate-300">{c.email}</span>,
            <span key="phone" className="text-slate-600 dark:text-slate-300">{c.phone ?? "—"}</span>,
            <span key="orders">{c.total_orders}</span>,
            <span key="spent" className="font-medium text-slate-900 dark:text-slate-100">{formatMoney(c.total_spent)}</span>,
            <span key="created" className="text-xs text-slate-500 dark:text-slate-400">{formatDate(c.created_at)}</span>,
            <div key="actions" className="flex justify-end">
              {can("customers.update") && (
                <Button variant="ghost" size="sm" onClick={() => openEdit(c)}>
                  Edit
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
        title={editing ? "Edit customer" : "Add customer"}
        description={editing ? `Updating ${fullName(editing.first_name, editing.last_name)}` : "Create a new customer record"}
        onClose={() => setModalOpen(false)}
        loading={saving}
        footer={
          <Button onClick={handleSave} loading={saving}>
            {editing ? "Save changes" : "Create customer"}
          </Button>
        }
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="First name" error={formErrors.first_name}>
            <Input value={form.first_name} onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))} />
          </Field>
          <Field label="Last name" error={formErrors.last_name}>
            <Input value={form.last_name} onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))} />
          </Field>
          <div className="sm:col-span-2">
            <Field label="Email" error={formErrors.email}>
              <Input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
            </Field>
          </div>
          <div className="sm:col-span-2">
            <Field label="Phone">
              <Input value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} placeholder="+998 90 123 45 67" />
            </Field>
          </div>
          <div className="sm:col-span-2">
            <Field label="Address">
              <Textarea rows={2} value={form.address} onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))} />
            </Field>
          </div>
        </div>
      </Modal>

      <Toast message={toast} />
    </div>
  );
}