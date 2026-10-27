import os
import pandas as pd
import streamlit as st
import mysql.connector
from pathlib import Path

st.set_page_config(page_title="International Debt Analysis", layout="wide")

st.title("International Debt Analysis")
st.write("Explore international debt data using MySQL.")
def load_saved_debt_data():
    return None

# --------------------------------------------------
# DASHBOARD: FOUR CHARTS
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

@st.cache_data
def load_csv(filename):
    path = BASE_DIR / filename

    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path, low_memory=False)
    except Exception as error:
        st.error(f"Could not read {filename}: {error}")
        return pd.DataFrame()


debt = load_csv("Total_External_Debt.csv")
top10_file = load_csv("top_10_external_debt.csv")
bottom10_file = load_csv("bottom_10_external_debt.csv")
indicator_file = load_csv("Indicator_Summary_2024.csv")

def standardize_columns(df):
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\ufeff", "", regex=False)
    )
    return df


debt = standardize_columns(debt)
top10_file = standardize_columns(top10_file)
bottom10_file = standardize_columns(bottom10_file)
indicator_file = standardize_columns(indicator_file)


def find_column(df, candidates):
    """Find a column without depending on capitalization."""
    lookup = {str(c).strip().lower(): c for c in df.columns}

    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]

    return None


country_col = find_column(
    debt, ["Country Name", "Country", "Country_Name"]
)
year_col = find_column(debt, ["Year"])
value_col = find_column(debt, ["Debt_Value", "Debt Value"])
series_col = find_column(debt, ["Series Name", "Indicator"])

top_country_col = find_column(
    top10_file, ["Country Name", "Country", "Country_Name"]
)
top_value_col = find_column(
    top10_file, ["Debt_Value", "Debt Value"]
)

bottom_country_col = find_column(
    bottom10_file, ["Country Name", "Country", "Country_Name"]
)
bottom_value_col = find_column(
    bottom10_file, ["Debt_Value", "Debt Value"]
)

indicator_name_col = find_column(
    indicator_file, ["Series Name", "Indicator"]
)
indicator_value_col = find_column(
    indicator_file, ["Debt_Value", "Debt Value"]
)

if value_col:
    debt[value_col] = pd.to_numeric(debt[value_col], errors="coerce")

if year_col:
    debt[year_col] = pd.to_numeric(debt[year_col], errors="coerce")

if country_col:
    debt[country_col] = debt[country_col].astype("string").str.strip()

if top_value_col:
    top10_file[top_value_col] = pd.to_numeric(
        top10_file[top_value_col], errors="coerce"
    )

if bottom_value_col:
    bottom10_file[bottom_value_col] = pd.to_numeric(
        bottom10_file[bottom_value_col], errors="coerce"
    )

if indicator_value_col:
    indicator_file[indicator_value_col] = pd.to_numeric(
        indicator_file[indicator_value_col], errors="coerce"
    )

st.header("Dashboard — Four Visualizations")
st.caption(
    "Country-wise distribution, highest and lowest debt, "
    "indicators, and historical trends."
)

if debt.empty:
    st.error(
        "Total_External_Debt.csv was not found or is empty. "
        "Place it in the same folder as debt_dashboard.py."
    )
    st.stop()

if not all([country_col, year_col, value_col]):
    st.error(
        "The debt CSV needs Country Name, Year, and Debt_Value columns. "
        f"Columns found: {list(debt.columns)}"
    )
    st.stop()


debt = debt.dropna(subset=[country_col, year_col, value_col]).copy()

aggregate_codes = {
    "WLD", "HIC", "MIC", "LIC", "LMC", "UMC",
    "EAS", "ECS", "LCN", "MEA", "NAC", "SAS",
    "SSF", "SSA", "EAP", "ECA", "LAC",
    "ARB", "CEB", "CSS", "EUU", "FCS", "OED",
    "OSS", "PSS", "PST", "TEA", "TEC", "TLA",
    "TMN", "TSA", "TSS", "VUT"
}

code_col = find_column(debt, ["Country Code", "Code"])

countries_data = debt.copy()
if code_col:
    countries_data = countries_data[
        ~countries_data[code_col].astype(str).str.upper().isin(aggregate_codes)
    ]

