"use client";

import { useCallback, useEffect, useState } from "react";

import { BrandHubModal } from "@/components/storefront/BrandHubModal";
import { CartDrawer } from "@/components/storefront/CartDrawer";
import { CheckoutModal } from "@/components/storefront/CheckoutModal";
import { LayersIcon, RefreshIcon, SearchIcon } from "@/components/storefront/icons";
import { ProductCard } from "@/components/storefront/ProductCard";
import { ProductComparisonModal } from "@/components/storefront/ProductComparisonModal";
import { QuickViewModal } from "@/components/storefront/QuickViewModal";
import { RecentlyViewedDock } from "@/components/storefront/RecentlyViewedDock";
import { StorefrontShell } from "@/components/storefront/StorefrontShell";
import { WishlistDrawer } from "@/components/storefront/WishlistDrawer";
import { api } from "@/lib/api-client";
import { StorefrontProvider, useStorefront } from "@/lib/storefront-context";
import type {
  StorefrontBrand,
  StorefrontCatalogResponse,
  StorefrontProduct,
} from "@/lib/types";

const PAGE_SIZE = 12;

const SORT_OPTIONS = [
  { value: "", label: "Featured" },
  { value: "price_asc", label: "Price: Low to High" },
  { value: "price_desc", label: "Price: High to Low" },
  { value: "newest", label: "Newest" },
  { value: "popular", label: "Most Popular" },
];

interface CatalogQuery {
  search: string;
  category: string | null;
  brand: string | null;
  sort_by: string;
  page: number;
}

function SkeletonCard() {
  return (
    <div className="animate-pulse overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="aspect-square bg-slate-200 dark:bg-slate-800" />
      <div className="space-y-2.5 p-4">
        <div className="h-2.5 w-1/3 rounded-full bg-slate-200 dark:bg-slate-800" />
        <div className="h-3.5 w-2/3 rounded-full bg-slate-200 dark:bg-slate-800" />
        <div className="h-3.5 w-1/2 rounded-full bg-slate-200 dark:bg-slate-800" />
        <div className="h-8 w-full rounded-xl bg-slate-200 dark:bg-slate-800" />
      </div>
    </div>
  );
}

