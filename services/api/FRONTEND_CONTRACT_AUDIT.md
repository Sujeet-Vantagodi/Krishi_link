# Frontend contract audit

## Continuation from `1dbca2e`

| UI operation | Live request and result | Follow-up |
| --- | --- | --- |
| Password sign-in | POST `/auth/login` with Indian mobile and password. FastAPI validates credentials and returns JWTs and the persisted role. | Provision operational accounts through administration. The form's role selector does not grant roles. |
| Buyer/farmer registration | POST `/auth/register` with the existing role and profile payload. Returns 201 with the persisted user and tokens. Duplicate phones return 409. | Phone and contact email ownership verification still needs a provider. The UI's static six-character hint predates the eight-character API minimum. |
| OTP challenge and confirmation | The existing handlers call `/auth/otp/request` and `/auth/otp/verify`. Bad or repeated challenges fail. | Explicit development OTP only. Production SMS is unavailable. Demo OTP cannot sign into password or operational accounts. |
| Protected route reload | Protected route redirects through the existing login handler, which calls `/me` and returns to the original route when verified. Expired access can trigger `/auth/refresh`. | Logout clears the local session. Server-side token revocation remains outstanding. |
| Transfers board | Authenticated GET `/transfers`, POST request, and POST approve/reject. Priorities and decisions persist. The adapter estimates distance and transit using hub coordinates and 35 km/h. | Status-only controls cannot safely provide an assigned trip, sent weight, or measured received weight. Older inactive hubs may also require additional presentation data. |
| Order status and telemetry | Native GET `/orders/{id}/tracking` returns persisted order status and the latest assigned-driver ping when present. | The protected tracking page still inserts placeholder OTP, ETA and driver details. The live adapter remains unavailable pending approval for that logic. |

Baseline: `9c9a89bb94e118817838c1058a0d7cf57c25651b`. The routes and TypeScript contracts under `src/` govern presentation.

Highest risks: legacy registration can issue an existing account token, legacy login accepts arbitrary passwords in demo mode, protected session state fabricates users, and the frontend network adapter mostly writes to memory. Transfer status buttons lack assignment and measured receipt inputs.

The table records adapter-level baseline status. Native routes are candidates until their payload, response, permissions and persistence are verified. Hook callers control loading and errors via React Query unless handled directly by the page.

