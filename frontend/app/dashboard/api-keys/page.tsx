"use client";

import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { Modal, Toast } from "@/components/ui/modal";
import { Badge } from "@/components/ui/states";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api-client";
import { formatDate } from "@/lib/format";
import type { ApiKey, ApiKeyCreate, ApiKeyWithSecret } from "@/lib/types";

const SCOPES = [
  "dashboard.read",
  "users.read",
  "users.create",
  "users.update",
  "users.delete",
  "sellers.read",
  "sellers.create",
  "sellers.update",
  "sellers.delete",
  "products.read",
  "products.create",
  "products.update",
  "products.delete",
  "customers.read",
  "customers.create",
  "customers.update",
  "customers.delete",
  "orders.read",
  "orders.create",
  "orders.update",
  "orders.delete",
  "inventory.read",
  "inventory.update",
  "analytics.read",
  "audit.read",
  "notifications.read",
  "suppliers.read",
  "suppliers.create",
  "suppliers.update",
  "suppliers.delete",
  "coupons.read",
  "coupons.create",
  "coupons.update",
  "coupons.delete",
  "settings.read",
  "settings.update",
];

interface FormState {
  name: string;
  scopes: string[];
  expires_at: string;
}

const EMPTY_FORM: FormState = { name: "", scopes: [], expires_at: "" };

