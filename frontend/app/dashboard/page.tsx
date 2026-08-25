"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Badge, EmptyState, ErrorState } from "@/components/ui/states";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { badgeClass, formatDate, formatMoney, ORDER_STATUS_COLORS } from "@/lib/format";
import type { DashboardData, RangePreset } from "@/lib/types";
import { useApi } from "@/lib/use-api";
import { useCountUp } from "@/lib/use-count-up";

const RANGES: { key: RangePreset; label: string }[] = [
  { key: "today", label: "Today" },
  { key: "7d", label: "7 days" },
  { key: "30d", label: "30 days" },
  { key: "90d", label: "90 days" },
  { key: "year", label: "This year" },
];

const ICONS: Record<string, string> = {
  Revenue: "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm0 5v10M9.5 8.5h3a2 2 0 1 0 0-4h-2M12 14.5h3a2 2 0 1 1 0 4h-3",
  Orders: "M12 2 2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
  "Avg order value": "M3 17l6-6 4 4 8-8M17 7h4v4",
  Customers: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm14 10v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75",
  "Active sellers": "M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0zM12 14a7 7 0 0 0-7 7h14a7 7 0 0 0-7-7z",
  "Commission earned": "M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6",
};

export default function Page() {
  const [range, setRange] = useState<RangePreset>("30d");
  const { data, loading, error, refetch } = useApi<DashboardData>("/analytics/dashboard", { range }, [range]);

  const exportCsv = () => {
    if (!data) return;
    const lines: string[] = ["Date,Revenue"];
    for (const p of data.revenue_over_time) lines.push(`${p.date},${Number(p.value).toFixed(2)}`);
    lines.push("", "Product,Orders,Value");
    for (const p of data.top_products) lines.push(`"${p.name.replace(/"/g, '""')}",${p.orders},${Number(p.value).toFixed(2)}`);
    lines.push("", "Seller,Orders,Value");
    for (const s of data.top_sellers) lines.push(`"${s.name.replace(/"/g, '""')}",${s.orders},${Number(s.value).toFixed(2)}`);
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `dashboard-${range}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">Dashboard</h1>
          <p className="mt-0.5 text-small text-slate-500 dark:text-slate-400">Business overview for the selected period</p>
        </div>
        <div className="flex items-center gap-2.5">
          <button
            onClick={exportCsv}
            disabled={!data}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200/80 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:text-slate-900 active:scale-[0.98] disabled:opacity-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-slate-700 dark:hover:text-white"
          >
            <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
            </svg>
            Export CSV
          </button>
          <div className="flex items-center gap-0.5 rounded-lg bg-slate-100 p-0.5 dark:bg-slate-800/80">
            {RANGES.map((r) => (
              <button
                key={r.key}
                onClick={() => setRange(r.key)}
                className={`rounded-md px-2.5 py-1 text-xs font-medium transition duration-150 active:scale-[0.98] ${
                  range === r.key
                    ? "bg-white text-indigo-700 shadow-xs dark:bg-slate-900 dark:text-indigo-300"
                    : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="skeleton h-28 rounded-xl" />
            ))}
          </div>
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="skeleton h-80 rounded-xl lg:col-span-2" />
            <div className="skeleton h-80 rounded-xl" />
          </div>
        </div>
      )}
      {error && <ErrorState message="Failed to load analytics" onRetry={refetch} />}
      {!loading && !error && data && (
        <>
          <StatCards summary={data.summary} points={data.revenue_over_time} />
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <RevenueChart points={data.revenue_over_time} />
            </div>
            <RevenueComparisonCard comparison={data.revenue_comparison} />
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <RecentOrders items={data.recent_orders} />
            <LowStockCard items={data.low_stock_products} />
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <StatusDistribution items={data.status_distribution} />
            <div className="grid gap-6 sm:grid-cols-2">
              <TopProducts items={data.top_products} />
              <TopSellers items={data.top_sellers} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function StatCards({ summary, points }: { summary: DashboardData["summary"]; points: DashboardData["revenue_over_time"] }) {
  const values = useMemo<number[]>(() => {
    if (!points.length) return [Number(summary.revenue)];
    return points.map((p) => Number(p.value));
  }, [points, summary.revenue]);
  const trend = useMemo(() => {
    if (values.length < 2) return null;
    const half = Math.floor(values.length / 2);
    const first = values.slice(0, half).reduce((a, b) => a + b, 0);
    const second = values.slice(half).reduce((a, b) => a + b, 0);
    if (first === 0) return null;
    return Math.round(((second - first) / first) * 100);
  }, [values]);

  const stats: {
    label: string;
    value: string;
    countTo?: number;
    format?: (n: number) => string;
    spark?: number[];
  }[] = [
    { label: "Revenue", value: formatMoney(summary.revenue), countTo: Number(summary.revenue), format: formatMoney, spark: values },
    { label: "Orders", value: String(summary.orders_count), countTo: Number(summary.orders_count), format: (n) => String(Math.round(n)) },
    { label: "Avg order value", value: formatMoney(summary.avg_order_value), countTo: Number(summary.avg_order_value), format: formatMoney },
    { label: "Customers", value: String(summary.customers_count), countTo: Number(summary.customers_count), format: (n) => String(Math.round(n)) },
    { label: "Active sellers", value: String(summary.active_sellers), countTo: Number(summary.active_sellers), format: (n) => String(Math.round(n)) },
    { label: "Commission earned", value: formatMoney(summary.total_commission), countTo: Number(summary.total_commission), format: formatMoney },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
      {stats.map((s, i) => (
        <StatCard key={s.label} {...s} trend={i === 0 ? trend : null} />
      ))}
    </div>
  );
}

function StatCard({
  label,
  value,
  countTo,
  format,
  spark,
  trend,
}: {
  label: string;
  value: string;
  countTo?: number;
  format?: (n: number) => string;
  spark?: number[];
  trend?: number | null;
}) {
  const animated = useCountUp(countTo ?? null);
  const display = countTo !== undefined && format ? format(animated) : value;
  const path = useMemo(() => {
    if (!spark || spark.length < 2) return null;
    const w = 96;
    const h = 32;
    const max = Math.max(...spark, 1);
    const min = Math.min(...spark);
    const range = Math.max(max - min, 1);
    const pts = spark.map((v, i) => [
      (i / (spark.length - 1)) * w,
      h - 4 - ((v - min) / range) * (h - 8),
    ]);
    let d = `M ${pts[0][0]},${pts[0][1]}`;
    for (let i = 1; i < pts.length; i++) {
      const [x0, y0] = pts[i - 1];
      const [x1, y1] = pts[i];
      const mx = (x0 + x1) / 2;
      d += ` C ${mx},${y0} ${mx},${y1} ${x1},${y1}`;
    }
    return { d, id: `spark-${label.replace(/\s+/g, "-").toLowerCase()}` };
  }, [spark, label]);

  return (
    <Card>
      <CardBody className="px-4 py-4">
        <div className="flex items-center justify-between">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
              <path d={ICONS[label] ?? ICONS.Revenue} />
            </svg>
          </span>
          {trend !== null && trend !== undefined && (
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                trend >= 0
                  ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
                  : "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300"
              }`}
            >
              {trend >= 0 ? "▲" : "▼"} {Math.abs(trend)}%
            </span>
          )}
        </div>
        <p className="mt-3 text-xs font-medium text-slate-500 dark:text-slate-400">{label}</p>
        <p className="mt-0.5 text-lg font-semibold tabular-nums text-slate-900 dark:text-slate-100">{display}</p>
        {path && (
          <svg className="mt-2 h-8 w-full" viewBox="0 0 96 32" preserveAspectRatio="none" aria-hidden="true">
            <defs>
              <linearGradient id={path.id} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#818cf8" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#818cf8" stopOpacity={0} />
              </linearGradient>
            </defs>
            <path d={`${path.d} L 96,32 L 0,32 Z`} fill={`url(#${path.id})`} />
            <path d={path.d} fill="none" stroke="#6366f1" strokeWidth={1.6} strokeLinecap="round" />
          </svg>
        )}
      </CardBody>
    </Card>
  );
}

function RevenueChart({ points }: { points: DashboardData["revenue_over_time"] }) {
  const data = useMemo(
    () => points.map((p) => ({ date: p.date, value: Number(p.value) })),
    [points],
  );
  return (
    <Card>
      <CardHeader title="Revenue" subtitle="Daily revenue over the selected period" />
      <CardBody>
        {data.length === 0 ? (
          <EmptyState title="No revenue yet" description="Revenue will appear once orders are delivered." />
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
                <defs>
                  <linearGradient id="revenue-fill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6366f1" stopOpacity={0.28} />
                    <stop offset="100%" stopColor="#6366f1" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-slate-200 dark:text-slate-800" vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: "#94a3b8" }}
                  tickLine={false}
                  axisLine={false}
                  minTickGap={32}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: "#94a3b8" }}
                  tickLine={false}
                  axisLine={false}
                  width={56}
                  tickFormatter={(v: number) =>
                    v >= 1000 ? `$${(v / 1000).toFixed(v >= 10000 ? 0 : 1)}k` : `$${v}`
                  }
                />
                <Tooltip
                  animationDuration={150}
                  content={({ active, payload, label }) => {
                    if (!active || !payload?.length) return null;
                    return (
                      <div className="origin-bottom-left animate-scale-in rounded-lg border border-slate-200/80 bg-white px-3 py-2 shadow-[var(--shadow-raised)] dark:border-slate-700 dark:bg-slate-900">
                        <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</p>
                        <p className="text-sm font-semibold tabular-nums text-slate-900 dark:text-slate-100">
                          {formatMoney(Number(payload[0].value))}
                        </p>
                      </div>
                    );
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#6366f1"
                  strokeWidth={2}
                  fill="url(#revenue-fill)"
                  animationDuration={450}
                  animationEasing="ease-out"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardBody>
    </Card>
  );
}

function TopProducts({ items }: { items: DashboardData["top_products"] }) {
  return (
    <Card>
      <CardHeader title="Top products" />
      <CardBody>
        {items.length === 0 ? (
          <EmptyState title="No data" description="No products sold in this period." />
        ) : (
          <ul className="divide-y divide-slate-100 dark:divide-slate-800">
            {items.map((item) => (
              <li key={item.id} className="flex items-center justify-between gap-3 py-2.5">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">{item.name}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{item.orders} orders</p>
                </div>
                <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">{formatMoney(item.value)}</span>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}

function TopSellers({ items }: { items: DashboardData["top_sellers"] }) {
  return (
    <Card>
      <CardHeader title="Top sellers" />
      <CardBody>
        {items.length === 0 ? (
          <EmptyState title="No data" description="No sellers with sales in this period." />
        ) : (
          <ul className="divide-y divide-slate-100 dark:divide-slate-800">
            {items.map((item) => (
              <li key={item.id} className="flex items-center justify-between gap-3 py-2.5">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                    {item.name.slice(0, 2).toUpperCase()}
                  </div>
                  <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">{item.name}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-500 dark:text-slate-400">{item.orders} orders</span>
                  <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">{formatMoney(item.value)}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}

const STATUS_PIE_COLORS: Record<string, string> = {
  pending: "#f59e0b",
  confirmed: "#3b82f6",
  processing: "#6366f1",
  shipped: "#a855f7",
  delivered: "#10b981",
  cancelled: "#ef4444",
};

function RevenueComparisonCard({ comparison }: { comparison: DashboardData["revenue_comparison"] }) {
  const change = Number(comparison.change_percent);
  const up = change >= 0;
  return (
    <Card>
      <CardHeader title="Revenue comparison" subtitle="This period vs previous period" />
      <CardBody className="flex h-full flex-col justify-center">
        <div className="flex items-end gap-6">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400 dark:text-slate-500">This period</p>
            <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">{formatMoney(comparison.current)}</p>
          </div>
          <div className="pb-1">
            <p className="text-xs uppercase tracking-wide text-slate-400 dark:text-slate-500">Previous</p>
            <p className="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">{formatMoney(comparison.previous)}</p>
          </div>
        </div>
        <span
          className={`mt-4 inline-flex w-fit items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${
            up
              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
              : "bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-300"
          }`}
        >
          {up ? "▲" : "▼"} {Math.abs(change)}% {up ? "increase" : "decrease"}
        </span>
        {Number(comparison.previous) === 0 && Number(comparison.current) === 0 && (
          <p className="mt-4 text-xs text-slate-400 dark:text-slate-500">No revenue in either period yet.</p>
        )}
      </CardBody>
    </Card>
  );
}

function RecentOrders({ items }: { items: DashboardData["recent_orders"] }) {
  return (
    <Card>
      <CardHeader
        title="Recent orders"
        actions={
          <Link href="/dashboard/orders" className="text-xs font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400">
            View all
          </Link>
        }
      />
      <CardBody className="px-2 py-1">
        {items.length === 0 ? (
          <div className="px-3 py-8">
            <EmptyState title="No orders" description="Orders will appear here as they are created." />
          </div>
        ) : (
          <ul className="divide-y divide-slate-100 dark:divide-slate-800">
            {items.map((o) => (
              <li key={o.id} className="flex items-center justify-between gap-3 px-3 py-2.5">
                <div className="min-w-0">
                  <p className="font-mono text-xs font-semibold text-indigo-600 dark:text-indigo-400">{o.order_number}</p>
                  <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">{o.customer_name}</p>
                  <p className="text-xs text-slate-400 dark:text-slate-500">{formatDate(o.created_at)}</p>
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  <Badge className={badgeClass(ORDER_STATUS_COLORS, o.status)}>{o.status}</Badge>
                  <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">{formatMoney(o.total)}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}

function LowStockCard({ items }: { items: DashboardData["low_stock_products"] }) {
  return (
    <Card>
      <CardHeader
        title="Low stock"
        subtitle="Products at or below their threshold"
        actions={
          <Link href="/dashboard/inventory" className="text-xs font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400">
            View inventory
          </Link>
        }
      />
      <CardBody className="px-2 py-1">
        {items.length === 0 ? (
          <div className="px-3 py-8">
            <EmptyState title="All stocked up" description="No products are running low." />
          </div>
        ) : (
          <ul className="divide-y divide-slate-100 dark:divide-slate-800">
            {items.map((p) => (
              <li key={p.id} className="flex items-center justify-between gap-3 px-3 py-2.5">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">{p.name}</p>
                  <p className="text-xs text-slate-400 dark:text-slate-500">{p.sku}</p>
                </div>
                <Badge
                  className={
                    p.stock_quantity === 0
                      ? "bg-red-100 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800"
                      : "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800"
                  }
                >
                  {p.stock_quantity} left
                </Badge>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}

function StatusDistribution({ items }: { items: DashboardData["status_distribution"] }) {
  const total = items.reduce((acc, i) => acc + i.count, 0);
  const data = items.map((i) => ({ name: i.status, value: i.count }));
  return (
    <Card>
      <CardHeader title="Order status" subtitle="Distribution of orders in this period" />
      <CardBody>
        {data.length === 0 ? (
          <EmptyState title="No orders" description="Order statuses will appear once orders exist." />
        ) : (
          <div className="flex flex-col items-center gap-4 sm:flex-row">
            <div className="h-44 w-44 shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={48}
                    outerRadius={76}
                    paddingAngle={3}
                    strokeWidth={0}
                    animationDuration={500}
                    animationEasing="ease-out"
                  >
                    {data.map((entry) => (
                      <Cell key={entry.name} fill={STATUS_PIE_COLORS[entry.name] ?? "#94a3b8"} />
                    ))}
                  </Pie>
                  <Tooltip
                    animationDuration={150}
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      const p = payload[0];
                      return (
                        <div className="animate-scale-in rounded-xl border border-slate-200 bg-white px-3 py-2 shadow-[var(--shadow-overlay)] dark:border-slate-700 dark:bg-slate-900">
                          <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{p.name}</p>
                          <p className="text-sm font-semibold tabular-nums text-slate-900 dark:text-slate-100">
                            {p.value} order{p.value === 1 ? "" : "s"}
                          </p>
                        </div>
                      );
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <ul className="w-full flex-1 space-y-1.5">
              {data.map((d) => (
                <li key={d.name} className="flex items-center justify-between gap-2 text-sm">
                  <span className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: STATUS_PIE_COLORS[d.name] ?? "#94a3b8" }} />
                    {d.name}
                  </span>
                  <span className="font-medium text-slate-900 dark:text-slate-100">
                    {d.value}
                    <span className="ml-1 text-xs text-slate-400 dark:text-slate-500">
                      ({total ? Math.round((d.value / total) * 100) : 0}%)
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardBody>
    </Card>
  );
}