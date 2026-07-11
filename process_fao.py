import requests
import json
import time

PRODUCT_FAO = {
    "Tomate": "2615", "Pomme de terre": "116", "Oignon": "403", "Ail": "406",
    "Concombre / Faqous": "397", "Aubergine": "399", "Carotte": "426",
    "Pomme": "515", "Orange": "490", "Citron / Agrumes": "497", "Pastèque": "567",
    "Melon": "568", "Pêche": "534", "Datte (Deglet)": "577", "Raisin": "560",
    "Huile d'olive vierge extra": "2610"
}

TARGET_COUNTRIES = {
    "114": "Kenya", "124": "Tanzania", "130": "Uganda", "200": "South Africa",
    "45": "Ghana", "57": "Egypt", "96": "Lebanon", "100": "India", "199": "Thailand",
    "160": "Nigeria", "38": "Morocco"
}

BASE_URL = "https://fenixservices.fao.org/faostat/api/v2/en/QA/QC"
results = []

total = len(TARGET_COUNTRIES) * len(PRODUCT_FAO)
count = 0

for area_code, area_name in TARGET_COUNTRIES.items():
    for product_name, item_code in PRODUCT_FAO.items():
        count += 1
        print(f"🔍 {count}/{total} {area_name} - {product_name}", end=" ... ")
        params = {
            "area": area_code,
            "item": item_code,
            "element": "5532",
            "year": "2023,2024",
            "show_codes": "false",
            "show_unit": "false",
            "output_type": "json"
        }
        try:
            resp = requests.get(BASE_URL, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data:
                    latest = max(data, key=lambda x: int(x["Year"]))
                    price_kg = round(latest["Value"] / 1000, 4)
                    results.append({
                        "Region": "Africa/ME/Asia",
                        "Country": area_name,
                        "Product (TN)": product_name,
                        "Price (Local)": price_kg,
                        "Currency": "USD",
                        "Unit": "kg",
                        "Date": str(latest["Year"]),
                        "Source": "FAOSTAT (live)"
                    })
                    print("✅")
                else:
                    print("⚠️ no data")
            else:
                print(f"❌ HTTP {resp.status_code}")
        except Exception as e:
            print(f"❌ {e}")
        time.sleep(0.3)

with open("fao_latest.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n✅ Created fao_latest.json with {len(results)} records.")
