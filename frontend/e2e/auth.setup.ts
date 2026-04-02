import { test as setup, expect } from '@playwright/test';
import { fileURLToPath } from 'url';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const authFile = path.join(__dirname, '../.auth/user.json');

setup('authenticate', async ({ page }) => {
  await page.goto('/');

  try {
    await page.waitForURL('**/dashboard', { timeout: 5000 });
    await page.context().storageState({ path: authFile });
    return;
  } catch {
  }

  const loginForm = await page.$('form, [data-testid="login-form"], input[name="username"]');
  if (!loginForm) {
    await page.context().storageState({ path: authFile });
    return;
  }

  await page.getByLabel(/username|email/i).fill('testuser');
  await page.getByLabel(/password/i).fill('testpass');
  await page.getByRole('button', { name: /sign in|login|submit/i }).click();

  await page.waitForURL('**/dashboard', { timeout: 30000 });

  await expect(page).toHaveURL(/dashboard/);

  await page.context().storageState({ path: authFile });
});
