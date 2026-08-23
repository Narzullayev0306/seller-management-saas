import { expect, Page } from "@playwright/test";

export const DEMO_OWNER = {
  email: "owner@techmart.uz",
  password: "DemoPass123!",
};

/** Sign in through the UI and wait for the dashboard. */
export async function loginAs(page: Page, email: string, password: string): Promise<void> {
  await page.goto("/login");
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL("**/dashboard");
}

/** Login as the seeded demo owner and land on /dashboard. */
export async function loginAsOwner(page: Page): Promise<void> {
  await loginAs(page, DEMO_OWNER.email, DEMO_OWNER.password);
  await expect(page).toHaveURL(/\/dashboard/);
}
