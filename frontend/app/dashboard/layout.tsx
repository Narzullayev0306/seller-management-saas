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
import { useLocalValue } from "@/lib/local-store";
import { ThemeToggle } from "@/components/ui/theme-toggle";

interface NavItem {
  href: string;
  label: string;
  icon: string;
  permission: string;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: "Overview",
    items: [
      {
        href: "/dashboard",
        label: "Dashboard",
        icon: "M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z",
        permission: "analytics.read",
      },
      {
        href: "/dashboard/reports",
        label: "Reports",
        icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
        permission: "analytics.read",
      },
    ],
  },
  {
    label: "Commerce",
    items: [
      {
        href: "/dashboard/products",
        label: "Products",
        icon: "M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zM6 8h12M6 12h12M6 16h8",
        permission: "products.read",
      },
      {
        href: "/dashboard/categories",
        label: "Categories",
        icon: "M4 6h7v7H4zM13 6h7v4h-7zM13 13h7v5h-7zM4 16h7v2H4z",
        permission: "products.read",
      },
      {
        href: "/dashboard/orders",
        label: "Orders",
        icon: "M12 2 2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
        permission: "orders.read",
      },
      {
        href: "/dashboard/customers",
        label: "Customers",
        icon: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm14 10v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75",
        permission: "customers.read",
      },
      {
        href: "/dashboard/inventory",
        label: "Inventory",
        icon: "M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16zM3.27 6.96 12 12.01l8.73-5.05M12 22.08V12",
        permission: "inventory.read",
      },
    ],
  },
  {
    label: "Operations",
    items: [
      {
        href: "/dashboard/sellers",
        label: "Sellers",
        icon: "M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0zM12 14a7 7 0 0 0-7 7h14a7 7 0 0 0-7-7z",
        permission: "sellers.read",
      },
      {
        href: "/dashboard/suppliers",
        label: "Suppliers",
        icon: "M17 8v3a4 4 0 0 1-8 0V8a2 2 0 1 1 4 0v3a6 6 0 0 1-12 0V8a2 2 0 1 1 4 0v3a2 2 0 1 0 4 0V8a4 4 0 1 0-8 0v3a8 8 0 0 0 16 0V8a4 4 0 1 0-8 0m-2 0v5",
        permission: "suppliers.read",
      },
      {
        href: "/dashboard/purchase-orders",
        label: "Purchase Orders",
        icon: "M3 3v18h18M7 9h10M7 13h6",
        permission: "inventory.read",
      },
      {
        href: "/dashboard/shipping",
        label: "Shipping",
        icon: "M1 3h15v13H1zM16 8h4l3 4v4h-7M5.5 21a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zm13 0a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z",
        permission: "settings.read",
      },
      {
        href: "/dashboard/refunds",
        label: "Refunds",
        icon: "M4 4h16v6a4 4 0 0 1-4 4h-8a4 4 0 0 1-4-4V4zm8 10v7m-4-3 4 3 4-3",
        permission: "orders.read",
      },
    ],
  },
  {
    label: "Marketing",
    items: [
      {
        href: "/dashboard/marketing",
        label: "Coupons",
        icon: "M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z",
        permission: "products.read",
      },
    ],
  },
  {
    label: "Team",
    items: [
      {
        href: "/dashboard/users",
        label: "Members",
        icon: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm14 10v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75",
        permission: "users.read",
      },
      {
        href: "/dashboard/audit",
        label: "Audit log",
        icon: "M12 8v4l3 3m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0z",
        permission: "audit.read",
      },
    ],
  },
  {
    label: "Developer",
    items: [
      {
        href: "/dashboard/webhooks",
        label: "Webhooks",
        icon: "M6 3v18M4 7l4 4-4 4M18 3v18M14 9l4 4-4 4",
        permission: "settings.read",
      },
      {
        href: "/dashboard/api-keys",
        label: "API Keys",
        icon: "M15 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0zm-4 4h8v3a2 2 0 0 1-2 2h-2v2h-2v2H9m-2-2v.01",
        permission: "settings.read",
      },
    ],
  },
  {
    label: "Settings",
    items: [
      {
        href: "/dashboard/billing",
        label: "Billing",
        icon: "M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7zm2 0h2v2h4V7h8v10H7v-2h2v-2H7V7zm4 0v2h6V7h-6z",
        permission: "billing.read",
      },
      {
        href: "/dashboard/settings",
        label: "Organization",
        icon: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm7.4-3a7.4 7.4 0 0 0-.1-1.2l2-1.5-2-3.5-2.4 1a7.4 7.4 0 0 0-2-1.2L14.5 3h-5l-.4 2.6a7.4 7.4 0 0 0-2 1.2l-2.4-1-2 3.5 2 1.5a7.4 7.4 0 0 0 0 2.4l-2 1.5 2 3.5 2.4-1a7.4 7.4 0 0 0 2 1.2l.4 2.6h5l.4-2.6a7.4 7.4 0 0 0 2-1.2l2.4 1 2-3.5-2-1.5c.07-.4.1-.8.1-1.2z",
        permission: "settings.read",
      },
    ],
  },
];

