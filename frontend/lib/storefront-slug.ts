import { api } from "@/lib/api-client";

export interface StorefrontInfo {
  slug: string;
  name: string;
  currency: string;
  timezone: string;
  logo_url: string | null;
}

let cached: Promise<string | null> | null = null;

export function getStorefrontSlug(): Promise<string | null> {
  if (!cached) {
    cached = api
      .get<StorefrontInfo>("/storefront/info")
      .then((info) => (info?.slug ? info.slug : null))
      .catch(() => null);
  }
  return cached;
}

export async function sfPath(path: string): Promise<string> {
  const slug = await getStorefrontSlug();
  return slug ? `/stores/${slug}${path}` : `/storefront${path}`;
}