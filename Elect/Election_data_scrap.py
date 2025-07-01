import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import csv
import os

class ECIResultsScraper:
    def __init__(self):
        self.session = requests.Session()
        # More comprehensive headers to mimic real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
    
    def setup_selenium_driver(self):
        """Setup Selenium WebDriver with stealth options"""
        chrome_options = Options()
        
        # Add stealth options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Uncomment next line to run headless (without browser window)
        # chrome_options.add_argument('--headless')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            # Execute script to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            print("Please install ChromeDriver: https://chromedriver.chromium.org/")
            return None
    
    def scrape_with_selenium(self, url):
        """Scrape using Selenium WebDriver to bypass bot detection"""
        driver = self.setup_selenium_driver()
        if not driver:
            return None
            
        try:
            print("Loading page with Selenium...")
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Add random delay to appear more human-like
            time.sleep(random.uniform(2, 4))
            
            # Get page source and parse with BeautifulSoup
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            return self.parse_tables(soup)
            
        except TimeoutException:
            print("Timeout waiting for page to load")
            return None
        except WebDriverException as e:
            print(f"WebDriver error: {e}")
            return None
        finally:
            driver.quit()
    
    def scrape_with_requests_advanced(self, url):
        """Advanced requests-based scraping with session management"""
        try:
            # First, visit the main ECI page to establish session
            main_url = "https://results.eci.gov.in/"
            print("Establishing session with main ECI page...")
            
            response = self.session.get(main_url, timeout=10)
            time.sleep(random.uniform(1, 3))
            
            # Now try to access the target URL
            print("Accessing target URL...")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return self.parse_tables(soup)
            
        except requests.exceptions.RequestException as e:
            print(f"Requests method failed: {e}")
            return None
    
    def parse_tables(self, soup):
        """Parse tables from BeautifulSoup object"""
        tables = soup.find_all('table')
        all_data = []
        
        print(f"Found {len(tables)} tables on the page")
        
        for table_idx, table in enumerate(tables):
            try:
                # Extract headers
                headers = []
                header_rows = table.find_all('tr')[:2]  # Check first 2 rows for headers
                
                for header_row in header_rows:
                    header_cells = header_row.find_all(['th', 'td'])
                    if header_cells:
                        potential_headers = [cell.get_text(strip=True) for cell in header_cells]
                        if any(header.strip() for header in potential_headers):
                            headers = potential_headers
                            break
                
                # Extract all rows
                rows = table.find_all('tr')
                table_data = []
                
                start_row = 1 if headers else 0
                for row in rows[start_row:]:
                    cells = row.find_all(['td', 'th'])
                    row_data = []
                    
                    for cell in cells:
                        # Handle merged cells and extract all text
                        cell_text = cell.get_text(separator=' ', strip=True)
                        row_data.append(cell_text)
                    
                    if row_data and any(cell.strip() for cell in row_data):
                        table_data.append(row_data)
                
                if table_data:
                    # Create DataFrame
                    max_cols = max(len(row) for row in table_data) if table_data else 0
                    
                    # Pad rows to have same number of columns
                    padded_data = []
                    for row in table_data:
                        padded_row = row + [''] * (max_cols - len(row))
                        padded_data.append(padded_row)
                    
                    df = pd.DataFrame(padded_data)
                    
                    # Set column names
                    if headers and len(headers) <= max_cols:
                        column_names = headers + [f'Column_{i}' for i in range(len(headers), max_cols)]
                        df.columns = column_names[:max_cols]
                    else:
                        df.columns = [f'Column_{i}' for i in range(max_cols)]
                    
                    all_data.append({
                        'table_index': table_idx,
                        'headers': headers,
                        'data': df,
                        'row_count': len(df),
                        'column_count': len(df.columns)
                    })
                    
                    print(f"Table {table_idx}: {len(df)} rows, {len(df.columns)} columns")
                    
            except Exception as e:
                print(f"Error parsing table {table_idx}: {e}")
                continue
        
        return all_data
    
    def save_data(self, data, base_filename="eci_results"):
        """Save data to multiple formats"""
        if not data:
            print("No data to save")
            return
        
        # Save individual CSV files for each table
        for table_info in data:
            table_idx = table_info['table_index']
            df = table_info['data']
            
            csv_filename = f"{base_filename}_table_{table_idx}.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"Saved table {table_idx} to {csv_filename}")
        
        # Save all tables to one Excel file with multiple sheets
        excel_filename = f"{base_filename}_all_tables.xlsx"
        try:
            with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
                for table_info in data:
                    sheet_name = f"Table_{table_info['table_index']}"
                    table_info['data'].to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"Saved all tables to {excel_filename}")
        except Exception as e:
            print(f"Error saving Excel file: {e}")
        
        return True
    
    def print_data_summary(self, data):
        """Print summary of scraped data"""
        if not data:
            print("No data found")
            return
        
        print(f"\n=== DATA SUMMARY ===")
        print(f"Total tables found: {len(data)}")
        
        for table_info in data:
            print(f"\nTable {table_info['table_index']}:")
            print(f"  Rows: {table_info['row_count']}")
            print(f"  Columns: {table_info['column_count']}")
            print(f"  Headers: {table_info['headers'][:5]}...")  # Show first 5 headers
            
            # Show sample data
            df = table_info['data']
            if not df.empty:
                print(f"  Sample data:")
                print(df.head(3).to_string(index=False, max_cols=5))

def main():
    scraper = ECIResultsScraper()
    url = "https://results.eci.gov.in/AcResultGenDecNew2023/RoundwiseS2961.htm?ac=61"
    
    print("ECI Election Results Scraper")
    print("="*50)
    print(f"Target URL: {url}")
    
    # Method 1: Try advanced requests method first
    print("\n1. Trying advanced requests method...")
    data = scraper.scrape_with_requests_advanced(url)
    
    # Method 2: If requests fail, try Selenium
    if not data:
        print("\n2. Requests method failed. Trying Selenium method...")
        print("Note: This requires ChromeDriver to be installed")
        data = scraper.scrape_with_selenium(url)
    
    # Process results
    if data:
        print("\n✅ Successfully scraped data!")
        scraper.print_data_summary(data)
        scraper.save_data(data, "eci_election_results")
    else:
        print("\n❌ Failed to scrape data from the website")
        print("\nTroubleshooting tips:")
        print("1. The website might be blocking automated requests")
        print("2. Install ChromeDriver for Selenium: https://chromedriver.chromium.org/")
        print("3. Try accessing the website manually first to check if it's working")
        print("4. The website structure might have changed")

if __name__ == "__main__":
    main()