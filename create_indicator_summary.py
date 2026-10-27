
import pandas as pd

input_file = "International_Debt_Long_Corrected.csv"
output_file = "Indicator_Summary_2024.csv"

summary_parts = []

# Read only 50,000 rows at a time
for chunk in pd.read_csv(input_file, chunksize=50000):
    chunk = chunk[
        (chunk["Year"] == 2024)
        & chunk["Series Name"].str.contains(
            "External debt stocks", case=False, na=False
        )
        & chunk["Debt_Value"].notna()
    ]

    if not chunk.empty:
        part = chunk.groupby("Series Name")["Debt_Value"].sum()
        summary_parts.append(part)

# Combine the smaller summaries
if summary_parts:
    summary = (
        pd.concat(summary_parts)
        .groupby(level=0)
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    summary.columns = ["Series Name", "Debt_Value"]
    summary.to_csv(output_file, index=False)

    print("Updated summary successfully!")
    print(summary.head(10))
else:
    print("No matching external-debt records found.")
