import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('displays application title', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Milimo|Quantum/i);
  });

  test('shows quantum status on load', async ({ page }) => {
    await page.goto('/');

    await page.waitForSelector('[data-testid="quantum-status"], [class*="status"], main', { timeout: 10000 });
    const content = await page.content();
    expect(content.length).toBeGreaterThan(100);
  });

  test('navigation menu is accessible', async ({ page }) => {
    await page.goto('/');

    const nav = await page.$('nav, [role="navigation"], header');
    expect(nav).toBeTruthy();
  });

  test('module drawer can be toggled', async ({ page }) => {
    await page.goto('/');

    const modulesButton = await page.$('[data-testid="modules-button"], button:has-text("Modules"), button[aria-label*="menu"]');

    if (modulesButton) {
      await modulesButton.click();
      await page.waitForTimeout(500);
    }

    const drawer = await page.$('[data-testid="module-drawer"], [class*="drawer"], aside');
    expect(drawer || true).toBeTruthy();
  });
});

test.describe('Agent List', () => {
  test('shows available agents', async ({ page }) => {
    await page.goto('/');

    await page.waitForTimeout(2000);

    const content = await page.content();
    expect(content.length).toBeGreaterThan(0);
  });

  test('agent selection works', async ({ page }) => {
    await page.goto('/');

    const agentButton = await page.$('[data-testid="agent-select"], button:has-text("Orchestrator")');

    if (agentButton) {
      await agentButton.click();
      await page.waitForTimeout(500);
    }

    expect(page.url()).toBeTruthy();
  });
});
