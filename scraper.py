# scraper.py
# Web scraper for GNGD Daily - Downloads CSV data from Bundesnetzagentur.de
# Uses Selenium to navigate JS-rendered pages and trigger CSV downloads

import os
import re
import time
import glob
import shutil
import logging
from datetime import datetime
import config

logger = logging.getLogger(__name__)


class GNGDScraper:
    """Downloads daily gas data CSVs from Bundesnetzagentur"""

    def __init__(self):
        self.logger = logger
        self.driver = None
        # Temporary download directory for browser CSV downloads
        self.browser_download_dir = os.path.join(config.DOWNLOADS_DIR, '_browser_temp')

    # =========================================================================
    # CHROME / SELENIUM SETUP
    # =========================================================================

    def get_chrome_version_from_registry(self):
        """Get installed Chrome version from Windows Registry"""

        import winreg

        self.logger.info("Checking Windows Registry for Chrome version...")

        registry_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Google\Update\Clients\{8A69D345-D564-463c-AFF1-A69D9E530F96}"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Google\Chrome\BLBeacon"),
        ]

        for hkey, path in registry_paths:
            try:
                key = winreg.OpenKey(hkey, path)
                version, _ = winreg.QueryValueEx(key, "version")
                winreg.CloseKey(key)

                major_version = int(version.split('.')[0])
                self.logger.info(f"Found Chrome version: {version} (major: {major_version})")
                return major_version
            except (FileNotFoundError, OSError):
                continue

        self.logger.warning("Chrome version not found in registry")
        return None

    def setup_driver(self):
        """Initialize Chrome driver with download directory configured"""

        import undetected_chromedriver as uc

        self.logger.info("Setting up Chrome browser...")

        # Create temporary download directory
        os.makedirs(self.browser_download_dir, exist_ok=True)

        # Get Chrome version from registry
        chrome_version = self.get_chrome_version_from_registry()

        options = uc.ChromeOptions()

        if config.HEADLESS_MODE:
            options.add_argument('--headless=new')

        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')

        # Configure automatic CSV download (no dialog)
        prefs = {
            'download.default_directory': self.browser_download_dir.replace('/', '\\'),
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True,
        }
        options.add_experimental_option('prefs', prefs)

        if chrome_version:
            self.logger.info(f"Using Chrome version {chrome_version} for driver")
            self.driver = uc.Chrome(options=options, version_main=chrome_version)
        else:
            self.logger.info("Using automatic version detection")
            self.driver = uc.Chrome(options=options)

        self.driver.set_page_load_timeout(config.WAIT_TIMEOUT)
        self.logger.info(f"Chrome driver initialized (downloads to: {self.browser_download_dir})")

    # =========================================================================
    # DOWNLOAD HELPERS
    # =========================================================================

    def clear_download_dir(self):
        """Remove all files from the browser download directory"""

        if os.path.exists(self.browser_download_dir):
            for f in os.listdir(self.browser_download_dir):
                filepath = os.path.join(self.browser_download_dir, f)
                if os.path.isfile(filepath):
                    os.remove(filepath)

    def wait_for_download(self, timeout=None):
        """
        Wait for a CSV file to appear in the download directory.
        Returns the path to the downloaded file or None on timeout.
        """

        if timeout is None:
            timeout = config.DOWNLOAD_WAIT_TIMEOUT

        self.logger.info(f"Waiting for CSV download (timeout: {timeout}s)...")

        start_time = time.time()

        while time.time() - start_time < timeout:
            # Look for CSV files (exclude .crdownload partial files)
            csv_files = glob.glob(os.path.join(self.browser_download_dir, '*.csv'))
            crdownload_files = glob.glob(os.path.join(self.browser_download_dir, '*.crdownload'))

            if csv_files and not crdownload_files:
                # Download complete
                csv_path = csv_files[0]
                self.logger.info(f"Download complete: {os.path.basename(csv_path)}")
                return csv_path

            time.sleep(0.5)

        self.logger.error(f"Download timed out after {timeout}s")
        return None

    def read_csv_content(self, filepath):
        """Read CSV file content, trying multiple encodings"""

        # Try UTF-8 first (browser typically downloads as UTF-8),
        # then latin-1/cp1252 as fallback for ANSI-encoded files.
        # Note: latin-1 never raises UnicodeDecodeError so it must come last.
        for encoding in ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                self.logger.info(f"Read CSV ({encoding}): {len(content)} chars")
                return content
            except UnicodeDecodeError:
                continue

        self.logger.error(f"Could not read CSV file with any encoding: {filepath}")
        return None

    # =========================================================================
    # PAGE NAVIGATION AND CSV DOWNLOAD
    # =========================================================================

    def navigate_and_download(self, url, source_key):
        """
        Navigate to a Bundesnetzagentur page and download its CSV data.

        Steps:
            1. Navigate to the URL
            2. Wait for JS to render the page
            3. Find the 'Daten als CSV-Datei herunterladen' link dynamically
            4. Click it to trigger CSV download
            5. Wait for file to appear in download directory
            6. Read and return the CSV content

        Args:
            url: The page URL to visit
            source_key: Identifier for this source ('imports', 'exports', 'production')

        Returns:
            str: CSV file content or None on failure
        """

        self.logger.info(f"Fetching {source_key}: {url}")

        try:
            # Clear download directory before each download
            self.clear_download_dir()

            # Navigate to page
            self.driver.get(url)
            self.logger.info(f"Page loaded, waiting {config.PAGE_LOAD_DELAY}s for JS render...")
            time.sleep(config.PAGE_LOAD_DELAY)

            # Find the CSV download link dynamically
            # Look for anchor with text containing 'Daten als CSV-Datei herunterladen'
            # or within a <p class="downloadLink"> element
            download_link = None

            # Method 1: Find by link text
            from selenium.webdriver.common.by import By

            try:
                links = self.driver.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    try:
                        link_text = link.text.strip()
                        if config.CSV_DOWNLOAD_LINK_TEXT in link_text:
                            download_link = link
                            self.logger.info(f"Found download link by text: '{link_text}'")
                            break
                    except Exception:
                        continue
            except Exception as e:
                self.logger.debug(f"Link text search failed: {e}")

            # Method 2: Find by CSS selector (downloadLink class)
            if download_link is None:
                try:
                    download_link = self.driver.find_element(
                        By.CSS_SELECTOR, 'p.downloadLink a'
                    )
                    self.logger.info("Found download link by CSS selector: p.downloadLink a")
                except Exception as e:
                    self.logger.debug(f"CSS selector search failed: {e}")

            # Method 3: Find by partial href containing 'csv_export'
            if download_link is None:
                try:
                    download_link = self.driver.find_element(
                        By.CSS_SELECTOR, 'a[href*="csv_export"]'
                    )
                    self.logger.info("Found download link by href containing 'csv_export'")
                except Exception as e:
                    self.logger.debug(f"Href search failed: {e}")

            if download_link is None:
                self.logger.error(f"Could not find CSV download link on {source_key} page")
                return None

            # Click the download link
            self.logger.info(f"Clicking download link for {source_key}...")
            download_link.click()

            # Wait for download to complete
            csv_path = self.wait_for_download()
            if csv_path is None:
                return None

            # Read the CSV content
            content = self.read_csv_content(csv_path)
            return content

        except Exception as e:
            self.logger.error(f"Error fetching {source_key}: {e}")
            return None

    def save_csv_file(self, source_key, content, download_dir):
        """Save CSV content to the downloads directory for traceability"""

        os.makedirs(download_dir, exist_ok=True)
        filename = f"csv_export_{source_key}.csv"
        filepath = os.path.join(download_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        self.logger.info(f"Saved: {filename} ({len(content)} chars)")
        return filepath

    # =========================================================================
    # MAIN FETCH METHOD
    # =========================================================================

    def fetch_data(self):
        """
        Main method to fetch CSV data from all 3 daily source URLs.

        Returns:
            dict: {source_key: csv_content} or None on failure
        """

        try:
            self.logger.info("Starting GNGD Daily data fetch")
            self.logger.info(f"Sources: {list(config.SOURCE_URLS.keys())}")

            # Setup browser
            self.setup_driver()

            fetched_data = {}

            for source_key, url in config.SOURCE_URLS.items():
                self.logger.info(f"\n{'='*70}")
                self.logger.info(f"FETCHING: {source_key.upper()}")
                self.logger.info(f"{'='*70}")

                content = self.navigate_and_download(url, source_key)

                if content is None:
                    self.logger.error(f"Failed to fetch {source_key}")
                    return None

                fetched_data[source_key] = content

                # Save raw CSV for traceability
                self.save_csv_file(source_key, content, config.DOWNLOADS_DIR)

            self.logger.info(f"\nSuccessfully fetched {len(fetched_data)} CSV files")
            return fetched_data

        except Exception as e:
            self.logger.error(f"Error during data fetch: {e}")
            return None

        finally:
            # Cleanup browser
            if self.driver:
                self.driver.quit()
                self.logger.info("Browser closed")

            # Cleanup temp download directory
            if os.path.exists(self.browser_download_dir):
                try:
                    shutil.rmtree(self.browser_download_dir)
                except Exception:
                    pass


def main():
    """Test the scraper"""
    from logger_setup import setup_logging

    setup_logging()

    scraper = GNGDScraper()
    data = scraper.fetch_data()

    if data:
        print(f"\n[SUCCESS] Fetched {len(data)} CSV files:")
        for source_key, content in data.items():
            lines = content.strip().split('\n')
            print(f"  {source_key}: {len(lines)} lines, {len(content)} chars")
    else:
        print("\n[FAILED] Could not fetch data files")


if __name__ == '__main__':
    main()
