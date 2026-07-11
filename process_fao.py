# process_fao.py
import pandas as pd
import requests
import json
from io import StringIO

# 1. Download the latest FAO QA.csv
url = "https://fenixservices.fao.org/faostat/static/bulkdownloads/QA.csv"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}
resp = requests.get(url, headers=headers)
resp.raise_for_status()

df = pd.read_csv(StringIO(resp.text), encoding="latin-1")

# 2. Filter for your products and countries
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

# Keep only producer prices (element 5532)
df = df[df["Element Code"] == 5532]
df = df[df["Area Code"].astype(str).isin(TARGET_COUNTRIES.keys())]
df = df[df["Item Code"].astype(str).isin(PRODUCT_FAO.values())]
df = df.dropna(subset=["Value"])

# Map codes to names
code_to_french = {v: k for k, v in PRODUCT_FAO.items()}
df["Product (TN)"] = df["Item Code"].astype(str).map(code_to_french)
df = df.dropna(subset=["Product (TN)"])

# Get the latest year per country/product
latest_idx = df.groupby(["Area", "Product (TN)"])["Year"].idxmax()
df_latest = df.loc[latest_idx]

# 3. Build the output list
output = []
for _, row in df_latest.iterrows():
    price_kg = round(float(row["Value"]) / 1000, 4)
    output.append({
        "Region": "Africa/ME/Asia",
        "Country": row["Area"],
        "Product (TN)": row["Product (TN)"],
        "Price (Local)": price_kg,
        "Currency": "USD",
        "Unit": "kg",
        "Date": str(int(row["Year"])),
        "Source": "FAOSTAT (live)"
    })

# 4. Write to fao_latest.json in the repository root
with open("fao_latest.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✅ Successfully updated fao_latest.json with {len(output)} records.")
