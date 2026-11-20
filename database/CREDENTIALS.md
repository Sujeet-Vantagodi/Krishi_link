# 🔐 KrishiLink Platform — User Credentials Directory

All accounts across all 5 roles are pre-configured in the database with active credentials.
Both **Phone + Password** authentication and **Phone + OTP** verification are fully supported.

---

## 🔑 Universal Demo Access
* **Default Password for ALL users:** `123456`
* **Default OTP for ALL users:** `123456` (or any 6-digit number in test mode)
* **Bcrypt Password Hash:** Stored securely in `users.password_hash` column.

---

## 1. 🛡️ Admin & Control Tower

| User ID | Name | Role | Phone (Login) | Password | Email | Location / Station |
|---|---|---|---|---|---|---|
| `u_admin_1` | Anita Rao (Ops Tower) | `admin` | `+919876543204` / `9876543204` | `123456` | `anita.admin@krishilink.in` | Yeshwanthpur Central Ops Tower |

---

## 2. 🏢 Hub Staff

| User ID | Name | Role | Phone (Login) | Password | Email | Assigned Hub |
|---|---|---|---|---|---|---|
| `u_staff_1` | Praveen Nayak | `hub_staff` | `+919876543205` / `9876543205` | `123456` | `praveen.staff@krishilink.in` | Kolar Village Mini Hub (`h_kolar`) |
| `u_staff_2` | Manjunath Swamy | `hub_staff` | `+919876543206` / `9876543206` | `123456` | `manjunath.staff@krishilink.in` | Yeshwanthpur Main Hub (`h_main`) |

---

## 3. 🚚 Drivers (Fleet Logistics)

| User ID | Name | Role | Phone (Login) | Password | Vehicle Assigned | Base Hub | Licence No |
|---|---|---|---|---|---|---|---|
| `u_driver_1` | Suresh Kumar | `driver` | `+919876543203` / `9876543203` | `123456` | KA 01 AB 1234 (Tata Ace) | Kolar (`h_kolar`) | `KA01-2018-0098765` |
| `u_driver_2` | Ramesh B | `driver` | `+919876543207` / `9876543207` | `123456` | KA 04 C 5678 (Mahindra Bolero) | Main Hub (`h_main`) | `KA04-2016-0043210` |
| `u_driver_3` | Venkatesh N | `driver` | `+919876543208` / `9876543208` | `123456` | KA 03 D 9012 (Ashok Leyland Dost) | HSR Layout (`h_hsr`) | `KA03-2019-0012345` |
| `u_driver_4` | Anand Gowda | `driver` | `+919876543209` / `9876543209` | `123456` | KA 51 E 3456 (Eicher Reefer) | Chikkaballapur (`h_chikkaballapur`) | `KA51-2015-0077889` |

---

## 4. 👨‍🌾 Farmers (Karnataka Smallholder Network)

