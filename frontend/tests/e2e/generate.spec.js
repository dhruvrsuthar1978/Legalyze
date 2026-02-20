import { test, expect } from '@playwright/test';

const CONTRACT_ID = 'contract-123';

test('generate preview flow shows generated preview', async ({ page }) => {
  await page.route('**/api/auth/me', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 'u1', name: 'E2E User', email: 'e2e@example.com', role: 'user' })
    });
  });

  await page.goto('/');
  await page.evaluate(() => localStorage.setItem('token', 'e2e-token'));

  await page.route('**/api/contracts/?page=1&limit=100', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        contracts: [
          {
            id: CONTRACT_ID,
            title: 'Master Services Agreement',
            filename: 'msa.pdf',
            analysis_status: 'completed',
            high_risk_count: 1,
            overall_risk_score: 35
          }
        ]
      })
    });
  });

  await page.route(`**/api/generate/${CONTRACT_ID}/preview`, route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ preview_text: 'Generated preview content' })
    });
  });

  await page.goto('/generate');
  await expect(page).toHaveURL(/\/generate/);

  await page.getByRole('button', { name: 'Choose a contract' }).click();
  await page.getByText('Master Services Agreement').click();
  await page.getByRole('button', { name: 'Preview Generated Contract' }).click();

  await expect(page.getByRole('heading', { name: 'Generated Preview' })).toBeVisible();
  await expect(page.getByText('Generated preview content')).toBeVisible();
});
