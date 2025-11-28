import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logic

# --- Page Config ---
st.set_page_config(
    page_title="Climate Analog Finder",
    page_icon="🌍",
    layout="wide"
)

# --- Language Settings ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'ja'

def toggle_lang():
    st.session_state.lang = 'en' if st.session_state.lang == 'ja' else 'ja'

# Dictionary for UI text
TEXT = {
    'ja': {
        'title': "気候類似年検索ツール (Climate Analog Finder)",
        'sidebar_title': "検索条件設定",
        'target_month': "対象月",
        'target_oni': "予想 ONI (ENSO)",
        'target_iod': "予想 IOD (インド洋ダイポール)",
        'pdo_phase': "PDO (太平洋十年規模振動) 位相",
        'pdo_threshold': "PDO 閾値 (絶対値)",
        'num_results': "表示件数",
        'search_btn': "類似年を検索",
        'loading_data': "データを取得中...",
        'results_title': "検索結果 (類似度順)",
        'no_results': "条件に一致する年が見つかりませんでした。",
        'graph_title': "気候指数の時系列推移",
        'score': "スコア (小さいほど類似)",
        'year': "年",
        'diff': "差分",
        'pdo_options': {'neg': '負 (Negative)', 'pos': '正 (Positive)', '0': '中立 (Neutral)', 'any': '指定なし (Any)'},
        'lang_btn': "English",
        'explanation': """
        **使い方**:
        1. 左側のサイドバーで対象月と予想される気候指数(ONI, IOD)を入力します。
        2. PDOの位相条件を選択します。
        3. 「類似年を検索」ボタンを押すと、過去のデータから条件に近い年が表示されます。
        """,
        'ref_title': "参考データ (最新予測)",
        'iod_link': "IOD予測 (Copernicus)",
        'enso_link': "ENSO予測 (IRI)",
        'noaa_link': "NOAA PSL Composites (詳細解析)"
    },
    'en': {
        'title': "Climate Analog Finder",
        'sidebar_title': "Search Settings",
        'target_month': "Target Month",
        'target_oni': "Target ONI (ENSO)",
        'target_iod': "Target IOD",
        'pdo_phase': "PDO Phase",
        'pdo_threshold': "PDO Threshold (Abs)",
        'num_results': "Number of Results",
        'search_btn': "Search Analog Years",
        'loading_data': "Loading Data...",
        'results_title': "Search Results (Ordered by Similarity)",
        'no_results': "No matching years found.",
        'graph_title': "Time Series of Climate Indices",
        'score': "Score (Lower is better)",
        'year': "Year",
        'diff': "Diff",
        'pdo_options': {'neg': 'Negative', 'pos': 'Positive', '0': 'Neutral', 'any': 'Any'},
        'lang_btn': "日本語",
        'explanation': """
        **How to use**:
        1. Set the target month and expected indices (ONI, IOD) in the sidebar.
        2. Select the PDO phase condition.
        3. Click "Search Analog Years" to find historical years with similar patterns.
        """,
        'ref_title': "Reference Data (Forecasts)",
        'iod_link': "IOD Forecast (Copernicus)",
        'enso_link': "ENSO Forecast (IRI)",
        'noaa_link': "NOAA PSL Composites"
    }
}

t = TEXT[st.session_state.lang]

# --- Sidebar ---
with st.sidebar:
    st.button(t['lang_btn'], on_click=toggle_lang)
    
    # --- Reference Section ---
    st.header(t['ref_title'])
    st.markdown(f"""
    - [{t['iod_link']}](https://climate.copernicus.eu/charts/packages/c3s_seasonal/products/c3s_seasonal_plume_mm?area=iod&base_time=202511010000&type=plume)
    - [{t['enso_link']}](https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/?enso_tab=enso-sst_table)
    """)
    st.divider()

    st.header(t['sidebar_title'])
    
    target_month = st.selectbox(t['target_month'], range(1, 13), index=0)
    
    target_oni = st.number_input(t['target_oni'], value=-0.5, step=0.1)
    target_iod = st.number_input(t['target_iod'], value=-0.4, step=0.1)
    
    pdo_options_map = t['pdo_options']
    # Reverse map for logic
    pdo_key_map = {v: k for k, v in pdo_options_map.items()}
    
    selected_pdo_display = st.selectbox(t['pdo_phase'], list(pdo_options_map.values()), index=0)
    pdo_phase = pdo_key_map[selected_pdo_display]
    
    pdo_threshold = st.slider(t['pdo_threshold'], 0.0, 2.0, 0.5, 0.1)
    
    top_n = st.slider(t['num_results'], 1, 20, 10)
    
    run_search = st.button(t['search_btn'], type="primary")

