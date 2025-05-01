import requests
import pandas as pd
import os
import settings
URL = settings.URL


def fetch_data(url):
    """Fetch data from the given URL and return it as a DataFrame."""
    response = requests.get(url)
    print(f"Fetching data from {url}...")
    if response.status_code == 200:
        print("Data fetched successfully.")
        data = response.content
        df = pd.read_xml(data)
        return df
    else:
        raise Exception(f"Failed to fetch data: {response.status_code}")


def filter_data(df):
    filtered = df.copy()
    filtered = filtered.loc[(filtered['postnr'] > settings.FILTER['lower_limit'])
                            & (filtered['postnr'] < settings.FILTER['upper_limit'])]
    filtered = filtered.loc[filtered['seneste_kontrol']
                            == settings.CONTROL_STATUS]

    return filtered.sort_values(by='seneste_kontrol_dato', ascending=True)


def check_for_hits(df: pd.DataFrame):
    """
    Compare the freshly scraped `df` with the stored CSV and return
    (new_hits, removed).  The CSV is overwritten **only** when a change
    is detected.
    """
    # 1. load previous snapshot (same column order & dtypes if possible)
    if os.path.exists(settings.PREVIOUS_CSV):
        old = pd.read_csv(settings.PREVIOUS_CSV)
    else:
        old = pd.DataFrame(columns=df.columns)   # empty but same cols

    # 2. outer merge to detect diffs row-by-row
    combo = (
        df.merge(
            old,
            how="outer",
            indicator=True,          # adds the _merge column
            copy=False,
        )
    )

    new_hits = combo.loc[combo["_merge"] == "left_only", df.columns]
    removed = combo.loc[combo["_merge"] == "right_only", df.columns]

    # 3. persist only when something changed
    if not new_hits.empty or not removed.empty:
        df.to_csv(settings.PREVIOUS_CSV, index=False)

    return new_hits, removed


df = fetch_data(URL)
df = filter_data(df)
new_hits, removed = check_for_hits(df)
print(f"New hits: {len(new_hits)}")
print(f"Removed: {len(removed)}")
