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
import { useTheme } from "@/lib/theme";

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
  const { theme, toggle: toggleTheme } = useTheme();
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
  const isStaff = Boolean(user && user.permissions.length > 0);

  return (
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
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              aria-label="Toggle theme"
              className="rounded-xl p-2.5 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 active:scale-[0.98] dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
            >
              {theme === "dark" ? (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
                </svg>
              ) : (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
                </svg>
              )}
            </button>

            {/* Seller Workspace / Dashboard Link (Staff / Admins only) */}
            {isStaff && (
              <Link
                href="/dashboard"
                className="hidden items-center gap-1.5 rounded-xl border border-indigo-200 bg-indigo-50/80 px-3 py-1.5 text-xs font-semibold text-indigo-700 transition hover:bg-indigo-600 hover:text-white active:scale-[0.98] md:flex dark:border-indigo-900/60 dark:bg-indigo-950/50 dark:text-indigo-300 dark:hover:bg-indigo-600 dark:hover:text-white"
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
                </svg>
                Dashboard
              </Link>
            )}

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
                      {isStaff && (
                        <Link
                          href="/dashboard"
                          onClick={() => setUserMenuOpen(false)}
                          className="block px-4 py-2 text-xs font-medium text-indigo-600 hover:bg-indigo-50 dark:text-indigo-400 dark:hover:bg-indigo-950/40"
                        >
                          Go to Dashboard
                        </Link>
                      )}
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

      {heroVisible && (
        <div className="border-t border-indigo-100/60 bg-gradient-to-br from-indigo-600 via-indigo-500 to-violet-600 dark:border-indigo-900/60 dark:from-indigo-900 dark:via-indigo-800 dark:to-violet-900">
          <div className="mx-auto flex max-w-7xl flex-col items-start gap-4 px-4 py-10 sm:px-6 sm:py-14 lg:px-8">
            <span className="flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-indigo-100 backdrop-blur-sm">
              <SparklesIcon className="h-3 w-3" />
              {featuredCount !== null ? `${featuredCount} featured products` : "New arrivals weekly"}
            </span>
            <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Elevate your everyday
            </h1>
            <p className="max-w-xl text-sm leading-relaxed text-indigo-100 sm:text-base">
              Discover a curated catalog of essentials and tech worth owning — free shipping on
              orders over $150.
            </p>
            <a
              href="#catalog"
              className="mt-1 rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-indigo-700 shadow-sm transition hover:bg-indigo-50 active:scale-[0.98] dark:bg-slate-900 dark:text-white dark:hover:bg-slate-800"
            >
              Shop the collection
            </a>
          </div>
        </div>
      )}
    </header>
  );
}