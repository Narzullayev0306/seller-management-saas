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
import { formatDate, formatRelative } from "@/lib/format";
import type { Webhook, WebhookCreate, WebhookDelivery, WebhookUpdate } from "@/lib/types";

const EVENTS = [
  "order.created",
  "order.cancelled",
  "order.status_changed",
  "product.created",
  "product.updated",
  "stock.low",
  "inventory.restocked",
];

interface FormState {
  name: string;
  url: string;
  events: string[];
  is_active: boolean;
}

const EMPTY_FORM: FormState = { name: "", url: "", events: [], is_active: true };

export default function WebhooksPage() {
  const { can } = useAuth();
  const canUpdate = can("settings.update");

  const [hooks, setHooks] = useState<Webhook[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Webhook | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [saving, setSaving] = useState(false);
  const [createdSecret, setCreatedSecret] = useState<string | null>(null);

  const [deliveriesOpen, setDeliveriesOpen] = useState(false);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[] | null>(null);
  const [deliveriesTitle, setDeliveriesTitle] = useState("");
  const [testing, setTesting] = useState<string | null>(null);

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 3000);
  }, []);

  const load = useCallback(() => {
    setError(null);
    api
      .get<Webhook[]>("/webhooks")
      .then(setHooks)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load webhooks"));
  }, []);

  useEffect(() => {
    const t = setTimeout(() => void load(), 0);
    return () => clearTimeout(t);
  }, [load]);

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormErrors({});
    setCreatedSecret(null);
    setModalOpen(true);
  };

  const openEdit = (w: Webhook) => {
    setEditing(w);
    setForm({ name: w.name, url: w.url, events: w.events, is_active: w.is_active });
    setFormErrors({});
    setCreatedSecret(null);
    setModalOpen(true);
  };

  function toggleEvent(event: string) {
    setForm((f) => ({
      ...f,
      events: f.events.includes(event) ? f.events.filter((e) => e !== event) : [...f.events, event],
    }));
  }

  function validate(): boolean {
    const next: Partial<Record<keyof FormState, string>> = {};
    if (!form.name.trim()) next.name = "Name is required";
    if (!form.url.trim()) next.url = "Endpoint URL is required";
    else if (!/^https?:\/\//.test(form.url.trim())) next.url = "URL must start with http:// or https://";
    if (form.events.length === 0) next.events = "Select at least one event";
    setFormErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSave() {
    if (!validate()) return;
    setSaving(true);
    try {
      const payload: WebhookCreate = {
        name: form.name.trim(),
        url: form.url.trim(),
        events: form.events,
        is_active: form.is_active,
      };
      if (editing) {
        const update: WebhookUpdate = payload;
        await api.patch(`/webhooks/${editing.id}`, update);
        showToast("Webhook updated");
      } else {
        const created = await api.post<Webhook>("/webhooks", payload);
        setCreatedSecret(created.secret);
        showToast("Webhook created");
      }
      setModalOpen(false);
      load();
    } catch (err) {
      setFormErrors({ name: err instanceof Error ? err.message : "Failed to save webhook" });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(w: Webhook) {
    if (!window.confirm(`Delete webhook "${w.name}"?`)) return;
    try {
      await api.delete(`/webhooks/${w.id}`);
      showToast("Webhook deleted");
      load();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to delete webhook");
    }
  }

  async function testWebhook(w: Webhook) {
    setTesting(w.id);
    try {
      const result = await api.post<{ ok: boolean; response_status: number | null; response_body: string | null; error: string | null }>(
        `/webhooks/${w.id}/test`,
      );
      if (result.ok) showToast("Test ping delivered successfully");
      else showToast(result.error ?? `Test failed (HTTP ${result.response_status ?? "?"})`);
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to send test ping");
    } finally {
      setTesting(null);
    }
  }

  async function openDeliveries(w: Webhook) {
    setDeliveriesOpen(true);
    setDeliveries(null);
    setDeliveriesTitle(`${w.name} — deliveries`);
    try {
      setDeliveries(await api.get<WebhookDelivery[]>(`/webhooks/${w.id}/deliveries`));
    } catch (err) {
      setDeliveries([]);
      showToast(err instanceof Error ? err.message : "Failed to load deliveries");
    }
  }

  return (
    <div>
      <PageHeader
        title="Webhooks"
        description="Notify external services when events happen in your store."
        actions={
          canUpdate && (
            <Button onClick={openCreate}>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Add webhook
            </Button>
          )
        }
      />

      <Card>
        <div className="overflow-x-auto">
          {!error && !hooks ? (
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
          ) : hooks!.length === 0 ? (
            <div className="flex flex-col items-center gap-2 px-6 py-14 text-center">
              <p className="text-sm font-semibold text-slate-700">No webhooks</p>
              <p className="text-sm text-slate-500">Create a webhook to receive event payloads on your endpoint.</p>
            </div>
          ) : (
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/60 dark:border-slate-800 dark:bg-slate-800/40">
                  {["Name", "Endpoint", "Events", "Status", "Last delivery", ""].map((h) => (
                    <th key={h} className="px-4 py-3 font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {hooks!.map((w) => (
                  <tr key={w.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-900 dark:text-slate-100">{w.name}</p>
                      <p className="text-xs text-slate-500">Secret: {w.secret}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="max-w-64 truncate text-slate-600 dark:text-slate-300" title={w.url}>
                        {w.url}
                      </p>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex max-w-64 flex-wrap gap-1">
                        {w.events.map((e) => (
                          <span key={e} className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px] font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                            {e}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge
                        className={
                          w.is_active
                            ? "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800"
                            : "bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700"
                        }
                      >
                        {w.is_active ? "active" : "inactive"}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">
                      {w.last_delivered_at ? formatRelative(w.last_delivered_at) : "Never"}
                    </td>
                    <td className="px-4 py-3">
                      {canUpdate && (
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="sm" loading={testing === w.id} onClick={() => void testWebhook(w)}>
                            Test
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => void openDeliveries(w)}>
                            Deliveries
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => openEdit(w)}>
                            Edit
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40"
                            onClick={() => void handleDelete(w)}
                          >
                            Delete
                          </Button>
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
        title={editing ? "Edit webhook" : "Add webhook"}
        description={editing ? `Updating ${editing.name}` : "Configure an endpoint to receive events"}
        onClose={() => setModalOpen(false)}
        loading={saving}
        footer={
          <Button onClick={handleSave} loading={saving}>
            {editing ? "Save changes" : "Create webhook"}
          </Button>
        }
      >
        <div className="space-y-4">
          {createdSecret && (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 dark:border-emerald-800 dark:bg-emerald-950/40">
              <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">Signing secret (shown once)</p>
              <p className="mt-1 break-all font-mono text-xs text-emerald-700 dark:text-emerald-400">{createdSecret}</p>
              <p className="mt-1 text-xs text-emerald-600 dark:text-emerald-500">
                Use it to verify the X-Webhook-Signature header. It cannot be retrieved again.
              </p>
            </div>
          )}
          <Field label="Name" error={formErrors.name}>
            <Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder="Order notifications" />
          </Field>
          <Field label="Endpoint URL" error={formErrors.url}>
            <Input
              value={form.url}
              onChange={(e) => setForm((f) => ({ ...f, url: e.target.value }))}
              placeholder="https://example.com/hooks/orders"
            />
          </Field>
          <Field label="Events" error={formErrors.events}>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {EVENTS.map((event) => (
                <label
                  key={event}
                  className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm transition ${
                    form.events.includes(event)
                      ? "border-indigo-500 bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300"
                      : "border-slate-200 text-slate-600 hover:border-slate-300 dark:border-slate-700 dark:text-slate-300"
                  }`}
                >
                  <input
                    type="checkbox"
                    className="h-4 w-4 accent-indigo-600"
                    checked={form.events.includes(event)}
                    onChange={() => toggleEvent(event)}
                  />
                  <span className="font-mono text-xs">{event}</span>
                </label>
              ))}
            </div>
          </Field>
          <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input
              type="checkbox"
              className="h-4 w-4 accent-indigo-600"
              checked={form.is_active}
              onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
            />
            Active (deliveries are sent immediately)
          </label>
        </div>
      </Modal>

      <Modal
        open={deliveriesOpen}
        title={deliveriesTitle}
        onClose={() => setDeliveriesOpen(false)}
      >
        {!deliveries ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
            ))}
          </div>
        ) : deliveries.length === 0 ? (
          <p className="py-6 text-center text-sm text-slate-500">No deliveries recorded yet.</p>
        ) : (
          <div className="max-h-96 space-y-2 overflow-y-auto">
            {deliveries.map((d) => (
              <div key={d.id} className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-mono text-xs font-medium text-slate-900 dark:text-slate-100">{d.event_type}</p>
                  <Badge
                    className={
                      d.error || (d.response_status ?? 0) >= 400
                        ? "bg-red-100 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800"
                        : "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800"
                    }
                  >
                    {d.error ? "error" : d.response_status ?? "sent"}
                  </Badge>
                </div>
                <p className="mt-1 text-xs text-slate-500">{formatDate(d.created_at)}</p>
                {(d.error || d.response_body) && (
                  <p className="mt-1 line-clamp-2 break-all font-mono text-[11px] text-slate-500">
                    {d.error ?? d.response_body}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </Modal>

      <Toast message={toast} />
    </div>
  );
}