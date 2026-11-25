import pandas as pd
import io
import re
from pydantic import BaseModel, field_validator
from typing import Optional


class CleaningReport(BaseModel):
    total_rows: int
    total_columns: int
    null_cells_fixed: int
    duplicate_rows_removed: int
    date_columns_fixed: list[str]
    type_issues_fixed: list[str]
    summary: str

    @field_validator("summary")
    @classmethod
    def summary_not_empty(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError("Summary cannot be empty")
        return v.strip()


def detect_date_columns(df: pd.DataFrame) -> list[str]:
    date_cols = []
    sample_patterns = [
        r"\d{4}-\d{2}-\d{2}",
        r"\d{2}/\d{2}/\d{4}",
        r"\d{2}-\d{2}-\d{4}",
    ]
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().head(20).astype(str)
            for pattern in sample_patterns:
                if sample.str.match(pattern).sum() > len(sample) * 0.5:
                    date_cols.append(col)
                    break
    return date_cols


def clean_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
    original_rows = len(df)
    null_before = df.isnull().sum().sum()
    type_issues = []

    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    dupes_before = len(df)
    df = df.drop_duplicates()
    dupes_removed = dupes_before - len(df)

    date_cols = detect_date_columns(df)
    formats_to_try = [
        "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y",
        "%d-%m-%Y", "%m-%d-%Y", "%d %b %Y", "%b %d %Y",
    ]
    for col in date_cols:
        try:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            mask = df[col].isna()
            if mask.any():
                for fmt in formats_to_try:
                    still_null = df[col].isna()
                    if not still_null.any():
                        break
                    parsed = pd.to_datetime(
                        df.loc[still_null, col].astype(str), format=fmt, errors="coerce"
                    )
                    df.loc[still_null, col] = parsed
        except Exception:
            pass

    for col in df.columns:
        if col in date_cols:
            continue
        if df[col].dtype == object:
            numeric_attempt = pd.to_numeric(df[col].str.replace(",", "").str.strip(), errors="coerce")
            if numeric_attempt.notna().sum() > len(df) * 0.7:
                df[col] = numeric_attempt
                type_issues.append(col)

    for col in df.columns:
        if df[col].dtype in ["float64", "int64"]:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
        elif df[col].dtype == object:
            mode_val = df[col].mode()
            df[col] = df[col].fillna(mode_val[0] if len(mode_val) > 0 else "Unknown")

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    null_after = df.isnull().sum().sum()
    null_fixed = int(null_before - null_after)

    report = CleaningReport(
        total_rows=len(df),
        total_columns=len(df.columns),
        null_cells_fixed=null_fixed,
        duplicate_rows_removed=dupes_removed,
        date_columns_fixed=date_cols,
        type_issues_fixed=type_issues,
        summary=(
            f"Processed {original_rows} rows across {len(df.columns)} columns. "
            f"Removed {dupes_removed} duplicate rows, fixed {null_fixed} null values, "
            f"standardized {len(date_cols)} date column(s), and corrected "
            f"{len(type_issues)} mixed-type column(s)."
        ),
    )
    return df, report


def load_file(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError("Only CSV and Excel files are supported.")


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def generate_pandas_script(df: pd.DataFrame, date_cols: list[str], type_cols: list[str]) -> str:
    date_block = ""
    if date_cols:
        cols_str = str(date_cols)
        date_block = f"""
# Fix date columns
date_columns = {cols_str}
for col in date_columns:
    df[col] = pd.to_datetime(df[col], infer_datetime_format=True, errors='coerce')
"""

    type_block = ""
    if type_cols:
        cols_str = str(type_cols)
        type_block = f"""
# Fix mixed-type columns that should be numeric
mixed_cols = {cols_str}
for col in mixed_cols:
    df[col] = pd.to_numeric(df[col].str.replace(',', '').str.strip(), errors='coerce')
"""

    script = f"""import pandas as pd

df = pd.read_csv("your_file.csv")

# Standardize column names
df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]

# Remove duplicate rows
df = df.drop_duplicates()
{date_block}{type_block}
# Fill nulls: median for numbers, mode for text
for col in df.columns:
    if df[col].dtype in ['float64', 'int64']:
        df[col] = df[col].fillna(df[col].median())
    elif df[col].dtype == object:
        mode_val = df[col].mode()
        df[col] = df[col].fillna(mode_val[0] if len(mode_val) > 0 else 'Unknown')

# Trim whitespace from text fields
for col in df.select_dtypes(include='object').columns:
    df[col] = df[col].str.strip()

df.to_csv("cleaned_output.csv", index=False)
print("Done. Cleaned file saved.")
"""
    return script