const ALL_NAV_ITEMS = NAV_GROUPS.flatMap((g) => g.items);

const COLLAPSE_KEY = "sms_sidebar_collapsed";

function Icon({ d }: { d: string }) {
  return (
    <svg
      className="h-[18px] w-[18px] shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={d} />
    </svg>
  );
}

function NavLink({
  item,
  collapsed,
  onNavigate,
}: {
  item: NavItem;
  collapsed: boolean;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      title={collapsed ? item.label : undefined}
      className={`group relative flex items-center gap-3 rounded-xl text-sm font-medium transition-all duration-150 ease-out active:scale-[0.98] ${
        collapsed ? "justify-center px-0 py-2.5" : "px-3 py-2"
      } ${
        active
          ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-300"
          : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/70 dark:hover:text-white"
      }`}
    >
      {/* Active indicator */}
      <span
        aria-hidden
        className={`absolute -left-2.5 top-1/2 h-5 w-1 -translate-y-1/2 rounded-full bg-indigo-600 transition-all duration-200 dark:bg-indigo-400 ${
          active ? "opacity-100 scale-100" : "opacity-0 scale-50"
        } ${collapsed ? "-left-1.5" : ""}`}
      />
      <span className={active ? "text-indigo-600 dark:text-indigo-300" : ""}>
        <Icon d={item.icon} />
      </span>
      {!collapsed && <span className="truncate">{item.label}</span>}
    </Link>
  );
}

function NavLinks({ collapsed, onNavigate }: { collapsed: boolean; onNavigate?: () => void }) {
  const { can } = useAuth();
  return (
    <nav aria-label="Dashboard" className={`flex-1 space-y-4 overflow-y-auto overflow-x-hidden px-3 py-3 ${collapsed ? "px-2" : ""}`}>
      {NAV_GROUPS.map((group) => {
        const visible = group.items.filter((n) => can(n.permission));
        if (visible.length === 0) return null;
        return (
          <div key={group.label}>
            {!collapsed && (
              <p className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-400 dark:text-slate-600">
                {group.label}
              </p>
            )}
            {collapsed && <div className="mx-auto mb-2 h-px w-6 bg-slate-200 dark:bg-slate-800" role="presentation" />}
            <div className="space-y-0.5">
              {visible.map((item) => (
                <NavLink key={item.href} item={item} collapsed={collapsed} onNavigate={onNavigate} />
              ))}
            </div>
          </div>
        );
      })}
    </nav>
  );
}

function Sidebar({
  collapsed,
  onToggleCollapse,
  onNavigate,
}: {
  collapsed: boolean;
  onToggleCollapse?: () => void;
  onNavigate?: () => void;
}) {
  const { user } = useAuth();
  return (
    <div
      className={`flex h-full flex-col border-r border-slate-200 bg-white transition-[width] duration-200 ease-out dark:border-slate-800 dark:bg-slate-900 ${
        collapsed ? "w-[68px]" : "w-64"
      }`}
    >
      <div className={`flex items-center gap-2.5 py-4 ${collapsed ? "justify-center px-2" : "px-5"}`}>
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-600 to-sky-400 text-sm font-bold text-white shadow-md shadow-indigo-500/25">
          S
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">Seller Manager</p>
            <p className="truncate text-xs text-slate-500 dark:text-slate-400">{user?.organization_name ?? "Workspace"}</p>
          </div>
        )}
      </div>
      {!collapsed && <OrgSwitcher />}
      <NavLinks collapsed={collapsed} onNavigate={onNavigate} />
      <div className={`border-t border-slate-200 dark:border-slate-800 ${collapsed ? "px-2 py-3" : "px-5 py-3"}`}>
        {collapsed ? (
          <div className="flex flex-col items-center gap-2">
            <span
              className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
              title={`${user?.full_name ?? ""} (${user?.email ?? ""})`}
            >
              {(user?.full_name ?? "?").slice(0, 2).toUpperCase()}
            </span>
            {onToggleCollapse && <CollapseButton collapsed onToggle={onToggleCollapse} />}
          </div>
        ) : (
          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">{user?.full_name}</p>
              <p className="truncate text-xs text-slate-500 dark:text-slate-400">{user?.email}</p>
              <p className="mt-0.5 truncate text-xs font-medium text-indigo-600 dark:text-indigo-400">
                {user?.roles.map((r) => r.name).join(", ")}
              </p>
            </div>
            {onToggleCollapse && <CollapseButton collapsed={false} onToggle={onToggleCollapse} />}
          </div>
        )}
      </div>
    </div>
  );
}

