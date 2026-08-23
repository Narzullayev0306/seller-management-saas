import { expect, test } from "@playwright/test";
import { DEMO_OWNER, loginAsOwner } from "../helpers";

test.describe("authentication", () => {
  test("login page renders and rejects bad credentials", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByText("Sign in to your account")).toBeVisible();

    await page.fill('input[type="email"]', DEMO_OWNER.email);
    await page.fill('input[type="password"]', "WrongPassword1!");
    await page.click('button[type="submit"]');
    await expect(page.getByText("Incorrect email or password").or(page.getByText("Login failed"))).toBeVisible();
  });

  test("demo owner can sign in and reaches the dashboard", async ({ page }) => {
    await loginAsOwner(page);
    await expect(page).not.toHaveURL(/\/login/);
  });

  test("unauthenticated users are redirected away from /dashboard", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });

  test("new organization signup lands on the dashboard with owner access", async ({ page }) => {
    const email = `e2e-owner-${Date.now()}@test.io`;
    await page.goto("/register");
    await page.fill('input[placeholder="John Doe"]', "E2E Owner");
    await page.fill('input[type="email"]', email);
    await page.locator('input[type="password"]').nth(0).fill("Str0ngPass!123");
    await page.locator('input[type="password"]').nth(1).fill("Str0ngPass!123");
    await page.click('button[type="submit"]');

    // The registering user becomes the org owner and gets dashboard access.
    await page.waitForURL("**/dashboard", { timeout: 20_000 });
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
