import pandas as pd


def clean_dataframe(df):
    cleaned = df.copy()
    cleaned = cleaned.drop_duplicates()
    cleaned.columns = [col.strip().lower().replace(' ', '_') for col in cleaned.columns]
    for col in cleaned.columns:
        if cleaned[col].dtype == 'object':
            cleaned[col] = cleaned[col].astype(str).str.strip()
    cleaned = cleaned.ffill().bfill()
    return cleaned
