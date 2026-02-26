# parser.py
# Parser for GNGD Daily - Parse downloaded CSVs and update master data

import os
import logging
from datetime import datetime
import config

logger = logging.getLogger(__name__)


class GNGDParser:
    """Parses Bundesnetzagentur CSV data and updates the master CSV"""

    def __init__(self):
        self.logger = logger

    def parse_csv_file(self, source_key, content):
        """
        Parse a single downloaded CSV file from Bundesnetzagentur.

        CSV format (semicolon-separated):
            Row 0: header with German column names
                   e.g. "                    .;Tschechien;Niederlande;..."
            Row 1+: data rows
                   e.g. "14.02.2026;0;800;706;..."

        Args:
            source_key: 'imports', 'exports', or 'production'
            content: Raw CSV content string

        Returns:
            dict: {date_str: {col_code: value}} or None on failure
        """

        self.logger.info(f"Parsing CSV: {source_key}")

        try:
            column_map = config.SOURCE_COLUMN_MAPS.get(source_key)
            if column_map is None:
                self.logger.error(f"No column mapping for source: {source_key}")
                return None

            lines = content.strip().split('\n')
            if len(lines) < 2:
                self.logger.error(f"CSV too short ({len(lines)} lines): {source_key}")
                return None

            # Parse header row
            header_line = lines[0]
            header_parts = [h.strip() for h in header_line.split(';')]

            self.logger.info(f"  Header columns ({len(header_parts)}): {header_parts}")

            # Build column index -> code mapping
            # First column is the date (header is whitespace + '.')
            col_index_to_code = {}
            mapped_count = 0
            skipped_cols = []

            for idx, german_name in enumerate(header_parts):
                if idx == 0:
                    continue  # Skip date column header

                if german_name in column_map:
                    col_index_to_code[idx] = column_map[german_name]
                    mapped_count += 1
                else:
                    skipped_cols.append(german_name)

            self.logger.info(f"  Mapped {mapped_count} columns to codes")
            if skipped_cols:
                self.logger.info(f"  Skipped columns (not in mapping): {skipped_cols}")

            # Parse data rows
            date_values = {}
            parse_errors = 0

            for line_num, line in enumerate(lines[1:], start=2):
                line = line.strip()
                if not line:
                    continue

                parts = line.split(';')
                if len(parts) < 2:
                    continue

                # Parse date (DD.MM.YYYY -> YYYY-MM-DD)
                date_raw = parts[0].strip()
                try:
                    dt = datetime.strptime(date_raw, config.SOURCE_DATE_FORMAT)
                    date_str = dt.strftime(config.OUTPUT_DATE_FORMAT)
                except ValueError:
                    if parse_errors < 5:
                        self.logger.warning(f"  Could not parse date on line {line_num}: '{date_raw}'")
                    parse_errors += 1
                    continue

                # Extract values for mapped columns
                row_values = {}
                for col_idx, col_code in col_index_to_code.items():
                    if col_idx < len(parts):
                        value_str = parts[col_idx].strip()
                        try:
                            row_values[col_code] = int(value_str)
                        except ValueError:
                            try:
                                row_values[col_code] = float(value_str)
                            except ValueError:
                                row_values[col_code] = 0

                if row_values:
                    date_values[date_str] = row_values

            if parse_errors > 0:
                self.logger.warning(f"  Total date parse errors: {parse_errors}")

            self.logger.info(f"  Extracted {len(date_values)} dates from {source_key}")
            if date_values:
                dates_sorted = sorted(date_values.keys())
                self.logger.info(f"  Date range: {dates_sorted[0]} to {dates_sorted[-1]}")

            return date_values

        except Exception as e:
            self.logger.error(f"Error parsing {source_key}: {e}")
            return None

    def parse_all_files(self, fetched_data):
        """
        Parse all fetched CSV files and merge into a unified date-indexed structure.

        Args:
            fetched_data: dict {source_key: csv_content} from scraper

        Returns:
            dict: {date_str: {col_code: value, ...}} or None on failure
        """

        self.logger.info(f"\n{'='*70}")
        self.logger.info("PARSING CSV FILES")
        self.logger.info(f"{'='*70}")

        merged_data = {}

        for source_key in config.SOURCE_URLS.keys():
            content = fetched_data.get(source_key)
            if content is None:
                self.logger.error(f"No content for: {source_key}")
                return None

            date_values = self.parse_csv_file(source_key, content)

            if date_values is None:
                return None

            # Merge into unified structure
            for date_str, col_values in date_values.items():
                if date_str not in merged_data:
                    merged_data[date_str] = {}
                merged_data[date_str].update(col_values)

        # Summary
        total_dates = len(merged_data)
        complete_dates = sum(
            1 for cols in merged_data.values()
            if len(cols) == len(config.OUTPUT_COLUMN_CODES)
        )

        self.logger.info(f"\nMerged data: {total_dates} total dates, {complete_dates} complete (all 21 columns)")

        return merged_data

    def load_master_data(self):
        """
        Load master CSV file, preserving the 2-row header structure.

        Master format:
            Row 0: ,GNGD.GASIMP.CZE.D,GNGD.GASIMP.NLD.D,...
            Row 1: ,"Gas imports, Czech","Gas imports, Netherlands",...
            Row 2+: YYYY-MM-DD,val,val,...

        Returns:
            tuple: (header_lines, data_rows) or (None, None) on failure
        """

        if not os.path.exists(config.MASTER_DATA_FILE):
            self.logger.warning(f"Master file not found: {config.MASTER_DATA_FILE}")
            self.logger.info("Will create new master file")
            header1 = ',' + ','.join(config.OUTPUT_COLUMN_CODES)
            header2 = ',' + ','.join(config.OUTPUT_COLUMN_DESCRIPTIONS)
            return [header1, header2], []

        try:
            with open(config.MASTER_DATA_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if len(lines) < 2:
                self.logger.error("Master file has fewer than 2 header lines")
                return None, None

            # First 2 lines are headers
            header_lines = [lines[0].rstrip('\n'), lines[1].rstrip('\n')]

            # Remaining lines are data
            data_rows = []
            for line in lines[2:]:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(',')
                data_rows.append(parts)

            self.logger.info(f"Loaded master data: {len(data_rows)} rows")
            if data_rows:
                self.logger.info(f"  Date range: {data_rows[0][0]} to {data_rows[-1][0]}")

            return header_lines, data_rows

        except Exception as e:
            self.logger.error(f"Error loading master data: {e}")
            return None, None

    def save_master_data(self, header_lines, data_rows):
        """
        Save master CSV file with the 2-row header structure.

        Args:
            header_lines: [header_line1, header_line2]
            data_rows: list of [date, val1, val2, ...]
        """

        try:
            os.makedirs(os.path.dirname(config.MASTER_DATA_FILE), exist_ok=True)

            with open(config.MASTER_DATA_FILE, 'w', encoding='utf-8', newline='') as f:
                f.write(header_lines[0] + '\n')
                f.write(header_lines[1] + '\n')

                for row in data_rows:
                    f.write(','.join(str(v) for v in row) + '\n')

            self.logger.info(f"Saved master data: {len(data_rows)} rows")

        except Exception as e:
            self.logger.error(f"Error saving master data: {e}")

    def update_master(self, parsed_data):
        """
        Update master CSV with new data from parsed CSV files.
        Only adds dates AFTER the last date in the master (forward-only).
        Never adds old/historical dates backwards. Never overwrites existing data.

        Args:
            parsed_data: dict {date_str: {col_code: value, ...}} from parse_all_files

        Returns:
            tuple: (header_lines, data_rows) with updated data, or (None, None) on failure
        """

        self.logger.info(f"\n{'='*70}")
        self.logger.info("UPDATING MASTER DATA")
        self.logger.info(f"{'='*70}")

        # Load existing master
        header_lines, data_rows = self.load_master_data()
        if header_lines is None:
            return None, None

        # Find the last date in the master (cutoff for new data)
        if data_rows:
            last_master_date = max(row[0] for row in data_rows)
        else:
            last_master_date = ''

        self.logger.info(f"Existing rows in master: {len(data_rows)}")
        self.logger.info(f"Last date in master: {last_master_date}")

        # Only add dates AFTER the last master date (forward-only)
        new_rows = []
        skipped_old = 0
        for date_str in sorted(parsed_data.keys()):
            if date_str <= last_master_date:
                skipped_old += 1
                continue

            cols = parsed_data[date_str]

            # Build row in correct column order (matching master)
            row = [date_str]
            for col_code in config.OUTPUT_COLUMN_CODES:
                value = cols.get(col_code, '')
                row.append(str(value) if value != '' else '')

            new_rows.append(row)

        if skipped_old > 0:
            self.logger.info(f"Skipped {skipped_old} dates at or before {last_master_date}")
        self.logger.info(f"New dates to add: {len(new_rows)}")

        if new_rows:
            # Merge new rows into existing data maintaining date order
            all_rows = data_rows + new_rows
            all_rows.sort(key=lambda r: r[0])

            data_rows = all_rows

            self.logger.info(f"First new date: {new_rows[0][0]}")
            self.logger.info(f"Last new date: {new_rows[-1][0]}")
        else:
            self.logger.info("No new dates to add - master is up to date")

        # Summary
        self.logger.info(f"\n{'='*70}")
        self.logger.info("SUMMARY")
        self.logger.info(f"{'='*70}")
        self.logger.info(f"New rows added: {len(new_rows)}")
        self.logger.info(f"Total rows in master: {len(data_rows)}")
        self.logger.info(f"{'='*70}\n")

        # Save updated master
        self.save_master_data(header_lines, data_rows)

        return header_lines, data_rows


def main():
    """Test the parser with a sample CSV"""
    from logger_setup import setup_logging

    setup_logging()

    sample_imports = """                    .;Tschechien;Niederlande;Belgien;Polen;Norwegen;Dänemark;Frankreich;Österreich;Schweiz;Russland;LNG;Deutschland Import
14.02.2026;0;800;706;0;1369;0;58;0;145;0;230;3308
15.02.2026;0;670;567;0;1054;0;43;0;101;0;193;2628"""

    parser = GNGDParser()
    result = parser.parse_csv_file('imports', sample_imports)

    if result:
        print(f"\n[SUCCESS] Parsed {len(result)} dates:")
        for date_str, values in result.items():
            print(f"  {date_str}: {values}")
    else:
        print("\n[FAILED] Could not parse test data")


if __name__ == '__main__':
    main()
