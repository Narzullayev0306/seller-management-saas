"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useStorefront } from "@/lib/storefront-context";
import { api } from "@/lib/api-client";
import { sfPath } from "@/lib/storefront-slug";
import { formatMoney } from "@/lib/format";
import type { StorefrontProduct, StorefrontProductDetail } from "@/lib/types";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import {
  BagIcon,
  HeartIcon,
  ImageIcon,
  SparklesIcon,
  StarIcon,
} from "@/components/storefront/icons";

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const productId = params?.id as string;

  const { addToCart, isWishlisted, toggleWishlist } = useStorefront();
  const [product, setProduct] = useState<StorefrontProductDetail | null>(null);
  const [relatedProducts, setRelatedProducts] = useState<StorefrontProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewName, setReviewName] = useState("");
  const [reviewBody, setReviewBody] = useState("");
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewSuccess, setReviewSuccess] = useState(false);
  const [addedNotice, setAddedNotice] = useState(false);

  useEffect(() => {
    if (!productId) return;
    async function loadData() {
      setLoading(true);
      try {
        const [detailPath, catalogPath] = await Promise.all([
          sfPath(`/products/${productId}`),
          sfPath("/catalog"),
        ]);
        const data = await api.get<StorefrontProductDetail>(detailPath);
        setProduct(data);
        setSelectedImage(data?.image_url || (data?.images?.[0]?.url ?? null));

        // Load related products from catalog
        if (data?.category) {
          const catalogRes = await api.get<{ items: StorefrontProduct[] }>(
            `${catalogPath}?category=${encodeURIComponent(data.category)}&page_size=4`,
          );
          if (catalogRes?.items) {
            setRelatedProducts(catalogRes.items.filter((p) => p.id !== productId));
          }
        }
      } catch {
        setProduct(null);
      } finally {
        setLoading(false);
      }
    }
    void loadData();
  }, [productId]);

  async function handleAddReview(e: React.FormEvent) {
    e.preventDefault();
    if (!reviewBody.trim() || !reviewName.trim() || !productId) return;
    setSubmittingReview(true);
    try {
      const reviewPath = await sfPath(`/products/${productId}/reviews`);
      await api.post(reviewPath, {
        rating: reviewRating,
        customer_name: reviewName,
        title: `${reviewRating} stars rating`,
        body: reviewBody,
      });
      setReviewSuccess(true);
      setReviewName("");
      setReviewBody("");
      // Reload product to show new review
      const detailPath = await sfPath(`/products/${productId}`);
      const updated = await api.get<StorefrontProductDetail>(detailPath);
      setProduct(updated);
    } catch {
      // ignore
    } finally {
      setSubmittingReview(false);
    }
  }

  const wished = product ? isWishlisted(product.id) : false;

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
          <p className="text-sm text-slate-500">Loading product details…</p>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-50 px-4 text-center dark:bg-slate-950">
        <h2 className="text-2xl font-black text-slate-900 dark:text-white">Product not found</h2>
        <p className="text-sm text-slate-500">This product is no longer available or was removed.</p>
        <Link
          href="/storefront"
          className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500"
        >
          Back to Storefront
        </Link>
      </div>
    );
  }

  const allImages = [
    ...(product.image_url ? [product.image_url] : []),
    ...(product.images?.map((i) => i.url) || []),
  ].filter((url, idx, self) => self.indexOf(url) === idx);

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
              Back to catalog
            </Link>
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

      {/* Product Showcase */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-12">
          {/* Images Gallery */}
          <div className="lg:col-span-7 space-y-4">
            <div className="relative aspect-square overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
              {selectedImage ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={selectedImage}
                  alt={product.name}
                  className="h-full w-full object-contain p-6 transition-all duration-300"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-slate-300 dark:text-slate-700">
                  <ImageIcon className="h-20 w-20" />
                </div>
              )}
            </div>

            {/* Thumbnails */}
            {allImages.length > 1 && (
              <div className="flex items-center gap-3 overflow-x-auto pb-2">
                {allImages.map((imgUrl, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setSelectedImage(imgUrl)}
                    className={`h-20 w-20 shrink-0 overflow-hidden rounded-2xl border-2 transition-all ${
                      selectedImage === imgUrl
                        ? "border-indigo-600 ring-2 ring-indigo-600/20"
                        : "border-slate-200 opacity-60 hover:opacity-100 dark:border-slate-800"
                    }`}
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={imgUrl} alt="" className="h-full w-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Product Details & Actions */}
          <div className="lg:col-span-5 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-400">
                  {product.brand_name || product.brand?.name || product.category || "Essential"}
                </span>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${
                    product.stock_status === "out_of_stock"
                      ? "bg-red-100 text-red-700 dark:bg-red-950/50 dark:text-red-300"
                      : "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300"
                  }`}
                >
                  {product.stock_status === "out_of_stock" ? "Out of stock" : "In stock"}
                </span>
              </div>

              <h1 className="text-3xl font-black tracking-tight text-slate-900 dark:text-white sm:text-4xl">
                {product.name}
              </h1>

              {/* Rating */}
              <div className="flex items-center gap-2">
                <div className="flex text-amber-400">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <StarIcon
                      key={star}
                      className={`h-4 w-4 ${
                        Number(product.rating || 5) >= star ? "fill-current" : "opacity-30"
                      }`}
                    />
                  ))}
                </div>
                <span className="text-xs font-bold text-slate-600 dark:text-slate-400">
                  {Number(product.rating || 5).toFixed(1)} ({product.review_count || product.reviews?.length || 0} reviews)
                </span>
              </div>

              {/* Price */}
              <div className="flex items-baseline gap-3">
                <span className="text-3xl font-black text-slate-900 dark:text-white">
                  {formatMoney(product.price)}
                </span>
              </div>

              {/* Description */}
              <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-300">
                {product.description || "High quality product crafted with premium grade materials. Comes with full warranty and satisfaction guarantee."}
              </p>

              {/* Quantity Picker */}
              <div className="pt-2">
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
                  Quantity
                </label>
                <div className="mt-1.5 flex items-center gap-3">
                  <div className="flex items-center rounded-xl border border-slate-200 bg-white p-1 dark:border-slate-800 dark:bg-slate-900">
                    <button
                      type="button"
                      onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                      className="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                    >
                      -
                    </button>
                    <span className="w-10 text-center text-sm font-bold text-slate-900 dark:text-white">
                      {quantity}
                    </span>
                    <button
                      type="button"
                      onClick={() => setQuantity((q) => q + 1)}
                      className="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                    >
                      +
                    </button>
                  </div>
                  <span className="text-xs text-slate-400">
                    Total: {formatMoney(Number(product.price) * quantity)}
                  </span>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="mt-8 space-y-3 pt-6 border-t border-slate-200 dark:border-slate-800">
              {addedNotice && (
                <div className="rounded-xl bg-emerald-50 p-2.5 text-center text-xs font-bold text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
                  ✓ Added {quantity} item(s) to your cart!
                </div>
              )}

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  disabled={product.stock_status === "out_of_stock"}
                  onClick={() => {
                    addToCart(product, quantity);
                    setAddedNotice(true);
                    setTimeout(() => setAddedNotice(false), 3000);
                  }}
                  className="flex-1 flex items-center justify-center gap-2 rounded-2xl bg-indigo-600 py-3.5 text-sm font-bold text-white shadow-lg shadow-indigo-600/25 transition hover:bg-indigo-500 active:scale-[0.98] disabled:opacity-50"
                >
                  <BagIcon className="h-5 w-5" />
                  Add to Cart
                </button>

                <button
                  type="button"
                  onClick={() => toggleWishlist(product)}
                  className={`flex h-12 w-12 items-center justify-center rounded-2xl border transition active:scale-[0.98] ${
                    wished
                      ? "border-red-200 bg-red-50 text-red-500 dark:border-red-950 dark:bg-red-950/40"
                      : "border-slate-200 bg-white text-slate-400 hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900"
                  }`}
                  aria-label="Wishlist"
                >
                  <HeartIcon className={`h-5 w-5 ${wished ? "fill-current" : ""}`} />
                </button>
              </div>

              <button
                type="button"
                disabled={product.stock_status === "out_of_stock"}
                onClick={() => {
                  addToCart(product, quantity);
                  router.push("/storefront");
                }}
                className="w-full rounded-2xl border border-slate-200 bg-slate-900 py-3 text-sm font-bold text-white shadow-sm transition hover:bg-slate-800 active:scale-[0.98] dark:bg-slate-800 dark:hover:bg-slate-700 disabled:opacity-50"
              >
                Go to Checkout
              </button>
            </div>
          </div>
        </div>

        {/* Customer Reviews Section */}
        <section className="mt-16 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-10">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-6 dark:border-slate-800">
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white sm:text-2xl">
                Customer Reviews
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Real feedback from verified buyers
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-10 lg:grid-cols-12 pt-8">
            {/* Reviews List */}
            <div className="lg:col-span-7 space-y-4">
              {product.reviews && product.reviews.length > 0 ? (
                product.reviews.map((rev) => (
                  <div
                    key={rev.id}
                    className="rounded-2xl border border-slate-100 bg-slate-50/50 p-4 dark:border-slate-800 dark:bg-slate-800/50"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900 dark:text-white">
                        {rev.customer_name}
                      </span>
                      <div className="flex text-amber-400">
                        {[1, 2, 3, 4, 5].map((s) => (
                          <StarIcon
                            key={s}
                            className={`h-3.5 w-3.5 ${s <= rev.rating ? "fill-current" : "opacity-30"}`}
                          />
                        ))}
                      </div>
                    </div>
                    <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                      {rev.comment || "Great product, highly recommend!"}
                    </p>
                    <span className="mt-2 block text-[10px] text-slate-400">
                      {new Date(rev.created_at).toLocaleDateString()}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-500 dark:text-slate-400 italic">
                  No reviews yet. Be the first to review this product!
                </p>
              )}
            </div>

            {/* Leave a Review Form */}
            <div className="lg:col-span-5 rounded-2xl border border-slate-200 bg-slate-50/50 p-6 dark:border-slate-800 dark:bg-slate-800/40">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Leave a Review
              </h3>

              {reviewSuccess ? (
                <div className="mt-4 rounded-xl bg-emerald-50 p-4 text-center text-xs font-semibold text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
                  Thank you! Your review has been submitted.
                </div>
              ) : (
                <form onSubmit={handleAddReview} className="mt-4 space-y-3">
                  <div>
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Rating
                    </label>
                    <div className="mt-1 flex items-center gap-1">
                      {[1, 2, 3, 4, 5].map((s) => (
                        <button
                          key={s}
                          type="button"
                          onClick={() => setReviewRating(s)}
                          className="p-1 text-amber-400 transition hover:scale-110"
                        >
                          <StarIcon className={`h-5 w-5 ${s <= reviewRating ? "fill-current" : "opacity-30"}`} />
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Your Name
                    </label>
                    <input
                      type="text"
                      required
                      value={reviewName}
                      onChange={(e) => setReviewName(e.target.value)}
                      placeholder="e.g. John Doe"
                      className="mt-1 w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Review Comment
                    </label>
                    <textarea
                      required
                      rows={3}
                      value={reviewBody}
                      onChange={(e) => setReviewBody(e.target.value)}
                      placeholder="What did you think of this product?"
                      className="mt-1 w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={submittingReview}
                    className="w-full rounded-xl bg-indigo-600 py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-indigo-500 active:scale-[0.98] disabled:opacity-50"
                  >
                    {submittingReview ? "Submitting…" : "Post Review"}
                  </button>
                </form>
              )}
            </div>
          </div>
        </section>

        {/* Related Products */}
        {relatedProducts.length > 0 && (
          <section className="mt-16">
            <div className="flex items-center gap-2 mb-6">
              <SparklesIcon className="h-5 w-5 text-indigo-600" />
              <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                You might also like
              </h2>
            </div>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {relatedProducts.map((p) => (
                <Link
                  key={p.id}
                  href={`/storefront/product/${p.id}`}
                  className="group flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white p-3 transition hover:shadow-lg dark:border-slate-800 dark:bg-slate-900"
                >
                  <div className="aspect-square w-full overflow-hidden rounded-xl bg-slate-100 dark:bg-slate-800">
                    {p.image_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={p.image_url}
                        alt={p.name}
                        className="h-full w-full object-cover transition group-hover:scale-105"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center text-slate-300">
                        <ImageIcon className="h-8 w-8" />
                      </div>
                    )}
                  </div>
                  <h4 className="mt-3 truncate text-xs font-bold text-slate-900 dark:text-white">
                    {p.name}
                  </h4>
                  <p className="mt-1 text-xs font-bold text-indigo-600 dark:text-indigo-400">
                    {formatMoney(p.price)}
                  </p>
                </Link>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
