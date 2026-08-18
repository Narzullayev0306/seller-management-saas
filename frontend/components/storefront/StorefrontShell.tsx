"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  BagIcon,
  ChevronDownIcon,
  HeartIcon,
  SearchIcon,
  SparklesIcon,
  StoreIcon,
  TagIcon,
  XIcon,
} from "@/components/storefront/icons";
import { useAuth } from "@/lib/auth";
import { useStorefront } from "@/lib/storefront-context";
import { ThemeToggle } from "@/components/ui/theme-toggle";

interface StorefrontShellProps {
  onSearch: (value: string) => void;
  onOpenCart: () => void;
  onOpenWishlist: () => void;
  onOpenBrands: () => void;
  categories: string[];
  activeCategory: string | null;
  activeBrand: string | null;
  onSelectCategory: (category: string | null) => void;
  onClearFilters: () => void;
  featuredCount: number | null;
}

export function StorefrontShell({
  onSearch,
  onOpenCart,
  onOpenWishlist,
  onOpenBrands,
  categories,
  activeCategory,
  activeBrand,
  onSelectCategory,
  onClearFilters,
  featuredCount,
}: StorefrontShellProps) {
  const { user, logout } = useAuth();
  const { cartCount, wishlist } = useStorefront();
  const [searchInput, setSearchInput] = useState("");
  const [categoriesOpen, setCategoriesOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => {
      onSearch(searchInput);
    }, 350);
    return () => clearTimeout(t);
  }, [searchInput, onSearch]);

  const heroVisible = searchInput.trim() === "" && !activeCategory && !activeBrand;

  return (
    <>
      {/* Sticky Top Navbar Only */}
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-900/95">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between gap-3 sm:gap-6">
            <button
              type="button"
              onClick={onClearFilters}
              className="flex shrink-0 items-center gap-2.5"
              aria-label="TechMart home"
            >
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-sm font-bold text-white shadow-sm">
                S
              </span>
              <span className="hidden text-lg font-bold tracking-tight text-slate-900 dark:text-white sm:block">
                Tech<span className="text-indigo-600 dark:text-indigo-400">Mart</span>
              </span>
            </button>

            <nav className="hidden shrink-0 items-center gap-1 text-sm font-medium text-slate-600 dark:text-slate-300 md:flex">
              <a
                href="#catalog"
                className="rounded-xl px-3 py-2 transition hover:bg-slate-100 hover:text-slate-900 active:scale-[0.98] dark:hover:bg-slate-800 dark:hover:text-white"
              >
                Shop
              </a>
              <button
                type="button"
                onClick={onOpenBrands}
                className="flex items-center gap-1.5 rounded-xl px-3 py-2 transition hover:bg-slate-100 hover:text-slate-900 active:scale-[0.98] dark:hover:bg-slate-800 dark:hover:text-white"
              >
                <StoreIcon className="h-4 w-4" />
                Brands
              </button>
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setCategoriesOpen((v) => !v)}
                  className="flex items-center gap-1.5 rounded-xl px-3 py-2 transition hover:bg-slate-100 hover:text-slate-900 active:scale-[0.98] dark:hover:bg-slate-800 dark:hover:text-white"
                >
                  <TagIcon className="h-4 w-4" />
                  Categories
                  <ChevronDownIcon className="h-3.5 w-3.5" />
                </button>
                {categoriesOpen && (
                  <div className="absolute left-0 top-full mt-2 w-56 animate-in fade-in zoom-in-95 duration-150 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-xl dark:border-slate-800 dark:bg-slate-900">
                    <button
                      type="button"
                      onClick={() => {
                        onSelectCategory(null);
                        setCategoriesOpen(false);
                      }}
                      className="block w-full rounded-xl px-3 py-2 text-left text-sm text-slate-700 transition hover:bg-indigo-50 hover:text-indigo-700 active:scale-[0.98] dark:text-slate-300 dark:hover:bg-indigo-950/40 dark:hover:text-indigo-400"
                    >
                      All categories
                    </button>
                    {categories.map((cat) => (
                      <button
                        key={cat}
                        type="button"
                        onClick={() => {
                          onSelectCategory(cat);
                          setCategoriesOpen(false);
                        }}
                        className={`block w-full rounded-xl px-3 py-2 text-left text-sm transition active:scale-[0.98] ${
                          activeCategory === cat
                            ? "bg-indigo-50 font-semibold text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-400"
                            : "text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                        }`}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </nav>

            <div className="relative hidden max-w-md flex-1 sm:block">
              <SearchIcon className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search products…"
                className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm text-slate-900 placeholder:text-slate-400 transition focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-indigo-500 dark:focus:bg-slate-900"
              />
              {searchInput && (
                <button
                  type="button"
                  onClick={() => setSearchInput("")}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded-full p-1 text-slate-400 transition hover:bg-slate-200 hover:text-slate-700 active:scale-[0.98] dark:hover:bg-slate-700 dark:hover:text-slate-200"
                  aria-label="Clear search"
                >
                  <XIcon className="h-3.5 w-3.5" />
                </button>
              )}
            </div>

            <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
              <ThemeToggle />

              {/* Wishlist Button */}
              <button
                type="button"
                onClick={onOpenWishlist}
                className="relative rounded-xl p-2.5 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 active:scale-[0.98] dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                aria-label="Open wishlist"
              >
                <HeartIcon className="h-5 w-5" />
                {wishlist.length > 0 && (
                  <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
                    {wishlist.length}
                  </span>
                )}
              </button>

              {/* Cart Button */}
              <button
                type="button"
                onClick={onOpenCart}
                className="relative rounded-xl p-2.5 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 active:scale-[0.98] dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                aria-label="Open cart"
              >
                <BagIcon className="h-5 w-5" />
                {cartCount > 0 && (
                  <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-indigo-600 px-1 text-[10px] font-bold text-white">
                    {cartCount}
                  </span>
                )}
              </button>

              {/* User Account Menu / Login */}
              {user ? (
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setUserMenuOpen((o) => !o)}
                    className="flex items-center gap-2 rounded-xl p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800"
                  >
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                      {user.full_name.slice(0, 2).toUpperCase()}
                    </span>
                    <span className="hidden text-xs font-medium text-slate-700 dark:text-slate-200 lg:block max-w-28 truncate">
                      {user.full_name.split(" ")[0]}
                    </span>
                  </button>
                  {userMenuOpen && (
                    <>
                      <div className="fixed inset-0 z-10" onClick={() => setUserMenuOpen(false)} />
                      <div className="absolute right-0 z-20 mt-2 w-52 animate-in fade-in zoom-in-95 duration-150 origin-top-right rounded-2xl border border-slate-200 bg-white py-1 shadow-xl dark:border-slate-700 dark:bg-slate-900">
                        <div className="border-b border-slate-100 px-4 py-2.5 dark:border-slate-800">
                          <p className="truncate text-xs font-semibold text-slate-900 dark:text-slate-100">{user.full_name}</p>
                          <p className="truncate text-[11px] text-slate-500 dark:text-slate-400">{user.email}</p>
                          <span className="mt-1 inline-block rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                            {user.roles.map((r) => r.name).join(", ") || "Customer"}
                          </span>
                        </div>
                        <div className="py-1 border-b border-slate-100 dark:border-slate-800">
                          <Link
                            href="/storefront/orders"
                            onClick={() => setUserMenuOpen(false)}
                            className="block px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                          >
                            📦 My Orders
                          </Link>
                          <Link
                            href="/storefront/account/profile"
                            onClick={() => setUserMenuOpen(false)}
                            className="block px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                          >
                            👤 My Profile
                          </Link>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            setUserMenuOpen(false);
                            void logout();
                          }}
                          className="w-full px-4 py-2 text-left text-xs font-medium text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/40"
                        >
                          Sign out
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-1.5">
                  <Link
                    href="/login"
                    className="rounded-xl px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
                  >
                    Sign in
                  </Link>
                  <Link
                    href="/register"
                    className="rounded-xl bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-indigo-500"
                  >
                    Register
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Non-sticky, Smooth Scrollable Hero Banner */}
      {heroVisible && (
        <section className="relative overflow-hidden border-b border-indigo-100 bg-gradient-to-br from-indigo-600 via-indigo-600 to-violet-700 py-10 text-white dark:border-slate-800 dark:from-slate-900 dark:via-indigo-950 dark:to-slate-900 sm:py-14">
          <div className="pointer-events-none absolute inset-0 opacity-15">
            <div className="absolute -left-20 -top-20 h-72 w-72 rounded-full bg-white blur-3xl" />
            <div className="absolute right-0 top-0 h-96 w-96 rounded-full bg-indigo-300 blur-3xl" />
          </div>

          <div className="relative mx-auto flex max-w-7xl flex-col items-start gap-3.5 px-4 sm:px-6 lg:px-8">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-indigo-100 backdrop-blur-md dark:bg-indigo-900/60 dark:text-indigo-300">
              <SparklesIcon className="h-3.5 w-3.5" />
              {featuredCount !== null ? `${featuredCount} featured products` : "New arrivals weekly"}
            </span>

            <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
              Elevate your everyday
            </h1>

            <p className="max-w-xl text-sm leading-relaxed text-indigo-100 sm:text-base">
              Discover a curated catalog of essentials and electronics worth owning — free shipping on orders over $150.
            </p>

            <div className="mt-1 flex flex-wrap items-center gap-3">
              <a
                href="#catalog"
                className="rounded-xl bg-white px-5 py-2.5 text-sm font-bold text-indigo-700 shadow-sm transition hover:bg-indigo-50 active:scale-[0.98] dark:bg-indigo-600 dark:text-white dark:hover:bg-indigo-500"
              >
                Shop the collection
              </a>
              <button
                type="button"
                onClick={onOpenBrands}
                className="rounded-xl border border-white/20 bg-white/10 px-4 py-2.5 text-sm font-semibold text-white backdrop-blur transition hover:bg-white/20 active:scale-[0.98] dark:border-slate-700 dark:bg-slate-800/60 dark:hover:bg-slate-800"
              >
                Explore brands
              </button>
            </div>
          </div>
        </section>
      )}
    </>
  );
}