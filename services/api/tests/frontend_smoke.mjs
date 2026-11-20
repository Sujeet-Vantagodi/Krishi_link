import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium, request } = require(process.env.KRISHILINK_PLAYWRIGHT_MODULE || 'playwright');
const frontend = process.env.KRISHILINK_FRONTEND_URL ?? 'http://127.0.0.1:5173';
const api = process.env.KRISHILINK_API_URL ?? 'http://127.0.0.1:8000/api/v1';
const artifacts = resolve(process.env.KRISHILINK_SCREENSHOTS ?? 'frontend-screenshots');
const mode = process.argv[2] ?? 'screenshots';

const browser = await chromium.launch({
  executablePath: process.env.KRISHILINK_BROWSER_EXECUTABLE,
});
try {
  if (mode === 'screenshots') {
    const routes = [
      ['landing', '/', 'h1'],
      ['login', '/auth/login', 'h3'],
      ['buyer', '/buyer', 'input[type="text"]', 'buyer'],
      ['farmer', '/farmer', 'h2', 'farmer'],
      ['driver', '/driver', 'h2', 'driver'],
      ['admin', '/admin', 'h2', 'admin'],
    ];
    await mkdir(artifacts, { recursive: true });
    for (const [size, viewport] of [
      ['desktop', { width: 1440, height: 900 }],
      ['mobile', { width: 390, height: 844 }],
    ]) {
      for (const [name, path, ready, role] of routes) {
        const context = await browser.newContext({ viewport, reducedMotion: 'reduce' });
        try {
          await context.route('**/*', (route) => (
            new URL(route.request().url()).origin === new URL(frontend).origin
              ? route.continue()
              : route.abort()
          ));
          if (role) {
            await context.addInitScript((selectedRole) => {
              const user = { id: `u_${selectedRole}_1`, name: 'Smoke Test', role: selectedRole, language: 'en' };
              localStorage.setItem('krishilink_user', JSON.stringify(user));
              localStorage.setItem('krishilink_token', `mock_jwt_${selectedRole}`);
            }, role);
          }
          const page = await context.newPage();
          await page.clock.setFixedTime(new Date('2026-11-21T12:00:00+05:30'));
          await page.goto(frontend + path);
          await page.locator(`${ready}:visible`).first().waitFor({ timeout: 10000 });
          if (name === 'admin') {
            await page.getByText('Whitefield Hub: French Beans OUT OF STOCK', { exact: true }).waitFor();
          }
          assert.equal(new URL(page.url()).pathname, path);
          await page.evaluate(() => document.fonts.ready);
          await page.screenshot({ path: resolve(artifacts, `${name}-${size}.png`), animations: 'disabled' });
          console.log(`Captured ${name} (${size})`);
        } finally {
          await context.close();
        }
      }
    }
    console.log('Captured 12 route screenshots');
  } else if (mode === 'live') {
    const backend = await request.newContext();
    try {
      const login = await backend.post(`${api}/auth/demo-login`, { data: { role: 'farmer' } });
      assert.equal(login.status(), 200);
      const session = await login.json();
      const headers = { Authorization: `Bearer ${session.access_token}` };
      const path = '/farmers/me/threshold';
      const original = await (await backend.get(api + path, { headers })).json();
      const catalog = await backend.get(`${api}/crops`);
      const crop = (await catalog.json()).items.find((item) => item.slug === 'demo-tomato');
      assert.ok(crop?.price);
      const buyerContext = await browser.newContext();
      try {
        const page = await buyerContext.newPage();
        const phone = String(7000000000 + Math.floor(Math.random() * 999999999));
        const password = 'browser-smoke-password';
        await page.goto(frontend + '/auth/login?mode=register&role=buyer');
        await page.getByPlaceholder('e.g. Udupi Upahar').fill('Browser Smoke Buyer');
        await page.getByPlaceholder('9876543201').fill(phone);
        await page.locator('form input[type=password]').fill(password);
        const registration = page.waitForResponse((response) => response.url() === `${api}/auth/register`);
        await page.getByRole('button', { name: 'Create BUYER Account' }).click();
        assert.equal((await registration).status(), 201);
        await page.waitForURL('**/buyer');
        await page.evaluate(() => localStorage.clear());
        await page.goto(frontend + '/auth/login');
        await page.locator('form input[type=tel]').fill(phone);
        await page.getByPlaceholder('Enter your password').fill('incorrect-password');
        const denied = page.waitForResponse((response) => response.url() === `${api}/auth/login`);
        await page.getByRole('button', { name: /sign in as buyer/i }).click();
        assert.equal((await denied).status(), 401);
        await page.getByPlaceholder('Enter your password').fill(password);
        const buyerCatalog = page.waitForResponse((response) => response.url().startsWith(`${api}/crops?`));
        await page.getByRole('button', { name: /sign in as buyer/i }).click();
        assert.equal((await buyerCatalog).status(), 200);
        await page.getByText(crop.name_en, { exact: true }).first().waitFor();
        const detail = page.waitForResponse((response) => response.url() === `${api}/catalog/crops/${crop.id}`);
        await page.goto(frontend + `/buyer/crop/${crop.id}`);
        assert.equal((await detail).status(), 200);
        await page.waitForURL(`**/buyer/crop/${crop.id}`);
        await page.getByText('Shelf Life', { exact: true }).waitFor();
        await page.getByRole('button', { name: 'ADD', exact: true }).click();
        await page.getByRole('button', { name: /view cart/i }).click();
        await page.getByRole('button', { name: 'Proceed to Checkout' }).click();
        const checkout = page.waitForResponse((response) => response.url() === `${api}/orders/checkout`);
        await page.getByRole('button', { name: 'Confirm & Place Order' }).click();
        const response = await checkout;
        assert.equal(response.status(), 201);
        const order = await response.json();
        assert.equal(order.status, 'PLACED');
        assert.equal(order.payment_status, 'PENDING');
        await page.getByText('Order Placed Successfully!', { exact: true }).waitFor();
        await page.getByRole('button', { name: 'View All Orders' }).click();
        await page.getByText(`#${order.id}`, { exact: true }).waitFor();
        await page.reload();
        await page.getByText(`#${order.id}`, { exact: true }).waitFor();
        await page.getByText('PLACED', { exact: true }).first().waitFor();
      } finally {
        await buyerContext.close();
      }
      const otpContext = await browser.newContext();
      try {
        const page = await otpContext.newPage();
        await page.goto(frontend + '/auth/login');
        await page.locator('form input[type=tel]').fill('9999002002');
        const sent = page.waitForResponse((response) => response.url() === `${api}/auth/otp/request`);
        await page.getByRole('button', { name: /sign in using sms otp/i }).click();
        const challenge = await (await sent).json();
        await page.waitForURL('**/auth/verify?*');
        const fields = page.locator('input[inputmode=numeric]');
        for (const [index, digit] of [...challenge.mock_otp].entries()) await fields.nth(index).fill(digit);
        const verified = page.waitForResponse((response) => response.url() === `${api}/auth/otp/verify`);
        await page.getByRole('button', { name: 'Verify & Continue' }).click();
        assert.equal((await verified).status(), 200);
        await page.waitForURL('**/buyer');
      } finally {
        await otpContext.close();
      }
      assert.equal((await backend.get(api + path)).status(), 401);
      const target = original.default_min_kg + 10;
      const context = await browser.newContext();
      try {
        await context.addInitScript(({ user, access_token }) => {
          localStorage.setItem('krishilink_user', JSON.stringify(user));
          localStorage.setItem('krishilink_token', access_token);
        }, session);
        const page = await context.newPage();
        const initialFetch = page.waitForResponse((response) =>
          response.url() === api + path && response.request().method() === 'GET');
        await page.goto(frontend + '/farmer/threshold');
        assert.equal((await initialFetch).status(), 200);
        await page.getByText(String(original.default_min_kg), { exact: true }).first().waitFor();
        await page.getByRole('button', { name: '+10', exact: true }).click();
        const save = page.waitForResponse((response) =>
          response.url() === api + path && response.request().method() === 'PUT');
        await page.getByRole('button', { name: /save/i }).click();
        assert.equal((await save).status(), 200);
        await page.waitForURL('**/farmer');
        const afterRefresh = page.waitForResponse((response) =>
          response.url() === api + path && response.request().method() === 'GET');
        await page.goto(frontend + '/farmer/threshold');
        assert.equal((await (await afterRefresh).json()).default_min_kg, target);
        await page.getByText(String(target), { exact: true }).first().waitFor();

        await page.goto(frontend + '/farmer');
        await page.getByRole('heading', { name: crop.name_en, exact: true }).click();
        const listings = `${api}/farmers/me/listings`;
        const created = page.waitForResponse((response) =>
          response.url() === listings && response.request().method() === 'POST');
        await page.getByRole('button', { name: /submit ready harvest/i }).click();
        const listingResponse = await created;
        assert.equal(listingResponse.status(), 201);
        const listing = await listingResponse.json();
        assert.equal(listing.crop_id, crop.id);
        assert.equal(listing.est_kg, 50);
        const afterReload = page.waitForResponse((response) =>
          response.url() === listings && response.request().method() === 'GET');
        await page.reload();
        assert.ok((await (await afterReload).json()).items.some((item) => item.id === listing.id));
        await page.getByText(`${crop.name_en} · 50 kg`, { exact: true }).first().waitFor();
      } finally {
        await context.close();
        assert.equal((await backend.put(api + path, { headers, data: original })).status(), 200);
      }

      const adminLogin = await backend.post(`${api}/auth/demo-login`, { data: { role: 'admin' } });
      assert.equal(adminLogin.status(), 200);
      const adminSession = await adminLogin.json();
      const settled = await backend.post(`${api}/admin/settlements/calculate?settle_date=${crop.price.date}`, {
        headers: { Authorization: `Bearer ${adminSession.access_token}` },
      });
      assert.equal(settled.status(), 200);
      const reconciliation = (await settled.json()).items.find(({ farmer_id }) => farmer_id === session.user.id);
      assert.equal(reconciliation?.accepted_kg, 20);
      const statementContext = await browser.newContext();
      try {
        await statementContext.addInitScript(({ user, access_token }) => {
          localStorage.setItem('krishilink_user', JSON.stringify(user));
          localStorage.setItem('krishilink_token', access_token);
        }, session);
        const page = await statementContext.newPage();
        const statement = page.waitForResponse((response) => response.url() === `${api}/farmers/me/settlements`);
        await page.goto(frontend + '/farmer/payments');
        assert.ok((await (await statement).json()).items.some(({ id }) => id === reconciliation.id));
        await page.getByText('Settlement Statements', { exact: true }).waitFor();
      } finally {
        await statementContext.close();
      }
      const adminContext = await browser.newContext();
      try {
        await adminContext.addInitScript(({ user, access_token }) => {
          localStorage.setItem('krishilink_user', JSON.stringify(user));
          localStorage.setItem('krishilink_token', access_token);
        }, adminSession);
        const page = await adminContext.newPage();
        const inventory = page.waitForResponse((response) => response.url() === `${api}/hubs/stock-matrix`);
        await page.goto(frontend + '/admin/hubs');
        assert.equal((await inventory).status(), 200);
        await page.getByRole('heading', { name: 'Karnataka Hub Network & Stock Matrix' }).waitFor();
        const stockUpdate = page.waitForResponse((response) =>
          response.url().includes('/stock-status/') && response.request().method() === 'PUT');
        await page.getByRole('button', { name: 'Low Stock', exact: true }).first().click();
        const stockResult = await stockUpdate;
        assert.equal(stockResult.status(), 200);
        const changed = await stockResult.json();
        assert.equal(changed.status, 'LOW');
        const inventoryReload = page.waitForResponse((response) => response.url() === `${api}/hubs/stock-matrix`);
        await page.reload();
        const hubRows = (await (await inventoryReload).json()).hubs;
        const hub = hubRows.find((row) => row.id === changed.hub_id);
        assert.equal(hub.cells.find((cell) => cell.crop_id === changed.crop_id).status, 'LOW');
        const settlements = page.waitForResponse((response) => response.url() === `${api}/admin/settlements`);
        await page.goto(frontend + '/admin/payments');
        const statements = await settlements;
        assert.equal(statements.status(), 200);
        const [statement] = (await statements.json()).items;
        assert.ok(statement?.farmer_name);
        await page.getByText(statement.farmer_name, { exact: true }).first().waitFor();
        const transfers = `${api}/transfers`;
        const [origin, destination] = (await (await backend.get(`${api}/hubs`)).json()).items;
        const newTransfer = await backend.post(transfers, {
          headers: { Authorization: `Bearer ${adminSession.access_token}` },
          data: { from_hub_id: origin.id, to_hub_id: destination.id, crop_id: crop.id, requested_kg: 9, urgency: 'HIGH' },
        });
        assert.equal(newTransfer.status(), 201);
        await page.goto(frontend + '/admin/transfers');
        const approved = page.waitForResponse((response) =>
          response.url().startsWith(`${transfers}/`) && response.url().endsWith('/approve'));
        await page.getByRole('button', { name: 'Approve', exact: true }).first().click();
        const approval = await approved;
        assert.equal(approval.status(), 200);
        const updated = await approval.json();
        const reloadedTransfers = page.waitForResponse((response) => response.url() === transfers);
        await page.reload();
        assert.ok((await (await reloadedTransfers).json()).items.some(({ id, status }) =>
          id === updated.id && status === 'APPROVED'));
      } finally {
        await adminContext.close();
      }
      console.log('Live auth, catalog, checkout/history, harvest, hub stock, reconciled settlements and transfer approval passed');
    } finally {
      await backend.dispose();
    }
  } else {
    throw new Error(`Unknown smoke mode: ${mode}`);
  }
} finally {
  await browser.close();
}
