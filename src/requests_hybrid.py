import asyncio
import requests
import logging
from playwright.async_api import async_playwright
import re
from typing import Dict, Optional, List
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import time
import subprocess
import sys

# Global flag to track if browsers are installed
_browsers_installed = False

def ensure_playwright_browsers():
    """Ensure Playwright browsers are installed (call once at startup)"""
    global _browsers_installed
    if _browsers_installed:
        return True
    
    try:
        # Check if chromium is available by trying to get its version
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                # Try to get browser path - if this fails, browser isn't installed
                browser_path = p.chromium.executable_path
                _browsers_installed = True
                logging.info(f"Playwright browsers already installed at: {browser_path}")
                return True
            except Exception:
                pass
    except Exception:
        pass
    
    # If we get here, browsers need to be installed
    logging.info("Installing Playwright browsers...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install", "chromium"
        ], check=True, capture_output=True, text=True, timeout=300)
        
        _browsers_installed = True
        logging.info("Playwright browsers installed successfully")
        return True
        
    except subprocess.TimeoutExpired:
        logging.error("Playwright installation timed out")
        return False
    except Exception as e:
        logging.error(f"Failed to install Playwright browsers: {e}")
        return False

class ISCRequestsHybrid:
    """
    Hybrid approach: Use Playwright for login, then extract cookies for requests library
    This is most similar to your original MechanicalSoup workflow
    """
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.authenticated = False
        
    async def login(self) -> bool:
        """Login using Playwright, then extract cookies for requests session"""
        playwright = await async_playwright().start()
        
        try:
            # Try to launch browser normally first
            browser = await playwright.chromium.launch(headless=True)
        except Exception as e:
            if "Executable doesn't exist" in str(e):
                # Install browsers and try again
                logging.info("Installing Playwright browsers...")
                import subprocess
                import sys
                try:
                    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                                 check=True, capture_output=True, text=True, timeout=120)
                    # Try again with cloud-safe args
                    browser = await playwright.chromium.launch(
                        headless=True,
                        args=["--no-sandbox", "--disable-setuid-sandbox"]
                    )
                except Exception as install_error:
                    logging.error(f"Failed to install/launch browser: {install_error}")
                    await playwright.stop()
                    return False
            else:
                logging.error(f"Browser launch failed: {e}")
                await playwright.stop()
                return False
        
        page = await browser.new_page()
        
        try:
            # Login with Playwright
            await page.goto("https://isc.onlinemga.com/amp/login")
            await page.fill('input[name="username"]', self.username)
            await page.fill('input[name="password"]', self.password)
            await page.click('button.btn.btn-lg.btn-block.btn-default[type="submit"]')
            await page.wait_for_load_state("networkidle")
            
            # Check if login was successful
            if "login" in page.url:
                return False
            
            # Extract all cookies from Playwright
            cookies = await page.context.cookies()
            
            # Add cookies to requests session
            for cookie in cookies:
                self.session.cookies.set(
                    name=cookie['name'],
                    value=cookie['value'],
                    domain=cookie['domain'],
                    path=cookie.get('path', '/'),
                    secure=cookie.get('secure', False)
                )
            
            # Set proper headers to mimic browser
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            self.authenticated = True
            return True
            
        except Exception as e:
            logging.error(f"Login failed: {e}")
            return False
            
        finally:
            await browser.close()
            await playwright.stop()
    
    def search_by_policy(self, policy_number: str) -> Optional[Dict]:
        """Search for policy using requests and extract data from search results table"""
        if not self.authenticated:
            raise Exception("Must login first")
        
        try:
            # This is exactly like your MechanicalSoup workflow!
            search_url = "https://isc.onlinemga.com/amp/search/advancedsearch"
            
            # Parameters based on user's working URL - it's a GET request!
            params = {
                'status_id': '',
                'program_name': '',
                'effective_date_start': '',
                'effective_date_end': '',
                'bind_date_start': '',
                'bind_date_end': '',
                'created_date_start': '',
                'created_date_end': '',
                'ren': '',
                'has_esign': '',
                'has_endorsements': '',
                'has_claim': '',
                'has_certificate': '',
                'item_id': '',
                'policy_number': policy_number,  # This is the key parameter
                'agency_name': '',
                'company_name': '',
                'applicant_first': '',
                'applicant_last': '',
                'applicant_phone': '',
                'applicant_state': '',
                'applicant_email': '',
                'producer_first': '',
                'producer_last': ''
            }
            
            # GET request with parameters (just like browser.get(url) with params)
            response = self.session.get(search_url, params=params)
            if response.status_code == 200:
                # Extract data from search results table (like original scraper)
                return self._extract_search_results_data(response.text, policy_number)
            
            return None
            
        except Exception as e:
            logging.error(f"Search failed for {policy_number}: {e}")
            return None



    def process_policy(self, policy_number: str) -> Optional[Dict]:
        """Process a single policy - get search results data then detail page data"""
        try:
            # Get data from search results table
            search_data = self.search_by_policy(policy_number)
            if not search_data:
                return None
            
            # Get additional data from detail page
            app_id = search_data.get('app_id')
            if app_id:
                detail_data = self.get_application_details(app_id)
                
                # Carefully merge detail page data without overwriting search results
                # Only add missing fields or fields that should come from detail page
                if detail_data.get('expiration_date'):
                    search_data['expiration_date'] = detail_data['expiration_date']
                if detail_data.get('cancellation_date'):
                    search_data['cancellation_date'] = detail_data['cancellation_date']
                # If detail page has better effective date, use it
                if detail_data.get('effective_date'):
                    search_data['effective_date'] = detail_data['effective_date']
            
            return search_data
            
        except Exception as e:
            logging.error(f"Error processing policy {policy_number}: {e}")
            return None

    def get_application_details(self, app_id: str) -> Dict:
        """Get additional details from the detail page (effective/expiration/cancellation dates)"""
        if not self.authenticated:
            raise Exception("Must login first")
        
        try:
            detail_url = f"https://isc.onlinemga.com/amp/detail/view/{app_id}"
            
            # This is exactly like browser.get(url) in MechanicalSoup!
            response = self.session.get(detail_url)
            
            if response.status_code == 200:
                return self._parse_detail_page_html(response.text)
            
            return {}
            
        except Exception as e:
            logging.error(f"Detail page retrieval failed for {app_id}: {e}")
            return {}

    def process_policies_concurrent(self, policy_numbers: List[str], max_workers: int = 10, progress_callback=None) -> List[Dict]:
        """Process multiple policies concurrently using ThreadPoolExecutor"""
        
        print(f"🚀 Processing {len(policy_numbers)} policies with {max_workers} threads...")
        start_time = time.time()
        
        results = []
        successful = 0
        failed = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_policy = {
                executor.submit(self.process_policy, policy): policy 
                for policy in policy_numbers
            }
            
            # Collect results as they complete
            for i, future in enumerate(future_to_policy):
                policy = future_to_policy[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        successful += 1
                        company = result.get('applicant_company', 'N/A')
                        status = result.get('status', 'N/A')
                        print(f"  ✅ {i+1}/{len(policy_numbers)}: {policy} - {company} ({status})")
                    else:
                        failed += 1
                        print(f"  ❌ {i+1}/{len(policy_numbers)}: {policy} - Not found")
                    
                    # Call progress callback if provided
                    if progress_callback:
                        progress_callback(i + 1, len(policy_numbers), successful, failed)
                        
                except Exception as e:
                    failed += 1
                    print(f"  ❌ {i+1}/{len(policy_numbers)}: {policy} - Error: {e}")
                    if progress_callback:
                        progress_callback(i + 1, len(policy_numbers), successful, failed)
        
        elapsed = time.time() - start_time
        print(f"\n🎯 Completed: {successful}/{len(policy_numbers)} policies in {elapsed:.2f}s")
        print(f"📊 Average: {elapsed/len(policy_numbers):.2f}s per policy")
        print(f"💡 That's {len(policy_numbers)*60/elapsed:.0f} policies per minute!")
        
        return results
    
    def _extract_search_results_data(self, html: str, policy_number: str) -> Optional[Dict]:
        """Extract data from search results table based on actual HTML structure"""
        try:
            # Find the table row for this policy
            # Look for a row that contains the policy number (HTML uses single quotes!)
            row_pattern = rf"<tr[^>]*class='[^']*itemRow[^']*'[^>]*data-id='(\d+)'[^>]*>.*?{re.escape(policy_number)}.*?</tr>"
            row_match = re.search(row_pattern, html, re.DOTALL)
            
            if not row_match:
                logging.warning(f"No search results found for policy {policy_number}")
                return None
            
            app_id = row_match.group(1)
            row_html = row_match.group(0)
            
            # Extract data from table columns based on actual structure
            # [0]Empty, [1]App ID, [2]Policy, [3]Status, [4]Applicant Company, [5]State, [6]Program, [7]Total Cost, [8]Effective Date
            td_pattern = r'<td[^>]*>(.*?)</td>'
            cells = re.findall(td_pattern, row_html, re.DOTALL)
            
            # Initialize data with what we know
            data = {
                'policy_number': policy_number,
                'app_id': app_id,
                'status': '',
                'applicant_company': '',
                'state': '',
                'program': '',
                'total_cost': '',
                'effective_date': ''
            }
            
            # Extract data from table cells based on actual column structure
            if len(cells) >= 9:
                # [0]Empty, [1]App ID, [2]Policy, [3]Status, [4]Company, [5]State, [6]Program, [7]Cost, [8]Effective Date
                data['status'] = self._clean_cell_text(cells[3])
                data['applicant_company'] = self._clean_cell_text(cells[4])
                data['state'] = self._clean_cell_text(cells[5])
                data['program'] = self._clean_cell_text(cells[6])
                data['total_cost'] = self._clean_cell_text(cells[7])
                data['effective_date'] = self._clean_cell_text(cells[8])
            elif len(cells) >= 8:
                # Fallback for slightly different table structure
                data['status'] = self._clean_cell_text(cells[3])
                data['applicant_company'] = self._clean_cell_text(cells[4])
                data['state'] = self._clean_cell_text(cells[5])
                data['program'] = self._clean_cell_text(cells[6])
                data['total_cost'] = self._clean_cell_text(cells[7])
            
            logging.info(f"Extracted search data for {policy_number}: {data}")
            return data
            
        except Exception as e:
            logging.error(f"Error extracting search results for {policy_number}: {e}")
            return None

    def _clean_cell_text(self, cell_html: str) -> str:
        """Clean HTML from table cell and extract text"""
        # Remove HTML tags and clean up text
        text = re.sub(r'<[^>]+>', '', cell_html)
        text = text.replace('&nbsp;', ' ')
        # Remove extra whitespace and newlines
        text = ' '.join(text.split())
        return text.strip()

    def _parse_detail_page_html(self, html: str) -> Dict:
        """Parse detail page for expiration and cancellation dates (search results gives us effective date)"""
        details = {}
        
        try:
            # Extract cancellation date if present (same as original scraper)
            cancellation_pattern = r'Cancellation Date:\s*</dt>\s*<dd[^>]*>\s*(\d{2}/\d{2}/\d{4})'
            cancellation_match = re.search(cancellation_pattern, html, re.DOTALL)
            if cancellation_match:
                details['cancellation_date'] = cancellation_match.group(1).strip()
                logging.info(f"Found cancellation date: {details['cancellation_date']}")
            else:
                # Alternative pattern for different HTML structures
                alt_cancellation_pattern = r'Cancellation Date:\s*</dt>\s*<dd[^>]*>([^<]+)</dd>'
                alt_match = re.search(alt_cancellation_pattern, html, re.DOTALL)
                if alt_match:
                    cancellation_text = alt_match.group(1).strip()
                    date_in_text = re.search(r'(\d{2}/\d{2}/\d{4})', cancellation_text)
                    if date_in_text:
                        details['cancellation_date'] = date_in_text.group(1)
                        logging.info(f"Found cancellation date (alt): {details['cancellation_date']}")
            
            # Extract policy term dates for expiration date (we already have effective from search results)
            # Method 1: Primary regex - Policy Term with date range pattern
            date_pattern = r'Policy Term:.*?(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})'
            match = re.search(date_pattern, html, re.DOTALL)
            if match:
                # We prefer the more detailed effective/expiration dates from detail page over search results
                details['effective_date'] = match.group(1).strip()
                details['expiration_date'] = match.group(2).strip()
                logging.info(f"Found policy term (method 1): {details['effective_date']} - {details['expiration_date']}")
                return details
            
            # Method 2: Alternative HTML structure regex
            alt_pattern = r'<dt[^>]*>Policy Term:</dt>\s*<dd[^>]*>([^<]+)</dd>'
            match = re.search(alt_pattern, html, re.DOTALL)
            if match:
                term_text = match.group(1).strip()
                logging.info(f"Found policy term text (method 2): {term_text}")
                dates = [date.strip() for date in term_text.split('-')]
                if len(dates) == 2:
                    details['effective_date'] = dates[0].strip()
                    details['expiration_date'] = dates[1].strip()
                    logging.info(f"Parsed dates: {details['effective_date']} - {details['expiration_date']}")
                    return details
            
            # Method 3: General date range pattern search
            general_date_pattern = r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})'
            matches = re.findall(general_date_pattern, html)
            if matches:
                logging.info(f"Found {len(matches)} date ranges in detail page")
                # Take the first reasonable match for policy terms
                for i, match in enumerate(matches):
                    try:
                        from datetime import datetime
                        start_date = datetime.strptime(match[0], '%m/%d/%Y')
                        end_date = datetime.strptime(match[1], '%m/%d/%Y')
                        
                        # Basic validation for policy terms
                        current_year = datetime.now().year
                        if (start_date.year >= current_year - 1 and 
                            end_date.year <= current_year + 2 and 
                            end_date > start_date):
                            details['effective_date'] = match[0]
                            details['expiration_date'] = match[1]
                            logging.info(f"Found valid policy term (method 3): {details['effective_date']} - {details['expiration_date']}")
                            return details
                    except Exception as date_error:
                        logging.warning(f"Date validation failed for match {i+1}: {date_error}")
                        continue
            
            # If we didn't find expiration date, at least return what we found
            if not details.get('expiration_date'):
                logging.warning("Could not find expiration date in detail page")
            
            return details
            
        except Exception as e:
            logging.error(f"Error parsing detail page: {e}")
            return details

