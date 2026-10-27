# International Debt Analysis System

## Project Overview
The International Debt Analysis System analyzes international debt data using Python, MySQL, Streamlit, and data visualization tools. It helps users explore debt trends, compare countries, and understand debt indicators through interactive dashboards and SQL queries.

## Objectives
- Clean and preprocess international debt data.
- Store and analyze data using MySQL.
- Perform data analysis using SQL queries.
- Visualize debt patterns and trends.
- Identify countries with the highest and lowest external debt.

## Technologies Used
- **Python** — data cleaning and preprocessing
- **Pandas** — data manipulation and analysis
- **MySQL** — database storage and SQL analysis
- **Streamlit** — interactive web application
- **Plotly** — data visualization

## Project Features
- Data cleaning and handling of missing values and duplicates
- Interactive dashboard with four visualization sections
- Country-wise external debt analysis
- Top 10 and bottom 10 country comparisons
- Debt indicator distribution analysis
- Historical debt trend visualization
- 30 SQL questions with results displayed in Streamlit

## Project Files
- `main.py` — data cleaning and CSV preparation code
- `mainfinal.py` — Streamlit dashboard and SQL questions
- `create_indicator_summary.py` — indicator summary preparation
- `IDS_ALLCountries_Data.csv` — original debt dataset
- `IDS_CountryMetaData.csv` — country metadata
- Dashboard CSV files — prepared data used by the visualizations

## How to Run the Project

1. Install Python and MySQL.
2. Install the required packages:

   ```bash
   pip install pandas streamlit plotly mysql-connector-python
   ```

3. Configure the MySQL database and set the `MYSQL_PASSWORD` environment variable.
4. Ensure the required CSV files are available in the project folder.
5. Start the Streamlit application:

   ```bash
   streamlit run mainfinal.py
   ```

## Database Requirements
The SQL section connects to the MySQL database `international_debt_db`. The database and required tables must be created and populated before running the SQL queries.

## Expected Outcome
An interactive application for exploring international debt data, analyzing country-level debt patterns, and answering SQL-based analytical questions.

## Author
International Debt Analysis Project
