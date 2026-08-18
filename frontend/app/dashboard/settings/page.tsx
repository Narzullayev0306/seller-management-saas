"use client";

import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Field, Input, Select } from "@/components/ui/input";
import { ConfirmDialog, Toast } from "@/components/ui/modal";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api-client";
import type { OrganizationSettings, User } from "@/lib/types";

const CURRENCIES = ["USD", "EUR", "UZS", "RUB", "GBP", "AED"];
const TIMEZONES = [
  "UTC",
  "Asia/Tashkent",
  "Europe/London",
  "Europe/Paris",
  "Europe/Moscow",
  "America/New_York",
  "America/Los_Angeles",
  "Asia/Dubai",
  "Asia/Almaty",
  "Asia/Tokyo",
];
const PLANS = ["free", "pro", "enterprise"];

export default function SettingsPage() {
  const { hasRole, logout } = useAuth();
  const isOwner = hasRole("owner");
  const [org, setOrg] = useState<OrganizationSettings | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const [members, setMembers] = useState<User[]>([]);
  const [transferTarget, setTransferTarget] = useState("");
  const [transferring, setTransferring] = useState(false);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [planSaving, setPlanSaving] = useState(false);
  const [closeConfirm, setCloseConfirm] = useState("");
  const [closing, setClosing] = useState(false);
  const [showCloseModal, setShowCloseModal] = useState(false);

  // Change Password state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordSaving, setPasswordSaving] = useState(false);

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 3000);
  }, []);

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await api.get<OrganizationSettings>("/organizations/me");
      setOrg(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => void load(), 0);
    return () => clearTimeout(t);
  }, [load]);

  useEffect(() => {
    if (!isOwner) return;
    const t = setTimeout(() => {
      void api
        .get<{ items: User[] }>("/users", { page: 1, page_size: 100 })
        .then((data) => setMembers(data.items))
        .catch(() => setMembers([]));
    }, 0);
    return () => clearTimeout(t);
  }, [isOwner]);

  async function changePlan(plan: string) {
    setPlanSaving(true);
    try {
      const updated = await api.patch<OrganizationSettings>("/organizations/me/plan", { plan });
      setOrg(updated);
      showToast(`Plan changed to ${plan}`);
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to change plan");
    } finally {
      setPlanSaving(false);
    }
  }

  async function handlePasswordChange(e: React.FormEvent) {
    e.preventDefault();
    if (!currentPassword) {
      showToast("Please enter your current password");
      return;
    }
    if (newPassword.length < 8) {
      showToast("New password must be at least 8 characters");
      return;
    }
    if (newPassword !== confirmPassword) {
      showToast("New passwords do not match");
      return;
    }
    setPasswordSaving(true);
    try {
      await api.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      showToast("Password updated successfully");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to update password");
    } finally {
      setPasswordSaving(false);
    }
  }

  function handleTransferClick() {
    if (!transferTarget) {
      showToast("Select a member to transfer ownership to");
      return;
    }
    setShowTransferModal(true);
  }

  async function confirmTransferOwnership() {
    setShowTransferModal(false);
    setTransferring(true);
    try {
      await api.post("/organizations/me/transfer-ownership", { user_id: transferTarget });
      showToast("Ownership transferred");
      setTransferTarget("");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to transfer ownership");
    } finally {
      setTransferring(false);
    }
  }

  function handleCloseClick() {
    if (closeConfirm !== org?.name) {
      showToast("Type the company name to confirm");
      return;
    }
    setShowCloseModal(true);
  }

  async function confirmCloseCompany() {
    setShowCloseModal(false);
    setClosing(true);
    try {
      await api.post("/organizations/me/close");
      showToast("Company closed");
      window.setTimeout(() => void logout(), 1200);
    } catch (err) {
      setClosing(false);
      showToast(err instanceof Error ? err.message : "Failed to close company");
    }
  }

  function update<K extends keyof OrganizationSettings>(key: K, value: OrganizationSettings[K]) {
    setOrg((o) => (o ? { ...o, [key]: value } : o));
    setSaved(false);
  }

  function validate(): boolean {
    if (!org) return false;
    if (org.name.trim().length < 2) {
      showToast("Company name must be at least 2 characters");
      return false;
    }
    if (org.currency.trim().length < 3) {
      showToast("Currency must be at least 3 characters");
      return false;
    }
    if (!org.timezone.trim()) {
      showToast("Timezone is required");
      return false;
    }
    return true;
  }

  async function handleSave() {
    if (!org || !validate()) return;
    setSaving(true);
    setSaved(false);
    try {
      const updated = await api.patch<OrganizationSettings>("/organizations/me", {
        name: org.name.trim(),
        logo_url: org.logo_url || null,
        currency: org.currency.trim(),
        timezone: org.timezone,
        address: org.address || null,
        phone: org.phone || null,
        email: org.email || null,
      });
      setOrg(updated);
      setSaved(true);
      showToast("Settings saved");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Settings"
        description="Company profile, branding and regional preferences."
        actions={
          <Button onClick={() => void handleSave()} loading={saving} disabled={!org}>
            {saving ? "Saving..." : "Save changes"}
          </Button>
        }
      />

      {error && (
        <Card>
          <div className="flex flex-col items-center gap-3 px-6 py-12 text-center">
            <p className="text-sm font-medium text-slate-700 dark:text-slate-200">Failed to load settings</p>
            <p className="text-sm text-slate-500 dark:text-slate-400">{error}</p>
            <Button variant="outline" size="sm" onClick={() => void load()}>
              Retry
            </Button>
          </div>
        </Card>
      )}

      {!error && !org && (
        <Card>
          <div className="space-y-4 px-5 py-6">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-10 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
            ))}
          </div>
        </Card>
      )}

      {org && (
        <div className="space-y-6">
          <Card>
            <CardHeader title="Company profile" subtitle="Public details shown across the workspace." />
            <CardBody>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Company name">
                  <Input value={org.name} onChange={(e) => update("name", e.target.value)} />
                </Field>
                <Field label="Slug">
                  <Input value={org.slug} disabled className="opacity-60" />
                </Field>
                <Field label="Logo URL">
                  <Input
                    value={org.logo_url ?? ""}
                    onChange={(e) => update("logo_url", e.target.value)}
                    placeholder="https://..."
                  />
                </Field>
                <Field label="Company email">
                  <Input
                    type="email"
                    value={org.email ?? ""}
                    onChange={(e) => update("email", e.target.value)}
                    placeholder="hello@company.com"
                  />
                </Field>
                <Field label="Phone">
                  <Input value={org.phone ?? ""} onChange={(e) => update("phone", e.target.value)} placeholder="+1 555 000 0000" />
                </Field>
                <Field label="Address">
                  <Input
                    value={org.address ?? ""}
                    onChange={(e) => update("address", e.target.value)}
                    placeholder="123 Main Street"
                  />
                </Field>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Regional preferences" subtitle="Currency and timezone for reports and invoices." />
            <CardBody>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Currency">
                  <select
                    value={org.currency}
                    onChange={(e) => update("currency", e.target.value)}
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                  >
                    {CURRENCIES.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Timezone">
                  <select
                    value={org.timezone}
                    onChange={(e) => update("timezone", e.target.value)}
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                  >
                    {TIMEZONES.map((tz) => (
                      <option key={tz} value={tz}>
                        {tz}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>
              {saved && (
                <p className="mt-4 text-sm font-medium text-emerald-600 dark:text-emerald-400">
                  Changes saved. They apply to the whole workspace.
                </p>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              title="Security & Password"
              subtitle="Update your personal account password."
            />
            <CardBody>
              <form onSubmit={(e) => void handlePasswordChange(e)} className="max-w-xl space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <Field label="Current password">
                    <Input
                      type="password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      placeholder="••••••••"
                      autoComplete="current-password"
                    />
                  </Field>
                  <Field label="New password">
                    <Input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="Min 8 chars"
                      autoComplete="new-password"
                    />
                  </Field>
                  <Field label="Confirm new password">
                    <Input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      autoComplete="new-password"
                    />
                  </Field>
                </div>
                <div className="flex justify-start">
                  <Button type="submit" variant="outline" loading={passwordSaving} disabled={!currentPassword || !newPassword}>
                    {passwordSaving ? "Updating..." : "Update password"}
                  </Button>
                </div>
              </form>
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              title="Billing"
              subtitle={isOwner ? "Choose a plan for your workspace." : "Only the company owner can change the plan."}
            />
            <CardBody>
              <div className="grid gap-3 sm:grid-cols-3">
                {PLANS.map((plan) => {
                  const active = org.plan === plan;
                  return (
                    <button
                      key={plan}
                      onClick={() => void changePlan(plan)}
                      disabled={!isOwner || planSaving || active}
                      className={`rounded-xl border p-4 text-left transition active:scale-[0.98] disabled:cursor-not-allowed ${
                        active
                          ? "border-indigo-500 bg-indigo-50 ring-2 ring-indigo-500/20 dark:border-indigo-500 dark:bg-indigo-950/40"
                          : "border-slate-200 hover:border-slate-300 dark:border-slate-700 dark:hover:border-slate-600"
                      }`}
                    >
                      <p className="text-sm font-semibold capitalize text-slate-900 dark:text-slate-100">{plan}</p>
                      <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                        {plan === "free" && "Basic features for small teams"}
                        {plan === "pro" && "Advanced analytics and integrations"}
                        {plan === "enterprise" && "Unlimited everything"}
                      </p>
                      <p className={`mt-2 text-xs font-semibold ${active ? "text-indigo-600 dark:text-indigo-400" : "text-slate-400"}`}>
                        {active ? "Current plan" : isOwner ? "Click to switch" : "Owner only"}
                      </p>
                    </button>
                  );
                })}
              </div>
            </CardBody>
          </Card>

          {isOwner && (
            <Card>
              <CardHeader title="Ownership" subtitle="Transfer the owner role to another active member." />
              <CardBody>
                <div className="flex flex-wrap items-end gap-3">
                  <div className="min-w-56 flex-1">
                    <Field label="New owner">
                      <Select value={transferTarget} onChange={(e) => setTransferTarget(e.target.value)}>
                        <option value="">Select a member...</option>
                        {members
                          .filter((m) => m.status === "active" && !m.roles.includes("owner"))
                          .map((m) => (
                            <option key={m.id} value={m.id}>
                              {m.full_name} ({m.email})
                            </option>
                          ))}
                      </Select>
                    </Field>
                  </div>
                  <Button variant="outline" loading={transferring} disabled={!transferTarget} onClick={handleTransferClick}>
                    Transfer ownership
                  </Button>
                </div>
              </CardBody>
            </Card>
          )}

          {isOwner && (
            <Card>
              <CardHeader
                title="Danger zone"
                subtitle="Irreversible actions that affect the whole company."
              />
              <CardBody className="border-t border-red-100 dark:border-red-950/40">
                <div className="flex flex-wrap items-center gap-3">
                  <div className="min-w-56 flex-1">
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100">Close company</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      Locks every member out immediately. Data is kept for recovery. Type{" "}
                      <span className="font-mono font-semibold text-slate-700 dark:text-slate-300">{org.name}</span> to confirm.
                    </p>
                  </div>
                  <Input
                    value={closeConfirm}
                    onChange={(e) => setCloseConfirm(e.target.value)}
                    placeholder={org.name}
                    className="w-56"
                  />
                  <Button variant="danger" loading={closing} onClick={handleCloseClick}>
                    Close company
                  </Button>
                </div>
              </CardBody>
            </Card>
          )}
        </div>
      )}

      {/* Ownership Transfer Confirm Dialog */}
      <ConfirmDialog
        open={showTransferModal}
        title="Transfer Organization Ownership"
        description={`Are you sure you want to transfer ownership to ${
          members.find((m) => m.id === transferTarget)?.full_name ?? "this member"
        }? You will immediately lose owner privileges and become an administrator.`}
        confirmLabel="Transfer Ownership"
        variant="danger"
        loading={transferring}
        onConfirm={() => void confirmTransferOwnership()}
        onClose={() => setShowTransferModal(false)}
      />

      {/* Close Company Confirm Dialog */}
      <ConfirmDialog
        open={showCloseModal}
        title="Close Company Workspace"
        description={`This action will close ${org?.name} and immediately revoke access for all members. All active sessions will be terminated.`}
        confirmLabel="Yes, Close Company"
        variant="danger"
        loading={closing}
        onConfirm={() => void confirmCloseCompany()}
        onClose={() => setShowCloseModal(false)}
      />

      <Toast message={toast} />
    </div>
  );
}