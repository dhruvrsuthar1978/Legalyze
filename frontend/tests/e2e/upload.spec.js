const { test, expect } = require('@playwright/test');
const path = require('path');

test('upload flow shows progress and navigates to contract page', async ({ page }) => {
  // Intercept upload POST and return fake contract id
  await page.route('**/api/contracts/upload', route => {
    route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({ id: 'fake-contract-123', filename: 'sample.pdf' })
    });
  });

  // Intercept status polling to simulate processing -> completed
  let pollCount = 0;
  await page.route('**/api/contracts/*/status', route => {
    pollCount += 1;
    const body = pollCount < 2
      ? { status: 'processing', progress: 30 }
      : { status: 'completed', progress: 100 };
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
  });

  await page.goto('/');
  await page.click('text=Upload Contract');

  const input = await page.$('input[type=file]#file-upload');
  await input.setInputFiles(path.join(__dirname, '..', 'fixtures', 'sample.pdf'));

  await page.click('text=Upload & Analyze');

  // Expect progress bar to show
  await expect(page.locator('text=Uploading...')).toBeVisible();

  // Wait for navigation to contract page (simulated)
  await page.waitForURL('**/contract/fake-contract-123', { timeout: 10000 });
  await expect(page).toHaveURL(/contract\/fake-contract-123/);
});
