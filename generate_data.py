import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

routes = {
    ("Mumbai", "Delhi"): 8200,
    ("Mumbai", "Goa"): 4800,
    ("Mumbai", "Srinagar"): 14500,
    ("Delhi", "Goa"): 11200,
    ("Delhi", "Mumbai"): 9200,
    ("Srinagar", "Mumbai"): 15800,
    ("Goa", "Mumbai"): 5800,
}

dates = pd.date_range(
    start="2022-01-01",
    end="2026-12-01",
    freq="MS"
)

rows = []

for (origin, destination), base_price in routes.items():

    for date in dates:

        month = date.month
        year_index = date.year - 2022

        # General yearly price increase
        trend = year_index * 250

        # Monthly seasonal effect
        seasonal_effect = {
            1: 0.90,
            2: 0.85,
            3: 0.95,
            4: 1.00,
            5: 1.05,
            6: 1.10,
            7: 1.08,
            8: 1.02,
            9: 0.90,
            10: 0.98,
            11: 1.08,
            12: 1.25,
        }[month]

        # Random variation
        noise = np.random.normal(0, 250)

        price = (
            (base_price + trend)
            * seasonal_effect
            + noise
        )

        price = max(2500, round(price / 50) * 50)

        rows.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Origin": origin,
            "Destination": destination,
            "Average_Price": int(price)
        })

df = pd.DataFrame(rows)

output_dir = Path("data")
output_dir.mkdir(exist_ok=True)

output_file = output_dir / "sample_flight_prices.csv"

df.to_csv(output_file, index=False)

print(f"Dataset created: {output_file}")
print(f"Rows: {len(df)}")
print(df.head())