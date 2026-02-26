# file_generator.py
# Generate output files for GNGD Daily data

import os
import csv
import io
import logging
import shutil
import zipfile
import xlwt
import config

logger = logging.getLogger(__name__)


class GNGDFileGenerator:
    """Generates output files (XLS DATA, XLS META, ZIP) from master data"""

    def __init__(self):
        self.logger = logger

    def create_xls_file(self, header_lines, data_rows, output_dir):
        """
        Create XLS DATA file from master data.

        XLS structure mirrors the master CSV:
            Row 0: (blank), GNGD.GASIMP.CZE.D, GNGD.GASIMP.NLD.D, ...
            Row 1: (blank), "Gas imports, Czech", "Gas imports, Netherlands", ...
            Row 2+: date, value, value, ...

        Args:
            header_lines: [header_line1, header_line2] from master
            data_rows: list of [date, val1, val2, ...]
            output_dir: Directory to save file

        Returns:
            str: Path to created XLS file or None
        """

        self.logger.info("Creating XLS DATA file...")

        try:
            filename = config.DATA_FILE_PATTERN.format(date=config.RUN_DATE)
            filepath = os.path.join(output_dir, filename)

            wb = xlwt.Workbook(encoding='utf-8')
            ws = wb.add_sheet('DATA')

            # Row 0: Column codes from header line 1
            header1_parts = next(csv.reader(io.StringIO(header_lines[0])))
            for col_idx, value in enumerate(header1_parts):
                ws.write(0, col_idx, value)

            # Row 1: Column descriptions from header line 2
            # Must use csv.reader to handle quoted fields with commas
            # e.g. "Gas imports, Czech" should stay as one field
            header2_parts = next(csv.reader(io.StringIO(header_lines[1])))
            for col_idx, value in enumerate(header2_parts):
                ws.write(1, col_idx, value)

            # Row 2+: Data rows
            for row_idx, row in enumerate(data_rows):
                for col_idx, value in enumerate(row):
                    if col_idx == 0:
                        # Date column - write as string
                        ws.write(row_idx + 2, col_idx, value)
                    else:
                        # Value columns - write as number if possible
                        try:
                            ws.write(row_idx + 2, col_idx, int(value))
                        except (ValueError, TypeError):
                            try:
                                ws.write(row_idx + 2, col_idx, float(value))
                            except (ValueError, TypeError):
                                ws.write(row_idx + 2, col_idx, value)

            wb.save(filepath)

            self.logger.info(f"Created XLS file: {filename} ({len(data_rows)} data rows)")
            return filepath

        except Exception as e:
            self.logger.error(f"Error creating XLS file: {e}")
            return None

    def create_meta_file(self, output_dir):
        """
        Create XLS META file with static metadata for each timeseries.

        XLS structure:
            Row 0: 17 column headers (CODE, CODE_MNEMONIC, DESCRIPTION, ...)
            Row 1-21: One row per timeseries (21 total)

        Args:
            output_dir: Directory to save file

        Returns:
            str: Path to created META XLS file or None
        """

        self.logger.info("Creating XLS META file...")

        try:
            filename = config.META_FILE_PATTERN.format(date=config.RUN_DATE)
            filepath = os.path.join(output_dir, filename)

            wb = xlwt.Workbook(encoding='utf-8')
            ws = wb.add_sheet('META')

            # Row 0: Column headers
            for col_idx, col_name in enumerate(config.META_COLUMNS):
                ws.write(0, col_idx, col_name)

            # Row 1+: Data rows (one per timeseries)
            for row_idx, row_data in enumerate(config.META_ROWS):
                for col_idx, col_name in enumerate(config.META_COLUMNS):
                    value = row_data.get(col_name, '')
                    ws.write(row_idx + 1, col_idx, value)

            wb.save(filepath)

            self.logger.info(f"Created META file: {filename} ({len(config.META_ROWS)} rows)")
            return filepath

        except Exception as e:
            self.logger.error(f"Error creating META file: {e}")
            return None

    def create_zip_file(self, data_file, meta_file, output_dir):
        """
        Create ZIP file containing the XLS DATA and META files.

        Args:
            data_file: Path to XLS DATA file
            meta_file: Path to XLS META file
            output_dir: Directory to save ZIP

        Returns:
            str: Path to created ZIP file or None
        """

        self.logger.info("Creating ZIP file...")

        try:
            zip_filename = config.ZIP_FILE_PATTERN.format(date=config.RUN_DATE)
            zip_filepath = os.path.join(output_dir, zip_filename)

            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if data_file and os.path.exists(data_file):
                    zipf.write(data_file, os.path.basename(data_file))
                    self.logger.info(f"Added to ZIP: {os.path.basename(data_file)}")
                if meta_file and os.path.exists(meta_file):
                    zipf.write(meta_file, os.path.basename(meta_file))
                    self.logger.info(f"Added to ZIP: {os.path.basename(meta_file)}")

            self.logger.info(f"Created ZIP file: {zip_filename}")
            return zip_filepath

        except Exception as e:
            self.logger.error(f"Error creating ZIP file: {e}")
            return None

    def copy_to_latest(self, files, latest_dir):
        """
        Copy files to 'latest' directory, replacing any existing files.

        Args:
            files: Dict of {file_type: filepath}
            latest_dir: Path to latest directory
        """

        self.logger.info("Copying files to 'latest' directory...")

        try:
            os.makedirs(latest_dir, exist_ok=True)

            # Remove all existing files in latest directory
            for existing_file in os.listdir(latest_dir):
                file_path = os.path.join(latest_dir, existing_file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    self.logger.debug(f"Removed old file: {existing_file}")

            # Copy new files
            for file_type, filepath in files.items():
                if filepath and os.path.exists(filepath):
                    dest = os.path.join(latest_dir, os.path.basename(filepath))
                    shutil.copy2(filepath, dest)
                    self.logger.info(f"Copied {file_type}: {os.path.basename(filepath)}")

        except Exception as e:
            self.logger.error(f"Error copying to latest: {e}")

    def generate_files(self, header_lines, data_rows):
        """
        Main method: Generate all output files (DATA XLS, META XLS, ZIP).

        Args:
            header_lines: [header_line1, header_line2] from master
            data_rows: list of [date, val1, val2, ...]

        Returns:
            dict with paths to all generated files
        """

        self.logger.info("\n" + "=" * 70)
        self.logger.info("GENERATING OUTPUT FILES")
        self.logger.info("=" * 70)

        # Create output directory
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)

        output_files = {}

        # Create XLS DATA file
        data_file = self.create_xls_file(header_lines, data_rows, config.OUTPUT_DIR)
        output_files['data_file'] = data_file

        # Create XLS META file
        meta_file = self.create_meta_file(config.OUTPUT_DIR)
        output_files['meta_file'] = meta_file

        # Create ZIP file (includes both DATA and META)
        zip_file = self.create_zip_file(data_file, meta_file, config.OUTPUT_DIR)
        output_files['zip_file'] = zip_file

        # Copy to latest directory
        self.copy_to_latest(output_files, config.LATEST_OUTPUT_DIR)

        self.logger.info("=" * 70 + "\n")

        return output_files


def main():
    """Test the file generator"""
    from logger_setup import setup_logging
    from parser import GNGDParser

    setup_logging()

    parser = GNGDParser()
    header_lines, data_rows = parser.load_master_data()

    if header_lines and data_rows:
        generator = GNGDFileGenerator()
        output_files = generator.generate_files(header_lines, data_rows)

        if output_files:
            print("\n[SUCCESS] Files generated:")
            for file_type, filepath in output_files.items():
                if filepath:
                    print(f"  {file_type}: {filepath}")
        else:
            print("\n[FAILED] Could not generate files")
    else:
        print("\n[FAILED] Could not load master data")


if __name__ == '__main__':
    main()
