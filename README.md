# GNGD Daily Runbook

Automated data pipeline for collecting **daily** German natural gas data (imports, exports, production) from the Federal Network Agency (Bundesnetzagentur).

## Data Sources

| Source | URL | Columns |
|--------|-----|---------|
| Gas Imports | [Gasimporte](https://www.bundesnetzagentur.de/DE/Gasversorgung/aktuelle_gasversorgung/_svg/Gasimporte/Gasimporte.html) | 11 countries (CZE, NLD, BEL, POL, NOR, DNK, AUT, CHE, RUS, FRA, DEU) |
| Gas Exports | [Gasexporte](https://www.bundesnetzagentur.de/DE/Gasversorgung/aktuelle_gasversorgung/_svg/Gasexporte/Gasexporte.html) | 9 countries (CZE, NLD, BEL, POL, DNK, AUT, CHE, FRA, DEU) |
| Gas Production | [Gasfoerderung](https://www.bundesnetzagentur.de/DE/Gasversorgung/aktuelle_gasversorgung/_svg/Gasfoerderung/Gasfoerderung.html) | 1 column (GASPROD) |

**Total: 21 timeseries columns** | Unit: GWh per day | Frequency: Daily

## Pipeline

```
python orchestrator.py
```

4-step pipeline:
1. **Fetch** - Selenium browser navigates to 3 URLs, clicks "Daten als CSV-Datei herunterladen" to download CSVs
2. **Parse** - Semicolon-separated CSVs parsed, German column names mapped to codes (LNG column dropped)
3. **Update Master** - New dates appended to master CSV (forward-only, never overwrites existing data)
4. **Generate Output** - XLS DATA, XLS META, and ZIP files created

## Project Structure

```
GNGD_Runbook/
  config.py           - Configuration (URLs, column mappings, META rows, paths)
  logger_setup.py     - Dual file + console logging
  scraper.py          - Selenium-based CSV downloader
  parser.py           - CSV parsing, column mapping, master update
  file_generator.py   - XLS DATA/META/ZIP generation
  orchestrator.py     - Main entry point (4-step pipeline)
  requirements.txt    - Python dependencies
  Master_Data/
    Master_GNGD_DATA_DAILY.csv   - Cumulative master (2-row header + data)
  output/
    {timestamp}/       - Timestamped output per run
    latest/            - Always contains most recent output
  downloads/
    {timestamp}/       - Raw downloaded CSVs per run
  logs/
    {timestamp}/       - Log files per run
```

## Output Files

| File | Description |
|------|-------------|
| `GNGD_DATA_DAILY_{date}.xls` | Data file (2-row header + all data rows, 22 columns) |
| `GNGD_META_DAILY_{date}.xls` | Metadata file (17 columns, 21 timeseries rows) |
| `GNGD_DAILY_{date}.zip` | ZIP containing both XLS files |

## Requirements

```
pip install -r requirements.txt
```

- Python 3.8+
- Google Chrome (for Selenium)
- `undetected-chromedriver`, `selenium`, `xlwt`, `requests`, `beautifulsoup4`

## Master Update Rules

- Only dates **after** the last date in the master are added
- Existing data is never modified or overwritten
- The production CSV goes back to 2022 but only recent dates matching imports/exports are relevant
