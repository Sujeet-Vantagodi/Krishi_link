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
const controlArtifacts = process.env.KRISHILINK_CONTROL_SCREENSHOTS;

async function captureControls(page, name) {
  if (!controlArtifacts) return;
  await mkdir(controlArtifacts, { recursive: true });
  const previous = page.viewportSize();
  for (const [size, viewport] of [['desktop', { width: 1440, height: 900 }], ['mobile', { width: 390, height: 844 }]]) {
    await page.setViewportSize(viewport);
    await page.screenshot({ path: resolve(controlArtifacts, `${name}-${size}.png`), animations: 'disabled' });
  }
  if (previous) await page.setViewportSize(previous);
}

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
  } else if (mode === 'controls-before') {
    assert.ok(controlArtifacts, 'Set KRISHILINK_CONTROL_SCREENSHOTS for controls-before');
    const context = await browser.newContext();
    try {
      await context.addInitScript(() => {
        localStorage.setItem('krishilink_user', JSON.stringify({ id: 'u_admin_1', name: 'Smoke Test', role: 'admin', language: 'en' }));
        localStorage.setItem('krishilink_token', 'mock_jwt_admin');
      });
      const page = await context.newPage();
      await page.goto(frontend + '/admin/hubs/h_main');
      await page.getByText('Current Produce Inventory Status', { exact: true }).waitFor();
      await captureControls(page, 'before-hub');
      await page.goto(frontend + '/admin/transfers');
      await page.getByText('Inter-Hub Stock Transfers', { exact: true }).waitFor();
      await captureControls(page, 'before-transfer');
      await page.goto(frontend + '/admin/dispatch');
      await page.getByText('Driver & Vehicle Assignment', { exact: true }).waitFor();
      await captureControls(page, 'before-dispatch');
    } finally {
      await context.close();
    }
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
      let buyerSession;
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
        const registrationResult = await registration;
        assert.equal(registrationResult.status(), 201);
        buyerSession = await registrationResult.json();
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
        await page.goto(frontend + `/buyer/orders/${order.id}`);
        await page.getByText('GPS unavailable', { exact: true }).waitFor();
        await page.getByText('ETA unavailable', { exact: true }).waitFor();
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
      let submittedListing;
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
        submittedListing = listing;
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
        const driverLogin = await backend.post(`${api}/auth/demo-login`, { data: { role: 'driver' } });
        const driverSession = await driverLogin.json();
        assert.equal(driverLogin.status(), 200);
        const driverHeaders = { Authorization: `Bearer ${driverSession.access_token}` };
        const operatorHeaders = { Authorization: `Bearer ${adminSession.access_token}` };
        const allHubs = (await (await backend.get(`${api}/hubs`)).json()).items;
        const central = allHubs.find((item) => item.type === 'main');
        const city = allHubs.find((item) => item.type === 'city');
        const driverRecord = (await (await backend.get(`${api}/admin/drivers/available`, { headers: operatorHeaders })).json())
          .find((item) => item.user_id === driverSession.user.id);
        await page.goto(frontend + '/admin/dispatch');
        await page.getByText(`${submittedListing.est_kg} kg`, { exact: true }).first().click();
        await page.getByLabel('Destination hub').selectOption(central.id);
        const selects = page.locator('select');
        await selects.nth(1).selectOption(driverSession.user.id);
        await selects.nth(2).selectOption(driverRecord.vehicle.id);
        await captureControls(page, 'after-dispatch');
        const assignment = page.waitForResponse((response) => response.url() === `${api}/admin/assign`);
        await page.getByRole('button', { name: /assign.*trip|dispatch.*trip/i }).last().click();
        const assignmentResult = await assignment;
        assert.equal(assignmentResult.status(), 201, await assignmentResult.text());
        const pickup = await assignmentResult.json();
        assert.equal(pickup.stops[0].listing_id, submittedListing.id);
        const { lat, lng } = pickup.stops[0].location;
        const driverContext = await browser.newContext({ permissions: ['geolocation'], geolocation: { latitude: lat, longitude: lng } });
        try {
          await driverContext.addInitScript(({ user, access_token }) => {
            localStorage.setItem('krishilink_user', JSON.stringify(user));
            localStorage.setItem('krishilink_token', access_token);
          }, driverSession);
          const driverPage = await driverContext.newPage();
          await driverPage.goto(frontend + '/driver');
          const acknowledge = driverPage.waitForResponse((response) => response.url() === `${api}/trips/${pickup.id}/acknowledge`);
          await driverPage.getByRole('button', { name: /acknowledge trip/i }).first().click();
          assert.equal((await acknowledge).status(), 200);
          await driverPage.goto(frontend + `/driver/trip/${pickup.id}`);
          await driverPage.getByRole('button', { name: /start trip/i }).click();
          await driverPage.getByRole('button', { name: /arrived at location/i }).click();
          await driverPage.getByRole('button', { name: /record produce/i }).click();
          await driverPage.getByRole('button', { name: '+25', exact: true }).click();
          await driverPage.getByText('Farmer witnessed weighing on scale', { exact: true }).click();
          const completed = driverPage.waitForResponse((response) => response.url().endsWith('/complete-pickup'));
          await driverPage.getByRole('button', { name: /confirm & complete stop/i }).click();
          assert.equal((await completed).status(), 200);
          await driverPage.getByRole('button', { name: /reached hub/i }).click();
          await driverPage.getByRole('button', { name: /return to base/i }).waitFor();
          const forbidden = await backend.get(`${api}/hubs/${central.id}/inbound-trips`, { headers: driverHeaders });
          assert.equal(forbidden.status(), 403);
          const staffLogin = await backend.post(`${api}/auth/demo-login`, { data: { role: 'hub_staff' } });
          assert.equal(staffLogin.status(), 200);
          const staffContext = await browser.newContext();
          try {
            await staffContext.addInitScript(({ user, access_token }) => {
              localStorage.setItem('krishilink_user', JSON.stringify(user));
              localStorage.setItem('krishilink_token', access_token);
            }, await staffLogin.json());
            const hubPage = await staffContext.newPage();
            await hubPage.goto(frontend + `/admin/hubs/${central.id}`);
            await hubPage.getByLabel('Inbound trip').selectOption(pickup.id);
            await hubPage.getByLabel('Crop').selectOption(crop.id);
            await captureControls(hubPage, 'after-hub');
            await hubPage.getByLabel('Measured total (kg)').fill('24');
            await hubPage.getByLabel('Grade A (kg)').fill('22');
            await hubPage.getByLabel('Grade B (kg)').fill('1');
            await hubPage.getByLabel('Rejected (kg)').fill('1');
            await hubPage.getByRole('button', { name: 'Record Hub Receipt' }).click();
            await hubPage.getByText('Hub receipt recorded.', { exact: true }).waitFor();
            await hubPage.reload();
            await hubPage.getByLabel('Inbound trip').waitFor();
            assert.equal(await hubPage.locator(`option[value="${pickup.id}"]`).count(), 0);
          } finally {
            await staffContext.close();
          }
          await driverPage.getByRole('button', { name: /return to base/i }).click();
          await driverPage.getByText(/trip completed & returned/i).waitFor();
        } finally {
          await driverContext.close();
        }
        const transfers = `${api}/transfers`;
        const newTransfer = await backend.post(transfers, {
          headers: operatorHeaders,
          data: { from_hub_id: central.id, to_hub_id: city.id, crop_id: crop.id, requested_kg: 9, urgency: 'HIGH' },
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
        await page.getByRole('button', { name: 'Assign Transfer Trip', exact: true }).first().click();
        await page.getByLabel('Transfer trip').selectOption(`driver:${driverSession.user.id}`);
        await captureControls(page, 'after-transfer');
        const assignedTransfer = page.waitForResponse((response) => response.url() === `${transfers}/${updated.id}/assign`);
        await page.getByRole('button', { name: 'Confirm', exact: true }).click();
        const assignedResult = await assignedTransfer;
        assert.equal(assignedResult.status(), 200);
        const transferTrip = (await assignedResult.json()).trip_id;
        await page.getByRole('button', { name: 'Dispatch Transfer', exact: true }).click();
        await page.getByLabel('Measured sent weight (kg)', { exact: true }).fill('9');
        const dispatched = page.waitForResponse((response) => response.url() === `${transfers}/${updated.id}/dispatch`);
        await page.getByRole('button', { name: 'Confirm', exact: true }).click();
        assert.equal((await dispatched).status(), 200);
        const transferDriver = await browser.newContext();
        try {
          await transferDriver.addInitScript(({ user, access_token }) => {
            localStorage.setItem('krishilink_user', JSON.stringify(user));
            localStorage.setItem('krishilink_token', access_token);
          }, driverSession);
          const route = await transferDriver.newPage();
          await route.goto(frontend + '/driver');
          const acknowledge = route.waitForResponse((response) => response.url() === `${api}/trips/${transferTrip}/acknowledge`);
          await route.getByRole('button', { name: /acknowledge trip/i }).first().click();
          assert.equal((await acknowledge).status(), 200);
          await route.goto(frontend + `/driver/trip/${transferTrip}`);
          await route.getByRole('button', { name: /start trip/i }).click();
          await route.getByRole('button', { name: /reached hub/i }).click();
          await route.getByRole('button', { name: /return to base/i }).waitFor();
        } finally {
          await transferDriver.close();
        }
        await page.getByRole('button', { name: 'Confirm Received at Hub', exact: true }).click();
        await page.getByLabel('Measured received weight (kg)', { exact: true }).fill('8');
        const received = page.waitForResponse((response) => response.url() === `${transfers}/${updated.id}/receive`);
        await page.getByRole('button', { name: 'Confirm', exact: true }).click();
        assert.equal((await received).status(), 200);
        const receiveReload = page.waitForResponse((response) => response.url() === transfers);
        await page.reload();
        assert.ok((await (await receiveReload).json()).items.some(({ id, status, received_kg }) =>
          id === updated.id && status === 'RECEIVED' && received_kg === 8));
        const ledger = (await (await backend.get(`${api}/hubs/${city.id}/stock-ledger`, { headers: operatorHeaders })).json()).items;
        assert.ok(ledger.some((entry) => entry.reason === 'TRANSFER_IN' && entry.delta_kg === 8));
        const sourceLedger = (await (await backend.get(`${api}/hubs/${central.id}/stock-ledger`, { headers: operatorHeaders })).json()).items;
        assert.ok(sourceLedger.some((entry) => entry.reason === 'PICKUP' && entry.delta_kg === 23));
        assert.ok(sourceLedger.some((entry) => entry.reason === 'TRANSFER_OUT' && entry.delta_kg === -9));
        const finalBuyer = await browser.newContext();
        const finalFarmer = await browser.newContext();
        try {
          for (const [roleContext, auth] of [[finalBuyer, buyerSession], [finalFarmer, session]]) {
            await roleContext.addInitScript(({ user, access_token }) => {
              localStorage.setItem('krishilink_user', JSON.stringify(user));
              localStorage.setItem('krishilink_token', access_token);
            }, auth);
          }
          const checkoutPage = await finalBuyer.newPage();
          await checkoutPage.goto(frontend + `/buyer/crop/${crop.id}`);
          await checkoutPage.getByRole('button', { name: 'ADD', exact: true }).click();
          await checkoutPage.getByRole('button', { name: /view cart/i }).click();
          await checkoutPage.getByRole('button', { name: 'Proceed to Checkout' }).click();
          const created = checkoutPage.waitForResponse((response) => response.url() === `${api}/orders/checkout`);
          await checkoutPage.getByRole('button', { name: 'Confirm & Place Order' }).click();
          const orderResponse = await created;
          assert.equal(orderResponse.status(), 201);
          const order = await orderResponse.json();
          await checkoutPage.getByRole('button', { name: 'View All Orders' }).click();
          await checkoutPage.reload();
          await checkoutPage.getByText(`#${order.id}`, { exact: true }).waitFor();
          await checkoutPage.goto(frontend + `/buyer/orders/${order.id}`);
          await checkoutPage.getByText('PLACED', { exact: true }).waitFor();
          const calculated = await backend.post(`${api}/admin/settlements/calculate?settle_date=${submittedListing.listing_date}`, { headers: operatorHeaders });
          assert.equal(calculated.status(), 200);
          const settlement = (await calculated.json()).items.find((item) => item.farmer_id === session.user.id);
          assert.equal(settlement?.accepted_kg, 23);
          const farmerPage = await finalFarmer.newPage();
          const paid = farmerPage.waitForResponse((response) => response.url() === `${api}/farmers/me/settlements`);
          await farmerPage.goto(frontend + '/farmer/payments');
          assert.ok((await (await paid).json()).items.some(({ id }) => id === settlement.id));
          await farmerPage.getByText(/23 kg/i).first().waitFor();
        } finally {
          await finalBuyer.close();
          await finalFarmer.close();
        }
      } finally {
        await adminContext.close();
      }
      console.log('Live auth, checkout/history/tracking, harvest, pickup assignment, driver receipts, hub intake, settlement review and measured transfers passed');
    } finally {
      await backend.dispose();
    }
  } else {
    throw new Error(`Unknown smoke mode: ${mode}`);
  }
} finally {
  await browser.close();
}
