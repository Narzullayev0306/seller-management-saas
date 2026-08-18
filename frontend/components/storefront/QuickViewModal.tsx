"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import {
  ArrowRightIcon,
  BagIcon,
  BellIcon,
  CheckIcon,
  HeartIcon,
  ImageIcon,
  MinusIcon,
  PlusIcon,
  StarIcon,
  TrendingDownIcon,
  TrendingUpIcon,
  XIcon,
} from "@/components/storefront/icons";
import { formatDateShort, formatMoney } from "@/lib/format";
import { api } from "@/lib/api-client";
import { toNumber, useStorefront } from "@/lib/storefront-context";
import { sfPath } from "@/lib/storefront-slug";
import type { StorefrontProduct, StorefrontProductDetail } from "@/lib/types";

type TabKey = "details" | "reviews" | "price";

const STOCK_BADGES: Record<string, { label: string; className: string }> = {
  in_stock: { label: "In stock", className: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300" },
  low_stock: { label: "Low stock", className: "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300" },
  out_of_stock: { label: "Out of stock", className: "bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300" },
};

function Stars({ rating }: { rating: number | null }) {
  const value = rating !== null ? Number(rating) : null;
  return (
    <span className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <StarIcon
          key={i}
          className={`h-3.5 w-3.5 ${
            value !== null && value >= i - 0.25 ? "fill-indigo-500 text-indigo-500" : "text-slate-300 dark:text-slate-700"
          }`}
        />
      ))}
    </span>
  );
}

interface QuickViewModalProps {
  product: StorefrontProduct | null;
  onClose: () => void;
}

