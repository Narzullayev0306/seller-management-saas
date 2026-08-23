import { expect, test } from "@playwright/test";
import { loginAsOwner } from "../helpers";

test.describe("orders", () => {
  test("owner can create an order and sees it in the pipeline", async ({ page }) => {
    await loginAsOwner(page);
    await page.goto("/dashboard/orders");
    await expect(page.getByRole("heading", { name: "Orders" })).toBeVisible();

    await page.getByRole("button", { name: "New order" }).click();
    // The Modal component is a plain fixed-position div (no dialog role).
    const modal = page.locator("div.fixed.inset-0");

    // Pick the first available customer and product from the async-loaded selects.
    const selects = modal.locator("select");
    const customerSelect = selects.first();
    await expect(customerSelect.locator("option:not([value=''])").first()).toBeAttached({
      timeout: 15_000,
    });
    await customerSelect.selectOption({ index: 1 });

    // Select order: [0] customer, [1] seller (optional), [2] product.
    const productSelect = selects.nth(2);
    await expect(productSelect.locator("option:not([value=''])").first()).toBeAttached({
      timeout: 15_000,
    });
    await productSelect.selectOption({ index: 1 });

    await page.getByRole("button", { name: "Create order" }).click();

    // Success toast confirms creation; a fresh pending order lands in the table.
    await expect(page.getByText("Order created")).toBeVisible({ timeout: 15_000 });
    await expect(
      page.locator("table tbody tr").filter({ hasText: "pending" }).first()
    ).toBeVisible({ timeout: 15_000 });
  });
});