| Operation | Direct caller evidence | Baseline |
| --- | --- | --- |
| `getCrops` | `src/features/catalog/hooks.ts:7` | MOCK ONLY |
| `getCropById` | `src/features/catalog/hooks.ts:15` | MOCK ONLY |
| `getTodayPrices` | `src/features/catalog/hooks.ts:23` | MOCK ONLY |
| `createOrder` | `src/features/orders/hooks.ts:22` | MOCK ONLY |
| `getOrders` | `src/features/orders/hooks.ts:7` | MOCK ONLY |
| `getOrderById` | `src/features/orders/hooks.ts:14` | MOCK ONLY |
| `cancelOrder` | `src/features/orders/hooks.ts:32` | MOCK ONLY |
| `getOrderTracking` | `src/features/tracking/hooks.ts:7` | MOCK ONLY |
| `confirmDelivery` | `src/features/orders/hooks.ts:43` | MOCK ONLY |
| `requestMaskedCall` | `src/features/tracking/hooks.ts:18`, `src/components/call/CallButton.tsx:40` | MOCK ONLY |
| `getFarmerThreshold` | `src/features/listings/hooks.ts:21` | MOCK ONLY |
| `updateFarmerThreshold` | `src/features/listings/hooks.ts:29` | MOCK ONLY |
| `getFarmerListings` | `src/features/listings/hooks.ts:14` | MOCK ONLY |
| `createFarmerListing` | `src/features/listings/hooks.ts:39` | MOCK ONLY |
| `deleteFarmerListing` | `src/features/listings/hooks.ts:49` | MOCK ONLY |
| `getFarmerPickup` | `src/features/listings/hooks.ts:59` | MOCK ONLY |
| `getFarmerPayments` | `src/features/payments/hooks.ts:12` | MOCK ONLY |
| `getDriverTrips` | `src/features/trips/hooks.ts:21` | PARTIALLY SUPPORTED |
| `getDriverTripById` | `src/features/trips/hooks.ts:28` | MOCK ONLY |
| `acknowledgeTrip` | `src/features/trips/hooks.ts:54` | MOCK ONLY |
| `startTrip` | `src/features/trips/hooks.ts:65` | MOCK ONLY |
| `arriveAtStop` | `src/features/trips/hooks.ts:77` | MOCK ONLY |
| `submitPickupReceipt` | `src/features/trips/hooks.ts:95` | MOCK ONLY |
| `submitDelivery` | `src/features/trips/hooks.ts:114` | MOCK ONLY |
| `skipStop` | `src/features/trips/hooks.ts:133` | MOCK ONLY |
| `reachedHub` | `src/features/trips/hooks.ts:143` | MOCK ONLY |
| `returnTrip` | `src/features/trips/hooks.ts:153` | MOCK ONLY |
| `getHubs` | `src/features/hubs/hooks.ts:8` | MOCK ONLY |
| `getHubById` | `src/features/hubs/hooks.ts:15` | MOCK ONLY |
| `getStockMatrix` | `src/features/hubs/hooks.ts:23` | MOCK ONLY |
| `updateStockStatus` | `src/features/hubs/hooks.ts:41` | MOCK ONLY |
| `getTransfers` | `src/features/transfers/hooks.ts:7` | MOCK ONLY |
| `createTransfer` | `src/features/transfers/hooks.ts:15` | MOCK ONLY |
| `updateTransferStatus` | `src/features/transfers/hooks.ts:26` | MOCK ONLY |
| `getDispatchPool` | `src/pages/admin/Dispatch.tsx:17` | MOCK ONLY |
| `assignTrip` | `src/features/trips/hooks.ts:163` | MOCK ONLY |
| `getAdminTrips` | `src/features/trips/hooks.ts:37` | MOCK ONLY |
| `getAdminTripById` | `src/features/trips/hooks.ts:45` | MOCK ONLY |
| `getAvailableDrivers` | `src/pages/admin/Dispatch.tsx:22` | MOCK ONLY |
| `getPricingForecasts` | `src/features/pricing/hooks.ts:13` | MOCK ONLY |
| `publishPrices` | `src/features/pricing/hooks.ts:27` | MOCK ONLY |
| `getDemandForecasts` | `src/features/pricing/hooks.ts:20` | MOCK ONLY |
| `getAdminSettlements` | `src/features/payments/hooks.ts:19` | MOCK ONLY |
| `approveSettlement` | `src/features/payments/hooks.ts:26` | MOCK ONLY |
| `triggerPayouts` | `src/features/payments/hooks.ts:36` | MOCK ONLY |
| `getAlerts` | `src/features/pricing/hooks.ts:38` | MOCK ONLY |
| `getSettings` | `src/features/pricing/hooks.ts:46` | MOCK ONLY |
| `getFarmersList` | No direct invocation identified | MOCK ONLY |
| `getBuyersList` | No direct invocation identified | MOCK ONLY |
| `getDriversList` | No direct invocation identified | MOCK ONLY |
| `parseVoiceListing` | No direct invocation identified | MOCK ONLY |

## Protected call sites outside the adapter

