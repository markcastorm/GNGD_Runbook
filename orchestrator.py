#!/usr/bin/env python3
# orchestrator.py
# Main orchestrator for GNGD Daily - German Natural Gas Data Collection

import os
import sys
from datetime import datetime
import config
from logger_setup import setup_logging
from scraper import GNGDScraper
from parser import GNGDParser
from file_generator import GNGDFileGenerator
import logging

logger = logging.getLogger(__name__)


def print_banner():
    """Print a welcome banner"""
    print("\n" + "=" * 70)
    print(" GNGD Daily - German Natural Gas Data")
    print(" Bundesnetzagentur - Daily Gas Imports/Exports/Production")
    print("=" * 70 + "\n")


def print_configuration():
    """Print current configuration"""
    print("Configuration:")
    print("-" * 70)
    print(f"  Sources: {len(config.SOURCE_URLS)} URLs")
    for key, url in config.SOURCE_URLS.items():
        print(f"    - {key}: {url}")
    print(f"  Output Columns: {len(config.OUTPUT_COLUMN_CODES)}")
    print(f"  Output: {config.OUTPUT_DIR}")
    print(f"  Master Data: {config.MASTER_DATA_FILE}")
    print(f"  Timestamp: {config.RUN_TIMESTAMP}")
    print("-" * 70 + "\n")


def main():
    """Main execution flow"""

    try:
        # Setup logging
        setup_logging()

        print_banner()
        print_configuration()

        # Step 1: Fetch CSV data from Bundesnetzagentur
        print("STEP 1: Fetching CSV Data from Bundesnetzagentur")
        print("=" * 70 + "\n")

        scraper = GNGDScraper()
        fetched_data = scraper.fetch_data()

        if not fetched_data:
            logger.error("Failed to fetch CSV data from Bundesnetzagentur")
            print("\n[ERROR] Failed to fetch CSV data. Exiting.")
            sys.exit(1)

        print(f"[SUCCESS] Fetched {len(fetched_data)} CSV files:")
        for source_key, content in fetched_data.items():
            lines = content.strip().split('\n')
            print(f"  {source_key}: {len(lines)} lines")
        print()

        logger.info(f"Successfully fetched {len(fetched_data)} CSV files")

        # Step 2: Parse CSV files
        print("\nSTEP 2: Parsing CSV Data")
        print("=" * 70 + "\n")

        parser = GNGDParser()
        parsed_data = parser.parse_all_files(fetched_data)

        if not parsed_data:
            logger.error("Failed to parse CSV data")
            print("\n[ERROR] Failed to parse CSV data. Exiting.")
            sys.exit(1)

        total_dates = len(parsed_data)
        print(f"[SUCCESS] Parsed {total_dates} dates from {len(fetched_data)} sources\n")
        logger.info(f"Successfully parsed {total_dates} dates")

        # Step 3: Update master data
        print("\nSTEP 3: Updating Master Data")
        print("=" * 70 + "\n")

        header_lines, data_rows = parser.update_master(parsed_data)

        if header_lines is None or data_rows is None:
            logger.error("Failed to update master data")
            print("\n[ERROR] Failed to update master data. Exiting.")
            sys.exit(1)

        print(f"[SUCCESS] Master data updated: {len(data_rows)} total rows")
        if data_rows:
            print(f"  Date range: {data_rows[0][0]} to {data_rows[-1][0]}")
        print()

        logger.info(f"Successfully updated master with {len(data_rows)} rows")

        # Step 4: Generate output files
        print("\nSTEP 4: Generating Output Files")
        print("=" * 70 + "\n")

        generator = GNGDFileGenerator()
        output_files = generator.generate_files(header_lines, data_rows)

        if not output_files:
            logger.error("Failed to generate output files")
            print("\n[ERROR] Failed to generate output files. Exiting.")
            sys.exit(1)

        # Summary
        print("\n" + "=" * 70)
        print(" EXECUTION COMPLETE")
        print("=" * 70 + "\n")

        print("Summary:")
        print(f"  Total rows in master: {len(data_rows)}")
        if data_rows:
            print(f"  Date range: {data_rows[0][0]} to {data_rows[-1][0]}")
        print(f"  Columns: {len(config.OUTPUT_COLUMN_CODES)}")
        print()

        print("Output files:")
        if output_files.get('data_file'):
            print(f"  DATA: {os.path.basename(output_files['data_file'])}")
        if output_files.get('meta_file'):
            print(f"  META: {os.path.basename(output_files['meta_file'])}")
        if output_files.get('zip_file'):
            print(f"  ZIP:  {os.path.basename(output_files['zip_file'])}")
        print()

        if output_files.get('data_file'):
            print(f"Output directory: {os.path.dirname(output_files['data_file'])}")
        print(f"Latest files: {config.LATEST_OUTPUT_DIR}")
        print(f"Master data: {config.MASTER_DATA_FILE}")
        print()

        print("=" * 70 + "\n")

        logger.info("Orchestrator completed successfully")

        return 0

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Process interrupted by user")
        logger.warning("Process interrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        logger.exception("Unexpected error in orchestrator")
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
