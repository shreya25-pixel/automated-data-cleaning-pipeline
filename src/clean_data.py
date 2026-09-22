import pandas as pd

input_file = "data/raw/customers.csv"
output_file = "data/cleaned/customers_cleaned.csv"

df = pd.read_csv(input_file)

# Remove duplicate records
df = df.drop_duplicates()

# Remove unnecessary spaces
df.columns = df.columns.str.strip()

# Standardize text
df["customer_name"] = df["customer_name"].str.strip().str.title()

# Handle missing values
df["email"] = df["email"].fillna("unknown@email.com")

# Convert date
df["order_date"] = pd.to_datetime(
    df["order_date"],
    errors="coerce"
)

# Remove invalid records
df = df.dropna(subset=["customer_id"])

df.to_csv(output_file, index=False)

print("Data cleaning completed successfully!")