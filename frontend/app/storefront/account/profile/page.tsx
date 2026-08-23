"use client";

import Link from "next/link";
import { useState } from "react";

import { useAuth } from "@/lib/auth";
import { ThemeToggle } from "@/components/ui/theme-toggle";

interface SavedAddress {
  id: string;
  label: string;
  street: string;
  city: string;
  zip: string;
  country: string;
  isDefault: boolean;
}

export default function CustomerProfilePage() {
  const { user } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [phone, setPhone] = useState("");
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Address state
  const [addresses, setAddresses] = useState<SavedAddress[]>([
    {
      id: "addr-1",
      label: "Home",
      street: "124 Amir Temur Avenue, Apt 4B",
      city: "Tashkent",
      zip: "100000",
      country: "Uzbekistan",
      isDefault: true,
    },
  ]);
  const [newStreet, setNewStreet] = useState("");
  const [newCity, setNewCity] = useState("");
  const [newLabel, setNewLabel] = useState("Work");
  const [showAddressForm, setShowAddressForm] = useState(false);

  // Re-sync form fields when the auth context delivers/changes the user
  // (adjust-state-on-prop-change pattern; setState during render is allowed here).
  const [syncedUser, setSyncedUser] = useState(user);
  if (user !== syncedUser) {
    setSyncedUser(user);
    setFullName(user?.full_name ?? "");
    setEmail(user?.email ?? "");
  }

  function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  }

  function handleAddAddress(e: React.FormEvent) {
    e.preventDefault();
    if (!newStreet.trim() || !newCity.trim()) return;
    const newAddr: SavedAddress = {
      id: "addr-" + Date.now(),
      label: newLabel,
      street: newStreet,
      city: newCity,
      zip: "100000",
      country: "Uzbekistan",
      isDefault: addresses.length === 0,
    };
    setAddresses([...addresses, newAddr]);
    setNewStreet("");
    setNewCity("");
    setShowAddressForm(false);
  }

  function handleDeleteAddress(id: string) {
    setAddresses(addresses.filter((a) => a.id !== id));
  }

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
                {(fullName || "Customer").slice(0, 2).toUpperCase()}
              </div>
              <h2 className="mt-4 font-bold text-slate-900 dark:text-white">
                {fullName || "Customer"}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">{email}</p>
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
            </div>
          </div>

          {/* Profile Forms */}
          <div className="md:col-span-2 space-y-6">
            {/* Personal Details */}
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

              <form onSubmit={handleSaveProfile} className="mt-6 space-y-4">
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Full Name
                  </label>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none dark:border-slate-800 dark:bg-slate-800 dark:text-white"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Email Address
                  </label>
                  <input
                    type="email"
                    disabled
                    value={email}
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-100 p-2.5 text-sm text-slate-500 cursor-not-allowed dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-400"
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

                <button
                  type="submit"
                  className="rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-indigo-500 active:scale-[0.98]"
                >
                  Save Changes
                </button>
              </form>
            </div>

            {/* Saved Shipping Addresses */}
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-8">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                    Delivery Addresses
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Manage your saved shipping locations.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setShowAddressForm(!showAddressForm)}
                  className="rounded-xl bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200"
                >
                  {showAddressForm ? "Cancel" : "+ Add New"}
                </button>
              </div>

              {/* Add address form */}
              {showAddressForm && (
                <form onSubmit={handleAddAddress} className="mt-4 space-y-3 rounded-2xl bg-slate-50 p-4 dark:bg-slate-800/50">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400">Label</label>
                      <select
                        value={newLabel}
                        onChange={(e) => setNewLabel(e.target.value)}
                        className="mt-1 w-full rounded-lg border border-slate-200 bg-white p-2 text-xs text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                      >
                        <option value="Home">Home</option>
                        <option value="Work">Work</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400">City</label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. Tashkent"
                        value={newCity}
                        onChange={(e) => setNewCity(e.target.value)}
                        className="mt-1 w-full rounded-lg border border-slate-200 bg-white p-2 text-xs text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400">Street Address</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. 45 Navoi Avenue, Apt 12"
                      value={newStreet}
                      onChange={(e) => setNewStreet(e.target.value)}
                      className="mt-1 w-full rounded-lg border border-slate-200 bg-white p-2 text-xs text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                    />
                  </div>
                  <button
                    type="submit"
                    className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-indigo-500"
                  >
                    Save Address
                  </button>
                </form>
              )}

              {/* Address cards */}
              <div className="mt-4 space-y-3">
                {addresses.map((addr) => (
                  <div
                    key={addr.id}
                    className="flex items-start justify-between rounded-2xl border border-slate-100 bg-slate-50/50 p-4 dark:border-slate-800 dark:bg-slate-800/30"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs text-slate-900 dark:text-white">
                          {addr.label}
                        </span>
                        {addr.isDefault && (
                          <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[9px] font-bold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                            Default
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-xs text-slate-600 dark:text-slate-300">
                        {addr.street}, {addr.city}
                      </p>
                      <p className="text-[11px] text-slate-400">{addr.country}</p>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleDeleteAddress(addr.id)}
                      className="text-xs text-red-500 hover:text-red-700"
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
