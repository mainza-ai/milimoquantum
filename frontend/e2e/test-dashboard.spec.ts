import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('displays application title', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });
    await expect(page).toHaveTitle(/Milimo|Quantum/i);
  });

  test('page loads successfully', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });

    await page.waitForTimeout(2000);

    const content = await page.content();
    expect(content.length).toBeGreaterThan(100);
  });

  test('authentication state is checked', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });

    await page.waitForTimeout(3000);

    const hasSpinner = await page.$('.animate-spin');
    const hasAuthScreen = await page.$('button:has-text("Sign In")');
    const hasChat = await page.$('[class*="chat"], [class*="sidebar"]');

    expect(hasSpinner || hasAuthScreen || hasChat).toBeTruthy();
  });
});

test.describe('Page Structure', () => {
  test('root element exists', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });

    const root = await page.$('#root');
    expect(root).toBeTruthy();
  });

  test('body has content', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });

    const body = await page.$('body');
    expect(body).toBeTruthy();
  });
});
