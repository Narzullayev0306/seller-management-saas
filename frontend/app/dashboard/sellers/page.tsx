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
import { badgeClass, formatMoney, fullName, SELLER_STATUS_COLORS } from "@/lib/format";
import type { Seller, SellerCreate, SellerStatus } from "@/lib/types";

interface FormState {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  commission_rate: string;
  status: SellerStatus;
}

const EMPTY_FORM: FormState = {
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  commission_rate: "5",
  status: "active",
};

export default function SellersPage() {
  const { can } = useAuth();
  const { data, loading, error, query, setSearch, setPage, setFilter, toggleSort, refetch } =
    useList<Seller>("/sellers", { sortBy: "created_at", sortOrder: "desc" });

  const [search, setSearchInput] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Seller | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

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

  const openEdit = (s: Seller) => {
    setEditing(s);
    setForm({
      first_name: s.first_name,
      last_name: s.last_name,
      email: s.email,
      phone: s.phone ?? "",
      commission_rate: s.commission_rate,
      status: s.status,
    });
    setFormErrors({});
    setModalOpen(true);
  };

  function validate(): boolean {
    const next: Partial<Record<keyof FormState, string>> = {};
    if (!form.first_name.trim()) next.first_name = "First name is required";
    if (!form.last_name.trim()) next.last_name = "Last name is required";
    if (!form.email.trim()) next.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) next.email = "Enter a valid email";
    const rate = parseFloat(form.commission_rate);
    if (!form.commission_rate.trim() || Number.isNaN(rate) || rate < 0 || rate > 100)
      next.commission_rate = "Commission must be 0–100%";
    setFormErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSave() {
    if (!validate()) return;
    setSaving(true);
    try {
      const payload: SellerCreate = {
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim() || undefined,
        commission_rate: parseFloat(form.commission_rate),
        status: form.status,
      };
      if (editing) {
        await api.patch(`/sellers/${editing.id}`, payload);
        showToast("Seller updated");
      } else {
        await api.post("/sellers", payload);
        showToast("Seller created");
      }
      setModalOpen(false);
      refetch();
    } catch (err) {
      setFormErrors({ email: err instanceof Error ? err.message : "Failed to save" });
    } finally {
      setSaving(false);
    }
  }

  async function handleDeactivate(seller: Seller) {
    setDeleting(seller.id);
    try {
      await api.delete(`/sellers/${seller.id}`);
      showToast("Seller deactivated");
      refetch();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to deactivate");
    } finally {
      setDeleting(null);
    }
  }

  const columns = [
    { key: "name", header: "Seller" },
    { key: "email", header: "Email" },
    { key: "commission_rate", header: "Commission" },
    { key: "total_orders", header: "Orders" },
    { key: "total_sales", header: "Total sales" },
    { key: "status", header: "Status" },
    { key: "actions", header: "" },
  ];

  return (
    <div>
      <PageHeader
        title="Sellers"
        description="Team members selling for your organization."
        actions={
          can("sellers.create") && (
            <Button onClick={openCreate}>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Add seller
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
          filters={
            <Select value={(query.status as string) ?? ""} onChange={(e) => setFilter("status", e.target.value || undefined)} className="w-36">
              <option value="">All statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="suspended">Suspended</option>
            </Select>
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
          renderMobileCard={(s) => (
            <MobileCard
              title={fullName(s.first_name, s.last_name)}
              subtitle={`${s.email} · ${s.commission_rate}% commission`}
              actions={
                <>
                  {can("sellers.update") && (
                    <Button variant="ghost" size="sm" onClick={() => openEdit(s)}>
                      Edit
                    </Button>
                  )}
                  {can("sellers.delete") && s.status === "active" && (
                    <Button variant="ghost" size="sm" loading={deleting === s.id} onClick={() => handleDeactivate(s)}>
                      Deactivate
                    </Button>
                  )}
                </>
              }
            >
              <span className="text-sm font-semibold tabular-nums">{formatMoney(s.total_sales)}</span>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {s.total_orders} order{s.total_orders === 1 ? "" : "s"}
              </span>
              <Badge className={badgeClass(SELLER_STATUS_COLORS, s.status)}>{s.status}</Badge>
            </MobileCard>
          )}
          renderRow={(s) => [
            <div key="name" className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-xs font-semibold text-emerald-700">
                {s.first_name[0] ?? ""}
                {s.last_name[0] ?? ""}
              </div>
              <p className="font-medium text-slate-900 dark:text-slate-100">{fullName(s.first_name, s.last_name)}</p>
            </div>,
            <span key="email" className="text-slate-600 dark:text-slate-300">{s.email}</span>,
            <span key="rate">{s.commission_rate}%</span>,
            <span key="orders">{s.total_orders}</span>,
            <span key="sales" className="font-medium text-slate-900 dark:text-slate-100">{formatMoney(s.total_sales)}</span>,
            <Badge key="status" className={badgeClass(SELLER_STATUS_COLORS, s.status)}>{s.status}</Badge>,
            <div key="actions" className="flex justify-end gap-1">
              {can("sellers.update") && (
                <Button variant="ghost" size="sm" onClick={() => openEdit(s)}>
                  Edit
                </Button>
              )}
              {can("sellers.delete") && s.status === "active" && (
                <Button variant="ghost" size="sm" loading={deleting === s.id} onClick={() => handleDeactivate(s)}>
                  Deactivate
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
        title={editing ? "Edit seller" : "Add seller"}
        description={editing ? `Updating ${fullName(editing.first_name, editing.last_name)}` : "Create a new seller profile"}
        onClose={() => setModalOpen(false)}
        loading={saving}
        footer={
          <Button onClick={handleSave} loading={saving}>
            {editing ? "Save changes" : "Create seller"}
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
          <Field label="Phone">
            <Input value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} placeholder="+998 90 123 45 67" />
          </Field>
          <Field label="Commission rate (%)" error={formErrors.commission_rate}>
            <Input type="number" step="0.1" min="0" max="100" value={form.commission_rate} onChange={(e) => setForm((f) => ({ ...f, commission_rate: e.target.value }))} />
          </Field>
          <div className="sm:col-span-2">
            <Field label="Status">
              <Select value={form.status} onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as SellerStatus }))}>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="suspended">Suspended</option>
              </Select>
            </Field>
          </div>
        </div>
      </Modal>

      <Toast message={toast} />
    </div>
  );
}