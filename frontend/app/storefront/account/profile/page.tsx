"use client";

import Link from "next/link";
import { useState } from "react";

import { useCustomerAuth } from "@/lib/customer-auth";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import type { CustomerMe } from "@/lib/types";

function ProfileForm({ customer }: { customer: CustomerMe }) {
  const { updateProfile } = useCustomerAuth();
  const [first_name, setFirstName] = useState(customer.first_name);
  const [last_name, setLastName] = useState(customer.last_name);
  const [phone, setPhone] = useState(customer.phone ?? "");
  const [address, setAddress] = useState(customer.address ?? "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const payload: Record<string, string> = {};
      if (first_name.trim() !== customer.first_name) payload.first_name = first_name.trim();
      if (last_name.trim() !== customer.last_name) payload.last_name = last_name.trim();
      if (phone.trim() !== (customer.phone ?? "")) payload.phone = phone.trim();
      if (address.trim() !== (customer.address ?? "")) payload.address = address.trim();
      if (newPassword) {
        if (newPassword.length < 8) {
          setError("New password must be at least 8 characters");
          return;
        }
        payload.current_password = currentPassword;
        payload.password = newPassword;
      }
      if (Object.keys(payload).length === 0) return;
      await updateProfile(payload);
      setCurrentPassword("");
      setNewPassword("");
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-8">
      <h3 className="text-lg font-bold text-slate-900 dark:text-white">
        Personal Information
      </h3>
      <p className="text-xs text-slate-500 dark:text-slate-400">
        Update your contact details for faster checkouts.
      </p>

      {savedSuccess && (
        <div className="mt-4 rounded-xl bg-emerald-50 p-3 text-xs font-semibold text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
          Profile information updated successfully!
        </div>
      )}
      {error && (
        <div className="mt-4 rounded-xl bg-red-50 p-3 text-xs font-semibold text-red-700 dark:bg-red-950/40 dark:text-red-300">
          {error}
        </div>
      )}

      <form onSubmit={handleSaveProfile} className="mt-6 space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              First Name
            </label>
            <input
              type="text"
              required
              value={first_name}
              onChange={(e) => setFirstName(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none dark:border-slate-800 dark:bg-slate-800 dark:text-white"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Last Name
            </label>
            <input
              type="text"
              required
              value={last_name}
              onChange={(e) => setLastName(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none dark:border-slate-800 dark:bg-slate-800 dark:text-white"
            />
          </div>
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Email Address
          </label>
          <input
            type="email"
            disabled
            value={customer.email}
            className="mt-1 w-full cursor-not-allowed rounded-xl border border-slate-200 bg-slate-100 p-2.5 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-400"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Phone Number
          </label>
          <input
            type="tel"
            placeholder="+998 90 123 45 67"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none dark:border-slate-800 dark:bg-slate-800 dark:text-white"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Delivery Address
          </label>
          <input
            type="text"
            placeholder="Street, city, country"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none dark:border-slate-800 dark:bg-slate-800 dark:text-white"
          />
        </div>

        <div className="border-t border-slate-100 pt-4 dark:border-slate-800">
          <h4 className="text-sm font-bold text-slate-900 dark:text-white">Change password</h4>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Leave blank to keep your current password.
          </p>
          <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Current Password
              </label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="••••••••"
                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none dark:border-slate-800 dark:bg-slate-800 dark:text-white"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                New Password
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="At least 8 characters"
                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none dark:border-slate-800 dark:bg-slate-800 dark:text-white"
              />
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-indigo-500 active:scale-[0.98] disabled:opacity-60"
        >
          {saving ? "Saving…" : "Save Changes"}
        </button>
      </form>
    </div>
  );
}

export default function CustomerProfilePage() {
  const { customer, logout } = useCustomerAuth();

  const fullName = customer ? [customer.first_name, customer.last_name].filter(Boolean).join(" ") : "";
  const initials = (fullName || "CU").slice(0, 2).toUpperCase();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 selection:bg-indigo-500 selection:text-white dark:bg-slate-950 dark:text-slate-100">
      {/* Sticky Header */}
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-900/95">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4">
            <Link
              href="/storefront"
              className="flex items-center gap-2 text-sm font-semibold text-slate-600 transition hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
              Back to store
            </Link>
            <div className="h-4 w-px bg-slate-200 dark:bg-slate-800" />
            <h1 className="text-base font-bold text-slate-900 dark:text-white sm:text-lg">
              Account Profile
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link
              href="/storefront/orders"
              className="rounded-xl border border-slate-200 px-3.5 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-100 dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              My Orders
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
          {/* Profile Sidebar */}
          <div className="md:col-span-1 space-y-4">
            <div className="rounded-3xl border border-slate-200 bg-white p-6 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-indigo-100 text-2xl font-black text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                {initials}
              </div>
              <h2 className="mt-4 font-bold text-slate-900 dark:text-white">
                {fullName || "Customer"}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">{customer?.email}</p>
              <span className="mt-2 inline-block rounded-full bg-slate-100 px-3 py-0.5 text-[10px] font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                Customer Account
              </span>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <Link
                href="/storefront/orders"
                className="flex items-center justify-between rounded-xl px-3 py-2.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                <span>📦 Order History</span>
                <span className="text-slate-400">➔</span>
              </Link>
              <Link
                href="/storefront"
                className="flex items-center justify-between rounded-xl px-3 py-2.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                <span>🛍️ Store Catalog</span>
                <span className="text-slate-400">➔</span>
              </Link>
              <button
                type="button"
                onClick={() => void logout()}
                className="flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-xs font-semibold text-red-600 transition hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/40"
              >
                <span>Sign out</span>
                <span className="text-slate-400">➔</span>
              </button>
            </div>
          </div>

          {/* Profile Forms */}
          <div className="md:col-span-2 space-y-6">
            {customer ? (
              <ProfileForm key={customer.id} customer={customer} />
            ) : (
              <div className="rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Please{" "}
                  <Link
                    href="/storefront/auth/login"
                    className="font-semibold text-indigo-600 dark:text-indigo-400"
                  >
                    sign in
                  </Link>{" "}
                  to manage your profile.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}