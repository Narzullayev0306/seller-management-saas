import { expect, test } from "@playwright/test";
import { loginAsOwner } from "../helpers";

test.describe("products", () => {
  test("owner can create a product and find it in the catalog", async ({ page }) => {
    await loginAsOwner(page);
    await page.goto("/dashboard/products");
    await expect(page.getByText("Manage your product catalog").or(page.getByRole("heading", { name: "Products" })).first()).toBeVisible();

    const sku = `E2E-${Date.now().toString(36).toUpperCase()}`;

    await page.getByRole("button", { name: "Add product" }).click();
    await page.locator('input[placeholder="Wireless Mouse"]').fill("E2E Test Widget");
    await page.locator('input[placeholder="WM-001"]').fill(sku);
    await page.locator('input[placeholder="Electronics"]').fill("Test Category");
    await page.locator('input[placeholder="29.99"]').first().fill("19.99");
    await page.locator('input[placeholder="100"]').fill("25");
    await page.getByRole("button", { name: "Create product" }).click();

    // Success toast confirms the API accepted the payload.
    await expect(page.getByText("Product created")).toBeVisible({ timeout: 15_000 });

    // The debounced search filters the refreshed list down to the new SKU.
    await page.fill('input[placeholder="Search by name or SKU..."]', sku);
    await expect(page.getByText("E2E Test Widget").first()).toBeVisible({ timeout: 15_000 });
  });
});
