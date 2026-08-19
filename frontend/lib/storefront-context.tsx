"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";

import { customerRequest } from "@/lib/customer-auth";
import { sfPath } from "@/lib/storefront-slug";
import type { CartRead, CartItemRead, StorefrontProduct } from "@/lib/types";

export interface CartItem {
  product: StorefrontProduct;
  quantity: number;
  serverId?: string;
}

function toCartItem(item: CartItemRead): CartItem {
  return {
    product: {
      id: item.product_id,
      name: item.name,
      category: "",
      price: item.price,
      stock_quantity: item.stock_quantity,
      stock_status: item.stock_quantity > 0 ? "in_stock" : "out_of_stock",
      image_url: item.image_url,
      brand_name: null,
      rating: null,
      review_count: 0,
      featured: false,
    },
    quantity: item.quantity,
    serverId: item.id,
  };
}

interface StorefrontContextValue {
  cart: CartItem[];
  addToCart: (product: StorefrontProduct, quantity?: number) => void;
  removeFromCart: (productId: string) => void;
  setQuantity: (productId: string, quantity: number) => void;
  clearCart: () => void;
  cartCount: number;
  cartSubtotal: number;
  cartDiscount: number;
  freeShippingThreshold: number;
  shippingCost: number;
  cartTotal: number;
  wishlist: StorefrontProduct[];
  toggleWishlist: (product: StorefrontProduct) => void;
  isWishlisted: (productId: string) => boolean;
  recentlyViewed: string[];
  viewedProducts: Record<string, StorefrontProduct>;
  pushRecentlyViewed: (id: string, product?: StorefrontProduct) => void;
  clearRecentlyViewed: () => void;
  promo: string | null;
  applyPromo: (code: string) => void;
}

const StorefrontContext = createContext<StorefrontContextValue | null>(null);

const CART_KEY = "sms_cart";
const WISHLIST_KEY = "sms_wishlist";
const PROMO_KEY = "sms_promo";

const MAX_RECENTLY_VIEWED = 8;
export const FREE_SHIPPING_THRESHOLD = 150;
const SHIPPING_FLAT = 9.99;
const PROMO_DISCOUNT = 0.1;

function readStorage<T>(key: string): T | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

function writeStorage(key: string, value: unknown): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // storage full or unavailable — ignore
  }
}

export function toNumber(value: string | number): number {
  return typeof value === "number" ? value : parseFloat(value) || 0;
}

