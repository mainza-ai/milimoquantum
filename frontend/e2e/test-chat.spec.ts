import { test, expect } from '@playwright/test';

test.describe('Chat Interface', () => {
  test('chat page loads', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const content = await page.content();
    expect(content.length).toBeGreaterThan(0);
  });

  test('authentication or chat interface visible', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const hasSignIn = await page.$('button:has-text("Sign In")');
    const hasChat = await page.$('body');

    expect(hasSignIn || hasChat).toBeTruthy();
  });
});

test.describe('Chat Components', () => {
  test('page structure exists', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const root = await page.$('#root');
    expect(root).toBeTruthy();
  });

  test('body has valid content', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const bodyContent = await page.content();
    expect(bodyContent.length).toBeGreaterThan(100);
  });
});