# --- Main Content ---
st.title(t['title'])
st.markdown(t['explanation'])

# Load Data
with st.spinner(t['loading_data']):
    df = logic.get_climate_indices()

if df.empty:
    st.error("Failed to load data.")
    st.stop()

# Create Date column for better plotting (Global)
df['Day'] = 1
df['Date'] = pd.to_datetime(df[['Year', 'Month', 'Day']])

# Search Logic
if run_search:
    results = logic.search_analog_years(
        df, 
        target_month, 
        target_oni, 
        target_iod, 
        pdo_phase, 
        pdo_threshold, 
        top_n=top_n
    )
    
    if results.empty:
        st.warning(t['no_results'])
    else:
        st.subheader(t['results_title'])
        
        # Display Results Table
        display_cols = ['Year', 'Score', 'ONI', 'IOD', 'PDO', 'ONI_Diff', 'IOD_Diff']
        st.dataframe(
            results[display_cols].style.format({
                'Score': '{:.3f}',
                'ONI': '{:.2f}',
                'IOD': '{:.2f}',
                'PDO': '{:.2f}',
                'ONI_Diff': '{:+.2f}',
                'IOD_Diff': '{:+.2f}'
            }),
            use_container_width=True
        )
        
        # --- Visualization ---
        st.subheader(t['graph_title'])
        
        # Create interactive plot
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                            subplot_titles=("ONI (ENSO)", "IOD", "PDO"))
        
        # Full Time Series (Background)
        fig.add_trace(go.Scatter(x=df['Date'], y=df['ONI'], 
                                 mode='lines', name='ONI', line=dict(color='gray', width=1), opacity=0.3), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Date'], y=df['IOD'], 
                                 mode='lines', name='IOD', line=dict(color='gray', width=1), opacity=0.3), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['Date'], y=df['PDO'], 
                                 mode='lines', name='PDO', line=dict(color='gray', width=1), opacity=0.3), row=3, col=1)
        
        # Highlight Analog Years
        analog_years = results['Year'].tolist()
        # Extended color palette for up to 20 lines
        import plotly.colors
        colors = plotly.colors.qualitative.Plotly + plotly.colors.qualitative.D3
        
        for i, year in enumerate(analog_years):
            # Get data for that specific year
            year_data = df[df['Year'] == year]
            color = colors[i % len(colors)]
            label = f"{year} (Rank {i+1})"
            
            fig.add_trace(go.Scatter(x=year_data['Date'], y=year_data['ONI'],
                                     mode='lines+markers', name=f"ONI {label}", line=dict(color=color, width=2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=year_data['Date'], y=year_data['IOD'],
                                     mode='lines+markers', name=f"IOD {label}", line=dict(color=color, width=2)), row=2, col=1)
            fig.add_trace(go.Scatter(x=year_data['Date'], y=year_data['PDO'],
                                     mode='lines+markers', name=f"PDO {label}", line=dict(color=color, width=2)), row=3, col=1)

        fig.update_layout(
            height=800, 
            showlegend=True,
            hovermode="x unified"
        )
        fig.update_xaxes(
            tickformat="%Y-%m",
            hoverformat="%Y-%m"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # --- NOAA Link ---
        st.markdown(f"🔗 [{t['noaa_link']}](https://psl.noaa.gov/cgi-bin/data/composites/printpage.pl)")

else:
    # Default view: Just show the graphs of recent data or all data
    st.info("👈 " + ("左のサイドバーから条件を設定して検索してください。" if st.session_state.lang == 'ja' else "Configure settings in the sidebar to search."))
    
    # Show simple preview graph
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, subplot_titles=("ONI", "IOD", "PDO"))
    recent_df = df[df['Year'] >= 2000]
    
    fig.add_trace(go.Scatter(x=recent_df['Date'], y=recent_df['ONI'], name='ONI'), row=1, col=1)
    fig.add_trace(go.Scatter(x=recent_df['Date'], y=recent_df['IOD'], name='IOD'), row=2, col=1)
    fig.add_trace(go.Scatter(x=recent_df['Date'], y=recent_df['PDO'], name='PDO'), row=3, col=1)
    
    fig.update_layout(
        height=600, 
        title_text="Recent Climate Indices (Since 2000)",
        hovermode="x unified"
    )
    fig.update_xaxes(
        tickformat="%Y-%m",
        hoverformat="%Y-%m"
    )
    st.plotly_chart(fig, use_container_width=True)

