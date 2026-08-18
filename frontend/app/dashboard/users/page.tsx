"use client";

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/states";
import { PageHeader, Toolbar } from "@/components/page-header";
import { DataTable, Pagination } from "@/components/ui/table";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Field, Input, Select } from "@/components/ui/input";
import { ConfirmDialog, Modal, Toast } from "@/components/ui/modal";
import { useAuth } from "@/lib/auth";
import { useList } from "@/lib/use-list";
import { api } from "@/lib/api-client";
import { badgeClass, formatDate } from "@/lib/format";
import type { User, UserStatus } from "@/lib/types";

const ROLE_COLORS: Record<string, string> = {
  owner: "bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-800",
  admin: "bg-indigo-100 text-indigo-800 border-indigo-200 dark:bg-indigo-950/40 dark:text-indigo-300 dark:border-indigo-800",
  manager: "bg-sky-100 text-sky-800 border-sky-200 dark:bg-sky-950/40 dark:text-sky-300 dark:border-sky-800",
  seller: "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
  viewer: "bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
};

const STATUS_COLORS: Record<UserStatus, string> = {
  active: "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
  invited: "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800",
  suspended: "bg-red-100 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800",
};

const PERM_GROUPS: { module: string; codes: string[] }[] = [
  { module: "Dashboard", codes: ["dashboard.read"] },
  { module: "Users", codes: ["users.read", "users.create", "users.update", "users.delete"] },
  { module: "Sellers", codes: ["sellers.read", "sellers.create", "sellers.update", "sellers.delete"] },
  { module: "Products", codes: ["products.read", "products.create", "products.update", "products.delete"] },
  { module: "Customers", codes: ["customers.read", "customers.create", "customers.update", "customers.delete"] },
  { module: "Orders", codes: ["orders.read", "orders.create", "orders.update", "orders.delete"] },
  { module: "Inventory", codes: ["inventory.read", "inventory.update"] },
  { module: "Analytics", codes: ["analytics.read"] },
  { module: "Audit", codes: ["audit.read"] },
];

interface MatrixRole {
  id: string;
  name: string;
  code: string;
  is_system: boolean;
  permissions: string[];
}
interface PermissionInfo {
  code: string;
  description: string;
}
interface RoleMatrix {
  roles: MatrixRole[];
  permissions: PermissionInfo[];
}

interface FormState {
  email: string;
  full_name: string;
  role_codes: string[];
}

const EMPTY_FORM: FormState = { email: "", full_name: "", role_codes: ["viewer"] };