export function StorefrontProvider({ children }: { children: ReactNode }) {
  const [cart, setCart] = useState<CartItem[]>([]);
  const [wishlist, setWishlist] = useState<StorefrontProduct[]>([]);
  const [recentlyViewed, setRecentlyViewed] = useState<string[]>([]);
  const [viewedProducts, setViewedProducts] = useState<Record<string, StorefrontProduct>>({});
  const [promo, setPromo] = useState<string | null>(null);
  const cartRef = useRef<CartItem[]>([]);

  useEffect(() => {
    cartRef.current = cart;
  }, [cart]);

  useEffect(() => {
    const t = setTimeout(() => {
      setCart(readStorage<CartItem[]>(CART_KEY) ?? []);
      setWishlist(readStorage<StorefrontProduct[]>(WISHLIST_KEY) ?? []);
      setPromo(readStorage<string>(PROMO_KEY) ?? null);
    }, 0);
    return () => clearTimeout(t);
  }, []);

  // Sync the persisted cart with the backend cart (guest or customer) once.
  useEffect(() => {
    let cancelled = false;
    async function syncFromServer() {
      try {
        const path = await sfPath("/cart");
        const res = await customerRequest<CartRead>(path);
        if (cancelled) return;
        setCart((prev) => {
          const server = res.items.map(toCartItem);
          const merged = [...server];
          for (const local of prev) {
            if (!merged.some((m) => m.product.id === local.product.id)) {
              merged.push(local);
            }
          }
          return merged;
        });
      } catch {
        // backend unavailable — keep the local cart
      }
    }
    void syncFromServer();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    writeStorage(CART_KEY, cart);
  }, [cart]);

  useEffect(() => {
    writeStorage(WISHLIST_KEY, wishlist);
  }, [wishlist]);

  useEffect(() => {
    writeStorage(PROMO_KEY, promo);
  }, [promo]);

  const addToCart = useCallback((product: StorefrontProduct, quantity = 1) => {
    setCart((prev) => {
      const existing = prev.find((i) => i.product.id === product.id);
      if (existing) {
        return prev.map((i) =>
          i.product.id === product.id ? { ...i, quantity: i.quantity + quantity } : i,
        );
      }
      return [...prev, { product, quantity }];
    });
    void (async () => {
      try {
        const path = await sfPath("/cart/items");
        const res = await customerRequest<CartRead>(path, {
          method: "POST",
          body: { product_id: product.id, quantity },
        });
        setCart(res.items.map(toCartItem));
      } catch {
        // keep the optimistic local cart if the backend is unavailable
      }
    })();
  }, []);

  const removeFromCart = useCallback((productId: string) => {
    const serverId = cartRef.current.find((i) => i.product.id === productId)?.serverId;
    setCart((prev) => prev.filter((i) => i.product.id !== productId));
    void (async () => {
      try {
        const path = serverId
          ? await sfPath(`/cart/items/${serverId}`)
          : await sfPath("/cart");
        const res = await customerRequest<CartRead>(path, { method: "DELETE" });
        setCart(res.items.map(toCartItem));
      } catch {
        // keep local state
      }
    })();
  }, []);

  const setQuantity = useCallback((productId: string, quantity: number) => {
    const serverId = cartRef.current.find((i) => i.product.id === productId)?.serverId;
    setCart((prev) =>
      quantity <= 0
        ? prev.filter((i) => i.product.id !== productId)
        : prev.map((i) => (i.product.id === productId ? { ...i, quantity } : i)),
    );
    void (async () => {
      if (!serverId) return;
      try {
        const path = await sfPath(`/cart/items/${serverId}`);
        const res = await customerRequest<CartRead>(path, {
          method: "PATCH",
          body: { quantity },
        });
        setCart(res.items.map(toCartItem));
      } catch {
        // keep local state
      }
    })();
  }, []);

  const clearCart = useCallback(() => {
    setCart([]);
    void (async () => {
      try {
        const path = await sfPath("/cart");
        const res = await customerRequest<CartRead>(path, { method: "DELETE" });
        setCart(res.items.map(toCartItem));
      } catch {
        // keep local state
      }
    })();
  }, []);

  const toggleWishlist = useCallback((product: StorefrontProduct) => {
    setWishlist((prev) =>
      prev.some((p) => p.id === product.id)
        ? prev.filter((p) => p.id !== product.id)
        : [product, ...prev],
    );
  }, []);

  const isWishlisted = useCallback(
    (productId: string) => wishlist.some((p) => p.id === productId),
    [wishlist],
  );

  const pushRecentlyViewed = useCallback((id: string, product?: StorefrontProduct) => {
    setRecentlyViewed((prev) => [id, ...prev.filter((x) => x !== id)].slice(0, MAX_RECENTLY_VIEWED));
    if (product) {
      setViewedProducts((prev) => ({ ...prev, [id]: product }));
    }
  }, []);

  const clearRecentlyViewed = useCallback(() => {
    setRecentlyViewed([]);
  }, []);

  const applyPromo = useCallback((code: string) => {
    const clean = code.trim().toUpperCase();
    if (clean === "SAVE10") {
      setPromo("SAVE10");
      return;
    }
    throw new Error("Invalid promo code");
  }, []);

  const cartSubtotal = useMemo(
    () => cart.reduce((sum, i) => sum + toNumber(i.product.price) * i.quantity, 0),
    [cart],
  );
  const cartDiscount = useMemo(
    () => (promo ? cartSubtotal * PROMO_DISCOUNT : 0),
    [promo, cartSubtotal],
  );
  const shippingCost = useMemo(() => {
    if (cart.length === 0) return 0;
    return cartSubtotal - cartDiscount >= FREE_SHIPPING_THRESHOLD ? 0 : SHIPPING_FLAT;
  }, [cart.length, cartSubtotal, cartDiscount]);
  const cartTotal = useMemo(
    () => cartSubtotal - cartDiscount + shippingCost,
    [cartSubtotal, cartDiscount, shippingCost],
  );
  const cartCount = useMemo(() => cart.reduce((sum, i) => sum + i.quantity, 0), [cart]);

  const value = useMemo<StorefrontContextValue>(
    () => ({
      cart,
      addToCart,
      removeFromCart,
      setQuantity,
      clearCart,
      cartCount,
      cartSubtotal,
      cartDiscount,
      freeShippingThreshold: FREE_SHIPPING_THRESHOLD,
      shippingCost,
      cartTotal,
      wishlist,
      toggleWishlist,
      isWishlisted,
      recentlyViewed,
      viewedProducts,
      pushRecentlyViewed,
      clearRecentlyViewed,
      promo,
      applyPromo,
    }),
    [
      cart,
      addToCart,
      removeFromCart,
      setQuantity,
      clearCart,
      cartCount,
      cartSubtotal,
      cartDiscount,
      shippingCost,
      cartTotal,
      wishlist,
      toggleWishlist,
      isWishlisted,
      recentlyViewed,
      viewedProducts,
      pushRecentlyViewed,
      clearRecentlyViewed,
      promo,
      applyPromo,
    ],
  );

  return <StorefrontContext.Provider value={value}>{children}</StorefrontContext.Provider>;
}

export function useStorefront(): StorefrontContextValue {
  const ctx = useContext(StorefrontContext);
  if (!ctx) throw new Error("useStorefront must be used within StorefrontProvider");
  return ctx;
}