function StorefrontPageInner() {
  const { pushRecentlyViewed } = useStorefront();
  const [query, setQuery] = useState<CatalogQuery>({
    search: "",
    category: null,
    brand: null,
    sort_by: "",
    page: 1,
  });
  const [items, setItems] = useState<StorefrontProduct[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [allBrands, setAllBrands] = useState<StorefrontBrand[]>([]);
  const [featuredCount, setFeaturedCount] = useState<number | null>(null);

  const [quickViewProduct, setQuickViewProduct] = useState<StorefrontProduct | null>(null);
  const [cartOpen, setCartOpen] = useState(false);
  const [wishlistOpen, setWishlistOpen] = useState(false);
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [compareOpen, setCompareOpen] = useState(false);
  const [brandHubOpen, setBrandHubOpen] = useState(false);
  const [compare, setCompare] = useState<StorefrontProduct[]>([]);

  useEffect(() => {
    let cancelled = false;
    const t = setTimeout(() => {
      setLoading(true);
      api
        .get<StorefrontCatalogResponse>("/storefront/catalog", {
          page: query.page,
          page_size: PAGE_SIZE,
          search: query.search || undefined,
          category: query.category || undefined,
          brand: query.brand || undefined,
          sort_by: query.sort_by || undefined,
        })
        .then((res) => {
          if (cancelled) return;
          setItems((prev) => (query.page === 1 ? res.items : [...prev, ...res.items]));
          setTotal(res.total);
          setTotalPages(res.total_pages);
          setCategories(res.categories);
          setError("");
        })
        .catch((err: unknown) => {
          if (!cancelled) {
            setError(err instanceof Error ? err.message : "Failed to load products");
            if (query.page === 1) setItems([]);
          }
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, 0);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [query]);

  useEffect(() => {
    let cancelled = false;
    api
      .get<StorefrontCatalogResponse>("/storefront/catalog", { featured: "true", page_size: 1 })
      .then((res) => {
        if (!cancelled) setFeaturedCount(res.total);
      })
      .catch(() => {
        if (!cancelled) setFeaturedCount(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    api
      .get<StorefrontBrand[]>("/storefront/brands")
      .then((res) => {
        if (!cancelled) setAllBrands(res);
      })
      .catch(() => {
        if (!cancelled) setAllBrands([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const setSearch = useCallback((value: string) => {
    setQuery((q) => ({ ...q, search: value, page: 1 }));
  }, []);

  const setCategory = useCallback((category: string | null) => {
    setQuery((q) => ({ ...q, category, page: 1 }));
  }, []);

  const setBrand = useCallback((brand: string | null) => {
    setQuery((q) => ({ ...q, brand, page: 1 }));
  }, []);

  const clearFilters = useCallback(() => {
    setQuery((q) => ({ ...q, search: "", category: null, brand: null, page: 1 }));
  }, []);

  const setSort = (value: string) => {
    setQuery((q) => ({ ...q, sort_by: value, page: 1 }));
  };

  const loadMore = () => {
    setQuery((q) => ({ ...q, page: q.page + 1 }));
  };

  const openQuickView = useCallback(
    (product: StorefrontProduct) => {
      setQuickViewProduct(product);
      pushRecentlyViewed(product.id, product);
    },
    [pushRecentlyViewed],
  );

  const toggleCompare = (product: StorefrontProduct) => {
    setCompare((prev) =>
      prev.some((p) => p.id === product.id)
        ? prev.filter((p) => p.id !== product.id)
        : prev.length >= 4
          ? prev
          : [...prev, product],
    );
  };

  const selectBrand = (brand: StorefrontBrand) => {
    setBrand(brand.name);
    setBrandHubOpen(false);
  };

  const showSkeleton = loading && items.length === 0;
  const activeFilter = Boolean(query.search || query.category || query.brand);
  const dockVisible =
    !quickViewProduct && !cartOpen && !wishlistOpen && !checkoutOpen && !compareOpen && !brandHubOpen;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 transition-colors duration-200 dark:bg-slate-950 dark:text-slate-100">
      <StorefrontShell
        onSearch={setSearch}
        onOpenCart={() => setCartOpen(true)}
        onOpenWishlist={() => setWishlistOpen(true)}
        onOpenBrands={() => setBrandHubOpen(true)}
        categories={categories}
        activeCategory={query.category}
        activeBrand={query.brand}
        onSelectCategory={setCategory}
        onClearFilters={clearFilters}
        featuredCount={featuredCount}
      />

      <main id="catalog" className="mx-auto max-w-7xl scroll-mt-20 px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-baseline gap-2">
              <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
                {activeFilter ? "Search results" : "Catalog"}
              </h2>
              {!loading && (
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  {total} {total === 1 ? "product" : "products"}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <select
                value={query.sort_by}
                onChange={(e) => setSort(e.target.value)}
                className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:focus:ring-indigo-900/40"
              >
                {SORT_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    Sort: {opt.label}
                  </option>
                ))}
              </select>
              {activeFilter && (
                <button
                  type="button"
                  onClick={clearFilters}
                  className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 active:scale-[0.98] dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
                >
                  Clear filters
                </button>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            <button
              type="button"
              onClick={() => setCategory(null)}
              className={`whitespace-nowrap rounded-xl px-4 py-2 text-xs font-semibold transition active:scale-[0.98] ${
                !query.category
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-white text-slate-600 hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
              }`}
            >
              All
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategory(query.category === cat ? null : cat)}
                className={`whitespace-nowrap rounded-xl px-4 py-2 text-xs font-semibold transition active:scale-[0.98] ${
                  query.category === cat
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "bg-white text-slate-600 hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {error ? (
          <div className="flex flex-col items-center gap-4 rounded-2xl border border-slate-200 bg-white py-16 text-center dark:border-slate-800 dark:bg-slate-900">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-50 text-red-500 dark:bg-red-950/50 dark:text-red-400">
              <SearchIcon className="h-7 w-7" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-white">Couldn&apos;t load the catalog</h3>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{error}</p>
            </div>
            <button
              type="button"
              onClick={() => setQuery((q) => ({ ...q, page: 1 }))}
              className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700 active:scale-[0.98]"
            >
              <RefreshIcon className="h-4 w-4" />
              Try again
            </button>
          </div>
        ) : showSkeleton ? (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center gap-3 rounded-2xl border border-slate-200 bg-white py-16 text-center dark:border-slate-800 dark:bg-slate-900">
            <SearchIcon className="h-10 w-10 text-slate-300 dark:text-slate-600" />
            <h3 className="font-semibold text-slate-900 dark:text-white">No products found</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">Try a different search or clear your filters.</p>
            <button
              type="button"
              onClick={clearFilters}
              className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700 active:scale-[0.98]"
            >
              Clear filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {items.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onOpen={openQuickView}
                isCompared={compare.some((p) => p.id === product.id)}
                onToggleCompare={toggleCompare}
              />
            ))}
          </div>
        )}

        {!error && items.length > 0 && query.page < totalPages && (
          <div className="mt-10 flex justify-center">
            <button
              type="button"
              onClick={loadMore}
              disabled={loading}
              className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-indigo-300 hover:text-indigo-700 active:scale-[0.98] disabled:opacity-60 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-indigo-500/50 dark:hover:text-indigo-400"
            >
              {loading && (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
              )}
              {loading ? "Loading…" : "Load more"}
            </button>
          </div>
        )}
      </main>

      {compare.length > 0 && (
        <button
          type="button"
          onClick={() => setCompareOpen(true)}
          className="fixed bottom-4 right-4 z-30 flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-indigo-700 active:scale-[0.98]"
        >
          <LayersIcon className="h-4 w-4" />
          Compare ({compare.length})
        </button>
      )}

      <RecentlyViewedDock visible={dockVisible} onOpenProduct={openQuickView} />

      <QuickViewModal product={quickViewProduct} onClose={() => setQuickViewProduct(null)} />
      <CartDrawer
        open={cartOpen}
        onClose={() => setCartOpen(false)}
        onCheckout={() => {
          setCartOpen(false);
          setCheckoutOpen(true);
        }}
      />
      <WishlistDrawer
        open={wishlistOpen}
        onClose={() => setWishlistOpen(false)}
        onOpenProduct={openQuickView}
      />
      <CheckoutModal open={checkoutOpen} onClose={() => setCheckoutOpen(false)} />
      <ProductComparisonModal
        open={compareOpen}
        onClose={() => setCompareOpen(false)}
        products={compare}
        onClearAll={() => setCompare([])}
      />
      <BrandHubModal
        open={brandHubOpen}
        onClose={() => setBrandHubOpen(false)}
        brands={allBrands}
        onSelectBrand={selectBrand}
      />
    </div>
  );
}

export default function StorefrontPage() {
  return (
    <StorefrontProvider>
      <StorefrontPageInner />
    </StorefrontProvider>
  );
}