export default function TeamPage() {
  const { can, user: me } = useAuth();
  const { data, loading, error, query, setSearch, setPage, setFilter, refetch } = useList<User>("/users", { sortBy: "created_at", sortOrder: "desc" });
  const [tab, setTab] = useState<"members" | "matrix">("members");
  const [search, setSearchInput] = useState("");

  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 3000);
  }, []);

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setFormErrors({});
    setModalOpen(true);
  };

  function validate(): boolean {
    const next: Partial<Record<keyof FormState, string>> = {};
    if (!form.email.trim()) next.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) next.email = "Enter a valid email";
    if (form.role_codes.length === 0) next.role_codes = "Select at least one role";
    setFormErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleCreate() {
    if (!validate()) return;
    setSaving(true);
    try {
      await api.post("/users/invite", {
        email: form.email.trim(),
        full_name: form.full_name.trim() || undefined,
        role_codes: form.role_codes,
      });
      showToast("Invitation sent");
      setModalOpen(false);
      refetch();
    } catch (err) {
      setFormErrors({ email: err instanceof Error ? err.message : "Failed to invite user" });
    } finally {
      setSaving(false);
    }
  }

  async function resendInvite(user: User) {
    try {
      await api.post("/users/invites/resend", { user_id: user.id });
      showToast("Invitation resent");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to resend invite");
    }
  }

  async function toggleActive(user: User) {
    try {
      await api.patch(`/users/${user.id}`, { is_active: !user.is_active });
      showToast(user.is_active ? "Member deactivated" : "Member reactivated");
      refetch();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to update member");
    }
  }

  async function changeRole(user: User, role: string) {
    if (role === (user.roles[0] ?? "")) return;
    try {
      await api.put(`/users/${user.id}/roles`, { role_codes: [role] });
      showToast(`Role changed to ${role}`);
      refetch();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to change role");
    }
  }

  const [userToDelete, setUserToDelete] = useState<User | null>(null);
  const [deleting, setDeleting] = useState(false);

  function removeMember(user: User) {
    setUserToDelete(user);
  }

  async function confirmRemoveMember() {
    if (!userToDelete) return;
    setDeleting(true);
    try {
      await api.delete(`/users/${userToDelete.id}`);
      showToast(userToDelete.status === "invited" ? "Invitation revoked" : "Member removed");
      setUserToDelete(null);
      refetch();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to remove member");
    } finally {
      setDeleting(false);
    }
  }

  const columns = [
    { key: "full_name", header: "Member" },
    { key: "roles", header: "Roles" },
    { key: "status", header: "Status" },
    { key: "created_at", header: "Joined" },
    { key: "actions", header: "" },
  ];

  return (
    <div>
      <PageHeader
        title="Team"
        description="Manage who can access your workspace and their roles."
        actions={
          tab === "members" &&
          can("users.create") && (
            <Button onClick={openCreate}>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Invite member
            </Button>
          )
        }
      />

      <div className="mb-4 flex items-center gap-1 rounded-xl bg-slate-100 p-1 dark:bg-slate-800" style={{ width: "fit-content" }}>
        <button
          onClick={() => setTab("members")}
          className={`rounded-lg px-4 py-1.5 text-sm font-medium transition active:scale-[0.98] ${
            tab === "members"
              ? "bg-white text-indigo-700 shadow-sm dark:bg-slate-900 dark:text-indigo-300"
              : "text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
          }`}
        >
          Members
        </button>
        <button
          onClick={() => setTab("matrix")}
          className={`rounded-lg px-4 py-1.5 text-sm font-medium transition active:scale-[0.98] ${
            tab === "matrix"
              ? "bg-white text-indigo-700 shadow-sm dark:bg-slate-900 dark:text-indigo-300"
              : "text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
          }`}
        >
          Permission matrix
        </button>
      </div>

      {tab === "members" ? (
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
                <option value="invited">Invited</option>
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
            renderRow={(u) => [
              <div key="name" className="flex items-center gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                  {u.full_name[0]?.toUpperCase() ?? "?"}
                </div>
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">{u.full_name}</p>
                  <p className="text-xs text-slate-400 dark:text-slate-500">{u.email}</p>
                </div>
              </div>,
              <div key="roles" className="flex items-center gap-2">
                <div className="flex flex-wrap gap-1">
                  {u.roles.map((r) => (
                    <Badge key={r} className={ROLE_COLORS[r] ?? ""}>
                      {r}
                    </Badge>
                  ))}
                </div>
                {can("users.update") && me?.id !== u.id && !u.roles.includes("owner") && (
                  <Select
                    value={u.roles[0] ?? ""}
                    onChange={(e) => void changeRole(u, e.target.value)}
                    className="w-28"
                    title="Change role"
                  >
                    <option value="admin">admin</option>
                    <option value="manager">manager</option>
                    <option value="seller">seller</option>
                    <option value="viewer">viewer</option>
                  </Select>
                )}
              </div>,
              <Badge key="status" className={badgeClass(STATUS_COLORS, u.status)}>
                {u.status}
              </Badge>,
              <span key="joined" className="text-xs text-slate-500 dark:text-slate-400">
                {formatDate(u.created_at)}
              </span>,
              <div key="actions" className="flex justify-end gap-1">
                {u.status === "invited" && can("users.create") && (
                  <Button variant="ghost" size="sm" onClick={() => void resendInvite(u)}>
                    Resend invite
                  </Button>
                )}
                {can("users.update") && me?.id !== u.id && u.status !== "invited" && (
                  <Button variant="ghost" size="sm" onClick={() => void toggleActive(u)}>
                    {u.status === "active" ? "Suspend" : "Reactivate"}
                  </Button>
                )}
                {can("users.delete") && me?.id !== u.id && u.status === "invited" && !u.roles.includes("owner") && (
                  <Button variant="ghost" size="sm" onClick={() => void removeMember(u)}>
                    Remove
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
      ) : (
        <PermissionMatrix />
      )}

      <Modal
        open={modalOpen}
        title="Invite team member"
        description="They will receive an email with a link to set their own password."
        onClose={() => setModalOpen(false)}
        loading={saving}
        footer={
          <Button onClick={handleCreate} loading={saving}>
            Send invite
          </Button>
        }
      >
        <div className="space-y-4">
          <Field label="Email" error={formErrors.email}>
            <Input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} placeholder="teammate@company.com" />
          </Field>
          <Field label="Full name (optional)">
            <Input value={form.full_name} onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))} placeholder="Jane Smith" />
          </Field>
          <Field label="Roles" error={formErrors.role_codes}>
            <Select
              value={form.role_codes[0] ?? "viewer"}
              onChange={(e) => setForm((f) => ({ ...f, role_codes: [e.target.value] }))}
            >
              <option value="admin">Admin</option>
              <option value="manager">Manager</option>
              <option value="seller">Seller</option>
              <option value="viewer">Viewer</option>
            </Select>
          </Field>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!userToDelete}
        title={userToDelete?.status === "invited" ? "Revoke Invitation" : "Remove Team Member"}
        description={
          userToDelete?.status === "invited"
            ? `Revoke pending invitation for ${userToDelete?.email}? They will not be able to join.`
            : `Are you sure you want to remove ${userToDelete?.full_name} (${userToDelete?.email})? They will lose access to this company workspace immediately.`
        }
        confirmLabel={userToDelete?.status === "invited" ? "Revoke Invite" : "Remove Member"}
        variant="danger"
        loading={deleting}
        onConfirm={() => void confirmRemoveMember()}
        onClose={() => setUserToDelete(null)}
      />

      <Toast message={toast} />
    </div>
  );
}

