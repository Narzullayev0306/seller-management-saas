"use client";

import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { Modal, Toast } from "@/components/ui/modal";
import { Badge } from "@/components/ui/states";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api-client";
import { formatDate, formatMoney } from "@/lib/format";
import type { Order, Refund, RefundCreate, ReturnRequest } from "@/lib/types";

const RETURN_STATUS_COLORS: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800",
  approved: "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800",
  received: "bg-indigo-100 text-indigo-800 border-indigo-200 dark:bg-indigo-950/40 dark:text-indigo-300 dark:border-indigo-800",
  completed: "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
  rejected: "bg-red-100 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800",
};

const REFUND_STATUS_COLORS: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800",
  processed: "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
  failed: "bg-red-100 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800",
};

const CONDITIONS: Record<string, string> = {
  unused: "Unused",
  defective: "Defective",
  damaged: "Damaged",
  wrong_item: "Wrong item",
};

export default function RefundsPage() {
  const { can } = useAuth();
  const canUpdate = can("orders.update");

  const [returns, setReturns] = useState<ReturnRequest[] | null>(null);
  const [refunds, setRefunds] = useState<Refund[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const [refundModalOpen, setRefundModalOpen] = useState(false);
  const [orders, setOrders] = useState<Order[]>([]);
  const [refundForm, setRefundForm] = useState({ order_id: "", amount: "", reason: "", payment_id: "" });
  const [refundErrors, setRefundErrors] = useState<{ order_id?: string; amount?: string }>({});
  const [refundSaving, setRefundSaving] = useState(false);

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 3000);
  }, []);

  const load = useCallback(() => {
    setError(null);
    Promise.all([
      api.get<ReturnRequest[]>("/returns"),
      api.get<Refund[]>("/refunds"),
    ])
      .then(([r, f]) => {
        setReturns(r);
        setRefunds(f);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load refunds"));
  }, []);

  useEffect(() => {
    const t = setTimeout(() => void load(), 0);
    return () => clearTimeout(t);
  }, [load]);

  async function decideReturn(r: ReturnRequest, action: string) {
    setActionLoading(`${r.id}:${action}`);
    try {
      await api.patch(`/returns/${r.id}`, { action });
      showToast(`Return ${action}${action.endsWith("e") ? "d" : "ed"}`);
      load();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to update return");
    } finally {
      setActionLoading(null);
    }
  }

  async function actOnRefund(r: Refund, action: string) {
    setActionLoading(`${r.id}:${action}`);
    try {
      await api.patch(`/refunds/${r.id}`, { action });
      showToast(`Refund marked as ${action}${action === "process" ? "ed" : "ed"}`);
      load();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to update refund");
    } finally {
      setActionLoading(null);
    }
  }

  function openRefundModal() {
    setRefundForm({ order_id: "", amount: "", reason: "", payment_id: "" });
    setRefundErrors({});
    setRefundModalOpen(true);
    api
      .get<{ items: Order[] }>("/orders", { page: 1, page_size: 100 })
      .then((data) => setOrders(data.items))
      .catch(() => setOrders([]));
  }

  function validateRefund(): boolean {
    const next: { order_id?: string; amount?: string } = {};
    if (!refundForm.order_id) next.order_id = "Select an order";
    if (!refundForm.amount || Number.isNaN(Number(refundForm.amount)) || Number(refundForm.amount) <= 0) {
      next.amount = "Enter a valid amount";
    }
    setRefundErrors(next);
    return Object.keys(next).length === 0;
  }

  async function createRefund() {
    if (!validateRefund()) return;
    setRefundSaving(true);
    try {
      const payload: RefundCreate = {
        order_id: refundForm.order_id,
        amount: Number(refundForm.amount),
        reason: refundForm.reason.trim() || undefined,
        payment_id: refundForm.payment_id || undefined,
      };
      await api.post("/refunds", payload);
      showToast("Refund created");
      setRefundModalOpen(false);
      load();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to create refund");
    } finally {
      setRefundSaving(false);
    }
  }

  const returnsActions = (r: ReturnRequest) => {
    const actions: { action: string; label: string; danger?: boolean }[] = [];
    if (r.status === "pending") {
      actions.push({ action: "approve", label: "Approve" });
      actions.push({ action: "reject", label: "Reject", danger: true });
    } else if (r.status === "approved") {
      actions.push({ action: "receive", label: "Receive" });
    } else if (r.status === "received") {
      actions.push({ action: "complete", label: "Complete" });
    }
    return actions;
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Refunds & Returns"
        description="Review customer return requests and issue refunds."
        actions={
          canUpdate && (
            <Button onClick={openRefundModal}>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              New refund
            </Button>
          )
        }
      />

      {error && (
        <Card>
          <div className="flex flex-col items-center gap-3 px-6 py-12 text-center">
            <p className="text-sm font-medium text-slate-700">{error}</p>
            <Button variant="outline" size="sm" onClick={load}>
              Try again
            </Button>
          </div>
        </Card>
      )}

      <Card>
        <CardHeader title="Return requests" subtitle="Customer-initiated returns awaiting your decision." />
        <CardBody className="p-0">
          {!error && !returns ? (
            <div className="space-y-3 p-5">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-10 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
              ))}
            </div>
          ) : !error && returns!.length === 0 ? (
            <div className="flex flex-col items-center gap-2 px-6 py-12 text-center">
              <p className="text-sm font-semibold text-slate-700">No return requests</p>
              <p className="text-sm text-slate-500">Return requests from customers will appear here.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/60 dark:border-slate-800 dark:bg-slate-800/40">
                    {["Product", "Qty", "Condition", "Reason", "Status", "Requested", ""].map((h) => (
                      <th key={h} className="px-4 py-3 font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {returns!.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                      <td className="px-4 py-3">
                        <p className="font-medium text-slate-900 dark:text-slate-100">{r.product_name}</p>
                        <p className="text-xs text-slate-500">Order item #{r.order_item_id.slice(0, 8)}</p>
                      </td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{r.quantity}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{CONDITIONS[r.condition] ?? r.condition}</td>
                      <td className="px-4 py-3">
                        <p className="max-w-56 truncate text-slate-600 dark:text-slate-300" title={r.reason ?? ""}>
                          {r.reason ?? "—"}
                        </p>
                      </td>
                      <td className="px-4 py-3">
                        <Badge className={RETURN_STATUS_COLORS[r.status]}>{r.status}</Badge>
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">{formatDate(r.created_at)}</td>
                      <td className="px-4 py-3">
                        {canUpdate && (
                          <div className="flex justify-end gap-1">
                            {returnsActions(r).map((a) => (
                              <Button
                                key={a.action}
                                variant={a.danger ? "ghost" : "outline"}
                                size="sm"
                                loading={actionLoading === `${r.id}:${a.action}`}
                                className={a.danger ? "text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40" : ""}
                                onClick={() => void decideReturn(r, a.action)}
                              >
                                {a.label}
                              </Button>
                            ))}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Refunds" subtitle="Issued refunds, from return approvals and manual entries." />
        <CardBody className="p-0">
          {!error && !refunds ? (
            <div className="space-y-3 p-5">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-10 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
              ))}
            </div>
          ) : !error && refunds!.length === 0 ? (
            <div className="flex flex-col items-center gap-2 px-6 py-12 text-center">
              <p className="text-sm font-semibold text-slate-700">No refunds yet</p>
              <p className="text-sm text-slate-500">Refunds created from returns or manually will appear here.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/60 dark:border-slate-800 dark:bg-slate-800/40">
                    {["Order", "Amount", "Reason", "Status", "Created", "Processed", ""].map((h) => (
                      <th key={h} className="px-4 py-3 font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {refunds!.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{r.order_number || "—"}</td>
                      <td className="px-4 py-3 font-semibold text-slate-900 dark:text-slate-100">{formatMoney(r.amount)}</td>
                      <td className="px-4 py-3">
                        <p className="max-w-56 truncate text-slate-600 dark:text-slate-300" title={r.reason ?? ""}>
                          {r.reason ?? "—"}
                        </p>
                      </td>
                      <td className="px-4 py-3">
                        <Badge className={REFUND_STATUS_COLORS[r.status]}>{r.status}</Badge>
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">{formatDate(r.created_at)}</td>
                      <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">{r.processed_at ? formatDate(r.processed_at) : "—"}</td>
                      <td className="px-4 py-3">
                        {canUpdate && r.status === "pending" && (
                          <div className="flex justify-end gap-1">
                            <Button
                              variant="outline"
                              size="sm"
                              loading={actionLoading === `${r.id}:process`}
                              onClick={() => void actOnRefund(r, "process")}
                            >
                              Process
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40"
                              loading={actionLoading === `${r.id}:fail`}
                              onClick={() => void actOnRefund(r, "fail")}
                            >
                              Fail
                            </Button>
                          </div>
                        )}
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
        open={refundModalOpen}
        title="New refund"
        description="Issue a manual refund against an order"
        onClose={() => setRefundModalOpen(false)}
        loading={refundSaving}
        footer={
          <Button onClick={createRefund} loading={refundSaving}>
            Create refund
          </Button>
        }
      >
        <div className="space-y-4">
          <Field label="Order" error={refundErrors.order_id}>
            <Select
              value={refundForm.order_id}
              onChange={(e) => setRefundForm((f) => ({ ...f, order_id: e.target.value }))}
            >
              <option value="">Select an order...</option>
              {orders.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.order_number} — {o.customer_name} ({formatMoney(o.total)})
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Amount" error={refundErrors.amount}>
            <Input
              type="number"
              step="0.01"
              min="0.01"
              value={refundForm.amount}
              onChange={(e) => setRefundForm((f) => ({ ...f, amount: e.target.value }))}
              placeholder="0.00"
            />
          </Field>
          <Field label="Reason">
            <Textarea
              rows={2}
              value={refundForm.reason}
              onChange={(e) => setRefundForm((f) => ({ ...f, reason: e.target.value }))}
              placeholder="Why is this being refunded?"
            />
          </Field>
        </div>
      </Modal>

      <Toast message={toast} />
    </div>
  );
}