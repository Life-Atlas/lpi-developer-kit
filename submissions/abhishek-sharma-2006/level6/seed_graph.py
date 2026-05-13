import pandas as pd

print("Reading CSV files...")

production_df = pd.read_csv("factory_production.csv")
capacity_df = pd.read_csv("factory_capacity.csv")
workers_df = pd.read_csv("factory_workers.csv")

print("Factory Production Data")
print(production_df.head())

print("\nFactory Capacity Data")
print(capacity_df.head())

print("\nFactory Workers Data")
print(workers_df.head())

print("\nCSV files loaded successfully!")