- `src/pages/auth/Login.tsx:98,236,255` posts phone/password and a role-specific registration profile directly. It expects a token and user, reads string errors, and mutates demo data on registration. Move session handling to a live auth action once identity storage is agreed.
- `src/stores/authStore.ts:61,105,130,153,168,186,200` trusts stored/demo sessions, falls back on request failures, verifies locally, and logs out locally. In live mode hydrate and validate the real session, verify through the backend, and lock role selection to the server role. Preserve JSX and copy.
- `src/pages/auth/VerifyOtp.tsx:75` includes the demo OTP hint. Production should gate the hint and default input using explicit demo mode.
- `src/pages/admin/Buyers.tsx:10`, `Drivers.tsx:9`, `Farmers.tsx:11,99,113`, and `Settings.tsx:12,64` use demo state directly. Replace those reads and writes with authenticated queries and mutations once the endpoints and profile contracts exist.
- `src/lib/realtime/useChannel.ts:7` directly subscribes to mock activity. Switch to authenticated realtime or documented polling once the real event scopes are defined.
- `src/pages/farmer/FarmerThreshold.tsx:35` awaits the mutation without an error handler. Add error presentation using the existing page components with approval.

## Live contract matrix

Endpoints below use `/api/v1` unless otherwise indicated. UUIDs are JSON strings. Quantities are in kg and money is integer paise. `src/types/index.ts` defines the protected presentation shapes. React Query reads use the hook's loading and retry behavior. In several pages, query failures appear as an empty state or loading placeholder. Mutation errors propagate through their hooks and may require protected-page handling.

| Adapter operations | Existing UI | Method and request | Response and persistence | Integration evidence |
| --- | --- | --- | --- | --- |
| `getCrops`, `getCropById`, `getTodayPrices` | `/buyer`, `/buyer/crop/:id`, farmer crop selection and hub views | GET `/crops` with query/category/organic filters, GET `/catalog/crops/{id}`, GET `/prices/today` | Public `Crop[]`, `Crop` and crop ID/price pairs. Reads active crops, ledger balances and published prices. Days derived from hours, root/roots normalized. Rows missing price, shelf life or a supported category are excluded from the existing UI contract. | Implemented. `test_live_catalog_and_published_prices`. |
| `getFarmerThreshold`, `updateFarmerThreshold` | `/farmer`, `/farmer/threshold` | GET/PUT `/farmers/me/threshold`. PUT number `default_min_kg` and optional list of UUID/minimum pairs | Farmer's own default and crop-keyed numeric overrides. Omitted overrides are retained. Update resolves to success after commit. | Implemented. `test_farmer_thresholds_and_listings_persist`. |
| `getFarmerListings`, `createFarmerListing`, `deleteFarmerListing` | `/farmer` | GET/POST `/farmers/me/listings`, DELETE by ID. Create sends `crop_id`, `est_kg`, `listing_date`, UTC `ready_by`. | Farmer's own persisted listings and applied minimum/status. Adapter uses tomorrow in IST when the page supplies only a clock time. Delete transitions the stored row to cancelled and hides it from the existing page. A listing does not book a pickup or add stock. | Implemented. `test_farmer_thresholds_and_listings_persist`. Existing native create runs with pilot cutoff configuration. |
| `acknowledgeTrip`, `startTrip`, `reachedHub`, `returnTrip`, `arriveAtStop`, `skipStop` | `/driver`, `/driver/trip/:id`, stop actions | POST `/trips/{id}/{action}`, POST `/trips/{id}/stops/{stop_id}/{action}`. Arrival sends real lat/lng. Skip sends reason. | Status from Trip or TripStop after transition. Driver must own the trip. Driver hook currently drops coordinates. The itinerary itself is still blocked. | Partially implemented at workflow level. `test_driver_acknowledgement_and_start_contract` and native trip tests. |
| `getHubs`, `getHubById`, `getStockMatrix`, `updateStockStatus` | `/admin/hubs`, `/admin/hubs/:id` | GET `/hubs`, `/hubs/{id}`, `/hubs/stock-matrix`, PUT `/hubs/{id}/stock-status/{crop_id}` with status enum | Flat coordinates mapped into `Hub.location`, matrix cells keyed by IDs. Ledger kg and derived suggestion are distinct from staff-set status. Staff are scoped to assigned hubs for matrix and status writes. | Implemented at API level. `test_hub_status_write_is_scoped_and_does_not_create_inventory`. The page sets its success toast before the request resolves. |
| `getFarmerPayments`, `getAdminSettlements`, `approveSettlement` | `/farmer/payments`, `/admin/payments` | GET `/farmers/me/settlements` and `/admin/settlements`, POST `/admin/settlements/{id}/approve` | Real settlement amount breakdown. Adapter presents stored DRAFT as DUE. Approval changes status with no paid date or payout. Farmer read is owner-scoped. | Implemented. `test_settlement_approval_persists_without_marking_paid`. |