function PermissionMatrix() {
  const [matrix, setMatrix] = useState<RoleMatrix | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await api.get<RoleMatrix>("/roles/matrix");
      setMatrix(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load permission matrix");
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => void load(), 0);
    return () => clearTimeout(t);
  }, [load]);

  if (error) {
    return (
      <Card>
        <div className="flex flex-col items-center gap-3 px-6 py-12 text-center">
          <p className="text-sm font-medium text-slate-700 dark:text-slate-200">Failed to load permission matrix</p>
          <p className="text-sm text-slate-500 dark:text-slate-400">{error}</p>
          <Button variant="outline" size="sm" onClick={() => void load()}>
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  if (!matrix) {
    return (
      <Card>
        <div className="space-y-3 px-5 py-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-10 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
          ))}
        </div>
      </Card>
    );
  }

  const desc = new Map(matrix.permissions.map((p) => [p.code, p.description]));

  return (
    <Card>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50/60 dark:border-slate-800 dark:bg-slate-800/40">
              <th className="px-5 py-3 font-medium text-slate-500 dark:text-slate-400">Permission</th>
              {matrix.roles.map((r) => (
                <th key={r.id} className="px-4 py-3 text-center font-medium text-slate-500 dark:text-slate-400">
                  {r.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {PERM_GROUPS.map((group) => (
              <>
                <tr key={group.module} className="bg-slate-50/80 dark:bg-slate-800/30">
                  <td className="px-5 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                    {group.module}
                  </td>
                  {matrix.roles.map((r) => (
                    <td key={r.id} className="px-4 py-2" />
                  ))}
                </tr>
                {group.codes.map((code) => (
                  <tr key={code} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <td className="px-5 py-2.5">
                      <p className="font-medium text-slate-700 dark:text-slate-200">{code}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{desc.get(code) ?? ""}</p>
                    </td>
                    {matrix.roles.map((r) => {
                      const granted = r.permissions.includes(code);
                      return (
                        <td key={r.id} className="px-4 py-2.5 text-center">
                          <span
                            className={`inline-flex h-6 w-6 items-center justify-center rounded-full ${
                              granted
                                ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
                                : "bg-slate-100 text-slate-300 dark:bg-slate-800 dark:text-slate-600"
                            }`}
                            title={granted ? "Granted" : "Not granted"}
                          >
                            {granted && (
                              <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
                                <path d="M20 6 9 17l-5-5" />
                              </svg>
                            )}
                          </span>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}