| User ID | Name (English & Kannada) | Phone (Login) | Password | Village & Taluk | Nearest Hub | Land Size | UPI ID |
|---|---|---|---|---|---|---|---|
| `u_farmer_1` | Ramesh Gowda (ರಾಮೇಶ್ ಗೌಡ) | `+919876543202` / `9876543202` | `123456` | Vemgal, Kolar | Kolar (`h_kolar`) | 2.5 acres | `rameshgowda@oksbi` |
| `u_farmer_2` | Muniyappa K (ಮುನಿಯಪ್ಪ ಕೆ) | `+919876543211` / `9876543211` | `123456` | Sugatur, Kolar | Kolar (`h_kolar`) | 1.8 acres | `muniyappa@okaxis` |
| `u_farmer_3` | Narayanappa (ನಾರಾಯಣಪ್ಪ) | `+919876543212` / `9876543212` | `123456` | Narasapura, Kolar | Kolar (`h_kolar`) | 3.0 acres | `narayanappa@oksbi` |
| `u_farmer_4` | Krishnappa Reddy (ಕೃಷ್ಣಪ್ಪ ರೆಡ್ಡಿ) | `+919876543213` / `9876543213` | `123456` | Shidlaghatta Cross, Chikkaballapur | Chikkaballapur (`h_chikkaballapur`) | 2.0 acres | `krishnappa@okicici` |
| `u_farmer_5` | Shivalingaiah (ಶಿವಲಿಂಗಯ್ಯ) | `+919876543214` / `9876543214` | `123456` | Gauribidanur Road, Chikkaballapur | Chikkaballapur (`h_chikkaballapur`) | 2.2 acres | `shivaling@oksbi` |
| `u_farmer_6` | Venkataramanappa (ವೆಂಕಟರಮಣಪ್ಪ) | `+919876543215` / `9876543215` | `123456` | Bagepalli Cross, Chikkaballapur | Chikkaballapur (`h_chikkaballapur`) | 1.5 acres | `venkat@okaxis` |
| `u_farmer_7` | Anjanappa (ಆಂಜನಪ್ಪ) | `+919876543216` / `9876543216` | `123456` | Tubagere, Doddaballapur | Doddaballapur (`h_doddaballapur`) | 3.5 acres | `anjanappa@oksbi` |
| `u_farmer_8` | Lakshmamma (ಲಕ್ಷ್ಮಮ್ಮ) | `+919876543217` / `9876543217` | `123456` | Sasalu, Doddaballapur | Doddaballapur (`h_doddaballapur`) | 1.2 acres | `lakshmamma@okicici` |
| `u_farmer_9` | Chennappa (ಚೆನ್ನಪ್ಪ) | `+919876543218` / `9876543218` | `123456` | Kasaba, Doddaballapur | Doddaballapur (`h_doddaballapur`) | 2.8 acres | `chennappa@oksbi` |
| `u_farmer_10` | Byre Gowda (ಬೈರೇ ಗೌಡ) | `+919876543219` / `9876543219` | `123456` | Sulibele, Hoskote | Hoskote (`h_hoskote`) | 2.0 acres | `byregowda@okaxis` |
| `u_farmer_11` | Gopalappa (ಗೋಪಾಲಪ್ಪ) | `+919876543220` / `9876543220` | `123456` | Anugondanahalli, Hoskote | Hoskote (`h_hoskote`) | 4.0 acres | `gopalappa@oksbi` |
| `u_farmer_12` | Srinivas Murthy (ಶ್ರೀನಿವಾಸ ಮೂರ್ತಿ) | `+919876543221` / `9876543221` | `123456` | Jadigenahalli, Hoskote | Hoskote (`h_hoskote`) | 2.4 acres | `srinivas@okicici` |

---

## 5. 🛒 Bulk Buyers (Restaurants, Caterers, Hostels, Wholesalers)

| User ID | Business Name | Phone (Login) | Password | Type | Delivery Hub | Credit Limit | Credit Due |
|---|---|---|---|---|---|---|---|
| `u_buyer_1` | Udupi Upahar Veg Restaurant (Kiran Kumar) | `+919876543201` / `9876543201` | `123456` | Restaurant | HSR Layout (`h_hsr`) | ₹1,50,000 | ₹42,500 |
| `u_buyer_2` | Nagarjuna Restaurant Indiranagar | `+919876543231` / `9876543231` | `123456` | Restaurant | Whitefield (`h_whitefield`) | ₹2,50,000 | ₹1,10,000 |
| `u_buyer_3` | A2B Caterers & Sweets BTM | `+919876543232` / `9876543232` | `123456` | Caterer | HSR Layout (`h_hsr`) | ₹3,00,000 | ₹0 |
| `u_buyer_4` | Pai Comforts Student Hostel | `+919876543233` / `9876543233` | `123456` | Hostel | HSR Layout (`h_hsr`) | ₹1,00,000 | ₹35,000 |
| `u_buyer_5` | SLV Grand Veg Banashankari | `+919876543234` / `9876543234` | `123456` | Restaurant | Jayanagar (`h_jayanagar`) | ₹80,000 | ₹12,000 |
| `u_buyer_6` | Mavalli Tiffin Room (MTR Lalbagh) | `+919876543235` / `9876543235` | `123456` | Restaurant | Jayanagar (`h_jayanagar`) | ₹5,00,000 | ₹0 |
| `u_buyer_7` | Meghana Foods Koramangala | `+919876543236` / `9876543236` | `123456` | Restaurant | HSR Layout (`h_hsr`) | ₹2,00,000 | ₹89,000 |
| `u_buyer_8` | Bangalore Central Wholesale Market | `+919876543237` / `9876543237` | `123456` | Wholesaler | Yeshwanthpur Main (`h_main`) | ₹10,00,000 | ₹2,45,000 |

---

## ⚡ Fast Login Switcher Matrix

In the application login screen, quick role switching is supported using the default demo credentials:

```
Role: Buyer      -> Phone: 9876543201  | Password: 123456
Role: Farmer     -> Phone: 9876543202  | Password: 123456
Role: Driver     -> Phone: 9876543203  | Password: 123456
Role: Admin      -> Phone: 9876543204  | Password: 123456
Role: Hub Staff  -> Phone: 9876543205  | Password: 123456
```
