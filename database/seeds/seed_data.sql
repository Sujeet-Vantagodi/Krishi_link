-- ==============================================================================
-- KRISHILINK PLATFORM - PRODUCTION SEED DATA
-- Pre-populated with All 27 Users, Credentials, Hubs, Crops, Vehicles, Stock & Trips
-- Default demo password for all users: '123456' (Bcrypt hash below)
-- ==============================================================================

-- 1. HUBS
INSERT INTO hubs (id, name, type, parent_hub_id, location, latitude, longitude, address, capacity_kg, has_cold_room, active) VALUES
('h_main', 'Bengaluru Main Hub (Yeshwanthpur)', 'main', NULL, ST_SetSRID(ST_MakePoint(77.5400, 13.0285), 4326), 13.0285, 77.5400, 'APMC Yard, Yeshwanthpur, Bengaluru 560022', 50000.00, true, true),
('h_kolar', 'Kolar Village Mini Hub', 'village', 'h_main', ST_SetSRID(ST_MakePoint(78.1290, 13.1360), 4326), 13.1360, 78.1290, 'Mandi Road, Kolar Rural 563101', 12000.00, false, true),
('h_chikkaballapur', 'Chikkaballapur Village Mini Hub', 'village', 'h_main', ST_SetSRID(ST_MakePoint(77.7315, 13.4355), 4326), 13.4355, 77.7315, 'Near Old Bus Stand, Chikkaballapur 562101', 10000.00, false, true),
('h_doddaballapur', 'Doddaballapur Village Mini Hub', 'village', 'h_main', ST_SetSRID(ST_MakePoint(77.5750, 13.2257), 4326), 13.2257, 77.5750, 'Industrial Area Main Road, Doddaballapur 561203', 8000.00, false, true),
('h_hoskote', 'Hoskote Village Mini Hub', 'village', 'h_main', ST_SetSRID(ST_MakePoint(77.7982, 13.0707), 4326), 13.0707, 77.7982, 'National Highway Cross, Hoskote 562114', 9000.00, false, true),
('h_whitefield', 'Whitefield City Mini Hub', 'city', 'h_main', ST_SetSRID(ST_MakePoint(77.7500, 12.9698), 4326), 12.9698, 77.7500, 'ITPL Main Road, Whitefield, Bengaluru 560066', 15000.00, true, true),
('h_hsr', 'HSR Layout City Mini Hub', 'city', 'h_main', ST_SetSRID(ST_MakePoint(77.6389, 12.9116), 4326), 12.9116, 77.6389, 'Sector 2, 27th Main, HSR Layout, Bengaluru 560102', 15000.00, true, true),
('h_jayanagar', 'Jayanagar City Mini Hub', 'city', 'h_main', ST_SetSRID(ST_MakePoint(77.5838, 12.9308), 4326), 12.9308, 77.5838, '4th Block, 11th Main, Jayanagar, Bengaluru 560011', 12000.00, true, true),
('h_malleshwaram', 'Malleshwaram City Mini Hub', 'city', 'h_main', ST_SetSRID(ST_MakePoint(77.5647, 13.0035), 4326), 13.0035, 77.5647, '8th Cross, Sampige Road, Malleshwaram 560003', 10000.00, true, true)
ON CONFLICT (id) DO NOTHING;

-- 2. VEHICLES
INSERT INTO vehicles (id, reg_no, type, capacity_kg, ownership, active) VALUES
('v_1', 'KA 01 AB 1234', 'Tata Ace (Chota Hathi)', 1000.00, 'rent', true),
('v_2', 'KA 04 C 5678', 'Mahindra Bolero Maxi Truck', 1500.00, 'rent', true),
('v_3', 'KA 03 D 9012', 'Ashok Leyland Dost', 1250.00, 'own', true),
('v_4', 'KA 51 E 3456', 'Eicher Pro 2049 (Reefer)', 2500.00, 'rent', true)
ON CONFLICT (id) DO NOTHING;

