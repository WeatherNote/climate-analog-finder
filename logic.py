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

    # --- 4. Nino West (JMA) ---
    url_ninowest = "https://www.data.jma.go.jp/cpd/data/elnino/index/ninowidx.html"
    try:
        resp = requests.get(url_ninowest)
        # Simple parsing for <pre> block
        if "<pre>" in resp.text:
            pre_content = resp.text.split("<pre>")[1].split("</pre>")[0]
            lines = pre_content.strip().splitlines()
            for line in lines:
                parts = line.split()
                if not parts or not parts[0].isdigit(): continue
                year = int(parts[0])
                if year < start_year: continue
                # JMA table has Year then 12 months
                for m in range(1, 13):
                    if m <= len(parts) - 1:
                        try:
                            val = float(parts[m])
                            if val < 90: # 99.9 is missing
                                if (year, m) not in data_map: data_map[(year, m)] = {}
                                data_map[(year, m)]['NinoWest'] = val
                        except: pass
    except Exception as e:
        print(f"NinoWest Error: {e}")

    # --- 5. NAO (NOAA CPC) ---
    url_nao = "https://www.cpc.ncep.noaa.gov/products/precip/CWlink/pna/norm.nao.monthly.b5001.current.ascii.table"
    try:
        resp = requests.get(url_nao)
        lines = resp.text.splitlines()
        for line in lines:
            parts = line.split()
            if not parts or not parts[0].isdigit(): continue
            year = int(parts[0])
            if year < start_year: continue
            for m in range(1, 13):
                if m <= len(parts) - 1:
                    try:
                        val = float(parts[m])
                        if (year, m) not in data_map: data_map[(year, m)] = {}
                        data_map[(year, m)]['NAO'] = val
                    except: pass
    except Exception as e:
        print(f"NAO Error: {e}")

    # --- 6. PNA (NOAA CPC) ---
    url_pna = "https://www.cpc.ncep.noaa.gov/products/precip/CWlink/pna/norm.pna.monthly.b5001.current.ascii.table"
    try:
        resp = requests.get(url_pna)
        lines = resp.text.splitlines()
        for line in lines:
            parts = line.split()
            if not parts or not parts[0].isdigit(): continue
            year = int(parts[0])
            if year < start_year: continue
            for m in range(1, 13):
                if m <= len(parts) - 1:
                    try:
                        val = float(parts[m])
                        if (year, m) not in data_map: data_map[(year, m)] = {}
                        data_map[(year, m)]['PNA'] = val
                    except: pass
    except Exception as e:
        print(f"PNA Error: {e}")

    # --- 7. AO (NOAA CPC) ---
    url_ao = "https://www.cpc.ncep.noaa.gov/products/precip/CWlink/daily_ao_index/monthly.ao.index.b50.current.ascii.table"
    try:
        resp = requests.get(url_ao)
        lines = resp.text.splitlines()
        for line in lines:
            parts = line.split()
            if not parts or not parts[0].isdigit(): continue
            year = int(parts[0])
            if year < start_year: continue
            for m in range(1, 13):
                if m <= len(parts) - 1:
                    try:
                        val = float(parts[m])
                        if (year, m) not in data_map: data_map[(year, m)] = {}
                        data_map[(year, m)]['AO'] = val
                    except: pass
    except Exception as e:
        print(f"AO Error: {e}")

    # --- 8. QBO (NOAA CPC) ---
    # QBO 30hPa
    url_qbo30 = "https://www.cpc.ncep.noaa.gov/data/indices/qbo.u30.index"
    try:
        resp = requests.get(url_qbo30)
        lines = resp.text.splitlines()
        for line in lines:
            parts = line.split()
            if not parts or not parts[0].isdigit(): continue
            year = int(parts[0])
            if year < start_year: continue
            for m in range(1, 13):
                if m <= len(parts) - 1:
                    try:
                        val = float(parts[m])
                        if val > -900: # specific check for potential missing values
                             if (year, m) not in data_map: data_map[(year, m)] = {}
                             data_map[(year, m)]['QBO30'] = val
                    except: pass
    except Exception as e:
        print(f"QBO30 Error: {e}")

    # QBO 50hPa
    url_qbo50 = "https://www.cpc.ncep.noaa.gov/data/indices/qbo.u50.index"
    try:
        resp = requests.get(url_qbo50)
        lines = resp.text.splitlines()
        for line in lines:
            parts = line.split()
            if not parts or not parts[0].isdigit(): continue
            year = int(parts[0])
            if year < start_year: continue
            for m in range(1, 13):
                if m <= len(parts) - 1:
                    try:
                        val = float(parts[m])
                        if val > -900:
                            if (year, m) not in data_map: data_map[(year, m)] = {}
                            data_map[(year, m)]['QBO50'] = val
                    except: pass
    except Exception as e:
        print(f"QBO50 Error: {e}")

    # --- DataFrame化 ---
    rows = []
    for (y, m), vals in data_map.items():
        row = {'Year': y, 'Month': m}
        row.update(vals)
        rows.append(row)
    
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(['Year', 'Month'])
        cols = ['Year', 'Month', 'ONI', 'IOD', 'PDO', 'NinoWest', 'NAO', 'PNA', 'AO', 'QBO30', 'QBO50']
        existing_cols = [c for c in cols if c in df.columns]
        df = df[existing_cols]
        
    return df

def search_analog_years(
    df, 
    target_month, 
    targets, # dict { 'CurrentColName': val, ... }
    pdo_phase='neg', 
    pdo_threshold=0.5, 
    top_n=5
):
    """
    Searches for analog years based on the provided criteria.
    targets: dict of {column_name: target_value} to be used for distance calculation.
    """
    # 2. フィルタリング (月)
    candidates = df[df['Month'] == target_month].copy()
    
    # 3. フィルタリング & NaN除去
    # 必要なカラム(ターゲットになっているもの + PDO)が揃っている行だけ残す
    # PDO位相チェックが有効ならPDOも必須
    required_cols = list(targets.keys())
    if 'PDO' in df.columns:
        required_cols.append('PDO') # PDO is always used for filtering if present

    # Check if required columns exist in df
    valid_targets = {k: v for k, v in targets.items() if k in df.columns}
    if not valid_targets:
        return pd.DataFrame()
        
    candidates = candidates.dropna(subset=[c for c in required_cols if c in candidates.columns])
    
    if 'PDO' in candidates.columns:
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
    # distance = sqrt( sum( (val - target)^2 ) )
    
    # Calculate diffs for display and score
    sq_diff_sum = 0
    for col, target_val in valid_targets.items():
        candidates[f'{col}_Diff'] = candidates[col] - target_val
        sq_diff_sum += candidates[f'{col}_Diff'] ** 2
        
    candidates['Score'] = np.sqrt(sq_diff_sum)

    # 5. ソートして返す
    results = candidates.sort_values('Score').head(top_n)
    return results
