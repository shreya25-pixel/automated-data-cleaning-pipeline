from pathlib import Path
import pandas as pd
import re


# ============================================================
# CONFIGURATION
# ============================================================

RAW_DIR = Path("data/raw")
CLEANED_DIR = Path("data/cleaned")


# ============================================================
# 1. CLEAN COLUMN NAMES
# ============================================================

def clean_column_name(column):
    column = str(column).strip().lower()

    # Replace special characters/spaces with _
    column = re.sub(r"[^a-z0-9]+", "_", column)

    # Remove _ from beginning/end
    column = column.strip("_")

    # If column name becomes empty
    if not column:
        column = "unknown_column"

    return column


def make_unique_columns(columns):
    """
    Make duplicate column names unique.
    Example:
    Name, Name -> name, name_1
    """

    new_columns = []
    counts = {}

    for column in columns:

        if column not in counts:
            counts[column] = 0
            new_columns.append(column)

        else:
            counts[column] += 1
            new_columns.append(f"{column}_{counts[column]}")

    return new_columns


# ============================================================
# 2. CLEAN TEXT VALUES
# ============================================================

def clean_text_columns(df):

    text_columns = df.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in text_columns:

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

        # Remove multiple spaces
        df[column] = (
            df[column]
            .str.replace(r"\s+", " ", regex=True)
        )

        # Convert empty strings to NaN
        df[column] = df[column].replace(
            r"^\s*$",
            pd.NA,
            regex=True
        )

    return df


# ============================================================
# 3. CLEAN DATE COLUMNS
# ============================================================

def clean_date_columns(df):

    date_keywords = [
        "date",
        "dob",
        "birth",
        "created",
        "updated",
        "timestamp",
        "time"
    ]

    for column in df.columns:

        column_lower = column.lower()

        if any(keyword in column_lower for keyword in date_keywords):

            try:

                original_non_null = df[column].notna().sum()

                if original_non_null == 0:
                    continue

                converted = pd.to_datetime(
                    df[column],
                    errors="coerce"
                )

                valid_dates = converted.notna().sum()

                # Only convert when majority of existing values
                # can actually be interpreted as dates
                if valid_dates / original_non_null >= 0.5:

                    df[column] = converted

                    print(
                        f"Date converted      : {column}"
                    )

            except Exception as error:

                print(
                    f"Date conversion skipped: "
                    f"{column} -> {error}"
                )

    return df


# ============================================================
# 4. CLEAN NUMERIC COLUMNS
# ============================================================