-- 3. CROPS
INSERT INTO crops (id, slug, name_en, name_kn, category, is_organic, unit, shelf_life_hours, shelf_life_days, perishability, min_order_kg, default_min_kg, icon_url, image_emoji, active) VALUES
('c_tomato', 'tomato', 'Tomato', 'ಟೊಮೆಟೊ', 'fruit_veg', false, 'kg', 96, 4, 4, 10.00, 20.00, '/icons/tomato.png', '🍅', true),
('c_tomato_org', 'tomato-organic', 'Tomato (Organic)', 'ಟೊಮೆಟೊ (ಸಾವಯವ)', 'fruit_veg', true, 'kg', 96, 4, 4, 10.00, 20.00, '/icons/tomato_org.png', '🍅', true),
('c_onion', 'onion', 'Onion', 'ಈರುಳ್ಳಿ', 'roots', false, 'kg', 480, 20, 2, 25.00, 30.00, '/icons/onion.png', '🧅', true),
('c_potato', 'potato', 'Potato', 'ಆಲೂಗಡ್ಡೆ', 'roots', false, 'kg', 720, 30, 1, 25.00, 30.00, '/icons/potato.png', '🥔', true),
('c_carrot', 'carrot', 'Carrot', 'ಗಜ್ಜರಿ', 'roots', false, 'kg', 168, 7, 3, 10.00, 20.00, '/icons/carrot.png', '🥕', true),
('c_beans', 'french-beans', 'French Beans', 'ಬೀನ್ಸ್', 'fruit_veg', false, 'kg', 120, 5, 4, 10.00, 20.00, '/icons/beans.png', '🫘', true),
('c_cabbage', 'cabbage', 'Cabbage', 'ಎಲೆಕೋಸು', 'leafy', false, 'kg', 192, 8, 3, 15.00, 25.00, '/icons/cabbage.png', '🥬', true),
('c_cauliflower', 'cauliflower', 'Cauliflower', 'ಹೂಕೋಸು', 'fruit_veg', false, 'kg', 120, 5, 4, 10.00, 20.00, '/icons/cauliflower.png', '🥦', true),
('c_brinjal', 'brinjal', 'Brinjal (Eggplant)', 'ಬದನೆಕಾಯಿ', 'fruit_veg', false, 'kg', 144, 6, 3, 10.00, 20.00, '/icons/brinjal.png', '🍆', true),
('c_green_chilli', 'green-chilli', 'Green Chilli', 'ಹಸಿರು ಮೆಣಸಿನಕಾಯಿ', 'herbs', false, 'kg', 168, 7, 3, 5.00, 10.00, '/icons/chilli.png', '🌶️', true),
('c_capsicum', 'capsicum', 'Capsicum (Bell Pepper)', 'ದೊಡ್ಡ ಮೆಣಸಿನಕಾಯಿ', 'fruit_veg', false, 'kg', 144, 6, 4, 10.00, 20.00, '/icons/capsicum.png', '🫑', true)
ON CONFLICT (id) DO NOTHING;

