# Climate Analog Finder 🌍

A Streamlit application to find analog climate years based on ONI (ENSO), IOD, and PDO indices.

## Features
- **Bilingual Interface**: Switch between Japanese and English.
- **Analog Search**: Find years with similar climate patterns using historical data.
- **Interactive Visualization**: Zoomable time-series graphs powered by Plotly.
- **Adjustable Criteria**: Customize target month, indices, and PDO phase.

## How to Run Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the app:
   ```bash
   streamlit run app.py
   ```

## Data Sources
- **ONI**: NOAA PSL
- **IOD**: NOAA PSL (DMI)
- **PDO**: NOAA NCEI
