import { test, expect } from '@playwright/test';

const CONTRACT_ID = '1';

test('signature flow signs and verifies document', async ({ page }) => {
  await page.route('**/api/auth/me', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 'u1', name: 'E2E User', email: 'e2e@example.com', role: 'user' })
    });
  });

  await page.goto('/');
  await page.evaluate(() => localStorage.setItem('token', 'e2e-token'));

  await page.route('**/api/contracts/?page=1&limit=20', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        contracts: [
          { id: CONTRACT_ID, title: 'Test Contract', filename: 'test.pdf', uploaded_at: new Date().toISOString() }
        ]
      })
    });
  });

  await page.route(`**/api/contracts/${CONTRACT_ID}`, route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: CONTRACT_ID, title: 'Test Contract', filename: 'test.pdf' })
    });
  });

  let signed = false;
  await page.route(`**/api/signatures/${CONTRACT_ID}`, route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(
        signed
          ? {
              has_signature: true,
              status: 'signed',
              signer: { name: 'Jane Tester' },
              signed_at: new Date().toISOString(),
              algorithm: 'RSA-SHA256',
              pending_countersigners: 0
            }
          : {
              has_signature: false,
              status: 'pending',
              signer: null,
              signed_at: null,
              algorithm: 'RSA-SHA256',
              pending_countersigners: 1
            }
      )
    });
  });

  await page.route(`**/api/signatures/${CONTRACT_ID}/sign**`, route => {
    signed = true;
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ message: 'Signed successfully' })
    });
  });

  await page.route(`**/api/signatures/${CONTRACT_ID}/verify**`, route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        is_valid: true,
        verification_message: 'Signature valid',
        verification_outcome: 'valid'
      })
    });
  });

  await page.goto(`/signature/${CONTRACT_ID}`);
  await expect(page).toHaveURL(/\/signature\/1/);

  await page.getByRole('button', { name: 'Sign Contract' }).click();
  await page.getByPlaceholder('Enter your full name').fill('Jane Tester');
  await page.getByRole('button', { name: 'Confirm Signature' }).click();

  await expect(page.getByText('This contract already has a signature.')).toBeVisible({ timeout: 10000 });

  await page.getByRole('button', { name: 'Verify Signature' }).click();
  await expect(page.getByText('Last Verification')).toBeVisible();
  await expect(page.getByText('Signature valid').first()).toBeVisible();
});
