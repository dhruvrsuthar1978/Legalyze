import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test('compare flow uploads two files and shows diff', async ({ page }) => {
  await page.route('**/api/auth/me', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 'u1', name: 'E2E User', email: 'e2e@example.com', role: 'user' })
    });
  });

  await page.goto('/');
  await page.evaluate(() => localStorage.setItem('token', 'e2e-token'));

  await page.route('**/api/contracts/compare', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        differences: [
          { text: '- Clause A: 30 days' },
          { text: '+ Clause A: 60 days' }
        ]
      })
    });
  });

  await page.goto('/compare');
  await expect(page).toHaveURL(/\/compare/);

  const fixture = path.join(__dirname, '..', 'fixtures', 'sample.pdf');
  await page.setInputFiles('input#file1', fixture);
  await page.setInputFiles('input#file2', fixture);

  await page.getByRole('button', { name: 'Compare Contracts' }).click();

  await expect(page.getByText('Comparison Results')).toBeVisible();
  await expect(page.getByText('30 days').first()).toBeVisible();
  await expect(page.getByText('60 days').first()).toBeVisible();
});