countries_data = countries_data[
    countries_data[country_col].notna()
    & (countries_data[country_col].str.lower() != "world")
]

latest_year = int(countries_data[year_col].max())
latest_data = countries_data[countries_data[year_col] == latest_year].copy()

if series_col:
    external_total = latest_data[
        latest_data[series_col].astype(str).str.contains(
            "external debt stocks, total", case=False, na=False
        )
    ]

    if not external_total.empty:
        latest_data = external_total

country_totals = (
    latest_data.groupby(country_col, as_index=False)[value_col]
    .sum()
    )

excluded_names = [
    "World",
    "South Asia",
    "East Asia & Pacific",
    "Europe & Central Asia",
    "Latin America & Caribbean",
    "Middle East & North Africa",
    "Sub-Saharan Africa",
    "Low & middle income",
    "Lower middle income",
    "Upper middle income",
    "High income",
    "IDA total",
    "IBRD only",
]

country_totals = country_totals[
    ~country_totals[country_col].astype(str).str.strip().isin(excluded_names)
].sort_values(value_col, ascending=False)

# Show a dropdown for selecting a country.
country_options = sorted(countries_data[country_col].dropna().unique().tolist())

st.sidebar.header("Dashboard filter")
selected_country = st.sidebar.selectbox(
    "Select a country",
    country_options,
    index=country_options.index("India") if "India" in country_options else 0
)

selected_data = countries_data[
    countries_data[country_col] == selected_country
].copy()

if series_col and not selected_data.empty:
    external_total = selected_data[
        selected_data[series_col].astype(str).str.contains(
            "external debt stocks, total", case=False, na=False
        )
    ]
    if not external_total.empty:
        selected_data = external_total

country_trend = (
    selected_data.groupby(year_col, as_index=False)[value_col]
    .sum()
    .sort_values(year_col)
)

st.caption(f"Latest year in the available data: {latest_year}")

st.header("1. Country-wise Debt Distribution")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader(f"{selected_country} — {latest_year}")

    selected_latest = country_totals[
        country_totals[country_col] == selected_country
    ]

    if not selected_latest.empty:
        st.metric(
            label="External debt value",
            value=f"{selected_latest.iloc[0][value_col]:,.0f}"
        )
    else:
        st.info("No latest-year debt total was found for this country.")

with col2:
    st.subheader(f"Countries by External Debt ({latest_year})")
    number_countries = st.slider(
        "Number of countries to display",
        min_value=5,
        max_value=30,
        value=15
    )

    distribution = (
        country_totals.head(number_countries)
        .set_index(country_col)[value_col]
    )

    st.bar_chart(distribution, horizontal=True)

st.header("2. Highest and Lowest External Debt Countries")

left, right = st.columns(2)

with left:
    st.subheader(f"Top 10 Countries ({latest_year})")
    if top_country_col and top_value_col and not top10_file.empty:
        top_chart = top10_file.dropna(
            subset=[top_country_col, top_value_col]
        ).copy()

        excluded_names = [
            "South Asia",
            "World",
            "East Asia & Pacific",
            "Europe & Central Asia",
            "Latin America & Caribbean",
            "Middle East & North Africa",
            "Sub-Saharan Africa",
            "Low & middle income",
            "Lower middle income",
            "Upper middle income",
            "High income",
            "IDA total",
            "IBRD only",
        ]

        top_chart = top_chart[
            ~top_chart[top_country_col].astype(str).str.strip().isin(excluded_names)
        ]

        top_chart = top_chart.nlargest(10, top_value_col)

        st.bar_chart(
            top_chart.set_index(top_country_col)[top_value_col],
            horizontal=True
        )
    else:
        st.bar_chart(
            country_totals.head(10).set_index(country_col)[value_col],
            horizontal=True
        )
   
with right:
    st.subheader(f"Bottom 10 Countries ({latest_year})")

    if bottom_country_col and bottom_value_col and not bottom10_file.empty:
        bottom_chart = bottom10_file.dropna(
            subset=[bottom_country_col, bottom_value_col]
        ).nsmallest(10, bottom_value_col)

        st.bar_chart(
            bottom_chart.set_index(bottom_country_col)[bottom_value_col],
            horizontal=True
        )
    else:
    
        st.bar_chart(
            country_totals.tail(10).sort_values(value_col)
            .set_index(country_col)[value_col],
            horizontal=True
        )

