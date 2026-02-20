import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test('upload flow shows progress and navigates to contract page', async ({ page }) => {
  await page.route('**/api/auth/me', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 'u1', name: 'E2E User', email: 'e2e@example.com', role: 'user' })
    });
  });

  await page.goto('/');
  await page.evaluate(() => localStorage.setItem('token', 'e2e-token'));

  await page.route('**/api/contracts/upload', route => {
    route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({ id: 'fake-contract-123', filename: 'sample.pdf' })
    });
  });

  await page.route('**/api/analysis/fake-contract-123/run?mode=async', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'started' })
    });
  });

  let pollCount = 0;
  await page.route('**/api/contracts/fake-contract-123', route => {
    pollCount += 1;
    const body = pollCount < 2
      ? { id: 'fake-contract-123', analysis_status: 'processing' }
      : { id: 'fake-contract-123', analysis_status: 'completed' };

    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(body)
    });
  });

  await page.goto('/upload');
  await expect(page).toHaveURL(/\/upload/);

  await page.setInputFiles('input#file-upload', path.join(__dirname, '..', 'fixtures', 'sample.pdf'));
  await page.getByRole('button', { name: 'Upload & Analyze' }).click();

  await expect(page.getByText(/Uploading\.\.\.|Analyzing\.\.\./).first()).toBeVisible();
  await page.waitForURL('**/contract/fake-contract-123', { timeout: 15000 });
  await expect(page).toHaveURL(/contract\/fake-contract-123/);
});
