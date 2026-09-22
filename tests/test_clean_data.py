from pathlib import Path
import pandas as pd


RAW_DIR = Path("data/raw")
CLEANED_DIR = Path("data/cleaned")


def test_raw_folder_exists():
    """Check that the raw data folder exists."""
    assert RAW_DIR.exists(), "data/raw folder does not exist"


def test_csv_files_exist():
    """Check that at least one CSV file exists."""
    csv_files = list(RAW_DIR.glob("*.csv"))

    assert len(csv_files) > 0, (
        "No CSV files found in data/raw/"
    )


def test_cleaned_folder_exists():
    """Check that the cleaned folder exists."""
    assert CLEANED_DIR.exists(), (
        "data/cleaned folder does not exist"
    )


def test_cleaned_files_exist():
    """Check that cleaned CSV files were created."""

    csv_files = list(RAW_DIR.glob("*.csv"))

    for raw_file in csv_files:

        cleaned_file = CLEANED_DIR / (
            f"{raw_file.stem}_cleaned.csv"
        )

        assert cleaned_file.exists(), (
            f"Cleaned file missing: {cleaned_file}"
        )


def test_cleaned_files_are_readable():
    """Check that generated CSV files can be read."""

    cleaned_files = list(
        CLEANED_DIR.glob("*_cleaned.csv")
    )

    for file in cleaned_files:

        df = pd.read_csv(file)

        assert len(df.columns) > 0, (
            f"{file.name} has no columns"
        )


def test_no_duplicate_rows():
    """Check that cleaned files contain no duplicates."""

    cleaned_files = list(
        CLEANED_DIR.glob("*_cleaned.csv")
    )

    for file in cleaned_files:

        df = pd.read_csv(file)

        assert not df.duplicated().any(), (
            f"Duplicate rows found in {file.name}"
        )


def test_column_names_are_clean():
    """Check that column names contain no leading/trailing spaces."""

    cleaned_files = list(
        CLEANED_DIR.glob("*_cleaned.csv")
    )

    for file in cleaned_files:

        df = pd.read_csv(file)

        for column in df.columns:

            assert column == column.strip(), (
                f"Column '{column}' contains extra spaces"
            )
