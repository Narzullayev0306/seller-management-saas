"use client";

import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { ConfirmDialog, Modal, Toast } from "@/components/ui/modal";
import { Badge } from "@/components/ui/states";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api-client";
import { badgeClass, formatDate, formatMoney } from "@/lib/format";
import type { BillingSummary, Invoice, OrganizationDomain, Plan } from "@/lib/types";

const PLAN_STATUS_COLORS: Record<string, string> = {
  paid: "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
  pending: "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800",
  failed: "bg-red-100 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800",
};

const DOMAIN_STATUS_COLORS: Record<string, string> = {
  verified: "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
  pending: "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800",
};

const FEATURE_LABELS: Record<string, string> = {
  webhooks: "Webhooks",
  api_keys: "API keys",
  custom_domain: "Custom domain",
  advanced_analytics: "Advanced analytics",
  export: "Data export",
  priority_support: "Priority support",
};

function UsageBar({ label, used, limit }: { label: string; used: number; limit: number | null }) {
  const pct = limit && limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 100;
  const nearLimit = limit !== null && pct >= 80;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="text-slate-600 dark:text-slate-300">{label}</span>
        <span className={nearLimit ? "font-medium text-amber-600 dark:text-amber-400" : "text-slate-500 dark:text-slate-400"}>
          {limit === null ? `${used.toLocaleString()} / unlimited` : `${used.toLocaleString()} / ${limit.toLocaleString()}`}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
        <div
          className={`h-full rounded-full transition-all ${nearLimit ? "bg-amber-500" : "bg-indigo-600"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function BillingPage() {
  const { user } = useAuth();
  const isOwner = user?.roles?.some((r) => r.code === "owner") ?? false;

  const [plans, setPlans] = useState<Plan[]>([]);
  const [summary, setSummary] = useState<BillingSummary | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [domains, setDomains] = useState<OrganizationDomain[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [changingPlan, setChangingPlan] = useState<string | null>(null);
  const [confirmPlan, setConfirmPlan] = useState<Plan | null>(null);

  const [domainInput, setDomainInput] = useState("");
  const [addingDomain, setAddingDomain] = useState(false);
  const [domainModal, setDomainModal] = useState<OrganizationDomain | null>(null);
  const [verifyToken, setVerifyToken] = useState("");
  const [verifying, setVerifying] = useState(false);
  const [deletingDomain, setDeletingDomain] = useState<OrganizationDomain | null>(null);

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 3000);
  }, []);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [p, s, i, d] = await Promise.all([
        api.get<Plan[]>("/billing/plans"),
        api.get<BillingSummary>("/billing/summary"),
        api.get<Invoice[]>("/billing/invoices"),
        api.get<OrganizationDomain[]>("/domains").catch(() => [] as OrganizationDomain[]),
      ]);
      setPlans(p);
      setSummary(s);
      setInvoices(i);
      setDomains(d);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load billing");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => void load(), 0);
    return () => clearTimeout(t);
  }, [load]);

  async function confirmPlanChange() {
    if (!confirmPlan) return;
    setChangingPlan(confirmPlan.code);
    try {
      const updated = await api.post<BillingSummary>("/billing/change-plan", { plan: confirmPlan.code });
      setSummary(updated);
      showToast(`Plan changed to ${confirmPlan.name}`);
      void load();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to change plan");
    } finally {
      setChangingPlan(null);
      setConfirmPlan(null);
    }
  }

  async function addDomain(e: React.FormEvent) {
    e.preventDefault();
    if (!domainInput.trim()) return;
    setAddingDomain(true);
    try {
      const created = await api.post<OrganizationDomain>("/domains", { domain: domainInput.trim() });
      setDomains((prev) => [...prev, created]);
      setDomainModal(created);
      setDomainInput("");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to add domain");
    } finally {
      setAddingDomain(false);
    }
  }

  async function verifyDomain() {
    if (!domainModal) return;
    setVerifying(true);
    try {
      const updated = await api.post<OrganizationDomain>(`/domains/${domainModal.id}/verify`, {
        token: verifyToken.trim(),
      });
      setDomains((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      setDomainModal(null);
      setVerifyToken("");
      showToast("Domain verified");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Verification failed");
    } finally {
      setVerifying(false);
    }
  }

  async function confirmDomainDelete() {
    if (!deletingDomain) return;
    try {
      await api.delete(`/domains/${deletingDomain.id}`);
      setDomains((prev) => prev.filter((d) => d.id !== deletingDomain.id));
      showToast("Domain removed");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to remove domain");
    } finally {
      setDeletingDomain(null);
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-slate-500 dark:text-slate-400">
        Loading billing...
      </div>
    );
  }

  if (error && !summary) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3 text-sm text-slate-500 dark:text-slate-400">
        <p>{error}</p>
        <Button variant="outline" onClick={() => void load()}>Try again</Button>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Billing"
        description="Your plan, usage and invoices"
      />

      <div className="grid gap-4 lg:grid-cols-3">
        {plans.map((plan) => {
          const current = summary?.plan === plan.code;
          return (
            <Card key={plan.code} className={current ? "ring-2 ring-indigo-500" : ""}>
              <CardHeader
                title={plan.name}
                subtitle={plan.description}
                actions={
                  current ? (
                    <Badge className={badgeClass(DOMAIN_STATUS_COLORS, "verified")}>Current</Badge>
                  ) : null
                }
              />
              <CardBody>
                <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {formatMoney(plan.price)}
                  <span className="text-sm font-normal text-slate-500 dark:text-slate-400">/mo</span>
                </p>
                <ul className="mt-4 space-y-1.5 text-sm text-slate-600 dark:text-slate-300">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2">
                      <svg className="h-4 w-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                      {FEATURE_LABELS[f] ?? f}
                    </li>
                  ))}
                  {plan.features.length === 0 && (
                    <li className="text-slate-400 dark:text-slate-500">Core selling features</li>
                  )}
                </ul>
                {isOwner && !current && (
                  <Button
                    className="mt-5 w-full"
                    variant={plan.code === "pro" ? "primary" : "outline"}
                    loading={changingPlan === plan.code}
                    onClick={() => setConfirmPlan(plan)}
                  >
                    Switch to {plan.name}
                  </Button>
                )}
              </CardBody>
            </Card>
          );
        })}
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Usage" subtitle="Current usage vs your plan limits" />
          <CardBody className="space-y-4">
            <UsageBar label="Team members" used={summary?.usage.users ?? 0} limit={summary?.limits.users ?? 0} />
            <UsageBar label="Products" used={summary?.usage.products ?? 0} limit={summary?.limits.products ?? 0} />
            <UsageBar label="Orders this month" used={summary?.usage.orders_per_month ?? 0} limit={summary?.limits.orders_per_month ?? 0} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader
            title="Invoices"
            subtitle={summary?.period_end ? `Current period ends ${formatDate(summary.period_end)}` : undefined}
          />
          {invoices.length === 0 ? (
            <CardBody>
              <p className="text-sm text-slate-500 dark:text-slate-400">No invoices yet. Changing plans creates an invoice.</p>
            </CardBody>
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {invoices.map((inv) => (
                <div key={inv.id} className="flex items-center justify-between px-5 py-3 text-sm">
                  <div>
                    <p className="font-medium text-slate-900 dark:text-slate-100">{inv.invoice_number}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {inv.plan} plan · {formatDate(inv.created_at)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-slate-900 dark:text-slate-100">
                      {formatMoney(inv.amount)} {inv.currency}
                    </p>
                    <Badge className={badgeClass(PLAN_STATUS_COLORS, inv.status)}>{inv.status}</Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader
          title="Custom domains"
          subtitle="Point your own domain at your storefront. Add the TXT record with the verification token, then verify."
          actions={
            <form onSubmit={addDomain} className="flex items-center gap-2">
              <Input
                value={domainInput}
                onChange={(e) => setDomainInput(e.target.value)}
                placeholder="shop.example.com"
                className="w-56"
              />
              <Button type="submit" loading={addingDomain}>Add domain</Button>
            </form>
          }
        />
        {domains.length === 0 ? (
          <CardBody>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              No custom domains yet. Available on the Pro and Enterprise plans.
            </p>
          </CardBody>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {domains.map((d) => (
              <div key={d.id} className="flex flex-wrap items-center justify-between gap-2 px-5 py-3">
                <div>
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100">{d.domain}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {d.verified_at ? `Verified ${formatDate(d.verified_at)}` : "Pending verification"}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className={badgeClass(DOMAIN_STATUS_COLORS, d.status)}>{d.status}</Badge>
                  {d.status !== "verified" && (
                    <Button size="sm" variant="outline" onClick={() => { setDomainModal(d); setVerifyToken(""); }}>
                      Verify
                    </Button>
                  )}
                  <Button size="sm" variant="ghost" onClick={() => setDeletingDomain(d)}>Remove</Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <ConfirmDialog
        open={confirmPlan !== null}
        title={`Switch to ${confirmPlan?.name ?? ""} plan`}
        description={`Your plan will change immediately and an invoice for ${confirmPlan ? formatMoney(confirmPlan.price) : ""} will be issued.`}
        confirmLabel="Switch plan"
        variant="primary"
        loading={changingPlan !== null}
        onConfirm={confirmPlanChange}
        onClose={() => setConfirmPlan(null)}
      />

      <Modal
        open={domainModal !== null}
        title={`Verify ${domainModal?.domain ?? ""}`}
        description="Add this TXT record at your DNS provider, then paste the token below to verify."
        onClose={() => setDomainModal(null)}
        footer={
          <Button onClick={verifyDomain} loading={verifying}>Verify domain</Button>
        }
      >
        <div className="space-y-4">
          <div>
            <p className="mb-1 text-xs font-medium text-slate-500 dark:text-slate-400">DNS record</p>
            <code className="block break-all rounded-lg bg-slate-100 px-3 py-2 text-xs text-slate-800 dark:bg-slate-800 dark:text-slate-200">
              TXT · _seller-manager · {domainModal?.verification_token}
            </code>
          </div>
          <Field label="Verification token">
            <Input
              value={verifyToken}
              onChange={(e) => setVerifyToken(e.target.value)}
              placeholder={domainModal?.verification_token ?? ""}
            />
          </Field>
        </div>
      </Modal>

      <ConfirmDialog
        open={deletingDomain !== null}
        title="Remove domain"
        description={`Remove ${deletingDomain?.domain ?? ""} from your storefront?`}
        confirmLabel="Remove"
        onConfirm={confirmDomainDelete}
        onClose={() => setDeletingDomain(null)}
      />

      <Toast message={toast} />
    </div>
  );
}