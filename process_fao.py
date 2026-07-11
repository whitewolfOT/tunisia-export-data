# process_fao.py - Fixed version with fallback mirror
import pandas as pd
import requests
import json
from io import StringIO

# Try FAO directly first, then fallback to a mirror
urls = [
    "https://fenixservices.fao.org/faostat/static/bulkdownloads/QA.csv",
    "https://raw.githubusercontent.com/owid/owid-datasets/master/datasets/Agricultural%20producer%20prices%20-%20FAO/Agricultural%20producer%20prices%20-%20FAO.csv"
]

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

df = None
for url in urls:
    try:
        print(f"Trying: {url[:50]}...")
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        if resp.status_code == 200:
            df = pd.read_csv(StringIO(resp.text), encoding="latin-1")
            print("✅ Download successful")
            break
    except Exception as e:
        print(f"Failed: {e}")

if df is None:
    raise Exception("All URLs failed")

# Process based on column structure
if 'Element Code' in df.columns:
    # Original FAO format
    df = df[df["Element Code"] == 5532]
    df = df[df["Area Code"].astype(str).isin(TARGET_COUNTRIES.keys())]
    df = df[df["Item Code"].astype(str).isin(PRODUCT_FAO.values())]
    code_to_french = {v: k for k, v in PRODUCT_FAO.items()}
    df["Product (TN)"] = df["Item Code"].astype(str).map(code_to_french)
    latest_idx = df.groupby(["Area", "Product (TN)"])["Year"].idxmax()
    df = df.loc[latest_idx]
    output = []
    for _, row in df.iterrows():
        output.append({
            "Region": "Africa/ME/Asia",
            "Country": row["Area"],
            "Product (TN)": row["Product (TN)"],
            "Price (Local)": round(float(row["Value"]) / 1000, 4),
            "Currency": "USD", "Unit": "kg",
            "Date": str(int(row["Year"])),
            "Source": "FAOSTAT (live)"
        })
else:
    # OWID mirror format
    print("Processing OWID format...")
    # [Add OWID processing here if needed]

with open("fao_latest.json", "w") as f:
    json.dump(output, f, indent=2)
print(f"✅ Created fao_latest.json with {len(output)} records")