function CollapseButton({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={`h-4 w-4 transition-transform duration-200 ${collapsed ? "rotate-180" : ""}`}
        aria-hidden
      >
        <path d="M11 19l-7-7 7-7M19 19l-7-7 7-7" />
      </svg>
    </button>
  );
}

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const { loading, authenticated, user } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [collapsedStored, setCollapsedStored] = useLocalValue(COLLAPSE_KEY);
  const collapsed = collapsedStored === "true";

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

  function toggleCollapse() {
    setCollapsedStored(collapsed ? "false" : "true");
  }

  if (loading || !authenticated) return <PageLoading />;

  return (
    <div className="min-h-screen bg-slate-50 transition-colors duration-200 dark:bg-slate-950">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-indigo-600 focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white"
      >
        Skip to content
      </a>

      <CommandSearchModal open={searchOpen} onClose={() => setSearchOpen(false)} />

      <aside className="fixed inset-y-0 left-0 z-30 hidden lg:block">
        <Sidebar collapsed={collapsed} onToggleCollapse={toggleCollapse} />
      </aside>

      {drawerOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 animate-in fade-in duration-150 bg-slate-900/50 backdrop-blur-[2px]"
            onClick={() => setDrawerOpen(false)}
            aria-hidden
          />
          <div className="absolute inset-y-0 left-0 animate-in slide-in-from-left duration-200">
            <Sidebar collapsed={false} onNavigate={() => setDrawerOpen(false)} />
          </div>
        </div>
      )}

      <div className={`transition-[padding] duration-200 ease-out ${collapsed ? "lg:pl-[68px]" : "lg:pl-64"}`}>
        <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-slate-200 bg-white/85 px-4 py-3 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/85 lg:px-8">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setDrawerOpen(true)}
              className="rounded-xl p-2 text-slate-600 hover:bg-slate-100 lg:hidden dark:text-slate-300 dark:hover:bg-slate-800"
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
              <kbd className="ml-auto rounded-md border border-slate-200 bg-white px-1.5 py-0.5 font-mono text-[10px] font-medium text-slate-400 dark:border-slate-600 dark:bg-slate-900">⌘K</kbd>
            </button>
          </div>
          <div className="flex items-center gap-1.5">
            <Link
              href="/storefront"
              className="hidden items-center gap-1.5 rounded-xl bg-indigo-50 px-3 py-2 text-sm font-medium text-indigo-700 transition hover:bg-indigo-600 hover:text-white active:scale-[0.98] md:flex dark:bg-indigo-500/10 dark:text-indigo-300 dark:hover:bg-indigo-600 dark:hover:text-white"
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
        <main id="main-content" className="mx-auto max-w-7xl px-4 py-6 lg:px-8">
          <div key={pathname} className="page-enter">
            {children}
          </div>
        </main>
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
        <p className="text-small text-amber-800 dark:text-amber-300">
          Your email is not verified yet. Some features may be restricted.
        </p>
        {sent ? (
          <p className="text-small font-medium text-emerald-700 dark:text-emerald-400">Verification email sent.</p>
        ) : (
          <button
            onClick={() => void resend()}
            disabled={sending}
            className="text-small font-semibold text-amber-900 underline-offset-2 hover:underline disabled:opacity-60 dark:text-amber-200"
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
        aria-expanded={open}
        aria-haspopup="menu"
        className="flex items-center gap-2 rounded-xl px-2 py-1.5 text-sm transition hover:bg-slate-100 dark:hover:bg-slate-800"
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-tr from-indigo-500 to-indigo-700 text-xs font-semibold text-white shadow-sm">
          {user?.full_name.slice(0, 2).toUpperCase()}
        </span>
        <span className="hidden text-sm font-medium text-slate-700 sm:block dark:text-slate-200">{user?.full_name}</span>
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          className={`hidden h-3.5 w-3.5 text-slate-400 transition-transform duration-150 sm:block ${open ? "rotate-180" : ""}`}
          aria-hidden
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} aria-hidden />
          <div
            role="menu"
            className="absolute right-0 z-20 mt-2 w-52 origin-top-right animate-scale-in rounded-2xl border border-slate-200 bg-white py-1 shadow-[var(--shadow-overlay)] dark:border-slate-700 dark:bg-slate-900"
          >
            <div className="border-b border-slate-100 px-4 py-2.5 dark:border-slate-800">
              <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">{user?.full_name}</p>
              <p className="truncate text-xs text-slate-500 dark:text-slate-400">{user?.email}</p>
            </div>
            <Link
              href="/dashboard/settings"
              role="menuitem"
              onClick={() => setOpen(false)}
              className="block px-4 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              Organization settings
            </Link>
            <button
              role="menuitem"
              onClick={() => {
                setOpen(false);
                void logout().then(() => router.replace("/login"));
              }}
              className="w-full px-4 py-2 text-left text-sm text-red-600 transition-colors hover:bg-red-50 dark:hover:bg-red-950/40"
            >
              Sign out
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export { ALL_NAV_ITEMS };