def clean_numeric_columns(df):

    for column in df.columns:

        if df[column].dtype in ["object", "string"]:

            original_non_null = df[column].notna().sum()

            if original_non_null == 0:
                continue

            # Remove commas and currency symbols
            cleaned = (
                df[column]
                .astype("string")
                .str.replace(",", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.replace("₹", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.strip()
            )

            converted = pd.to_numeric(
                cleaned,
                errors="coerce"
            )

            numeric_values = converted.notna().sum()

            numeric_ratio = (
                numeric_values / original_non_null
            )

            # Convert only if >= 80% values are numeric
            if numeric_ratio >= 0.8:

                df[column] = converted

                print(
                    f"Numeric converted   : {column}"
                )

    return df


# ============================================================
# 5. STANDARDIZE COMMON TEXT VALUES
# ============================================================

def standardize_text_values(df):

    text_columns = df.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in text_columns:

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

        # Standardize common missing-value representations
        df[column] = df[column].replace(
            [
                "",
                "na",
                "n/a",
                "null",
                "none",
                "nan",
                "unknown",
                "-"
            ],
            pd.NA
        )

    return df


# ============================================================
# 6. MAIN CLEANING FUNCTION
# ============================================================

def clean_dataframe(df):

    original_rows = len(df)
    original_columns = len(df.columns)

    print("\nCleaning dataframe...")

    # --------------------------------------------------------
    # Clean column names
    # --------------------------------------------------------

    df.columns = [
        clean_column_name(column)
        for column in df.columns
    ]

    # Make duplicate column names unique
    df.columns = make_unique_columns(df.columns)

    # --------------------------------------------------------
    # Remove completely empty rows
    # --------------------------------------------------------

    before = len(df)

    df = df.dropna(how="all")

    empty_rows_removed = before - len(df)

    print(
        f"Empty rows removed  : {empty_rows_removed}"
    )

    # --------------------------------------------------------
    # Remove completely empty columns
    # --------------------------------------------------------

    before_columns = len(df.columns)

    df = df.dropna(
        axis=1,
        how="all"
    )

    empty_columns_removed = (
        before_columns - len(df.columns)
    )

    print(
        f"Empty columns removed: {empty_columns_removed}"
    )

    # --------------------------------------------------------
    # Remove duplicate rows
    # --------------------------------------------------------

    before_duplicates = len(df)

    df = df.drop_duplicates()

    duplicates_removed = (
        before_duplicates - len(df)
    )

    print(
        f"Duplicates removed   : {duplicates_removed}"
    )

    # --------------------------------------------------------
    # Clean text
    # --------------------------------------------------------

    df = clean_text_columns(df)

    # --------------------------------------------------------
    # Standardize missing values
    # --------------------------------------------------------

    df = standardize_text_values(df)

    # --------------------------------------------------------
    # Convert dates
    # --------------------------------------------------------

    df = clean_date_columns(df)

    # --------------------------------------------------------
    # Convert numeric columns
    # --------------------------------------------------------

    df = clean_numeric_columns(df)

    return (
        df,
        original_rows,
        original_columns,
        duplicates_removed
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print("=" * 70)
    print("AUTOMATED CSV DATA CLEANING PIPELINE")
    print("=" * 70)

    # Create directories
    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    CLEANED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Find CSV files
    # --------------------------------------------------------

    csv_files = list(
        RAW_DIR.glob("*.csv")
    )

    if not csv_files:

        raise FileNotFoundError(
            "No CSV files found in data/raw/"
        )

    print(
        f"\nFound {len(csv_files)} CSV file(s)."
    )

    successful_files = 0
    failed_files = 0

    # --------------------------------------------------------
    # Process every CSV
    # --------------------------------------------------------

    for input_file in csv_files:

        print("\n")
        print("=" * 70)
        print(
            f"PROCESSING: {input_file.name}"
        )
        print("=" * 70)

        try:

            # ------------------------------------------------
            # Read CSV
            # ------------------------------------------------

            df = pd.read_csv(
                input_file,
                encoding="utf-8",
                encoding_errors="replace"
            )

            print(
                f"Original rows       : {len(df)}"
            )

            print(
                f"Original columns    : {len(df.columns)}"
            )

            # ------------------------------------------------
            # Clean
            # ------------------------------------------------

            (
                df,
                original_rows,
                original_columns,
                duplicates_removed
            ) = clean_dataframe(df)

            # ------------------------------------------------
            # Output file
            # ------------------------------------------------

            output_file = (
                CLEANED_DIR /
                f"{input_file.stem}_cleaned.csv"
            )

            # ------------------------------------------------
            # Save
            # ------------------------------------------------

            df.to_csv(
                output_file,
                index=False,
                encoding="utf-8"
            )

            # ------------------------------------------------
            # Summary
            # ------------------------------------------------

            print("\n")
            print("-" * 70)
            print("CLEANING SUMMARY")
            print("-" * 70)

            print(
                f"Input file          : {input_file.name}"
            )

            print(
                f"Original rows       : {original_rows}"
            )

            print(
                f"Final rows          : {len(df)}"
            )

            print(
                f"Original columns    : {original_columns}"
            )

            print(
                f"Final columns       : {len(df.columns)}"
            )

            print(
                f"Duplicates removed  : {duplicates_removed}"
            )

            print(
                f"Output file         : {output_file}"
            )

            print(
                "STATUS              : SUCCESS"
            )

            successful_files += 1

        except Exception as error:

            failed_files += 1

            print(
                "\nSTATUS              : FAILED"
            )

            print(
                f"ERROR               : {error}"
            )

    # --------------------------------------------------------
    # Pipeline summary
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)

    print(
        f"Successful files    : {successful_files}"
    )

    print(
        f"Failed files        : {failed_files}"
    )

    if failed_files > 0:

        raise RuntimeError(
            "One or more CSV files failed."
        )

    print("\n")
    print(
        "ALL CSV FILES CLEANED SUCCESSFULLY!"
    )

    print("=" * 70)


# ============================================================
# RUN PIPELINE
# ============================================================

if __name__ == "__main__":
    main()
