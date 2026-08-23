"use client";

import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Card, CardHeader, CardBody } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { Modal, Toast } from "@/components/ui/modal";
import { Badge, PageLoading } from "@/components/ui/states";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api-client";
import { formatDate } from "@/lib/format";
import type { Category, CategoryCreate, CategoryTreeNode } from "@/lib/types";

interface FormState {
  name: string;
  slug: string;
  parent_id: string;
  description: string;
  sort_order: number;
  is_active: boolean;
}

const EMPTY_FORM: FormState = { name: "", slug: "", parent_id: "", description: "", sort_order: 0, is_active: true };

function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-");
}

export default function CategoriesPage() {
  const { can } = useAuth();
  const [tree, setTree] = useState<CategoryTreeNode[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Category | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 3000);
  }, []);

  const fetchTree = useCallback(() => {
    setLoading(true);
    api
      .get<CategoryTreeNode[]>("/categories/tree")
      .then((data) => {
        setTree(data);
        setError(null);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load categories");
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchTree();
  }, [fetchTree]);

  const flatten = (nodes: CategoryTreeNode[]): Category[] => {
    const out: Category[] = [];
    for (const node of nodes) {
      out.push(node);
      out.push(...flatten(node.children));
    }
    return out;
  };

  const categories = tree ? flatten(tree) : [];

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormErrors({});
    setModalOpen(true);
  };

  const openEdit = (c: Category) => {
    setEditing(c);
    setForm({
      name: c.name,
      slug: c.slug,
      parent_id: c.parent_id ?? "",
      description: c.description ?? "",
      sort_order: c.sort_order,
      is_active: c.is_active,
    });
    setFormErrors({});
    setModalOpen(true);
  };

  function validate(): boolean {
    const next: Partial<Record<keyof FormState, string>> = {};
    if (!form.name.trim()) next.name = "Name is required";
    if (form.slug.trim() && !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(form.slug.trim())) next.slug = "Lowercase letters, numbers and dashes only";
    setFormErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSave() {
    if (!validate()) return;
    setSaving(true);
    try {
      const payload: CategoryCreate = {
        name: form.name.trim(),
        slug: form.slug.trim() || undefined,
        parent_id: form.parent_id || undefined,
        description: form.description.trim() || undefined,
        sort_order: form.sort_order,
        is_active: form.is_active,
      };
      if (editing) {
        await api.patch(`/categories/${editing.id}`, payload);
        showToast("Category updated");
      } else {
        await api.post("/categories", payload);
        showToast("Category created");
      }
      setModalOpen(false);
      fetchTree();
    } catch (err) {
      setFormErrors({ name: err instanceof Error ? err.message : "Failed to save category" });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(c: Category) {
    if (!window.confirm(`Delete category "${c.name}"? Categories with children or products cannot be deleted.`)) return;
    try {
      await api.delete(`/categories/${c.id}`);
      showToast("Category deleted");
      fetchTree();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to delete category");
    }
  }

  const parentName = (id: string | null) => categories.find((c) => c.id === id)?.name ?? "—";
  const eligibleParents = editing ? categories.filter((c) => c.id !== editing.id) : categories;

  return (
    <div>
      <PageHeader
        title="Categories"
        description="Organize your catalog with a nested category tree."
        actions={
          can("products.create") && (
            <Button onClick={openCreate}>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Add category
            </Button>
          )
        }
      />

      <Card>
        <CardHeader title={`${categories.length} categories`} subtitle="Nested categories appear with product counts." />
        <CardBody className="p-0">
          {loading ? (
            <PageLoading label="Loading categories" />
          ) : error ? (
            <div className="flex flex-col items-center gap-3 px-6 py-14 text-center">
              <p className="text-sm font-semibold text-slate-700">{error}</p>
              <Button variant="outline" size="sm" onClick={fetchTree}>
                Try again
              </Button>
            </div>
          ) : categories.length === 0 ? (
            <div className="flex flex-col items-center gap-3 px-6 py-14 text-center">
              <p className="text-sm font-semibold text-slate-700">No categories yet</p>
              <p className="text-sm text-slate-500">Create your first category to start organizing products.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/60 dark:border-slate-800 dark:bg-slate-800/40">
                    {["Category", "Parent", "Products", "Slug", "Status", "Added", ""].map((h) => (
                      <th key={h} className="px-4 py-3 font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {categories.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                      <td className="px-4 py-3">
                        <p className="font-medium text-slate-900 dark:text-slate-100">{c.name}</p>
                        {c.description && <p className="max-w-72 truncate text-xs text-slate-500" title={c.description}>{c.description}</p>}
                      </td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{parentName(c.parent_id)}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{c.product_count}</td>
                      <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">{c.slug}</td>
                      <td className="px-4 py-3">
                        <Badge className={c.is_active ? "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800" : "bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700"}>
                          {c.is_active ? "active" : "inactive"}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">{formatDate(c.created_at)}</td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-1">
                          {can("products.update") && (
                            <Button variant="ghost" size="sm" onClick={() => openEdit(c)}>
                              Edit
                            </Button>
                          )}
                          {can("products.delete") && (
                            <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40" onClick={() => void handleDelete(c)}>
                              Delete
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      <Modal
        open={modalOpen}
        title={editing ? "Edit category" : "Add category"}
        description={editing ? `Updating ${editing.name}` : "Create a new category"}
        onClose={() => setModalOpen(false)}
        loading={saving}
        footer={
          <Button onClick={handleSave} loading={saving}>
            {editing ? "Save changes" : "Create category"}
          </Button>
        }
      >
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Name" error={formErrors.name}>
              <Input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value, slug: f.slug || slugify(e.target.value) }))}
                placeholder="Electronics"
              />
            </Field>
            <Field label="Slug" error={formErrors.slug} hint="Auto-generated from name. Lowercase letters, numbers and dashes.">
              <Input value={form.slug} onChange={(e) => setForm((f) => ({ ...f, slug: e.target.value }))} placeholder="electronics" />
            </Field>
          </div>
          <Field label="Parent category">
            <Select value={form.parent_id} onChange={(e) => setForm((f) => ({ ...f, parent_id: e.target.value }))}>
              <option value="">None (top level)</option>
              {eligibleParents.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Description">
            <Textarea rows={2} value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
          </Field>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Sort order">
              <Input
                type="number"
                min={0}
                value={form.sort_order}
                onChange={(e) => setForm((f) => ({ ...f, sort_order: Number(e.target.value) || 0 }))}
              />
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