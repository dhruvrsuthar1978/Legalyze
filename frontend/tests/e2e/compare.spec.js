const { test, expect } = require('@playwright/test');
const path = require('path');

test('compare flow uploads two files and shows diff', async ({ page }) => {
  // Mock compare endpoint
  await page.route('**/api/contracts/compare', route => {
    const body = {
      differences: [
        { text: '- Clause A: 30 days' },
        { text: '+ Clause A: 60 days' }
      ]
    };
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
  });

  await page.goto('/compare');

  const file1 = await page.$('input#file1');
  const file2 = await page.$('input#file2');

  await file1.setInputFiles(path.join(__dirname, '..', 'fixtures', 'sample.pdf'));
  await file2.setInputFiles(path.join(__dirname, '..', 'fixtures', 'sample.pdf'));

  await page.click('text=Compare Contracts');

  // Wait for results
  await expect(page.locator('text=Comparison Results')).toBeVisible();
  await expect(page.locator('text=Clause A')).toHaveCount(0); // clause label may be diff line
  await expect(page.locator('text=30 days')).toBeVisible();
  await expect(page.locator('text=60 days')).toBeVisible();
});
