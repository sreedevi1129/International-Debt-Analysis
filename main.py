import pandas as pd
import streamlit as st
import os
@st.cache_data
def load_saved_debt_data():
    return pd.read_csv("International_Debt_Long.csv")

df = pd.read_csv("IDS_ALLCountries_Data.csv", encoding="cp1252")
print(df.head())
print("Dataset shape:")
print(df.shape)
print("Missing values:")
print(df.isnull().sum())
print("Duplicate rows:", df.duplicated().sum())
print("\nMissing values in each column:")
print(df.isnull().sum())
missing_percentage = (df.isnull().sum() / len(df)) * 100
print("\nMissing-value percentage:")
print(missing_percentage.round(2))
total_missing = df.isnull().sum().sum()
print("\nTotal missing cells:", total_missing)
year_columns = [
    col for col in df.columns
    if str(col).isdigit()
]
yearly_data = df[year_columns]
print("\nTotal missing yearly values:")
print(yearly_data.isnull().sum().sum())
print("\nMissing values by year:")
print(yearly_data.isnull().sum())
print("\nAvailable values by year:")
print(yearly_data.notnull().sum())
df_clean = df.dropna(how="all").drop_duplicates().copy()
year_columns = sorted(
    [col for col in df_clean.columns if str(col).isdigit()],
    key=int
)
df_clean[year_columns] = df_clean[year_columns].apply(
    pd.to_numeric, errors="coerce"
)
year_data = df_clean[year_columns]
previous_value = year_data.ffill(axis=1).notna()
next_value = year_data.bfill(axis=1).notna()
single_gap = (
    year_data.isnull()
    & year_data.shift(1, axis=1).notna()
    & year_data.shift(-1, axis=1).notna()
)
filled_data = year_data.ffill(axis=1)

df_clean[year_columns] = year_data.where(
    ~single_gap, filled_data
)
print("\nMissing yearly values before filling:",
      year_data.isnull().sum().sum())
print("Missing yearly values after filling:",
      df_clean[year_columns].isnull().sum().sum())
df_clean.to_csv("IDS_ALLCountries_Cleaned.csv", index=False)
print("\nCleaned dataset saved successfully!")
df_long = df_clean.melt(
    id_vars=[
        col for col in df_clean.columns
        if col not in year_columns
    ],
    value_vars=year_columns,
    var_name="Year",
    value_name="Debt_Value"
)
df_long["Year"] = df_long["Year"].astype(int)
print("\nReshaped dataset:")
print(df_long.head())
print("\nReshaped dataset size:")
print(df_long.shape)
#df_long.to_csv("International_Debt_Long.csv", index=False)

print("\nLong-format dataset saved successfully!")
print("\nColumn names:")
print(df_long.columns.tolist())
print("\nNumber of countries:")
print(df_long["Country Code"].nunique())
print("\nNumber of indicators:")
print(df_long["Series Code"].nunique())
print("\nMissing debt values:")
print(df_long["Debt_Value"].isnull().sum())
print("\nSample indicators:")
print(
    df_long[["Series Code", "Series Name"]]
    .drop_duplicates()
    .head(10)
)
indicator_names = (
    df_long[["Series Code", "Series Name"]]
    .drop_duplicates()
)
debt_indicators = indicator_names[
    indicator_names["Series Name"]
    .str.contains("external debt stocks", case=False, na=False)
]
print("\nIndicators related to external debt stocks:")
print(debt_indicators.to_string(index=False))
total_debt_indicators = indicator_names[
    indicator_names["Series Name"].str.contains(
        "External debt stocks, total",
        case=False,
        na=False
    )
]

print("\nTotal external debt indicators:")
print(total_debt_indicators.to_string(index=False))
total_debt_code = "DT.DOD.DECT.CD"
debt_data = df_long[
    df_long["Series Code"] == total_debt_code
].copy()
debt_data["Debt_Value"] = pd.to_numeric(
    debt_data["Debt_Value"], errors="coerce"
)
available_data = debt_data.dropna(subset=["Debt_Value"])
latest_year = int(available_data["Year"].max())
latest_data = available_data[
    available_data["Year"] == latest_year
]
country_meta = pd.read_csv(
    "IDS_CountryMetaData.csv",
    encoding="cp1252"
)
print(country_meta.columns.tolist())
print(country_meta[["Code", "Long Name", "Income Group"]].head(10))
print("\nDebt dataset country codes:")
print(latest_data["Country Code"].head(10).tolist())
print("\nMetadata country codes:")
print(country_meta["Code"].head(10).tolist())
country_meta["Code"] = (
    country_meta["Code"].astype(str).str.strip()
)

latest_data["Country Code"] = (
    latest_data["Country Code"].astype(str).str.strip()
)
country_meta["Region"] = (
    country_meta["Region"].fillna("").astype(str).str.strip()
)

valid_codes = set(
    country_meta.loc[
        country_meta["Region"].ne("")
        & country_meta["Region"].ne("Aggregates"),
        "Code"
    ].astype(str).str.strip()
)

country_data = latest_data[
    latest_data["Country Code"].isin(valid_codes)
].copy()

