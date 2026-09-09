import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
test("sign in, review, apply, audit and keyboard accessibility", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Welcome to Atlas" }),
  ).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page
    .getByLabel("Password", { exact: true })
    .fill("browser-test-password-2026!");
  await page.getByRole("button", { name: "Sign in to workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Identity directory" }),
  ).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.getByRole("button", { name: "Manage Priya Rao" }).click();
  await page.getByRole("button", { name: "Preview manual change" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(page.getByRole("button", { name: "Go back" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(
    page.getByRole("button", { name: "Preview manual change" }),
  ).toBeFocused();
  await page.getByRole("button", { name: "Access review" }).click();
  await page.getByRole("button", { name: "Review change" }).first().click();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.getByRole("button", { name: "Confirm change" }).click();
  await expect(page.getByRole("status")).toContainText("Access updated");
  await page.getByRole("button", { name: "Audit activity" }).click();
  await expect(
    page.getByRole("cell", { name: "identity.suspend", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Feature rollout" }).click();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});
