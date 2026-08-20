"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { CommandSearchModal } from "@/components/command-search";
import { NotificationBell } from "@/components/notification-bell";
import { OrgSwitcher } from "@/components/org-switcher";
import { PageLoading } from "@/components/ui/states";
import { api } from "@/lib/api-client";
import { useAuth } from "@/lib/auth";
import { ThemeToggle } from "@/components/ui/theme-toggle";

const NAV = [
  { href: "/dashboard", label: "Overview", icon: "M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z", permission: "analytics.read" },
  { href: "/dashboard/products", label: "Products", icon: "M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zM6 8h12M6 12h12M6 16h8", permission: "products.read" },
  { href: "/dashboard/orders", label: "Orders", icon: "M12 2 2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5", permission: "orders.read" },
  { href: "/dashboard/customers", label: "Customers", icon: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm14 10v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75", permission: "customers.read" },
  { href: "/dashboard/reports", label: "Reports", icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z", permission: "analytics.read" },
  { href: "/dashboard/marketing", label: "Marketing", icon: "M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z", permission: "products.read" },
  { href: "/dashboard/sellers", label: "Sellers", icon: "M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0zM12 14a7 7 0 0 0-7 7h14a7 7 0 0 0-7-7z", permission: "sellers.read" },
  { href: "/dashboard/suppliers", label: "Suppliers", icon: "M17 8v3a4 4 0 0 1-8 0V8a2 2 0 1 1 4 0v3a6 6 0 0 1-12 0V8a2 2 0 1 1 4 0v3a2 2 0 1 0 4 0V8a4 4 0 1 0-8 0v3a8 8 0 0 0 16 0V8a4 4 0 1 0-8 0m-2 0v5", permission: "suppliers.read" },
  { href: "/dashboard/inventory", label: "Inventory", icon: "M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16zM3.27 6.96 12 12.01l8.73-5.05M12 22.08V12", permission: "inventory.read" },
  { href: "/dashboard/purchase-orders", label: "Purchase Orders", icon: "M3 3v18h18M7 9h10M7 13h6", permission: "inventory.read" },
  { href: "/dashboard/refunds", label: "Refunds", icon: "M4 4h16v6a4 4 0 0 1-4 4h-8a4 4 0 0 1-4-4V4zm8 10v7m-4-3 4 3 4-3", permission: "orders.read" },
  { href: "/dashboard/users", label: "Team", icon: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm14 10v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75", permission: "users.read" },
  { href: "/dashboard/audit", label: "Audit log", icon: "M12 8v4l3 3m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0z", permission: "audit.read" },
  { href: "/dashboard/webhooks", label: "Webhooks", icon: "M6 3v18M4 7l4 4-4 4M18 3v18M14 9l4 4-4 4", permission: "settings.read" },
  { href: "/dashboard/api-keys", label: "API Keys", icon: "M15 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0zm-4 4h8v3a2 2 0 0 1-2 2h-2v2h-2v2H9m-2-2v.01", permission: "settings.read" },
  { href: "/dashboard/billing", label: "Billing", icon: "M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7zm2 0h2v2h4V7h8v10H7v-2h2v-2H7V7zm4 0v2h6V7h-6z", permission: "billing.read" },
  { href: "/dashboard/settings", label: "Settings", icon: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm7.4-3a7.4 7.4 0 0 0-.1-1.2l2-1.5-2-3.5-2.4 1a7.4 7.4 0 0 0-2-1.2L14.5 3h-5l-.4 2.6a7.4 7.4 0 0 0-2 1.2l-2.4-1-2 3.5 2 1.5a7.4 7.4 0 0 0 0 2.4l-2 1.5 2 3.5 2.4-1a7.4 7.4 0 0 0 2 1.2l.4 2.6h5l.4-2.6a7.4 7.4 0 0 0 2-1.2l2.4 1 2-3.5-2-1.5c.07-.4.1-.8.1-1.2z", permission: "settings.read" },
];

function Icon({ d }: { d: string }) {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={d} />
    </svg>
  );
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { can } = useAuth();
  const visible = NAV.filter((n) => can(n.permission));
  return (
    <nav className="flex-1 space-y-1 px-3 py-4">
      {visible.map((item) => {
        const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            className={`relative flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition active:scale-[0.98] ${
              active
                ? "bg-indigo-600 text-white shadow-xs"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
            }`}
          >
            <Icon d={item.icon} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { user } = useAuth();
  return (
    <div className="flex h-full w-64 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center gap-2.5 px-5 py-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-600 to-sky-400 text-sm font-bold text-white shadow-md shadow-indigo-500/25">
          S
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Seller Manager</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{user?.organization_name ?? "Workspace"}</p>
        </div>
      </div>
      <OrgSwitcher />
      <NavLinks onNavigate={onNavigate} />
      <div className="border-t border-slate-200 px-5 py-3 dark:border-slate-800">
        <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">{user?.full_name}</p>
        <p className="truncate text-xs text-slate-500 dark:text-slate-400">{user?.email}</p>
        <p className="mt-1 text-xs font-medium text-indigo-600 dark:text-indigo-400">{user?.roles.map((r) => r.name).join(", ")}</p>
      </div>
    </div>
  );
}

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const { loading, authenticated, user } = useAuth();
  const router = useRouter();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  useEffect(() => {
    if (loading) return;
    if (!authenticated) {
      router.replace("/login");
    } else if (user && user.permissions.length === 0) {
      router.replace("/storefront");
    }
  }, [loading, authenticated, user, router]);

  useEffect(() => {
    if (loading || !authenticated) return;
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setSearchOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [loading, authenticated]);

  if (loading || !authenticated) return <PageLoading />;

  return (
    <div className="min-h-screen bg-slate-50 transition-colors duration-200 dark:bg-slate-950">
      <CommandSearchModal open={searchOpen} onClose={() => setSearchOpen(false)} />

      <aside className="fixed inset-y-0 left-0 z-30 hidden lg:block">
        <Sidebar />
      </aside>

      {drawerOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-slate-900/50" onClick={() => setDrawerOpen(false)} />
          <div className="absolute inset-y-0 left-0">
            <Sidebar onNavigate={() => setDrawerOpen(false)} />
          </div>
        </div>
      )}

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/90 lg:px-8">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setDrawerOpen(true)}
              className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden dark:text-slate-300 dark:hover:bg-slate-800"
              aria-label="Open menu"
            >
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M3 6h18M3 12h18M3 18h18" />
              </svg>
            </button>
            <button
              onClick={() => setSearchOpen(true)}
              className="hidden w-64 items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-400 transition hover:border-slate-300 sm:flex dark:border-slate-700 dark:bg-slate-800 dark:text-slate-500 dark:hover:border-slate-600"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
              Search…
              <kbd className="ml-auto rounded-md border border-slate-200 px-1.5 py-0.5 text-[10px] font-medium text-slate-400 dark:border-slate-600">⌘K</kbd>
            </button>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/storefront"
              className="hidden items-center gap-1.5 rounded-lg bg-indigo-50 px-3 py-1.5 text-sm font-medium text-indigo-700 transition hover:bg-indigo-600 hover:text-white md:flex dark:bg-indigo-950/60 dark:text-indigo-300 dark:hover:bg-indigo-600 dark:hover:text-white"
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
                <path d="M2.5 7h19l-2 12H4.5l-2-12zM6 7a6 6 0 0 1 12 0" />
              </svg>
              Storefront
            </Link>
            <NotificationBell />
            <ThemeToggle />
            <UserMenu />
          </div>
        </header>
        {user && !user.email_verified && <VerifyEmailBanner email={user.email} />}
        <main className="mx-auto max-w-7xl px-4 py-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}

function VerifyEmailBanner({ email }: { email: string }) {
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  async function resend() {
    setSending(true);
    try {
      await api.post("/auth/resend-verification", { email });
      setSent(true);
    } catch {
      setSent(false);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="border-b border-amber-200 bg-amber-50 px-4 py-2.5 dark:border-amber-900 dark:bg-amber-950/40 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-amber-800 dark:text-amber-300">
          Your email is not verified yet. Some features may be restricted.
        </p>
        {sent ? (
          <p className="text-sm font-medium text-emerald-700 dark:text-emerald-400">Verification email sent.</p>
        ) : (
          <button
            onClick={() => void resend()}
            disabled={sending}
            className="text-sm font-semibold text-amber-900 underline-offset-2 hover:underline disabled:opacity-60 dark:text-amber-200"
          >
            {sending ? "Sending..." : "Resend verification email"}
          </button>
        )}
      </div>
    </div>
  );
}

function UserMenu() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
          {user?.full_name.slice(0, 2).toUpperCase()}
        </span>
        <span className="hidden text-sm font-medium text-slate-700 sm:block dark:text-slate-200">{user?.full_name}</span>
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-20 mt-2 w-48 animate-in fade-in zoom-in-95 duration-150 origin-top-right rounded-xl border border-slate-200 bg-white py-1 shadow-xl dark:border-slate-700 dark:bg-slate-900">
            <div className="border-b border-slate-100 px-4 py-2 dark:border-slate-800">
              <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">{user?.full_name}</p>
              <p className="truncate text-xs text-slate-500 dark:text-slate-400">{user?.email}</p>
            </div>
            <button
              onClick={() => {
                setOpen(false);
                void logout().then(() => router.replace("/login"));
              }}
              className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40"
            >
              Sign out
            </button>
          </div>
        </>
      )}
    </div>
  );
}