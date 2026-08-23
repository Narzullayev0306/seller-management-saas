import { expect, test } from "@playwright/test";

test.describe("storefront (public)", () => {
  test("catalog is browsable without an account", async ({ page }) => {
    await page.goto("/storefront");
    await page.waitForLoadState("networkidle");

    // Seeded demo data guarantees a populated catalog of clickable cards.
    const cards = page.locator(".group.cursor-pointer");
    await expect(cards.first()).toBeVisible({ timeout: 15_000 });
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);
  });

  test("quick view opens from the catalog", async ({ page }) => {
    await page.goto("/storefront");
    const firstCard = page.locator(".group.cursor-pointer").first();
    await firstCard.waitFor({ state: "visible", timeout: 15_000 });
    await firstCard.click();

    // ProductCard opens a QuickViewModal with an "Add to cart" action.
    await expect(page.getByText("Add to cart").or(page.getByRole("button", { name: /add to cart/i })).first()).toBeVisible({ timeout: 10_000 });
  });
});
