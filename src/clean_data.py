from pathlib import Path
import pandas as pd
import re


# ============================================================
# CONFIGURATION
# ============================================================

RAW_DIR = Path("data/raw")
CLEANED_DIR = Path("data/cleaned")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_column_name(column):
    """Convert column names into clean snake_case names."""

    column = str(column).strip().lower()

    # Replace spaces and special characters with _
    column = re.sub(r"[^a-z0-9]+", "_", column)

    # Remove leading/trailing underscores
    column = column.strip("_")

    return column


def clean_dataframe(df):
    """Perform generic cleaning on a dataframe."""

    # --------------------------------------------------------
    # 1. Clean column names
    # --------------------------------------------------------

    df.columns = [clean_column_name(col) for col in df.columns]

    # --------------------------------------------------------
    # 2. Remove completely empty rows
    # --------------------------------------------------------

    df = df.dropna(how="all")

    # --------------------------------------------------------
    # 3. Remove completely empty columns
    # --------------------------------------------------------

    df = df.dropna(axis=1, how="all")

    # --------------------------------------------------------
    # 4. Remove duplicate rows
    # --------------------------------------------------------

    before_duplicates = len(df)

    df = df.drop_duplicates()

    duplicates_removed = before_duplicates - len(df)

    # --------------------------------------------------------
    # 5. Clean text columns
    # --------------------------------------------------------

    text_columns = df.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in text_columns:

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

        # Convert empty strings to missing values
        df[column] = df[column].replace(
            r"^\s*$",
            pd.NA,
            regex=True
        )

    # --------------------------------------------------------
    # 6. Try to convert date columns
    # --------------------------------------------------------

    date_keywords = [
        "date",
        "dob",
        "birth",
        "created",
        "updated",
        "timestamp"
    ]

    for column in df.columns:

        if any(keyword in column.lower()
               for keyword in date_keywords):

            try:

                converted = pd.to_datetime(
                    df[column],
                    errors="coerce"
                )

                # Only replace if at least one valid
                # date was detected
                if converted.notna().sum() > 0:
                    df[column] = converted

            except Exception:
                pass

    # --------------------------------------------------------
    # 7. Try to convert numeric-looking columns
    # --------------------------------------------------------

    for column in df.columns:

        if df[column].dtype == "object":

            converted = pd.to_numeric(
                df[column],
                errors="coerce"
            )

            # If most non-empty values are numeric,
            # convert the column to numeric
            non_empty = df[column].notna().sum()

            if non_empty > 0:

                numeric_values = converted.notna().sum()

                if numeric_values / non_empty >= 0.8:

                    df[column] = converted

    return df, duplicates_removed


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print("=" * 70)
    print("AUTOMATED CSV DATA CLEANING PIPELINE")
    print("=" * 70)

    # Create folders if they don't exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # Find CSV files
    # --------------------------------------------------------

    csv_files = list(RAW_DIR.glob("*.csv"))

    if not csv_files:

        raise FileNotFoundError(
            "No CSV files found in data/raw/. "
            "Please add at least one CSV file."
        )

    print(f"\nFound {len(csv_files)} CSV file(s).")

    successful_files = 0
    failed_files = 0

    # --------------------------------------------------------
    # Process every CSV
    # --------------------------------------------------------

    for input_file in csv_files:

        print("\n" + "-" * 70)
        print(f"Processing: {input_file.name}")
        print("-" * 70)

        try:

            # Read CSV
            df = pd.read_csv(
                input_file,
                encoding="utf-8",
                encoding_errors="replace"
            )

            print(f"Original rows    : {len(df)}")
            print(f"Original columns : {len(df.columns)}")

            # Clean dataframe
            df, duplicates_removed = clean_dataframe(df)

            # Output filename
            output_file = CLEANED_DIR / (
                f"{input_file.stem}_cleaned.csv"
            )

            # Save cleaned CSV
            df.to_csv(
                output_file,
                index=False,
                encoding="utf-8"
            )

            print(f"Duplicates removed: {duplicates_removed}")
            print(f"Final rows        : {len(df)}")
            print(f"Final columns     : {len(df.columns)}")
            print(f"Output            : {output_file}")
            print("STATUS            : SUCCESS")

            successful_files += 1

        except Exception as error:

            failed_files += 1

            print(f"STATUS            : FAILED")
            print(f"ERROR             : {error}")

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)

    print(f"Successful files : {successful_files}")
    print(f"Failed files     : {failed_files}")

    if failed_files > 0:

        raise RuntimeError(
            "One or more CSV files failed during processing."
        )

    print("\nALL CSV FILES CLEANED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
