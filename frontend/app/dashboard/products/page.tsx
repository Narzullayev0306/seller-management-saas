"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import Image from "next/image";

import { Badge } from "@/components/ui/states";
import { PageHeader } from "@/components/page-header";
import { Toolbar } from "@/components/page-header";
import { DataTable } from "@/components/ui/table";
import { Pagination } from "@/components/ui/table";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { Toast } from "@/components/ui/modal";
import { useAuth } from "@/lib/auth";
import { useList } from "@/lib/use-list";
import { api } from "@/lib/api-client";
import { badgeClass, formatMoney, STOCK_STATUS_COLORS } from "@/lib/format";
import type { Product, ProductCreate, ProductUpdate } from "@/lib/types";

interface FormState {
  name: string;
  sku: string;
  category: string;
  description: string;
  price: string;
  cost_price: string;
  stock_quantity: string;
  low_stock_threshold: string;
  status: "active" | "inactive";
  image_url: string;
}

const EMPTY_FORM: FormState = {
  name: "",
  sku: "",
  category: "",
  description: "",
  price: "",
  cost_price: "",
  stock_quantity: "",
  low_stock_threshold: "5",
  status: "active",
  image_url: "",
};

export default function ProductsPage() {
  const { can } = useAuth();
  const { data, loading, error, query, setSearch, setPage, setFilter, toggleSort, refetch } =
    useList<Product>("/products", { sortBy: "created_at", sortOrder: "desc" });

  const [search, setSearchInput] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Product | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const openEdit = (product: Product) => {
    setEditing(product);
    setForm({
      name: product.name,
      sku: product.sku,
      category: product.category,
      description: product.description ?? "",
      price: product.price,
      cost_price: product.cost_price,
      stock_quantity: String(product.stock_quantity),
      low_stock_threshold: String(product.low_stock_threshold),
      status: product.status,
      image_url: product.image_url ?? "",
    });
    setFormErrors({});
    setModalOpen(true);
  };

  function validate(): boolean {
    const next: Partial<Record<keyof FormState, string>> = {};
    if (!form.name.trim()) next.name = "Name is required";
    if (!form.sku.trim()) next.sku = "SKU is required";
    if (!form.category.trim()) next.category = "Category is required";
    if (!form.price.trim() || Number.isNaN(parseFloat(form.price)) || parseFloat(form.price) < 0)
      next.price = "Enter a valid price";
    if (!form.stock_quantity.trim() || !/^\d+$/.test(form.stock_quantity.trim()))
      next.stock_quantity = "Stock must be a whole number";
    if (!form.low_stock_threshold.trim() || !/^\d+$/.test(form.low_stock_threshold.trim()))
      next.low_stock_threshold = "Must be a whole number";
    setFormErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSave() {
    if (!validate()) return;
    setSaving(true);
    try {
      const payload: ProductCreate | ProductUpdate = {
        name: form.name.trim(),
        sku: form.sku.trim(),
        category: form.category.trim(),
        description: form.description.trim() || undefined,
        price: parseFloat(form.price),
        cost_price: parseFloat(form.cost_price) || 0,
        stock_quantity: parseInt(form.stock_quantity, 10),
        low_stock_threshold: parseInt(form.low_stock_threshold, 10),
        status: form.status,
        image_url: form.image_url || undefined,
      };
      if (editing) {
        await api.patch(`/products/${editing.id}`, payload);
        showToast("Product updated");
      } else {
        await api.post("/products", payload);
        showToast("Product created");
      }
      setModalOpen(false);
      refetch();
    } catch (err) {
      setFormErrors({ name: err instanceof Error ? err.message : "Failed to save" });
    } finally {
      setSaving(false);
    }
  }

  async function handleImageUpload(file: File) {
    if (!file.type.startsWith("image/")) {
      setUploadError("Please choose an image file");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setUploadError("Image must be under 5 MB");
      return;
    }
    setUploading(true);
    setUploadError(null);
    try {
      const { url, public_url } = await api.post<{ url: string; public_url: string }>(
        "/uploads/signed-url",
        { bucket: "products", content_type: file.type, filename: file.name },
      );
      const resp = await fetch(url, {
        method: "PUT",
        headers: { "x-upsert": "true", "Content-Type": file.type },
        body: file,
      });
      if (!resp.ok) throw new Error(`Upload failed (${resp.status})`);
      setForm((f) => ({ ...f, image_url: public_url }));
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleDeactivate(product: Product) {
    setDeleting(product.id);
    try {
      await api.delete(`/products/${product.id}`);
      showToast("Product deactivated");
      refetch();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to deactivate");
    } finally {
      setDeleting(null);
    }
  }

  const debouncedSearch = useCallback(
    (value: string) => {
      setSearchInput(value);
      const t = window.setTimeout(() => setSearch(value), 350);
      return () => window.clearTimeout(t);
    },
    [setSearch],
  );

  const categories = useMemo(
    () => Array.from(new Set((data?.items ?? []).map((p) => p.category))).sort(),
    [data],
  );

  const columns = [
    { key: "name", header: "Product" },
    { key: "sku", header: "SKU" },
    { key: "category", header: "Category" },
    { key: "price", header: "Price" },
    { key: "stock_quantity", header: "Stock" },
    { key: "stock_status", header: "Status" },
    { key: "actions", header: "" },
  ];

  return (
    <div>
      <PageHeader
        title="Products"
        description="Manage your product catalog and pricing."
        actions={
          can("products.create") && (
            <Button onClick={openCreate}>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Add product
            </Button>
          )
        }
      />

      <Card>
        <Toolbar
          search={search}
          onSearch={debouncedSearch}
          placeholder="Search by name or SKU..."
          filters={
            <>
              <Select value={(query.category as string) ?? ""} onChange={(e) => setFilter("category", e.target.value || undefined)} className="w-40">
                <option value="">All categories</option>
                {categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </Select>
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
          columns={columns}
          rows={data?.items ?? []}
          loading={loading}
          error={error}
          onRetry={refetch}
          onSort={toggleSort}
          sortBy={query.sort_by as string}
          sortOrder={query.sort_order as "asc" | "desc"}
          renderRow={(p) => [
            <div key="name">
              <p className="font-medium text-slate-900 dark:text-slate-100">{p.name}</p>
              {p.description && <p className="mt-0.5 line-clamp-1 text-xs text-slate-400 dark:text-slate-500">{p.description}</p>}
            </div>,
            <span key="sku" className="font-mono text-xs text-slate-500 dark:text-slate-400">{p.sku}</span>,
            <Badge key="cat" className="bg-slate-100 text-slate-600 border-slate-200">{p.category}</Badge>,
            <span key="price" className="font-medium">{formatMoney(p.price)}</span>,
            <span key="stock" className={p.stock_quantity <= p.low_stock_threshold ? "font-medium text-amber-600" : ""}>
              {p.stock_quantity}
            </span>,
            <Badge key="status" className={badgeClass(STOCK_STATUS_COLORS, p.stock_status)}>{p.stock_status.replace("_", " ")}</Badge>,
            <div key="actions" className="flex justify-end gap-1">
              {can("products.update") && (
                <Button variant="ghost" size="sm" onClick={() => openEdit(p)}>
                  Edit
                </Button>
              )}
              {can("products.delete") && p.status === "active" && (
                <Button variant="ghost" size="sm" loading={deleting === p.id} onClick={() => handleDeactivate(p)}>
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
        title={editing ? "Edit product" : "Add product"}
        description={editing ? `Updating ${editing.name}` : "Create a new catalog item"}
        onClose={() => setModalOpen(false)}
        loading={saving}
        footer={
          <Button onClick={handleSave} loading={saving}>
            {editing ? "Save changes" : "Create product"}
          </Button>
        }
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <Field label="Name" error={formErrors.name}>
              <Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder="Wireless Mouse" />
            </Field>
          </div>
          <Field label="SKU" error={formErrors.sku}>
            <Input value={form.sku} onChange={(e) => setForm((f) => ({ ...f, sku: e.target.value }))} placeholder="WM-001" />
          </Field>
          <Field label="Category" error={formErrors.category}>
            <Input value={form.category} onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))} placeholder="Electronics" />
          </Field>
          <div className="sm:col-span-2">
            <Field label="Product image">
              <div className="flex items-center gap-3">
                {form.image_url ? (
                  <Image
                    src={form.image_url}
                    alt="Product preview"
                    width={64}
                    height={64}
                    className="h-16 w-16 rounded-xl border border-slate-200 object-cover dark:border-slate-700"
                  />
                ) : (
                  <div className="flex h-16 w-16 items-center justify-center rounded-xl border border-dashed border-slate-300 text-slate-400 dark:border-slate-700">
                    <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="3" width="18" height="18" rx="2" />
                      <circle cx="9" cy="9" r="2" />
                      <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
                    </svg>
                  </div>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) void handleImageUpload(file);
                    e.target.value = "";
                  }}
                />
                <div className="flex flex-col gap-1.5">
                  <Button variant="outline" onClick={() => fileInputRef.current?.click()} disabled={uploading || saving}>
                    {uploading ? "Uploading…" : form.image_url ? "Replace image" : "Upload image"}
                  </Button>
                  {form.image_url && (
                    <button
                      type="button"
                      onClick={() => setForm((f) => ({ ...f, image_url: "" }))}
                      className="text-left text-xs font-medium text-slate-500 transition hover:text-red-600 dark:text-slate-400 dark:hover:text-red-400"
                    >
                      Remove image
                    </button>
                  )}
                </div>
              </div>
              {uploadError && <p className="mt-1.5 text-xs font-medium text-red-600 dark:text-red-400">{uploadError}</p>}
            </Field>
          </div>
          <div className="sm:col-span-2">
            <Field label="Description">
              <Textarea rows={2} value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} placeholder="Optional description" />
            </Field>
          </div>
          <Field label="Price (USD)" error={formErrors.price}>
            <Input type="number" step="0.01" min="0" value={form.price} onChange={(e) => setForm((f) => ({ ...f, price: e.target.value }))} placeholder="29.99" />
          </Field>
          <Field label="Cost price (USD)">
            <Input type="number" step="0.01" min="0" value={form.cost_price} onChange={(e) => setForm((f) => ({ ...f, cost_price: e.target.value }))} placeholder="15.00" />
          </Field>
          <Field label="Stock quantity" error={formErrors.stock_quantity}>
            <Input type="number" min="0" value={form.stock_quantity} onChange={(e) => setForm((f) => ({ ...f, stock_quantity: e.target.value }))} placeholder="100" />
          </Field>
          <Field label="Low stock threshold" error={formErrors.low_stock_threshold}>
            <Input type="number" min="0" value={form.low_stock_threshold} onChange={(e) => setForm((f) => ({ ...f, low_stock_threshold: e.target.value }))} placeholder="5" />
          </Field>
          <div className="sm:col-span-2">
            <Field label="Status">
              <Select value={form.status} onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as "active" | "inactive" }))}>
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