-- 4. USERS (WITH CREDENTIALS & BCRYPT PASSWORD HASH: password '123456')
-- Hash: $2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS
INSERT INTO users (id, phone, role, name, email, password_hash, language, is_active) VALUES
-- Admin
('u_admin_1', '+919876543204', 'admin', 'Anita Rao (Ops Tower)', 'anita.admin@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'en', true),
-- Hub Staff
('u_staff_1', '+919876543205', 'hub_staff', 'Praveen Nayak', 'praveen.staff@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
('u_staff_2', '+919876543206', 'hub_staff', 'Manjunath Swamy', 'manjunath.staff@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
-- Drivers
('u_driver_1', '+919876543203', 'driver', 'Suresh Kumar', 'suresh.driver@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'en', true),
('u_driver_2', '+919876543207', 'driver', 'Ramesh B', 'ramesh.driver@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
('u_driver_3', '+919876543208', 'driver', 'Venkatesh N', 'venkatesh.driver@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
('u_driver_4', '+919876543209', 'driver', 'Anand Gowda', 'anand.driver@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
-- 12 Farmers
('u_farmer_1', '+919876543202', 'farmer', 'Ramesh Gowda', 'ramesh.farmer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
('u_farmer_2', '+919876543211', 'farmer', 'Muniyappa K', 'muniyappa.farmer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
('u_farmer_3', '+919876543212', 'farmer', 'Narayanappa', 'narayanappa.farmer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
('u_farmer_4', '+919876543213', 'farmer', 'Krishnappa Reddy', 'krishnappa.farmer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
('u_farmer_5', '+919876543214', 'farmer', 'Shivalingaiah', 'shivalingaiah.farmer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
('u_farmer_6', '+919876543215', 'farmer', 'Venkataramanappa', 'venkataramana.farmer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
('u_farmer_7', '+919876543216', 'farmer', 'Anjanappa', 'anjanappa.farmer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
('u_farmer_8', '+919876543217', 'farmer', 'Lakshmamma', 'lakshmamma.farmer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
('u_farmer_9', '+919876543218', 'farmer', 'Chennappa', 'chennappa.farmer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
('u_farmer_10', '+919876543219', 'farmer', 'Byre Gowda', 'byregowda.farmer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
('u_farmer_11', '+919876543220', 'farmer', 'Gopalappa', 'gopalappa.farmer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
('u_farmer_12', '+919876543221', 'farmer', 'Srinivas Murthy', 'srinivas.farmer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'kn', true),
-- 8 Buyers
('u_buyer_1', '+919876543201', 'buyer', 'Kiran Kumar (Udupi Upahar)', 'kiran.buyer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'en', true),
('u_buyer_2', '+919876543231', 'buyer', 'Nagarjuna Restaurant Indiranagar', 'nagarjuna.buyer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'en', true),
('u_buyer_3', '+919876543232', 'buyer', 'A2B Caterers & Sweets BTM', 'a2b.buyer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'en', true),
('u_buyer_4', '+919876543233', 'buyer', 'Pai Comforts Student Hostel', 'paicomforts.buyer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'en', true),
('u_buyer_5', '+919876543234', 'buyer', 'SLV Grand Veg Banashankari', 'slvgrand.buyer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'en', true),
('u_buyer_6', '+919876543235', 'buyer', 'Mavalli Tiffin Room (MTR Lalbagh)', 'mtr.buyer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'en', true),
('u_buyer_7', '+919876543236', 'buyer', 'Meghana Foods Koramangala', 'meghana.buyer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'en', true),
('u_buyer_8', '+919876543237', 'buyer', 'Bangalore Central Wholesale Market', 'centralmarket.buyer@krishilink.in', '$2b$10$//cQVfIMahwLg9gOnUjzCe4yJxLY0xgZYzDPO5e6KS8KjXRUR7wwS', 'en', true)
ON CONFLICT (id) DO NOTHING;

-- 5. HUB STAFF MAPPINGS
INSERT INTO hub_staff (user_id, hub_id) VALUES
('u_staff_1', 'h_kolar'),
('u_staff_2', 'h_main')
ON CONFLICT (user_id, hub_id) DO NOTHING;

-- 6. DRIVER PROFILES
INSERT INTO drivers (user_id, licence_no, vehicle_id, home_hub_id, on_duty) VALUES
('u_driver_1', 'KA01-2018-0098765', 'v_1', 'h_kolar', true),
('u_driver_2', 'KA04-2016-0043210', 'v_2', 'h_main', true),
('u_driver_3', 'KA03-2019-0012345', 'v_3', 'h_hsr', true),
('u_driver_4', 'KA51-2015-0077889', 'v_4', 'h_chikkaballapur', false)
ON CONFLICT (user_id) DO NOTHING;

-- 7. FARMER PROFILES
INSERT INTO farmers (user_id, village, taluk, district, location, latitude, longitude, nearest_hub_id, land_acres, default_min_kg, upi_id, reliability_score, approved) VALUES
('u_farmer_1', 'Vemgal', 'Kolar', 'Kolar', ST_SetSRID(ST_MakePoint(78.0821, 13.1672), 4326), 13.1672, 78.0821, 'h_kolar', 2.5, 30.0, 'rameshgowda@oksbi', 4.9, true),
('u_farmer_2', 'Sugatur', 'Kolar', 'Kolar', ST_SetSRID(ST_MakePoint(78.1480, 13.1189), 4326), 13.1189, 78.1480, 'h_kolar', 1.8, 20.0, 'muniyappa@okaxis', 4.8, true),
('u_farmer_3', 'Narasapura', 'Kolar', 'Kolar', ST_SetSRID(ST_MakePoint(78.0163, 13.1495), 4326), 13.1495, 78.0163, 'h_kolar', 3.0, 40.0, 'narayanappa@oksbi', 4.7, true),
('u_farmer_4', 'Shidlaghatta Cross', 'Chikkaballapur', 'Chikkaballapur', ST_SetSRID(ST_MakePoint(77.7650, 13.4120), 4326), 13.4120, 77.7650, 'h_chikkaballapur', 2.0, 25.0, 'krishnappa@okicici', 4.9, true),
('u_farmer_5', 'Gauribidanur Road', 'Chikkaballapur', 'Chikkaballapur', ST_SetSRID(ST_MakePoint(77.7120, 13.4560), 4326), 13.4560, 77.7120, 'h_chikkaballapur', 2.2, 20.0, 'shivaling@oksbi', 4.6, true),
('u_farmer_6', 'Bagepalli Cross', 'Chikkaballapur', 'Chikkaballapur', ST_SetSRID(ST_MakePoint(77.7450, 13.4890), 4326), 13.4890, 77.7450, 'h_chikkaballapur', 1.5, 20.0, 'venkat@okaxis', 4.5, true),
('u_farmer_7', 'Tubagere', 'Doddaballapur', 'Bangalore Rural', ST_SetSRID(ST_MakePoint(77.5340, 13.2680), 4326), 13.2680, 77.5340, 'h_doddaballapur', 3.5, 35.0, 'anjanappa@oksbi', 5.0, true),
('u_farmer_8', 'Sasalu', 'Doddaballapur', 'Bangalore Rural', ST_SetSRID(ST_MakePoint(77.5890, 13.2950), 4326), 13.2950, 77.5890, 'h_doddaballapur', 1.2, 15.0, 'lakshmamma@okicici', 4.7, true),
('u_farmer_9', 'Kasaba', 'Doddaballapur', 'Bangalore Rural', ST_SetSRID(ST_MakePoint(77.5620, 13.2120), 4326), 13.2120, 77.5620, 'h_doddaballapur', 2.8, 30.0, 'chennappa@oksbi', 4.8, true),
('u_farmer_10', 'Sulibele', 'Hoskote', 'Bangalore Rural', ST_SetSRID(ST_MakePoint(77.8240, 13.1250), 4326), 13.1250, 77.8240, 'h_hoskote', 2.0, 25.0, 'byregowda@okaxis', 4.9, true),
('u_farmer_11', 'Anugondanahalli', 'Hoskote', 'Bangalore Rural', ST_SetSRID(ST_MakePoint(77.8420, 13.0450), 4326), 13.0450, 77.8420, 'h_hoskote', 4.0, 40.0, 'gopalappa@oksbi', 4.9, true),
('u_farmer_12', 'Jadigenahalli', 'Hoskote', 'Bangalore Rural', ST_SetSRID(ST_MakePoint(77.8710, 13.0820), 4326), 13.0820, 77.8710, 'h_hoskote', 2.4, 20.0, 'srinivas@okicici', 4.7, true)
ON CONFLICT (user_id) DO NOTHING;

-- 8. BUYER PROFILES
INSERT INTO buyers (user_id, business_name, business_type, gstin, address, location, latitude, longitude, delivery_hub_id, credit_limit, credit_days, credit_due, approved) VALUES
('u_buyer_1', 'Udupi Upahar Veg Restaurant', 'restaurant', '29ABCDE1234F1Z5', '14th Main, HSR Layout Sector 4, Bengaluru 560102', ST_SetSRID(ST_MakePoint(77.6389, 12.9116), 4326), 12.9116, 77.6389, 'h_hsr', 15000000, 7, 4250000, true),
('u_buyer_2', 'Nagarjuna Restaurant Indiranagar', 'restaurant', '29BCDEF2345G2Z6', '100ft Road, HAL 2nd Stage, Indiranagar, Bengaluru 560038', ST_SetSRID(ST_MakePoint(77.6412, 12.9719), 4326), 12.9719, 77.6412, 'h_whitefield', 25000000, 15, 11000000, true),
('u_buyer_3', 'A2B Caterers & Sweets BTM', 'caterer', '29CDEFG3456H3Z7', 'Outer Ring Road, BTM 2nd Stage, Bengaluru 560076', ST_SetSRID(ST_MakePoint(77.6101, 12.9166), 4326), 12.9166, 77.6101, 'h_hsr', 30000000, 10, 0, true),
('u_buyer_4', 'Pai Comforts Student Hostel', 'hostel', '29DEFGH4567J4Z8', 'Koramangala 5th Block, Bengaluru 560095', ST_SetSRID(ST_MakePoint(77.6245, 12.9352), 4326), 12.9352, 77.6245, 'h_hsr', 10000000, 7, 3500000, true),
('u_buyer_5', 'SLV Grand Veg Banashankari', 'restaurant', NULL, '80 Feet Road, 3rd Stage, Banashankari, Bengaluru 560085', ST_SetSRID(ST_MakePoint(77.5468, 12.9254), 4326), 12.9254, 77.5468, 'h_jayanagar', 8000000, 5, 1200000, true),
('u_buyer_6', 'Mavalli Tiffin Room (MTR Lalbagh)', 'restaurant', NULL, '14 Lalbagh Road, Mavalli, Bengaluru 560004', ST_SetSRID(ST_MakePoint(77.5855, 12.9553), 4326), 12.9553, 77.5855, 'h_jayanagar', 50000000, 15, 0, true),
('u_buyer_7', 'Meghana Foods Koramangala', 'restaurant', NULL, 'Koramangala 4th Block, 80 Feet Road, Bengaluru 560034', ST_SetSRID(ST_MakePoint(77.6310, 12.9325), 4326), 12.9325, 77.6310, 'h_hsr', 20000000, 7, 8900000, true),
('u_buyer_8', 'Bangalore Central Wholesale Market', 'wholesaler', NULL, 'K.R. Market Wholesale Yard, Bengaluru 560002', ST_SetSRID(ST_MakePoint(77.5768, 12.9642), 4326), 12.9642, 77.5768, 'h_main', 100000000, 30, 24500000, true)
ON CONFLICT (user_id) DO NOTHING;

-- 9. PUBLISHED PRICES (IN PAISE PER KG: e.g. 2500 = ₹25.00/kg)
INSERT INTO published_prices (date, crop_id, low, high, reference, overridden, published_by) VALUES
('2026-11-20', 'c_tomato', 2200, 3000, 2600, false, 'u_admin_1'),
('2026-11-20', 'c_tomato_org', 3200, 4200, 3700, false, 'u_admin_1'),
('2026-11-20', 'c_onion', 2800, 3400, 3100, false, 'u_admin_1'),
('2026-11-20', 'c_potato', 2400, 2900, 2650, false, 'u_admin_1'),
('2026-11-20', 'c_carrot', 3500, 4500, 4000, false, 'u_admin_1'),
('2026-11-20', 'c_beans', 4000, 5500, 4800, false, 'u_admin_1'),
('2026-11-20', 'c_cabbage', 1800, 2400, 2100, false, 'u_admin_1'),
('2026-11-20', 'c_cauliflower', 2600, 3600, 3100, false, 'u_admin_1'),
('2026-11-20', 'c_brinjal', 2500, 3500, 3000, false, 'u_admin_1'),
('2026-11-20', 'c_green_chilli', 5000, 7000, 6000, false, 'u_admin_1'),
('2026-11-20', 'c_capsicum', 4500, 6000, 5200, false, 'u_admin_1')
ON CONFLICT (date, crop_id) DO NOTHING;

-- 10. HUB STOCK STATUS (THREE-BUTTON MATRIX)
INSERT INTO hub_stock_status (hub_id, crop_id, status, suggested, set_by) VALUES
('h_hsr', 'c_tomato', 'LOW', 'OUT', 'u_admin_1'),
('h_hsr', 'c_onion', 'SUFFICIENT', 'SUFFICIENT', 'u_admin_1'),
('h_hsr', 'c_potato', 'SUFFICIENT', 'SUFFICIENT', 'u_admin_1'),
('h_whitefield', 'c_beans', 'OUT', 'OUT', 'u_admin_1'),
('h_whitefield', 'c_tomato', 'SUFFICIENT', 'SUFFICIENT', 'u_admin_1'),
('h_jayanagar', 'c_onion', 'LOW', 'LOW', 'u_admin_1'),
('h_jayanagar', 'c_tomato', 'SUFFICIENT', 'SUFFICIENT', 'u_admin_1'),
('h_malleshwaram', 'c_capsicum', 'OUT', 'LOW', 'u_admin_1'),
('h_kolar', 'c_tomato', 'SUFFICIENT', 'SUFFICIENT', 'u_staff_1'),
('h_kolar', 'c_beans', 'SUFFICIENT', 'SUFFICIENT', 'u_staff_1'),
('h_chikkaballapur', 'c_onion', 'SUFFICIENT', 'SUFFICIENT', 'u_staff_1'),
('h_doddaballapur', 'c_carrot', 'SUFFICIENT', 'SUFFICIENT', 'u_staff_1'),
('h_main', 'c_tomato', 'SUFFICIENT', 'SUFFICIENT', 'u_staff_2'),
('h_main', 'c_onion', 'SUFFICIENT', 'SUFFICIENT', 'u_staff_2')
ON CONFLICT (hub_id, crop_id) DO NOTHING;

-- 11. STOCK LEDGER (INITIAL SEED STOCK)
INSERT INTO stock_ledger (hub_id, crop_id, delta_kg, reason, ref_type, created_by) VALUES
('h_main', 'c_tomato', 2500.0, 'PICKUP', 'initial_seed', 'u_staff_2'),
('h_main', 'c_onion', 4200.0, 'PICKUP', 'initial_seed', 'u_staff_2'),
('h_main', 'c_potato', 3800.0, 'PICKUP', 'initial_seed', 'u_staff_2'),
('h_kolar', 'c_tomato', 1200.0, 'PICKUP', 'initial_seed', 'u_staff_1'),
('h_kolar', 'c_beans', 650.0, 'PICKUP', 'initial_seed', 'u_staff_1'),
('h_hsr', 'c_tomato', 120.0, 'TRANSFER_IN', 'initial_seed', 'u_admin_1'),
('h_hsr', 'c_onion', 850.0, 'TRANSFER_IN', 'initial_seed', 'u_admin_1');

-- 12. SAMPLE ORDERS
INSERT INTO orders (id, buyer_id, delivery_hub_id, delivery_date, slot, status, subtotal, delivery_fee, total, payment_mode, payment_status, delivery_otp, address) VALUES
('order_101', 'u_buyer_1', 'h_hsr', '2026-11-20', '07:00-08:00', 'OUT_FOR_DELIVERY', 183000, 5000, 188000, 'PREPAID', 'SUCCESS', '4821', 'Udupi Upahar, 14th Main, HSR Layout Sector 4, Bengaluru'),
('order_102', 'u_buyer_2', 'h_whitefield', '2026-11-20', '07:30-08:30', 'CONFIRMED', 245000, 5000, 250000, 'CREDIT', 'PENDING', '7192', 'Nagarjuna Restaurant, 100ft Road, Indiranagar, Bengaluru')
ON CONFLICT (id) DO NOTHING;

INSERT INTO order_items (id, order_id, crop_id, qty_kg, confirmed_kg, delivered_kg, price_per_kg_locked, note) VALUES
('oi_101_1', 'order_101', 'c_tomato', 50.0, 50.0, 50.0, 2600, 'FULL'),
('oi_101_2', 'order_101', 'c_onion', 25.0, 25.0, 25.0, 3100, 'FULL'),
('oi_102_1', 'order_102', 'c_beans', 30.0, 20.0, 0.0, 4800, 'PARTIAL'),
('oi_102_2', 'order_102', 'c_carrot', 25.0, 25.0, 0.0, 4000, 'FULL')
ON CONFLICT (id) DO NOTHING;

-- 13. SAMPLE TRIPS & STOPS
INSERT INTO trips (id, type, status, driver_id, vehicle_id, origin_hub_id, dest_hub_id, assigned_by, date, planned_start, planned_km, planned_minutes, total_planned_kg, total_actual_kg) VALUES
('trip_first_mile_1', 'FIRST_MILE', 'STARTED', 'u_driver_1', 'v_1', 'h_kolar', 'h_kolar', 'u_admin_1', '2026-11-20', '2026-11-20 04:00:00+00', 48.5, 120, 840.0, 520.0),
('trip_last_mile_1', 'LAST_MILE', 'STARTED', 'u_driver_3', 'v_3', 'h_hsr', 'h_hsr', 'u_admin_1', '2026-11-20', '2026-11-20 06:30:00+00', 22.0, 75, 450.0, 180.0)
ON CONFLICT (id) DO NOTHING;

INSERT INTO trip_stops (id, trip_id, seq, type, status, farmer_id, buyer_order_id, hub_id, name, address, phone, location, latitude, longitude, expected_kg, actual_kg, eta) VALUES
('stop_1_1', 'trip_first_mile_1', 1, 'PICKUP', 'COMPLETED', 'u_farmer_1', NULL, NULL, 'Ramesh Gowda Farm', 'Vemgal Village, Kolar', '+919876543202', ST_SetSRID(ST_MakePoint(78.0821, 13.1672), 4326), 13.1672, 78.0821, 200.0, 210.0, '04:20'),
('stop_1_2', 'trip_first_mile_1', 2, 'PICKUP', 'COMPLETED', 'u_farmer_2', NULL, NULL, 'Muniyappa Farm', 'Sugatur Village, Kolar', '+919876543211', ST_SetSRID(ST_MakePoint(78.1480, 13.1189), 4326), 13.1189, 78.1480, 310.0, 310.0, '04:55'),
('stop_1_3', 'trip_first_mile_1', 3, 'PICKUP', 'EN_ROUTE', 'u_farmer_3', NULL, NULL, 'Narayanappa Farm', 'Narasapura, Kolar', '+919876543212', ST_SetSRID(ST_MakePoint(78.0163, 13.1495), 4326), 13.1495, 78.0163, 330.0, 0.0, '05:40'),
('stop_1_4', 'trip_first_mile_1', 4, 'HUB', 'PLANNED', NULL, NULL, 'h_kolar', 'Kolar Village Mini Hub', 'Mandi Road, Kolar', '+919876543205', ST_SetSRID(ST_MakePoint(78.1290, 13.1360), 4326), 13.1360, 78.1290, 0.0, 0.0, '06:15'),
('stop_2_1', 'trip_last_mile_1', 1, 'DELIVERY', 'EN_ROUTE', NULL, 'order_101', NULL, 'Udupi Upahar Veg Restaurant', '14th Main, HSR Layout Sector 4, Bengaluru', '+919876543201', ST_SetSRID(ST_MakePoint(77.6389, 12.9116), 4326), 12.9116, 77.6389, 75.0, 0.0, '07:15')
ON CONFLICT (id) DO NOTHING;

-- 14. SETTINGS
INSERT INTO settings (key, value, updated_by) VALUES
('platform_config', '{"listing_cutoff_time": "18:00", "order_cutoff_time": "20:00", "min_route_payload_kg": 150, "max_variance_percent": 2.0}', 'u_admin_1')
ON CONFLICT (key) DO NOTHING;