# Example usage - almost identical to your MechanicalSoup script!
async def main():
    """Demo showing how this is almost identical to your MechanicalSoup workflow"""
    
    load_dotenv()
    username = os.getenv('ISC_USERNAME')
    password = os.getenv('ISC_PASSWORD')
    
    print("🔧 MechanicalSoup-style workflow with requests + ThreadPoolExecutor:")
    print("   ✅ Login once with Playwright (handles complex auth)")
    print("   ✅ Extract cookies to requests session")
    print("   ✅ Use requests.get() and requests.post() for everything else")
    print("   ✅ Parse HTML with regex (same as your original script)")
    print("   🚀 NEW: ThreadPoolExecutor for concurrent processing\n")
    
    # Initialize the hybrid client
    client = ISCRequestsHybrid(username, password)
    
    # Login (one-time browser usage)
    print("🔐 Logging in with Playwright...")
    if not await client.login():
        print("❌ Login failed")
        return
    
    print("✅ Login successful! Now using pure requests...\n")
    
    # Test policies
    test_policies = ['SCB-GL-000077835', 'SCB-GL-000077888', 'SCB-GL-000077925', 'SCB-GL-000078314']
    
    # Method 1: Sequential (like your original MechanicalSoup script)
    print("📋 Method 1: Sequential Processing (Original MechanicalSoup style)")
    sequential_start = time.time()
    
    applications = []
    for i, policy in enumerate(test_policies):
        print(f"  {i+1}. Processing {policy}...")
        
        # Process policy with new hybrid method
        application = client.process_policy(policy)
        
        if application:
            applications.append(application)
            company = application.get('applicant_company', 'N/A')
            status = application.get('status', 'N/A')
            print(f"    ✅ Found: {company} ({status})")
        else:
            print(f"    ❌ Not found")
    
    sequential_time = time.time() - sequential_start
    print(f"\n📊 Sequential: {len(applications)} policies in {sequential_time:.2f}s\n")
    
    # Method 2: Concurrent with ThreadPoolExecutor 🚀
    print("🚀 Method 2: Concurrent Processing with ThreadPoolExecutor")
    concurrent_applications = client.process_policies_concurrent(test_policies, max_workers=6)
    
    # Show comparison with your original code
    print("\n" + "="*60)
    print("COMPARISON WITH YOUR ORIGINAL MECHANICALSOUP CODE:")
    print("="*60)
    print("Original MechanicalSoup (Sequential):")
    print("  for app in apps:")
    print("    browser.open(search_url)")
    print("    browser.submit_selected()")
    print("    page = browser.get(detail_url)")
    print("    data = extract_data(page)")
    print("")
    print("New Requests + ThreadPoolExecutor (Concurrent):")
    print("  client = ISCRequestsHybrid(user, pass)")
    print("  await client.login()  # One-time Playwright auth")
    print("  results = client.process_policies_concurrent(policies, workers=10)")
    print("  # Multiple HTTP requests happen simultaneously! 🚀")
    
    if concurrent_applications:
        print(f"\n📋 Sample result with all required data points:")
        sample = concurrent_applications[0]
        
        # Show the key data points in order
        key_fields = ['policy_number', 'app_id', 'status', 'applicant_company', 'state', 
                     'program', 'total_cost', 'effective_date', 'expiration_date', 'cancellation_date']
        
        for field in key_fields:
            value = sample.get(field, 'N/A')
            print(f"   {field}: {value}")
        
        print(f"\n✅ Data extraction summary:")
        print(f"   📊 From search results: policy_number, app_id, status, applicant_company, state, program, total_cost, effective_date")
        print(f"   📄 From detail page: expiration_date, cancellation_date (when present)")
        print(f"   🚀 Much faster since we get most data from search results table!")

if __name__ == "__main__":
    asyncio.run(main()) 