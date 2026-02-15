const { test, expect } = require('@playwright/test');

test('signature flow signs and verifies document', async ({ page }) => {
  // Mock sign endpoint
  await page.route('**/api/signatures/*/sign**', route => {
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: 'Signed successfully' }) });
  });

  // Mock verify endpoint
  await page.route('**/api/signatures/*/verify**', route => {
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ is_valid: true, verification_message: 'Signature valid' }) });
  });

  await page.goto('/signature/1');

  // Click Sign Document to open modal
  await page.click('text=Sign Document');

  // Fill name input inside modal
  await page.fill('input[placeholder="Enter your full name as it appears on official documents"]', 'Jane Tester');

  // Confirm signature
  await page.click('text=Confirm Signature');

  // Wait for badge 'Verified' to appear for the current party
  await expect(page.locator('text=Verified')).toBeVisible({ timeout: 5000 });
});