st.header("3. Debt Distribution Across Indicators")

if (
    not indicator_file.empty
    and indicator_name_col
    and indicator_value_col
):
    indicators = indicator_file.dropna(
        subset=[indicator_name_col, indicator_value_col]
    ).nlargest(10, indicator_value_col)

    indicators = indicators.copy()
    indicators[indicator_name_col] = (
    indicators[indicator_name_col].astype(str).str.replace(
        "External debt stocks, ", "", regex=False
        )
    )

    indicators["Formatted Debt Value"] = indicators[indicator_value_col].map(
        lambda x: f"{x:,.2f}" if pd.notna(x) else ""
    )

    st.dataframe(
        indicators[[indicator_name_col, "Formatted Debt Value"]].rename(
            columns={
                indicator_name_col: "Debt Indicator",
                "Formatted Debt Value": "Debt Value"
            }
        ),
        hide_index=True,
        use_container_width=True
    )

    st.bar_chart(
        indicators.set_index(indicator_name_col)[indicator_value_col],
        horizontal=True
    )
        
    st.caption(
        "This chart compares the top indicators in the prepared "
        "Indicator_Summary_2024.csv file."
    )
else:
    st.warning(
        "Indicator summary unavailable. Check that "
        "Indicator_Summary_2024.csv has Series Name and Debt_Value columns."
    )

st.header("4. Trends and Patterns in International Debt")

if not country_trend.empty:
    st.subheader(f"External Debt Trend — {selected_country}")

    trend = country_trend.set_index(year_col)[value_col]
    st.line_chart(trend)

    st.caption(
        "Use the country dropdown on the left to change the country "
        "shown in this trend chart."
    )
else:
    st.warning(f"No debt trend data is available for {selected_country}.")

st.header("Key Insights")

if not country_totals.empty:
    highest = country_totals.iloc[0]
    lowest = country_totals.iloc[-1]

    st.write(
        f"- In {latest_year}, **{highest[country_col]}** had the highest "
        f"recorded value among the countries included in this chart."
    )
    st.write(
        f"- **{lowest[country_col]}** had the lowest recorded value "
        f"among the countries included in this chart."
    )

if not country_trend.empty:
    first_value = country_trend.iloc[0][value_col]
    last_value = country_trend.iloc[-1][value_col]

    if first_value != 0:
        change = ((last_value - first_value) / abs(first_value)) * 100
        direction = "increased" if change > 0 else "decreased" if change < 0 else "did not change"

        st.write(
            f"- {selected_country}'s recorded debt value {direction} by "
            f"{abs(change):.2f}% between {int(country_trend.iloc[0][year_col])} "
            f"and {int(country_trend.iloc[-1][year_col])}."
        )

st.caption(
    "Interpret insights in the context of the selected indicator, year, "
    "currency/unit, and data coverage."
)


# --------------------------------------------------
# SQL QUESTIONS AND ANSWERS (30 QUERIES)
# --------------------------------------------------
st.header("Dataset Overview")
st.info(
    "Full dataset is stored in MySQL. "
    "Use the SQL questions below to explore the data."
)

st.header("SQL Questions and Answers")

questions = [
    "1. Retrieve all distinct country names",
    "2. Count the total number of countries",
    "3. Find the total number of indicators",
    "4. Display the first 10 records",
    "5. Calculate the total global debt",
    "6. List all unique indicator names",
    "7. Find the number of records for each country",
    "8. Records where debt is greater than 1 billion USD",
    "9. Minimum, maximum, and average debt values",
    "10. Count total records",
    "11. Total debt for each country",
    "12. Top 10 countries by total debt",
    "13. Average debt per country",
    "14. Total debt for each indicator",
    "15. Indicator contributing the highest total debt",
    "16. Country with the lowest total debt",
    "17. Total debt by country and indicator",
    "18. Number of indicators per country",
    "19. Countries above the global average debt",
    "20. Rank countries by total debt",
    "21. Top 5 indicators contributing most to debt",
    "22. Percentage contribution of each country",
    "23. Top 3 countries for each indicator",
    "24. Maximum-minus-minimum debt for each country",
    "25. Create a view of the top 10 countries",
    "26. Categorize countries by debt level",
    "27. Cumulative debt per country using a window function",
    "28. Indicators with above-average debt",
    "29. Countries contributing more than 5% of global debt",
    "30. Most dominant indicator for each country",
]