print("Rows before filtering:", len(latest_data))
print("Rows after filtering:", len(country_data))
top_countries = (
    country_data
    .sort_values("Debt_Value", ascending=False)
    .head(10)
)
print("\nAnalysis year:", latest_year)
print("\nTop 10 countries by external debt:")
print(
    top_countries[
        ["Country Name", "Year", "Debt_Value"]
    ].to_string(index=False)
)
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))

plt.bar(
    top_countries["Country Name"],
    top_countries["Debt_Value"]
)

plt.title(f"Top 10 Countries by External Debt in {latest_year}")
plt.xlabel("Country")
plt.ylabel("External Debt (Current US$)")
plt.xticks(rotation=45, ha="right")

plt.tight_layout()
plt.savefig("top_10_external_debt.png", dpi=300)
plt.show()

print("\nBar chart saved successfully!")
country_meta = pd.read_csv(
    "IDS_CountryMetaData.csv",
    encoding="cp1252"
)
print("\nMetadata columns:")
print(country_meta.columns.tolist())
print("\nFirst 10 metadata rows:")
print(country_meta[["Code", "Long Name", "Income Group"]].head(10))
country_meta["Income Group"] = country_meta["Income Group"].fillna("")
individual_countries = country_meta[
    country_meta["Code"].notna()
    & country_meta["Income Group"].ne("")
].copy()
print("\nSample country metadata:")
print(
    individual_countries[
        ["Code", "Long Name", "Income Group"]
    ].head(10)
)
india_trend = debt_data[
    debt_data["Country Code"].astype(str).str.strip() == "IND"
].copy()
india_trend["Debt_Value"] = pd.to_numeric(
    india_trend["Debt_Value"], errors="coerce"
)
india_trend = india_trend.dropna(
    subset=["Debt_Value"]
).sort_values("Year")
plt.figure(figsize=(12, 6))
plt.plot(
    india_trend["Year"],
    india_trend["Debt_Value"],
    marker="o"
)
plt.title("India's External Debt Trend Over the Years")
plt.xlabel("Year")
plt.ylabel("External Debt (Current US$)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("india_external_debt_trend.png", dpi=300)
plt.show()
print("Long dataset columns:")
print(df_long.columns.tolist())
print("Long dataset shape:")
print(df_long.shape)
mysql_debt = df_long[
    df_long["Series Code"] == "DT.DOD.DECT.CD"
].copy()
mysql_debt.to_csv(
    "Total_External_Debt.csv",
    index=False
)
print("Total external debt data shape:", mysql_debt.shape)
print("Saved Total_External_Debt.csv")
print("CSV rows:", len(mysql_debt))
print("CSV rows with debt values:", mysql_debt["Debt_Value"].notna().sum())
print("Unique country codes:", mysql_debt["Country Code"].nunique())
missing_debt = mysql_debt[
    mysql_debt["Debt_Value"].isna()
]
print("Missing debt rows:", len(missing_debt))
print(
    missing_debt[
        ["Country Name", "Country Code", "Series Name", "Year", "Debt_Value"]
    ].head(20).to_string(index=False)
)
original_debt = df_long[
    df_long["Series Code"] == "DT.DOD.DECT.CD"
].copy()
print("Original indicator rows:", len(original_debt))
print("Original missing values:",
      original_debt["Debt_Value"].isna().sum())

print("\nExample missing records:")
print(
    original_debt.loc[
        original_debt["Debt_Value"].isna(),
        ["Country Name", "Country Code", "Year", "Debt_Value"]
    ].head(20).to_string(index=False)
)
print("\nMissing debt values by year (2000-2024):")
missing_by_year = (
    original_debt[
        original_debt["Debt_Value"].isna()
        & original_debt["Year"].between(2000, 2024)
    ]
    .groupby("Year")
    .size()
    .sort_index()
)
print(missing_by_year.to_string())
print("\nMissing records from 2011 to 2018:")

print(
    original_debt[
        original_debt["Debt_Value"].isna()
        & original_debt["Year"].between(2011, 2018)
    ][["Country Name", "Country Code", "Year"]]
    .to_string(index=False)
)
country_meta["Code"] = country_meta["Code"].astype(str).str.strip()
valid_country_codes = set(
    country_meta.loc[
        ~country_meta["Long Name"].str.contains(
            "income|region|IDA|IBRD|World|least developed countries", case=False, na=False
        ),
        "Code"
    ].dropna().astype(str).str.strip()
)
top10_debt = df_long.loc[
    (df_long["Series Code"] == "DT.DOD.DECT.CD")
    & (df_long["Year"] == 2024),
    ["Country Name", "Country Code", "Debt_Value"]
].copy()

top10_debt["Country Code"] = (
    top10_debt["Country Code"].astype(str).str.strip()
)

top10_debt = top10_debt[
    top10_debt["Country Code"].isin(valid_country_codes)
].dropna(subset=["Debt_Value"])

top10_debt = (
    top10_debt
    .drop_duplicates(subset=["Country Code"])
    .nlargest(10, "Debt_Value")
)

top10_debt.to_csv("top_10_external_debt.csv", index=False)
print("\nTop 10 debt CSV created successfully!")
print(top10_debt)




