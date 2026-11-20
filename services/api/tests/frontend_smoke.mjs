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
        const buyerCatalog = page.waitForResponse((response) => response.url().startsWith(`${api}/crops?`));
        await page.goto(frontend + '/buyer');
        assert.equal((await buyerCatalog).status(), 200);
        await page.getByText(crop.name_en, { exact: true }).first().waitFor();
        const detail = page.waitForResponse((response) => response.url() === `${api}/catalog/crops/${crop.id}`);
        await page.goto(frontend + `/buyer/crop/${crop.id}`);
        assert.equal((await detail).status(), 200);
        await page.getByText('Shelf Life', { exact: true }).waitFor();
      } finally {
        await buyerContext.close();
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
      const adminContext = await browser.newContext();
      try {
        await adminContext.addInitScript(({ user, access_token }) => {
          localStorage.setItem('krishilink_user', JSON.stringify(user));
          localStorage.setItem('krishilink_token', access_token);
        }, await adminLogin.json());
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
      } finally {
        await adminContext.close();
      }
      console.log('Live catalog/detail, threshold, harvest submission, hub matrix, and settlement review passed');
    } finally {
      await backend.dispose();
    }
  } else {
    throw new Error(`Unknown smoke mode: ${mode}`);
  }
} finally {
  await browser.close();
}
