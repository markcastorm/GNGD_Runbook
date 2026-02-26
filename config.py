# config.py
# GNGD - German Natural Gas Data (Daily) Configuration

import os
from datetime import datetime

# =============================================================================
# DATA SOURCE CONFIGURATION
# =============================================================================

PROVIDER_NAME = 'Federal Network Agency (Bundesnetzagentur)'
DATASET_NAME = 'GNGD'

# URLs for the 3 daily data sources
SOURCE_URLS = {
    'imports': 'https://www.bundesnetzagentur.de/DE/Gasversorgung/aktuelle_gasversorgung/_svg/Gasimporte/Gasimporte.html',
    'exports': 'https://www.bundesnetzagentur.de/DE/Gasversorgung/aktuelle_gasversorgung/_svg/Gasexporte/Gasexporte.html',
    'production': 'https://www.bundesnetzagentur.de/DE/Gasversorgung/aktuelle_gasversorgung/_svg/Gasfoerderung/Gasfoerderung.html',
}

# The text of the CSV download link to find on each page
CSV_DOWNLOAD_LINK_TEXT = 'Daten als CSV-Datei herunterladen'

# =============================================================================
# COLUMN MAPPING: German CSV headers -> Master column codes
# =============================================================================
# The downloaded CSVs use German country names as headers.
# We map each German name to its master column code.
# Order here defines the MASTER column order.
# Columns not in these mappings (e.g. LNG) are dropped.

IMPORT_COLUMN_MAP = {
    'Tschechien': 'GNGD.GASIMP.CZE.D',
    'Niederlande': 'GNGD.GASIMP.NLD.D',
    'Belgien': 'GNGD.GASIMP.BEL.D',
    'Polen': 'GNGD.GASIMP.POL.D',
    'Norwegen': 'GNGD.GASIMP.NOR.D',
    'Dänemark': 'GNGD.GASIMP.DNK.D',
    'Österreich': 'GNGD.GASIMP.AUT.D',
    'Schweiz': 'GNGD.GASIMP.CHE.D',
    'Russland': 'GNGD.GASIMP.RUS.D',
    'Frankreich': 'GNGD.GASIMP.FRA.D',
    'Deutschland Import': 'GNGD.GASIMP.DEU.D',
}

EXPORT_COLUMN_MAP = {
    'Tschechien': 'GNGD.GASEXP.CZE.D',
    'Niederlande': 'GNGD.GASEXP.NLD.D',
    'Belgien': 'GNGD.GASEXP.BEL.D',
    'Polen': 'GNGD.GASEXP.POL.D',
    'Dänemark': 'GNGD.GASEXP.DNK.D',
    'Österreich': 'GNGD.GASEXP.AUT.D',
    'Schweiz': 'GNGD.GASEXP.CHE.D',
    'Frankreich': 'GNGD.GASEXP.FRA.D',
    'Deutschland Exporte': 'GNGD.GASEXP.DEU.D',
}

PRODUCTION_COLUMN_MAP = {
    'Produktion': 'GNGD.GASPROD.D',
}

# Combined mapping: source_key -> column_map
SOURCE_COLUMN_MAPS = {
    'imports': IMPORT_COLUMN_MAP,
    'exports': EXPORT_COLUMN_MAP,
    'production': PRODUCTION_COLUMN_MAP,
}

# Master column order (must match existing master CSV exactly)
OUTPUT_COLUMN_CODES = [
    # Imports (11)
    'GNGD.GASIMP.CZE.D',
    'GNGD.GASIMP.NLD.D',
    'GNGD.GASIMP.BEL.D',
    'GNGD.GASIMP.POL.D',
    'GNGD.GASIMP.NOR.D',
    'GNGD.GASIMP.DNK.D',
    'GNGD.GASIMP.AUT.D',
    'GNGD.GASIMP.CHE.D',
    'GNGD.GASIMP.RUS.D',
    'GNGD.GASIMP.FRA.D',
    'GNGD.GASIMP.DEU.D',
    # Exports (9)
    'GNGD.GASEXP.CZE.D',
    'GNGD.GASEXP.NLD.D',
    'GNGD.GASEXP.BEL.D',
    'GNGD.GASEXP.POL.D',
    'GNGD.GASEXP.DNK.D',
    'GNGD.GASEXP.AUT.D',
    'GNGD.GASEXP.CHE.D',
    'GNGD.GASEXP.FRA.D',
    'GNGD.GASEXP.DEU.D',
    # Production (1)
    'GNGD.GASPROD.D',
]

