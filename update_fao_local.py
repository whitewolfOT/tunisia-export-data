import requests
import pandas as pd
import json
import os
from datetime import datetime
from io import StringIO

# ==========================================
# YOUR PRODUCT & COUNTRY MAPPING
# ==========================================
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

# ==========================================
# 1. Try FAOSTAT API v2 (more reliable than bulk CSV)
# ==========================================
def fetch_via_api():
    base = "https://fenixservices.fao.org/faostat/api/v2/en/QA/QC"
    results = []
    for area_code, area_name in TARGET_COUNTRIES.items():
        for prod_name, item_code in PRODUCT_FAO.items():
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
                resp = requests.get(base, params=params, timeout=15)
                if resp.status_code == 200 and resp.text.startswith('{'):
                    data = resp.json().get("data", [])
                    if data:
                        latest = max(data, key=lambda x: int(x["Year"]))
                        price_kg = round(latest["Value"] / 1000, 4)
                        results.append({
                            "Region": "Africa/ME/Asia",
                            "Country": area_name,
                            "Product (TN)": prod_name,
                            "Price (Local)": price_kg,
                            "Currency": "USD",
                            "Unit": "kg",
                            "Date": str(latest["Year"]),
                            "Source": "FAOSTAT (API)"
                        })
            except Exception as e:
                pass
    return results

# ==========================================
# 2. Fallback: download bulk CSV (often works from home IP)
# ==========================================
def fetch_via_csv():
    url = "https://fenixservices.fao.org/faostat/static/bulkdownloads/QA.csv"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text), encoding="latin-1")
    df = df[df["Element Code"] == 5532]
    df = df[df["Area Code"].astype(str).isin(TARGET_COUNTRIES.keys())]
    df = df[df["Item Code"].astype(str).isin(PRODUCT_FAO.values())]
    df = df.dropna(subset=["Value"])

    code_to_french = {v: k for k, v in PRODUCT_FAO.items()}
    df["Product (TN)"] = df["Item Code"].astype(str).map(code_to_french)
    idx = df.groupby(["Area", "Product (TN)"])["Year"].idxmax()
    df_latest = df.loc[idx]
    results = []
    for _, row in df_latest.iterrows():
        results.append({
            "Region": "Africa/ME/Asia",
            "Country": row["Area"],
            "Product (TN)": row["Product (TN)"],
            "Price (Local)": round(float(row["Value"]) / 1000, 4),
            "Currency": "USD",
            "Unit": "kg",
            "Date": str(int(row["Year"])),
            "Source": "FAOSTAT (CSV)"
        })
    return results

# ==========================================
# 3. Main execution
# ==========================================
print("🔄 Attempting API fetch...")
data = fetch_via_api()
if len(data) < 100:  # expected ~176 rows
    print("⚠️ API incomplete, trying CSV fallback...")
    try:
        data = fetch_via_csv()
        print(f"✅ CSV returned {len(data)} rows.")
    except Exception as e:
        print(f"❌ CSV failed: {e}")
else:
    print(f"✅ API returned {len(data)} rows.")

# Save
with open("fao_latest.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Saved fao_latest.json with {len(data)} records.")

# Optional: auto-commit and push if git is available
try:
    import subprocess
    subprocess.run(["git", "add", "fao_latest.json"], check=True)
    subprocess.run(["git", "commit", "-m", f"Update FAO {datetime.now().strftime('%Y-%m-%d')}"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("🚀 Changes pushed to GitHub.")
except Exception:
    print("⚠️ Could not auto-push (git not found or not configured). Please push manually.")
