import pandas as pd
import ijson
from tqdm import tqdm
from config import DATA_PATH
from datetime import datetime
import warnings

COLUMN_ALIASES = {
    'DayName': 'Day',
    'CallHour': 'Hour',
    'ProfessionType': 'ProfessionType',
}

def load_data(path):
    """
    Load data from Excel or JSON file into a DataFrame.
    """
    if path.endswith('.xlsx'):
        df = pd.read_excel(path)
    else:
        df = pd.read_json(path)
    df = preprocess(df)
    return df

def preprocess(df):
    """
    Clean and preprocess the DataFrame, handling missing columns gracefully.
    """
    # Rename columns
    for old, new in COLUMN_ALIASES.items():
        if old in df.columns and new not in df.columns:
            df.rename(columns={old: new}, inplace=True)

    # Handle DOB and Age
    if 'DOB' in df.columns:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df['DOB'] = pd.to_datetime(df['DOB'], format='%d-%m-%Y', errors='coerce')
        today = pd.Timestamp(datetime.today().date())
        df['Age'] = df['DOB'].apply(lambda dob: (today - dob).days // 365 if pd.notnull(dob) else None)
        def age_group(age):
            if pd.isnull(age): return None
            # Start at 18: 18-22, 23-27, ...
            if age < 18:
                return '<18'
            lower = 18 + 5 * ((int(age) - 18) // 5)
            upper = lower + 4
            return f"{lower}-{upper}"
        df['AgeGroup'] = df['Age'].apply(age_group)
    else:
        df['Age'] = None
        df['AgeGroup'] = None

    # Numeric conversions
    for col in ['Talktime', 'Income']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Income group with new brackets
    def income_group(income):
        if pd.isnull(income):
            return ''
        if income < 500000:
            return '0-5L'
        elif income < 1000000:
            return '5-10L'
        elif income < 1500000:
            return '10-15L'
        elif income < 2000000:
            return '15-20L'
        elif income < 3000000:
            return '20-30L'
        elif income < 5000000:
            return '30-50L'
        elif income < 10000000:
            return '50L-1Cr'
        else:
            return '1Cr above'
    if 'Income' in df.columns:
        df['IncomeGroup'] = df['Income'].apply(income_group)
    else:
        df['IncomeGroup'] = ''

    # PickupRate
    if 'AnsweredCalls' in df.columns and 'TotalCalls' in df.columns:
        df['PickupRate'] = (df['AnsweredCalls'] / df['TotalCalls']) * 100
    else:
        df['PickupRate'] = None

    # CallDuration
    if 'Talktime' in df.columns:
        df['CallDuration'] = df['Talktime']
    else:
        df['CallDuration'] = None

    # Drop rows with missing critical fields
    required = ['AgeGroup', 'Gender', 'Income', 'ProfessionType', 'CityId', 'Talktime', 'Brandname', 'Day', 'Hour', 'PickupRate', 'CallDuration', 'IncomeGroup']
    missing = [col for col in required if col not in df.columns]
    if missing:
        for col in missing:
            df[col] = None
    df = df.dropna(subset=required)
    return df

def stream_json_chunks(path, chunk_size=1250000, total_rows=None):
    """
    Stream a large JSON file in chunks, yielding preprocessed DataFrames.
    """
    with open(path, 'rb') as f:
        objects = ijson.items(f, 'item')
        chunk = []
        pbar = tqdm(total=total_rows, desc='Loading JSON', unit='rows') if total_rows else None
        for idx, obj in enumerate(objects, 1):
            chunk.append(obj)
            if pbar:
                pbar.update(1)
            if len(chunk) == chunk_size:
                df = pd.DataFrame(chunk)
                df = preprocess(df)
                yield df
                chunk.clear()
        if chunk:
            df = pd.DataFrame(chunk)
            df = preprocess(df)
            yield df
        if pbar:
            pbar.close()
            