export default function ApiKeysPage() {
  const { can, user } = useAuth();
  const canUpdate = can("settings.update");

  const [keys, setKeys] = useState<ApiKey[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [saving, setSaving] = useState(false);
  const [createdKey, setCreatedKey] = useState<ApiKeyWithSecret | null>(null);
  const [copied, setCopied] = useState(false);
  const [toggling, setToggling] = useState<string | null>(null);
  const [now, setNow] = useState(() => Date.now());

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 3000);
  }, []);

  const load = useCallback(() => {
    setError(null);
    api
      .get<ApiKey[]>("/api-keys")
      .then(setKeys)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load API keys"));
  }, []);

  useEffect(() => {
    const t = setTimeout(() => void load(), 0);
    return () => clearTimeout(t);
  }, [load]);

  useEffect(() => {
    if (!keys) return;
    const t = setTimeout(() => setNow(Date.now()), 0);
    return () => clearTimeout(t);
  }, [keys]);

  const availableScopes = user?.permissions.length ? SCOPES.filter((s) => user.permissions.includes(s)) : SCOPES;

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setFormErrors({});
    setCreatedKey(null);
    setModalOpen(true);
  };

  function toggleScope(scope: string) {
    setForm((f) => ({
      ...f,
      scopes: f.scopes.includes(scope) ? f.scopes.filter((s) => s !== scope) : [...f.scopes, scope],
    }));
  }

  function validate(): boolean {
    const next: Partial<Record<keyof FormState, string>> = {};
    if (!form.name.trim()) next.name = "Name is required";
    if (form.scopes.length === 0) next.scopes = "Select at least one scope";
    setFormErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleCreate() {
    if (!validate()) return;
    setSaving(true);
    try {
      const payload: ApiKeyCreate = {
        name: form.name.trim(),
        scopes: form.scopes,
        expires_at: form.expires_at ? new Date(form.expires_at).toISOString() : undefined,
      };
      const created = await api.post<ApiKeyWithSecret>("/api-keys", payload);
      setCreatedKey(created);
      showToast("API key created");
      setModalOpen(false);
      load();
    } catch (err) {
      setFormErrors({ name: err instanceof Error ? err.message : "Failed to create API key" });
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(key: ApiKey) {
    setToggling(key.id);
    try {
      await api.patch(`/api-keys/${key.id}`, { is_active: !key.is_active });
      showToast(key.is_active ? "API key revoked" : "API key activated");
      load();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to update API key");
    } finally {
      setToggling(null);
    }
  }

  async function handleDelete(key: ApiKey) {
    if (!window.confirm(`Delete API key "${key.name}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/api-keys/${key.id}`);
      showToast("API key deleted");
      load();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to delete API key");
    }
  }

  function copyKey() {
    if (!createdKey) return;
    void navigator.clipboard?.writeText(createdKey.key).then(() => {
      setCopied(true);
      showToast("Key copied to clipboard");
      window.setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div>
      <PageHeader
        title="API Keys"
        description="Programmatic access for integrations. Keys are shown only once."
        actions={
          canUpdate && (
            <Button onClick={openCreate}>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Create key
            </Button>
          )
        }
      />

      <Card>
        <div className="overflow-x-auto">
          {!error && !keys ? (
            <div className="space-y-3 p-5">
              {Array.from({ length: 4 }).map((_, i) => (
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
          ) : keys!.length === 0 ? (
            <div className="flex flex-col items-center gap-2 px-6 py-14 text-center">
              <p className="text-sm font-semibold text-slate-700">No API keys</p>
              <p className="text-sm text-slate-500">Create a key to let external services talk to your API.</p>
            </div>
          ) : (
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/60 dark:border-slate-800 dark:bg-slate-800/40">
                  {["Name", "Key", "Scopes", "Status", "Expires", "Last used", ""].map((h) => (
                    <th key={h} className="px-4 py-3 font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {keys!.map((k) => {
                  const expired = k.expires_at !== null && new Date(k.expires_at).getTime() < now;
                  return (
                    <tr key={k.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{k.name}</td>
                      <td className="px-4 py-3">
                        <span className="font-mono text-xs text-slate-500">{k.prefix}…</span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex max-w-56 flex-wrap gap-1">
                          {k.scopes.map((s) => (
                            <span key={s} className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px] font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                              {s}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          className={
                            expired
                              ? "bg-red-100 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800"
                              : k.is_active
                                ? "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800"
                                : "bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700"
                          }
                        >
                          {expired ? "expired" : k.is_active ? "active" : "revoked"}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">
                        {k.expires_at ? formatDate(k.expires_at) : "Never"}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">
                        {k.last_used_at ? formatDate(k.last_used_at) : "Never"}
                      </td>
                      <td className="px-4 py-3">
                        {canUpdate && (
                          <div className="flex justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              loading={toggling === k.id}
                              onClick={() => void toggleActive(k)}
                            >
                              {k.is_active ? "Revoke" : "Activate"}
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40"
                              onClick={() => void handleDelete(k)}
                            >
                              Delete
                            </Button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </Card>

      <Modal
        open={modalOpen}
        title="Create API key"
        description="Choose which permissions the key should have"
        onClose={() => setModalOpen(false)}
        loading={saving}
        footer={
          <Button onClick={handleCreate} loading={saving}>
            Create key
          </Button>
        }
      >
        <div className="space-y-4">
          <Field label="Name" error={formErrors.name}>
            <Input
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="Production integration"
            />
          </Field>
          <Field label="Scopes" error={formErrors.scopes}>
            <div className="max-h-56 space-y-1.5 overflow-y-auto rounded-lg border border-slate-200 p-3 dark:border-slate-700">
              {availableScopes.map((scope) => (
                <label
                  key={scope}
                  className={`flex cursor-pointer items-center gap-2 rounded-md px-2 py-1 text-sm transition ${
                    form.scopes.includes(scope) ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300" : "text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                  }`}
                >
                  <input
                    type="checkbox"
                    className="h-4 w-4 accent-indigo-600"
                    checked={form.scopes.includes(scope)}
                    onChange={() => toggleScope(scope)}
                  />
                  <span className="font-mono text-xs">{scope}</span>
                </label>
              ))}
            </div>
          </Field>
          <Field label="Expires at" hint="Leave empty for a key that never expires.">
            <Input
              type="date"
              value={form.expires_at}
              onChange={(e) => setForm((f) => ({ ...f, expires_at: e.target.value }))}
            />
          </Field>
        </div>
      </Modal>

      <Modal
        open={createdKey !== null}
        title="API key created"
        onClose={() => {
          setCreatedKey(null);
          setCopied(false);
        }}
        footer={
          <Button onClick={copyKey} variant={copied ? "success" : "outline"} className="transition-colors duration-150">
            {copied && (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden>
                <path d="M20 6L9 17l-5-5" />
              </svg>
            )}
            {copied ? "Copied" : "Copy key"}
          </Button>
        }
      >
        {createdKey && (
          <div className="space-y-3">
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 dark:border-emerald-800 dark:bg-emerald-950/40">
              <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">Your key (shown once)</p>
              <p className="mt-1 break-all font-mono text-xs text-emerald-700 dark:text-emerald-400">{createdKey.key}</p>
              <p className="mt-1 text-xs text-emerald-600 dark:text-emerald-500">
                Send it as <span className="font-mono">Authorization: Bearer smk_...</span> — it cannot be retrieved again.
              </p>
            </div>
            <p className="text-xs text-slate-500">
              Usage example: <span className="font-mono">GET /api/v1/public/products</span> with the key as Bearer token.
            </p>
          </div>
        )}
      </Modal>

      <Toast message={toast} />
    </div>
  );
}