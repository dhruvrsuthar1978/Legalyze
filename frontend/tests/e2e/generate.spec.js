const { test, expect } = require('@playwright/test');

test('generate preview flow shows generated preview', async ({ page }) => {
  // Mock adhoc preview endpoint
  await page.route('**/api/generate/adhoc/preview', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ preview_text: 'Generated preview content', filename: 'adhoc.pdf', estimated_pages: 2 })
    });
  });

  await page.goto('/generate');

  // Select contract type
  await page.click('text=Select contract type');
  // pick NDA option if visible
  const option = await page.locator('text=Non-Disclosure Agreement (NDA)').first();
  if (await option.count() > 0) await option.click();

  await page.fill('input[placeholder="e.g., ABC Company Inc."]', 'ABC Corp');
  await page.fill('input[placeholder="e.g., John Smith"]', 'John Doe');
  await page.fill('textarea[placeholder^="Example:"]', 'Include non-compete clause for 2 years');

  await page.click('text=Generate Balanced Contract');

  // Expect generated success header
  await expect(page.locator('text=Contract Generated Successfully!')).toBeVisible({ timeout: 5000 });
  await expect(page.locator('text=Generated preview content')).toBeVisible();
});