## Remaining contract mismatches

| Operations and UI | Candidate backend coverage | Missing contract or required change |
| --- | --- | --- |
| `createOrder`, `getOrders`, `getOrderById`, `cancelOrder`, `getOrderTracking`, `confirmDelivery` on buyer checkout, orders and tracking | `orders.py` has POST/GET /orders, GET detail and tracking, POST cancel and confirmation. Admin summary is separate. | Checkout submits slot string, selected payment mode, order lines and free-form address. API persists a delivery hub/window and amounts. Resolve immutable per-order address and payment state. Order list lacks the lines/address/location expected by the current page. Delivery needs per-crop receipt evidence and OTP, and tracking needs actual route/telemetry. Legacy fallback pricing and cancellation ledger rules require review. |
| `requestMaskedCall` | POST `/calls/masked` | Telecom provider and authentication/scope on call parties must be verified. BLOCKED BY EXTERNAL SERVICE. |
| `getFarmerPickup` | GET `/farmers/me/pickup` and `/receipts` | The frontend expects its nested trip/stop/vehicle shape, which requires real stop and support contact data. |
| `getDriverTrips`, `getDriverTripById`, `getAdminTrips`, `getAdminTripById` | `driver.py` and `admin.py` GET assigned trips, trip detail and admin lists | Summary and detail responses lack presentation joins for names/addresses, planned payload, route, and nullable telemetry. `src/pages/driver/DriverTrip.tsx:53` renders a vehicle marker using the first stop when current telemetry is absent. Approve changing this fallback and the coordinate forwarder in `src/features/trips/hooks.ts:77`. |
| `submitPickupReceipt`, `submitDelivery` | POST trip stop receipt and delivery | Existing pickup endpoint records one idempotent receipt line. The UI sends a batch and confirmation method. Delivery expects OTP plus per-crop received/rejected weights. The current aggregate UI data is insufficient for multi-crop verification. |
| `getTransfers`, `createTransfer`, `updateTransferStatus` | `transfers.py` lists/requests, approves, dispatches and receives | DB transfer response lacks persisted urgency and approval timestamp. The status-only UI omits assigned trip and receipt kg. Approve minimal wiring to verified existing assignment and measured receipt controls. |
| `getDispatchPool`, `getAvailableDrivers`, `assignTrip` | `admin.py` dispatch pool and `driver.py` available drivers and assignments | UI sends `driver_id`, `hub_id` and display-oriented stops. Native assignment requires `driver_user_id`, provenance identifiers and optional origin/destination. Resolve dispatch/stop shape and driver itinerary together. |
| `getPricingForecasts`, `getDemandForecasts`, `publishPrices` | Catalog reads published prices | No verified forecast provider or validated publication adapter for this UI. Forecasts are BLOCKED BY EXTERNAL SERVICE. |
| `triggerPayouts` | Approval stores only reviewed settlement state | No verified payout provider execution or confirmation adapter. BLOCKED BY EXTERNAL SERVICE. |
| `getAlerts`, `getSettings` | Admin overview and settings handlers exist | No validated alert list presentation with the UI's entity/labels. Settings page edits protected in-memory data directly. |
| `getFarmersList`, `getBuyersList`, `getDriversList` | Per-user profile and driver availability routes exist | Protected directory pages use mock data directly. Roles and profile output for actual admin directory routes still need contract validation. |
| `parseVoiceListing` | No wired native operation established | Mock text parsing remains explicit demo behavior. A real parser with validated crop matching has not been implemented. |