question = st.selectbox("Choose a SQL question", questions)

if st.button("Run SQL Query"):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=os.getenv("MYSQL_PASSWORD"),
            database="international_debt_db"
        )

        if question == "1. Retrieve all distinct country names":
            query = """
                SELECT DISTINCT country_name
                FROM international_debt_long_corrected
                ORDER BY country_name;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Query Results")
            st.dataframe(result_df, use_container_width=True)
            st.success(f"Found {len(result_df)} rows.")
            
        elif question == "2. Count the total number of countries":
            query = """
                SELECT COUNT(DISTINCT country_name) AS total_countries
                FROM international_debt_long_corrected;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Query Results")
            st.dataframe(result_df, use_container_width=True)

        elif question == "3. Find the total number of indicators":
            query = """
                SELECT COUNT(DISTINCT series_name) AS total_indicators
                FROM international_debt_long_corrected
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Query Results")
            st.dataframe(result_df, use_container_width=True)
        elif question == "4. Display the first 10 records":
            query = """
                SELECT *
                FROM international_debt_long_corrected
                LIMIT 10;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Query Results")
            st.dataframe(result_df, use_container_width=True)
    
        
        elif question == "5. Calculate the total global debt":
            query = """
                SELECT SUM(debt_value) AS total_global_debt
                FROM international_debt_long_corrected
                WHERE series_code = 'DT.DOD.DECT.CD'
                AND year = 2024
                AND counterpart_area_code = 'WLD';
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Total Global Debt (2024)")
            st.dataframe(result_df, use_container_width=True)
        elif question == "6. List all unique indicator names":
            query = """
                SELECT DISTINCT series_name
                FROM international_debt_long_corrected
                ORDER BY series_name;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Query Results")
            st.dataframe(result_df, use_container_width=True)
            st.success(f"Found {len(result_df)} indicators.")
        elif question == "7. Find the number of records for each country":
            query = """
                SELECT country_name, COUNT(*) AS total_records
                FROM international_debt_long_corrected
                GROUP BY country_name
                ORDER BY total_records DESC;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Number of Records for Each Country")
            st.dataframe(result_df, use_container_width=True)
        elif question == "8. Records where debt is greater than 1 billion USD":
            query = """
                SELECT *
                FROM international_debt_long_corrected
                WHERE debt_value > 1000000000
                LIMIT 1000;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Records with Debt Above 1 Billion USD")
            st.dataframe(result_df, use_container_width=True)
        elif question == "9. Minimum, maximum, and average debt values":
            query = """
                SELECT
                    MIN(debt_value) AS minimum_debt,
                    MAX(debt_value) AS maximum_debt,
                    AVG(debt_value) AS average_debt
                FROM international_debt_long_corrected;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Minimum, Maximum, and Average Debt")
            st.dataframe(result_df, use_container_width=True)

        elif question == "10. Count total records":
            query = """
                SELECT COUNT(*) AS total_records
                FROM international_debt_long_corrected;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Total Number of Records")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "11. Total debt for each country":
            query = """
                SELECT
                    country_name,
                    SUM(debt_value) AS total_debt
                FROM international_debt_long_corrected
                WHERE series_code = 'DT.DOD.DECT.CD'
                  AND year = 2024
                  AND debt_value IS NOT NULL
                GROUP BY country_name
                ORDER BY total_debt DESC;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Total Debt for Each Country (2024)")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "12. Top 10 countries by total debt":
            query = """
                SELECT
                    country_name,
                    SUM(debt_value) AS total_debt
                FROM international_debt_long_corrected
                WHERE series_code = 'DT.DOD.DECT.CD'
                  AND year = 2024
                  AND debt_value IS NOT NULL
                GROUP BY country_name
                ORDER BY total_debt DESC
                LIMIT 10;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Top 10 Countries by Total Debt (2024)")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "13. Average debt per country":
            query = """
                SELECT
                    country_name,
                    AVG(debt_value) AS average_debt
                FROM international_debt_long_corrected
                WHERE series_code = 'DT.DOD.DECT.CD'
                  AND year = 2024
                  AND debt_value IS NOT NULL
                GROUP BY country_name
                ORDER BY average_debt DESC;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Average Debt per Country (2024)")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "14. Total debt for each indicator":
            query = """
                SELECT
                    series_name,
                    SUM(debt_value) AS total_debt
                FROM international_debt_long_corrected
                WHERE year = 2024
                  AND debt_value IS NOT NULL
                  AND series_name IS NOT NULL
                GROUP BY series_name
                ORDER BY total_debt DESC;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Total Debt for Each Indicator (2024)")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "15. Indicator contributing the highest total debt":
            query = """
                SELECT
                    series_name,
                    SUM(debt_value) AS total_debt
                FROM international_debt_long_corrected
                WHERE year = 2024
                  AND debt_value IS NOT NULL
                  AND series_name IS NOT NULL
                GROUP BY series_name
                ORDER BY total_debt DESC
                LIMIT 1;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Indicator with the Highest Total Debt (2024)")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "16. Country with the lowest total debt":
            query = """
                SELECT
                    country_name,
                    SUM(debt_value) AS total_debt
                FROM international_debt_long_corrected
                WHERE series_code = 'DT.DOD.DECT.CD'
                  AND year = 2024
                  AND debt_value IS NOT NULL
                GROUP BY country_name
                ORDER BY total_debt ASC
                LIMIT 1;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Country with the Lowest Total Debt (2024)")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "17. Total debt by country and indicator":
            query = """
                SELECT
                    country_name,
                    series_name,
                    SUM(debt_value) AS total_debt
                FROM international_debt_long_corrected
                WHERE year = 2024
                  AND debt_value IS NOT NULL
                  AND series_name IS NOT NULL
                GROUP BY country_name, series_name
                ORDER BY country_name, total_debt DESC;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Total Debt by Country and Indicator (2024)")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "18. Number of indicators per country":
            query = """
                SELECT
                    country_name,
                    COUNT(DISTINCT series_code) AS number_of_indicators
                FROM international_debt_long_corrected
                WHERE series_code IS NOT NULL
                GROUP BY country_name
                ORDER BY number_of_indicators DESC;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Number of Indicators per Country")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "19. Countries above the global average debt":
            query = """
                SELECT
                    country_name,
                    SUM(debt_value) AS total_debt
                FROM international_debt_long_corrected
                WHERE series_code = 'DT.DOD.DECT.CD'
                  AND year = 2024
                  AND debt_value IS NOT NULL
                GROUP BY country_name
                HAVING SUM(debt_value) > (
                    SELECT AVG(country_debt)
                    FROM (
                        SELECT
                            country_name,
                            SUM(debt_value) AS country_debt
                        FROM international_debt_long_corrected
                        WHERE series_code = 'DT.DOD.DECT.CD'
                          AND year = 2024
                          AND debt_value IS NOT NULL
                        GROUP BY country_name
                    ) AS country_totals
                )
                ORDER BY total_debt DESC;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Countries Above the Average Debt (2024)")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "20. Rank countries by total debt":
            query = """
                SELECT
                    country_name,
                    SUM(debt_value) AS total_debt,
                    RANK() OVER (
                        ORDER BY SUM(debt_value) DESC
                    ) AS debt_rank
                FROM international_debt_long_corrected
                WHERE series_code = 'DT.DOD.DECT.CD'
                  AND year = 2024
                  AND debt_value IS NOT NULL
                GROUP BY country_name
                ORDER BY debt_rank;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Country Debt Rankings (2024)")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "21. Top 5 indicators contributing most to debt":
            query = """
                SELECT
                    series_name,
                    SUM(debt_value) AS total_debt
                FROM international_debt_long_corrected
                WHERE year = 2024
                  AND debt_value IS NOT NULL
                  AND series_name IS NOT NULL
                GROUP BY series_name
                ORDER BY total_debt DESC
                LIMIT 5;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Top 5 Indicators by Total Value (2024)")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "22. Percentage contribution of each country":
            query = """
                SELECT
                    country_name,
                    SUM(debt_value) AS total_debt,
                    ROUND(
                        100.0 * SUM(debt_value) /
                        NULLIF(SUM(SUM(debt_value)) OVER (), 0),
                        2
                    ) AS percentage_contribution
                FROM international_debt_long_corrected
                WHERE series_code = 'DT.DOD.DECT.CD'
                  AND year = 2024
                  AND debt_value IS NOT NULL
                GROUP BY country_name
                ORDER BY percentage_contribution DESC;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Country Percentage Contribution (2024)")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "23. Top 3 countries for each indicator":
            query = """
                WITH country_indicator_debt AS (
                    SELECT
                        series_name,
                        country_name,
                        SUM(debt_value) AS total_debt
                    FROM international_debt_long_corrected
                    WHERE year = 2024
                      AND debt_value IS NOT NULL
                      AND series_name IS NOT NULL
                    GROUP BY series_name, country_name
                ),
                ranked_countries AS (
                    SELECT
                        series_name,
                        country_name,
                        total_debt,
                        ROW_NUMBER() OVER (
                            PARTITION BY series_name
                            ORDER BY total_debt DESC
                        ) AS debt_rank
                    FROM country_indicator_debt
                )
                SELECT
                    series_name,
                    country_name,
                    total_debt,
                    debt_rank
                FROM ranked_countries
                WHERE debt_rank <= 3
                ORDER BY series_name, debt_rank;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Top 3 Countries per Indicator (2024)")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "24. Maximum-minus-minimum debt for each country":
            query = """
                SELECT
                    country_name,
                    MAX(debt_value) AS maximum_debt,
                    MIN(debt_value) AS minimum_debt,
                    MAX(debt_value) - MIN(debt_value) AS debt_difference
                FROM international_debt_long_corrected
                WHERE series_code = 'DT.DOD.DECT.CD'
                  AND debt_value IS NOT NULL
                GROUP BY country_name
                ORDER BY debt_difference DESC;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Maximum-Minimum Debt Difference")
            st.dataframe(result_df, use_container_width=True)
        
        
        elif question == "25. Create a view of the top 10 countries":
            query = """
                CREATE OR REPLACE VIEW top_10_countries_debt AS
                SELECT
                    country_name,
                    SUM(debt_value) AS total_debt
                FROM international_debt_long_corrected
                WHERE series_code = 'DT.DOD.DECT.CD'
                  AND year = 2024
                  AND debt_value IS NOT NULL
                  AND country_code NOT IN (
                      'WLD','HIC','LIC','LMC','UMC','MIC','LMY','HPC',
                      'IBD','IBT','IDA','IDB','IDX','EAP','ECA','LAC',
                      'MNA','SAS','SSA','EUU','ARB','CSS','ECS','EMU',
                      'FCS','NAC','OED','OSS','PSS','PST','SST','TEA',
                      'TEC','TLA','TMN','TSA','TSS'
                  )
                  AND country_name NOT LIKE '%income%'
                  AND country_name NOT LIKE '%excluding%'
                  AND country_name NOT LIKE '%total%'
                  AND country_name NOT LIKE '%IDA%'
                  AND country_name NOT LIKE '%IBRD%'
                  AND country_name NOT LIKE '%Caribbean%'
                  AND country_name NOT LIKE '%Africa%'
                  AND country_name NOT LIKE '%Asia%'
                  AND country_name NOT LIKE '%Europe%'
                  AND country_name NOT LIKE '%Pacific%'
                  AND country_name NOT LIKE 'Least developed countries%'
                GROUP BY country_name
                ORDER BY total_debt DESC
                LIMIT 10;
            """
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            cursor.execute("""
                    SELECT country_name, total_debt
                    FROM top_10_countries_debt
                    ORDER BY total_debt DESC
                """)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            result_df = pd.DataFrame(rows, columns=columns)
            cursor.close()
            st.subheader("Top 10 Countries Debt View (2024)")
            st.dataframe(result_df, use_container_width=True)
            st.success("View created successfully.")

        
        elif question == "26. Categorize countries by debt level":
            query = """
                SELECT
                    country_name,
                    SUM(debt_value) AS total_debt,
                    CASE
                        WHEN SUM(debt_value) >= 100000000000
                            THEN 'High'
                        WHEN SUM(debt_value) >= 10000000000
                            THEN 'Medium'
                        ELSE 'Low'
                    END AS debt_category
                FROM international_debt_long_corrected
                WHERE series_code = 'DT.DOD.DECT.CD'
                  AND year = 2024
                  AND debt_value IS NOT NULL
                GROUP BY country_name
                ORDER BY total_debt DESC;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Country Debt Categories (2024)")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "27. Cumulative debt per country using a window function":
            query = """
                SELECT
                    country_name,
                    year,
                    debt_value,
                    SUM(debt_value) OVER (
                        PARTITION BY country_name
                        ORDER BY year
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ) AS cumulative_debt
                FROM international_debt_long_corrected
                WHERE series_code = 'DT.DOD.DECT.CD'
                  AND debt_value IS NOT NULL
                ORDER BY country_name, year;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Cumulative Debt by Country and Year")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "28. Indicators with above-average debt":
            query = """
                SELECT
                    series_name,
                    AVG(debt_value) AS average_debt
                FROM international_debt_long_corrected
                WHERE year = 2024
                  AND debt_value IS NOT NULL
                  AND series_name IS NOT NULL
                GROUP BY series_name
                HAVING AVG(debt_value) > (
                    SELECT AVG(debt_value)
                    FROM international_debt_long_corrected
                    WHERE year = 2024
                      AND debt_value IS NOT NULL
                )
                ORDER BY average_debt DESC;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Indicators Above the Overall Average (2024)")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "29. Countries contributing more than 5% of global debt":
            query = """
                SELECT
                    country_name,
                    total_debt,
                    ROUND(
                        100.0 * total_debt / global_total,
                        2
                    ) AS percentage_contribution
                FROM (
                    SELECT
                        country_name,
                        SUM(debt_value) AS total_debt
                    FROM international_debt_long_corrected
                    WHERE series_code = 'DT.DOD.DECT.CD'
                      AND year = 2024
                      AND debt_value IS NOT NULL
                    GROUP BY country_name
                ) AS country_totals
                CROSS JOIN (
                    SELECT SUM(debt_value) AS global_total
                    FROM international_debt_long_corrected
                    WHERE series_code = 'DT.DOD.DECT.CD'
                      AND year = 2024
                      AND debt_value IS NOT NULL
                ) AS global_debt
                WHERE global_total > 0
                  AND 100.0 * total_debt / global_total > 5
                ORDER BY percentage_contribution DESC;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Countries Contributing More Than 5% (2024)")
            st.dataframe(result_df, use_container_width=True)
        
        elif question == "30. Most dominant indicator for each country":
            query = """
                WITH indicator_totals AS (
                    SELECT
                        country_name,
                        series_name,
                        SUM(debt_value) AS total_debt
                    FROM international_debt_long_corrected
                    WHERE year = 2024
                      AND debt_value IS NOT NULL
                      AND series_name IS NOT NULL
                    GROUP BY country_name, series_name
                ),
                ranked_indicators AS (
                    SELECT
                        country_name,
                        series_name,
                        total_debt,
                        ROW_NUMBER() OVER (
                            PARTITION BY country_name
                            ORDER BY total_debt DESC
                        ) AS indicator_rank
                    FROM indicator_totals
                )
                SELECT
                    country_name,
                    series_name AS dominant_indicator,
                    total_debt
                FROM ranked_indicators
                WHERE indicator_rank = 1
                ORDER BY country_name;
            """
            result_df = pd.read_sql(query, conn)
            st.subheader("Most Dominant Indicator per Country (2024)")
            st.dataframe(result_df, use_container_width=True)

        else:
            st.warning("We will add this SQL query next.")

        conn.close()

    except Exception as e:
        st.error(f"Database error: {e}")