export function QuickViewModal({ product, onClose }: QuickViewModalProps) {
  const { addToCart, isWishlisted, toggleWishlist, pushRecentlyViewed } = useStorefront();
  const [detail, setDetail] = useState<StorefrontProductDetail | null>(null);
  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const [quantity, setQuantity] = useState(1);
  const [activeTab, setActiveTab] = useState<TabKey>("details");
  const [justAdded, setJustAdded] = useState(false);
  const [zoom, setZoom] = useState<{ x: number; y: number } | null>(null);
  const stageRef = useRef<HTMLDivElement>(null);

  const [bisEmail, setBisEmail] = useState("");
  const [bisStatus, setBisStatus] = useState<"idle" | "loading" | "done" | "error">("idle");

  useEffect(() => {
    if (!product) return;
    pushRecentlyViewed(product.id, product);
    setActiveImageIndex(0);
    setQuantity(1);
    setActiveTab("details");
    setBisStatus("idle");
    setBisEmail("");

    let cancelled = false;
    sfPath(`/products/${product.id}`).then((path) =>
      api
        .get<StorefrontProductDetail>(path)
        .then((res) => {
          if (!cancelled) setDetail(res);
        })
        .catch(() => {
          if (!cancelled) setDetail(null);
        }),
    );

    return () => {
      cancelled = true;
    };
  }, [product, pushRecentlyViewed]);

  const imageList = useMemo(() => {
    const urls: string[] = [];
    if (product?.image_url) urls.push(product.image_url);
    detail?.images.forEach((img) => {
      if (img.url && !urls.includes(img.url)) urls.push(img.url);
    });
    return urls;
  }, [product, detail]);

  if (!product) return null;

  const wished = isWishlisted(product.id);
  const badge = STOCK_BADGES[product.stock_status];
  const mainImage = imageList[Math.min(activeImageIndex, imageList.length - 1)] ?? null;
  const isOutOfStock = product.stock_status === "out_of_stock";
  const description = detail?.description ?? null;
  const reviews = detail?.reviews ?? [];
  const priceHistory = detail?.price_history ?? [];
  const brand = detail?.brand ?? null;

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = stageRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setZoom({ x: Math.max(0, Math.min(100, x)), y: Math.max(0, Math.min(100, y)) });
  };

  const handleAdd = () => {
    addToCart(product, quantity);
    setJustAdded(true);
    setTimeout(() => setJustAdded(false), 1400);
  };

  const handleBackInStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bisEmail.trim()) return;
    setBisStatus("loading");
    try {
      const path = await sfPath(`/products/${product.id}/back-in-stock`);
      await api.post(path, { email: bisEmail.trim() });
      setBisStatus("done");
    } catch {
      setBisStatus("error");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto p-3 sm:p-6">
      <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={onClose} />

      <div className="relative z-10 my-auto w-full max-w-4xl animate-in fade-in zoom-in-95 duration-200 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 z-20 flex h-9 w-9 items-center justify-center rounded-full bg-white text-slate-500 shadow-sm transition hover:text-slate-900 active:scale-[0.98] dark:bg-slate-800 dark:text-slate-400 dark:hover:text-slate-100"
          aria-label="Close"
        >
          <XIcon className="h-5 w-5" />
        </button>

        <div className="grid grid-cols-1 sm:grid-cols-2">
          <div className="space-y-4 border-b border-slate-100 bg-slate-50 p-5 sm:border-b-0 sm:border-r dark:border-slate-800 dark:bg-slate-900/60">
            <div
              ref={stageRef}
              onMouseMove={handleMouseMove}
              onMouseLeave={() => setZoom(null)}
              className="relative aspect-square w-full cursor-crosshair overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-800"
            >
              {mainImage ? (
                <>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={mainImage}
                    alt={product.name}
                    className="h-full w-full select-none object-cover"
                    draggable={false}
                  />
                  {zoom && (
                    <div
                      className="pointer-events-none absolute inset-0"
                      style={{
                        backgroundImage: `url(${mainImage})`,
                        backgroundSize: "200% 200%",
                        backgroundPosition: `${zoom.x}% ${zoom.y}%`,
                        backgroundRepeat: "no-repeat",
                      }}
                    />
                  )}
                </>
              ) : (
                <div className="flex h-full w-full items-center justify-center text-slate-300 dark:text-slate-600">
                  <ImageIcon className="h-16 w-16" />
                </div>
              )}
            </div>

            {imageList.length > 1 && (
              <div className="flex items-center gap-2.5 overflow-x-auto pb-1">
                {imageList.map((url, idx) => (
                  <button
                    key={`${url}-${idx}`}
                    type="button"
                    onClick={() => setActiveImageIndex(idx)}
                    className={`h-16 w-16 shrink-0 overflow-hidden rounded-xl border-2 bg-white transition active:scale-[0.98] dark:bg-slate-800 ${
                      activeImageIndex === idx
                        ? "border-indigo-500 ring-2 ring-indigo-100 dark:ring-indigo-950"
                        : "border-slate-200 opacity-70 hover:opacity-100 dark:border-slate-700"
                    }`}
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={url} alt={`${product.name} thumbnail`} className="h-full w-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="flex flex-col gap-4 p-5 sm:p-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                {product.brand_name ? (
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                    {product.brand_name}
                  </span>
                ) : (
                  <span />
                )}
                {badge && (
                  <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider ${badge.className}`}>
                    {badge.label}
                  </span>
                )}
              </div>
              <h2 className="text-xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">{product.name}</h2>
              <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                <Stars rating={product.rating} />
                {product.rating !== null ? (
                  <span className="font-medium text-slate-700 dark:text-slate-300">
                    {Number(product.rating).toFixed(1)}
                    <span className="text-slate-400 dark:text-slate-500"> ({product.review_count} reviews)</span>
                  </span>
                ) : (
                  <span>No reviews yet</span>
                )}
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-2xl font-bold text-slate-900 dark:text-white">{formatMoney(product.price)}</span>
              <span className="text-xs text-slate-400 dark:text-slate-500">
                {product.stock_quantity > 0 ? `${product.stock_quantity} available` : "Currently unavailable"}
              </span>
            </div>

            {description && (
              <p className="line-clamp-3 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{description}</p>
            )}

            {isOutOfStock ? (
              <form onSubmit={handleBackInStock} className="space-y-2 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-800/50">
                <p className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300">
                  <BellIcon className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                  Get notified when it&apos;s back in stock
                </p>
                {bisStatus === "done" ? (
                  <p className="flex items-center gap-1.5 rounded-xl bg-emerald-100 px-3 py-2.5 text-xs font-medium text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                    <CheckIcon className="h-4 w-4" />
                    You&apos;ll be emailed when this product is back in stock.
                  </p>
                ) : (
                  <>
                    <div className="flex gap-2">
                      <input
                        type="email"
                        required
                        value={bisEmail}
                        onChange={(e) => setBisEmail(e.target.value)}
                        placeholder="you@example.com"
                        className="flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500"
                      />
                      <button
                        type="submit"
                        disabled={bisStatus === "loading"}
                        className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-indigo-700 active:scale-[0.98] disabled:opacity-60 dark:bg-indigo-600 dark:hover:bg-indigo-500"
                      >
                        {bisStatus === "loading" ? "Sending…" : "Notify me"}
                      </button>
                    </div>
                    {bisStatus === "error" && (
                      <p className="text-[11px] font-medium text-red-600 dark:text-red-400">
                        Something went wrong — please try again.
                      </p>
                    )}
                  </>
                )}
              </form>
            ) : (
              <div className="flex items-center gap-3">
                <div className="flex shrink-0 items-center overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700">
                  <button
                    type="button"
                    onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                    className="px-3 py-2.5 text-slate-600 transition hover:bg-slate-100 active:scale-[0.98] dark:text-slate-300 dark:hover:bg-slate-700"
                    aria-label="Decrease quantity"
                  >
                    <MinusIcon className="h-3.5 w-3.5" />
                  </button>
                  <span className="min-w-8 text-center text-sm font-bold text-slate-900 dark:text-white">{quantity}</span>
                  <button
                    type="button"
                    onClick={() => setQuantity((q) => q + 1)}
                    className="px-3 py-2.5 text-slate-600 transition hover:bg-slate-100 active:scale-[0.98] dark:text-slate-300 dark:hover:bg-slate-700"
                    aria-label="Increase quantity"
                  >
                    <PlusIcon className="h-3.5 w-3.5" />
                  </button>
                </div>
                <button
                  type="button"
                  onClick={handleAdd}
                  className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 active:scale-[0.98] dark:bg-indigo-600 dark:hover:bg-indigo-500"
                >
                  {justAdded ? (
                    <>
                      <CheckIcon className="h-4 w-4" />
                      Added!
                    </>
                  ) : (
                    <>
                      <BagIcon className="h-4 w-4" />
                      Add to cart • {formatMoney(toNumber(product.price) * quantity)}
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => toggleWishlist(product)}
                  className={`shrink-0 rounded-xl border p-3 transition active:scale-[0.98] ${
                    wished
                      ? "border-red-200 bg-red-50 text-red-500 dark:border-red-900 dark:bg-red-950/50 dark:text-red-400"
                      : "border-slate-200 text-slate-500 hover:text-red-500 dark:border-slate-700 dark:text-slate-400 dark:hover:text-red-400"
                  }`}
                  aria-label={wished ? "Remove from wishlist" : "Add to wishlist"}
                >
                  <HeartIcon className={`h-4 w-4 ${wished ? "fill-current" : ""}`} />
                </button>
              </div>
            )}

            <div className="mt-1 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-5 text-xs font-semibold">
                {(
                  [
                    { key: "details", label: "Details" },
                    { key: "reviews", label: `Reviews (${reviews.length})` },
                    { key: "price", label: "Price History" },
                  ] as { key: TabKey; label: string }[]
                ).map((tab) => (
                  <button
                    key={tab.key}
                    type="button"
                    onClick={() => setActiveTab(tab.key)}
                    className={`border-b-2 pb-2.5 transition active:scale-[0.98] ${
                      activeTab === tab.key
                        ? "border-indigo-600 text-indigo-700 dark:border-indigo-400 dark:text-indigo-400"
                        : "border-transparent text-slate-400 hover:text-slate-700 dark:text-slate-500 dark:hover:text-slate-300"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="max-h-56 space-y-3 overflow-y-auto pr-1 text-sm leading-relaxed">
              {activeTab === "details" && (
                <div className="space-y-3 text-slate-600 dark:text-slate-300">
                  <p>{description ? description : "No description available for this product."}</p>
                  <div className="rounded-xl bg-slate-50 p-3 text-xs dark:bg-slate-800/50">
                    <p>
                      <span className="font-semibold text-slate-700 dark:text-slate-300">Category:</span>{" "}
                      <span className="text-slate-500 dark:text-slate-400">{product.category}</span>
                    </p>
                    {brand && (
                      <p className="mt-1">
                        <span className="font-semibold text-slate-700 dark:text-slate-300">Brand:</span>{" "}
                        <span className="text-slate-500 dark:text-slate-400">{brand.name}</span>
                      </p>
                    )}
                    {brand?.description && (
                      <p className="mt-2 text-slate-500 dark:text-slate-400">{brand.description}</p>
                    )}
                  </div>
                </div>
              )}

              {activeTab === "reviews" &&
                (reviews.length === 0 ? (
                  <div className="rounded-xl bg-slate-50 p-6 text-center dark:bg-slate-800/50">
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-300">No reviews yet</p>
                    <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                      Be the first to review this product.
                    </p>
                  </div>
                ) : (
                  reviews.map((rev) => (
                    <div key={rev.id} className="space-y-1.5 rounded-xl border border-slate-100 bg-slate-50 p-3.5 dark:border-slate-800 dark:bg-slate-800/50">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-slate-900 dark:text-slate-100">{rev.customer_name}</span>
                          <Stars rating={rev.rating} />
                        </div>
                        <span className="text-[10px] text-slate-400 dark:text-slate-500">{formatDateShort(rev.created_at)}</span>
                      </div>
                      {rev.comment && <p className="text-xs text-slate-600 dark:text-slate-300">{rev.comment}</p>}
                    </div>
                  ))
                ))}

              {activeTab === "price" &&
                (priceHistory.length === 0 ? (
                  <div className="rounded-xl bg-slate-50 p-6 text-center dark:bg-slate-800/50">
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-300">No price changes recorded</p>
                    <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                      This product&apos;s price has stayed stable.
                    </p>
                  </div>
                ) : (
                  priceHistory.map((pt, idx) => {
                    const oldPrice = toNumber(pt.old_price);
                    const newPrice = toNumber(pt.new_price);
                    const delta = newPrice - oldPrice;
                    const dropped = delta < 0;
                    return (
                      <div key={idx} className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50 px-3.5 py-3 dark:border-slate-800 dark:bg-slate-800/50">
                        <div className="flex items-center gap-2 text-xs">
                          <span className="font-medium text-slate-500 line-through dark:text-slate-400">{formatMoney(pt.old_price)}</span>
                          <ArrowRightIcon className="h-3.5 w-3.5 text-slate-400 dark:text-slate-500" />
                          <span className="font-bold text-slate-900 dark:text-slate-100">{formatMoney(pt.new_price)}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {dropped ? (
                            <span className="flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-bold text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                              <TrendingDownIcon className="h-3 w-3" />
                              −{formatMoney(Math.abs(delta))}
                            </span>
                          ) : delta > 0 ? (
                            <span className="flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-[11px] font-bold text-red-700 dark:bg-red-950/60 dark:text-red-300">
                              <TrendingUpIcon className="h-3 w-3" />
                              +{formatMoney(delta)}
                            </span>
                          ) : (
                            <span className="rounded-full bg-slate-200 px-2 py-0.5 text-[11px] font-bold text-slate-600 dark:bg-slate-700 dark:text-slate-300">
                              No change
                            </span>
                          )}
                          <span className="text-[10px] text-slate-400 dark:text-slate-500">{formatDateShort(pt.changed_at)}</span>
                        </div>
                      </div>
                    );
                  })
                ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}