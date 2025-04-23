# etl.py  (drop-in replacement)

import pandas as pd, duckdb
from pathlib import Path

RAW = Path("data")
OUT_DUCK = "crm.duckdb"
OUT_PARQ = RAW / "pipeline.parquet"

# 1. load raw tables ----------------------------------------------------------
accounts   = pd.read_csv(RAW / "accounts.csv")
products   = pd.read_csv(RAW / "products.csv")
teams      = pd.read_csv(RAW / "sales_teams.csv")
pipeline   = pd.read_csv(RAW / "sales_pipeline.csv",
                         parse_dates=["engage_date", "close_date"])

# 2. feature engineering ------------------------------------------------------
pipeline = pipeline.assign(
    deal_age = (pipeline["close_date"] - pipeline["engage_date"]).dt.days,
    is_won   = (pipeline["deal_stage"].str.lower() == "won").astype(int),
    is_lost  = (pipeline["deal_stage"].str.lower() == "lost").astype(int),
)

# 3. join look-ups ------------------------------------------------------------
df = (pipeline
      .merge(accounts, on="account", how="left")
      .merge(teams,    on="sales_agent", how="left")
      .merge(products, on="product", how="left"))

# 4. save outputs -------------------------------------------------------------
df.to_parquet(OUT_PARQ, index=False)
duckdb.connect(OUT_DUCK).execute(
    "CREATE OR REPLACE TABLE pipeline AS SELECT * FROM df").close()

print(f"✅ ETL complete – {len(df):,} rows written to {OUT_PARQ} and {OUT_DUCK}")