OUTPUT_COLUMN_DESCRIPTIONS = [
    # Imports
    'Gas imports, Czech',
    'Gas imports, Netherlands',
    'Gas imports, Belgium',
    'Gas imports, Poland',
    'Gas imports, Norway',
    'Gas imports, Denmark',
    'Gas imports, Austria',
    'Gas imports, Switzerland',
    'Gas imports, Russia',
    'Gas imports, France',
    'Gas imports, Germany',
    # Exports
    'Gas exports, Czech',
    'Gas exports, Netherlands',
    'Gas exports, Belgium',
    'Gas exports, Poland',
    'Gas exports, Denmark',
    'Gas exports, Austria',
    'Gas exports, Switzerland',
    'Gas exports, France',
    'Gas exports, Germany',
    # Production
    'Gas production',
]

# =============================================================================
# DATE FORMATS
# =============================================================================

# Source date format in downloaded CSVs (DD.MM.YYYY)
SOURCE_DATE_FORMAT = '%d.%m.%Y'

# Output date format for master CSV and XLS
OUTPUT_DATE_FORMAT = '%Y-%m-%d'

# =============================================================================
# TIMESTAMPED FOLDERS CONFIGURATION
# =============================================================================

RUN_TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
RUN_DATE = datetime.now().strftime('%Y%m%d')
USE_TIMESTAMPED_FOLDERS = True

# =============================================================================
# DIRECTORY CONFIGURATION
# =============================================================================

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Master data file
MASTER_DATA_DIR = os.path.join(PROJECT_ROOT, 'Master_Data')
MASTER_DATA_FILE = os.path.join(MASTER_DATA_DIR, 'Master_GNGD_DATA_DAILY.csv')

# Downloads directory (timestamped subfolders)
BASE_DOWNLOADS_DIR = os.path.join(PROJECT_ROOT, 'downloads')
if USE_TIMESTAMPED_FOLDERS:
    DOWNLOADS_DIR = os.path.join(BASE_DOWNLOADS_DIR, RUN_TIMESTAMP)
else:
    DOWNLOADS_DIR = BASE_DOWNLOADS_DIR

# Output directory
BASE_OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
if USE_TIMESTAMPED_FOLDERS:
    OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, RUN_TIMESTAMP)
else:
    OUTPUT_DIR = BASE_OUTPUT_DIR

# Latest output directory
LATEST_OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, 'latest')

# Log directory
BASE_LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
if USE_TIMESTAMPED_FOLDERS:
    LOG_DIR = os.path.join(BASE_LOG_DIR, RUN_TIMESTAMP)
else:
    LOG_DIR = BASE_LOG_DIR

# =============================================================================
# FILE NAMING PATTERNS
# =============================================================================

DATA_FILE_PATTERN = 'GNGD_DATA_DAILY_{date}.xls'
META_FILE_PATTERN = 'GNGD_META_DAILY_{date}.xls'
ZIP_FILE_PATTERN = 'GNGD_DAILY_{date}.zip'
LOG_FILE_PATTERN = 'gngd_daily_{timestamp}.log'

# =============================================================================
# BROWSER CONFIGURATION
# =============================================================================

# Browser is REQUIRED for this runbook (JS-rendered pages with download buttons)
USE_BROWSER = True
HEADLESS_MODE = False

WAIT_TIMEOUT = 30
PAGE_LOAD_DELAY = 5
DOWNLOAD_WAIT_TIMEOUT = 30

# =============================================================================
# HTTP / SCRAPER CONFIGURATION
# =============================================================================

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 5.0

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

DEBUG_MODE = True
LOG_LEVEL = 'DEBUG' if DEBUG_MODE else 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_TO_CONSOLE = True
LOG_TO_FILE = True

# =============================================================================
# META FILE CONFIGURATION
# =============================================================================

META_COLUMNS = [
    'CODE', 'CODE_MNEMONIC', 'DESCRIPTION', 'FREQUENCY', 'MULTIPLIER',
    'AGGREGATION_TYPE', 'UNIT_TYPE', 'DATA_TYPE', 'DATA_UNIT',
    'SEASONALLY_ADJUSTED', 'ANNUALIZED', 'PROVIDER_MEASURE_URL',
    'PROVIDER', 'SOURCE', 'SOURCE_DESCRIPTION', 'COUNTRY', 'DATASET',
]

# Provider URLs for META file (from reference META xlsx)
_IMPORT_PROVIDER_URL = 'https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/Versorgungssicherheit/aktuelle_gasversorgung_/_svg/Gasimporte/Gasimporte.html;jsessionid=6B407174C279B4617D65D73C31E1EB3E?nn=1059464c'
_EXPORT_PROVIDER_URL = 'https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/Versorgungssicherheit/aktuelle_gasversorgung_/_svg/Gasexporte/Gasexporte.html?nn=1059464'
_PRODUCTION_PROVIDER_URL = 'https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/Versorgungssicherheit/aktuelle_gasversorgung_/_svg/Gasfoerderung/Gasfoerderung.html?nn=1059464'


