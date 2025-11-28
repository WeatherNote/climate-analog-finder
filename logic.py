import pandas as pd
import requests
import numpy as np
import streamlit as st

@st.cache_data(ttl=3600*24) # Cache data for 24 hours
def get_climate_indices(start_year=1950):
    """
    Fetches ONI, IOD, and PDO data from NOAA/PSL text sources.
    Returns a merged DataFrame.
    """
    # 全データを統合する辞書: (Year, Month) -> {ONI, IOD, PDO}
    data_map = {}

    # --- 1. ENSO (ONI) - NOAA PSL Text Data ---
    url_oni = "https://psl.noaa.gov/data/correlation/oni.data"
    try:
        resp = requests.get(url_oni)
        lines = resp.text.splitlines()
        for line in lines:
            parts = line.split()
            if parts and parts[0].isdigit() and len(parts) >= 13:
                year = int(parts[0])
                if year < start_year: continue
                for m in range(1, 13):
                    try:
                        val = float(parts[m])
                        if val > -90:
                            if (year, m) not in data_map: data_map[(year, m)] = {}
                            data_map[(year, m)]['ONI'] = val
                    except: pass
    except Exception as e:
        print(f"ONI Error: {e}")

    # --- 2. IOD (DMI) - NOAA PSL Text Data ---
    url_iod = "https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data"
    try:
        resp = requests.get(url_iod)
        lines = resp.text.splitlines()
        for line in lines:
            parts = line.split()
            if parts and parts[0].isdigit() and len(parts) >= 13:
                year = int(parts[0])
                if year < start_year: continue
                for m in range(1, 13):
                    try:
                        val = float(parts[m])
                        if val > -90:
                            if (year, m) not in data_map: data_map[(year, m)] = {}
                            data_map[(year, m)]['IOD'] = val
                    except: pass
    except Exception as e:
        print(f"IOD Error: {e}")

    # --- 3. PDO - NOAA NCEI Text Data ---
    url_pdo = "https://www.ncei.noaa.gov/pub/data/cmb/ersst/v5/index/ersst.v5.pdo.dat"
    try:
        resp = requests.get(url_pdo)
        lines = resp.text.splitlines()
        for line in lines:
            if "Year" in line: continue
            parts = line.split()
            if len(parts) >= 13:
                year = int(parts[0])
                if year < start_year: continue
                for m in range(1, 13):
                    try:
                        val = float(parts[m])
                        if val < 90:
                            if (year, m) not in data_map: data_map[(year, m)] = {}
                            data_map[(year, m)]['PDO'] = val
                    except: pass
    except Exception as e:
        print(f"PDO Error: {e}")

    # --- DataFrame化 ---
    rows = []
    for (y, m), vals in data_map.items():
        row = {'Year': y, 'Month': m}
        row.update(vals)
        rows.append(row)
    
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(['Year', 'Month'])
        cols = ['Year', 'Month', 'ONI', 'IOD', 'PDO']
        existing_cols = [c for c in cols if c in df.columns]
        df = df[existing_cols]
        
    return df

def search_analog_years(
    df, 
    target_month, 
    target_oni, 
    target_iod, 
    pdo_phase='neg', 
    pdo_threshold=0.5, 
    top_n=5
):
    """
    Searches for analog years based on the provided criteria.
    """
    # カラム特定
    oni_col = next((c for c in df.columns if 'ONI' in c or 'NINO' in c), None)
    iod_col = next((c for c in df.columns if 'IOD' in c or 'DMI' in c), None)
    
    if not oni_col or not iod_col:
        return pd.DataFrame()

    # 2. フィルタリング (月)
    candidates = df[df['Month'] == target_month].copy()
    
    # 3. フィルタリング (PDO位相)
    candidates = candidates.dropna(subset=['PDO', oni_col, iod_col])
    
    if pdo_phase == 'pos':
        candidates = candidates[candidates['PDO'] >= pdo_threshold]
    elif pdo_phase == 'neg':
        candidates = candidates[candidates['PDO'] <= -pdo_threshold]
    elif pdo_phase == '0':
        candidates = candidates[
            (candidates['PDO'] > -pdo_threshold) & 
            (candidates['PDO'] < pdo_threshold)
        ]
    
    if candidates.empty:
        return pd.DataFrame()

    # 4. 類似度スコア計算 (ユークリッド距離)
    candidates['ONI_Diff'] = candidates[oni_col] - target_oni
    candidates['IOD_Diff'] = candidates[iod_col] - target_iod
    candidates['Score'] = np.sqrt(candidates['ONI_Diff']**2 + candidates['IOD_Diff']**2)

    # 5. ソートして返す
    results = candidates.sort_values('Score').head(top_n)
    return results