def _meta_row(code, mnemonic, description, provider_url):
    """Helper to build a META row dict with common fields."""
    return {
        'CODE': code,
        'CODE_MNEMONIC': mnemonic,
        'DESCRIPTION': description,
        'FREQUENCY': 'D',
        'MULTIPLIER': 0,
        'AGGREGATION_TYPE': 'SUM',
        'UNIT_TYPE': 'FLOW',
        'DATA_TYPE': 'UNITS',
        'DATA_UNIT': 'GWh per day',
        'SEASONALLY_ADJUSTED': 'NSA',
        'ANNUALIZED': 'False',
        'PROVIDER_MEASURE_URL': provider_url,
        'PROVIDER': 'AfricaAI',
        'SOURCE': 'FNA',
        'SOURCE_DESCRIPTION': 'Federal Network Agency',
        'COUNTRY': 'DEU',
        'DATASET': 'GNGD',
    }


META_ROWS = [
    # Imports (11 rows)
    _meta_row('GNGD.GASIMP.CZE.D', 'GNGD.GASIMP.CZE', 'Gas imports, Czech', _IMPORT_PROVIDER_URL),
    _meta_row('GNGD.GASIMP.NLD.D', 'GNGD.GASIMP.NLD', 'Gas imports, Netherlands', _IMPORT_PROVIDER_URL),
    _meta_row('GNGD.GASIMP.BEL.D', 'GNGD.GASIMP.BEL', 'Gas imports, Belgium', _IMPORT_PROVIDER_URL),
    _meta_row('GNGD.GASIMP.POL.D', 'GNGD.GASIMP.POL', 'Gas imports, Poland', _IMPORT_PROVIDER_URL),
    _meta_row('GNGD.GASIMP.NOR.D', 'GNGD.GASIMP.NOR', 'Gas imports, Norway', _IMPORT_PROVIDER_URL),
    _meta_row('GNGD.GASIMP.DNK.D', 'GNGD.GASIMP.DNK', 'Gas imports, Denmark', _IMPORT_PROVIDER_URL),
    _meta_row('GNGD.GASIMP.AUT.D', 'GNGD.GASIMP.AUT', 'Gas imports, Austria', _IMPORT_PROVIDER_URL),
    _meta_row('GNGD.GASIMP.CHE.D', 'GNGD.GASIMP.CHE', 'Gas imports, Switzerland', _IMPORT_PROVIDER_URL),
    _meta_row('GNGD.GASIMP.RUS.D', 'GNGD.GASIMP.RUS', 'Gas imports, Russia', _IMPORT_PROVIDER_URL),
    _meta_row('GNGD.GASIMP.FRA.D', 'GNGD.GASIMP.FRA', 'Gas imports, France', _IMPORT_PROVIDER_URL),
    _meta_row('GNGD.GASIMP.DEU.D', 'GNGD.GASIMP.DEU', 'Gas imports, Germany', _IMPORT_PROVIDER_URL),
    # Exports (9 rows)
    _meta_row('GNGD.GASEXP.CZE.D', 'GNGD.GASEXP.CZE', 'Gas exports, Czech', _EXPORT_PROVIDER_URL),
    _meta_row('GNGD.GASEXP.NLD.D', 'GNGD.GASEXP.NLD', 'Gas exports, Netherlands', _EXPORT_PROVIDER_URL),
    _meta_row('GNGD.GASEXP.BEL.D', 'GNGD.GASEXP.BEL', 'Gas exports, Belgium', _EXPORT_PROVIDER_URL),
    _meta_row('GNGD.GASEXP.POL.D', 'GNGD.GASEXP.POL', 'Gas exports, Poland', _EXPORT_PROVIDER_URL),
    _meta_row('GNGD.GASEXP.DNK.D', 'GNGD.GASEXP.DNK', 'Gas exports, Denmark', _EXPORT_PROVIDER_URL),
    _meta_row('GNGD.GASEXP.AUT.D', 'GNGD.GASEXP.AUT', 'Gas exports, Austria', _EXPORT_PROVIDER_URL),
    _meta_row('GNGD.GASEXP.CHE.D', 'GNGD.GASEXP.CHE', 'Gas exports, Switzerland', _EXPORT_PROVIDER_URL),
    _meta_row('GNGD.GASEXP.FRA.D', 'GNGD.GASEXP.FRA', 'Gas exports, France', _EXPORT_PROVIDER_URL),
    _meta_row('GNGD.GASEXP.DEU.D', 'GNGD.GASEXP.DEU', 'Gas exports, Germany', _EXPORT_PROVIDER_URL),
    # Production (1 row)
    _meta_row('GNGD.GASPROD.D', 'GNGD.GASPROD', 'Gas production', _PRODUCTION_PROVIDER_URL),
]

# =============================================================================
# ERROR HANDLING
# =============================================================================

CONTINUE_ON_ERROR = True
