import asyncio
import logging
from playwright.async_api import async_playwright
import pandas as pd
from typing import List, Dict, Optional
import re

class ISCScraper:
    def __init__(self, username: str, password: str, headless: bool = True):
        self.username = username
        self.password = password
        self.headless = headless
        self.browser = None
        self.page = None
        
    async def initialize(self):
        """Initialize browser and create page"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-dev-shm-usage']  # Better for Windows
            )
            self.page = await self.browser.new_page()
            # Set reasonable timeouts
            self.page.set_default_timeout(30000)  # 30 seconds
            self.page.set_default_navigation_timeout(30000)
        except Exception as e:
            logging.error(f"Failed to initialize browser: {e}")
            await self.close()
            raise
    

        
    async def login(self) -> bool:
        """Login to ISC platform"""
        try:
            await self.page.goto("https://isc.onlinemga.com/amp/login")
            await self.page.fill('input[name="username"]', self.username)
            await self.page.fill('input[name="password"]', self.password)
            await self.page.click('button.btn.btn-lg.btn-block.btn-default[type="submit"]')
            
            # Wait for redirect and validate
            await self.page.wait_for_load_state("networkidle")
            return "login" not in self.page.url
            
        except Exception as e:
            logging.error(f"Login failed: {e}")
            return False

    async def search_policy(self, policy_number: str) -> Optional[Dict]:
        """Search for a policy by number and extract data from search results"""
        max_retries = 2
        row = None
        
        for attempt in range(max_retries + 1):
            try:
                # Navigate to search page with timeout
                await self.page.goto("https://isc.onlinemga.com/amp/search/advancedsearch", timeout=30000)
                await self.page.fill('input[name="policy_number"]', policy_number)
                await self.page.click('button.submitAdvancedSearch.btn.btn-green.btn-success')
                
                # Wait for results
                await self.page.wait_for_load_state("networkidle", timeout=30000)
                
                # Wait for and find the matching row
                row = await self.page.query_selector(f'tr.itemRow:has-text("{policy_number}")')
                if not row:
                    logging.warning(f"No results found for policy {policy_number}")
                    return None
                
                break  # Success, exit retry loop
                
            except Exception as e:
                if attempt < max_retries:
                    logging.warning(f"Attempt {attempt + 1} failed for {policy_number}: {e}. Retrying...")
                    await asyncio.sleep(1)  # Brief delay before retry
                    continue
                else:
                    logging.error(f"All attempts failed for policy {policy_number}: {e}")
                    return None
        
        try:
            # Extract data from the row
            app_id = await row.get_attribute('data-id')
            status = await row.query_selector('td:nth-child(4)')
            status_text = await status.text_content() if status else ""
            
            company = await row.query_selector('td:nth-child(5)')
            company_text = await company.text_content() if company else ""
            
            state = await row.query_selector('td:nth-child(6)')
            state_text = await state.text_content() if state else ""
            
            program = await row.query_selector('td:nth-child(7)')
            program_text = await program.text_content() if program else ""
            
            cost = await row.query_selector('td:nth-child(8)')
            cost_text = await cost.text_content() if cost else ""
            
            # Navigate directly to the detail page using app_id
            detail_url = f"https://isc.onlinemga.com/amp/detail/view/{app_id}"
            logging.info(f"Navigating to detail page: {detail_url}")
            await self.page.goto(detail_url)
            await self.page.wait_for_load_state("networkidle")
            
            # Verify we're on the detail page
            current_url = self.page.url
            logging.info(f"Current URL after navigation: {current_url}")
            
            if "detail/view" not in current_url:
                logging.warning(f"Failed to navigate to detail page. Current URL: {current_url}")
                details = {}
            else:
                # Extract additional details from the detail page
                details = await self.extract_policy_details()
            
            # Combine search results with detail page data
            return {
                'policy_number': policy_number,
                'app_id': app_id,
                'status': status_text.strip(),
                'applicant_company': company_text.strip(),
                'state': state_text.strip(),
                'program': program_text.strip(),
                'total_cost': cost_text.strip(),
                'effective_date': details.get('effective_date', ''),
                'expiration_date': details.get('expiration_date', ''),
                'cancellation_date': details.get('cancellation_date', '')
            }
            
        except Exception as e:
            logging.error(f"Search failed for policy {policy_number}: {e}")
            return None

    async def extract_policy_details(self) -> Dict:
        """Extract detailed policy information from the detail page"""
        try:
            details = {}
            
            # Wait for page to be fully loaded - be more patient
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(2000)  # Additional wait for dynamic content
            
            # Get the full page content
            page_content = await self.page.content()
            logging.info(f"Page content length: {len(page_content)} characters")
            
            # Extract cancellation date if present (check for cancelled policies)
            cancellation_pattern = r'Cancellation Date:\s*</dt>\s*<dd[^>]*>\s*(\d{2}/\d{2}/\d{4})'
            cancellation_match = re.search(cancellation_pattern, page_content, re.DOTALL)
            if cancellation_match:
                details['cancellation_date'] = cancellation_match.group(1).strip()
                logging.info(f"Extracted cancellation date: {details['cancellation_date']}")
            else:
                # Alternative pattern for different HTML structures
                alt_cancellation_pattern = r'Cancellation Date:\s*</dt>\s*<dd[^>]*>([^<]+)</dd>'
                alt_match = re.search(alt_cancellation_pattern, page_content, re.DOTALL)
                if alt_match:
                    cancellation_text = alt_match.group(1).strip()
                    # Extract date from the text (in case there's extra whitespace or formatting)
                    date_in_text = re.search(r'(\d{2}/\d{2}/\d{4})', cancellation_text)
                    if date_in_text:
                        details['cancellation_date'] = date_in_text.group(1)
                        logging.info(f"Extracted cancellation date (alternative): {details['cancellation_date']}")
            
            # Method 1: Primary regex - Policy Term with date pattern (PROVEN TO WORK)
            date_pattern = r'Policy Term:.*?(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})'
            match = re.search(date_pattern, page_content, re.DOTALL)
            if match:
                details['effective_date'] = match.group(1).strip()
                details['expiration_date'] = match.group(2).strip()
                logging.info(f"Method 1 - Extracted dates via Policy Term regex: {details}")
                return details
            
            # Method 2: Alternative HTML structure regex (PROVEN TO WORK)
            alt_pattern = r'<dt[^>]*>Policy Term:</dt>\s*<dd[^>]*>([^<]+)</dd>'
            match = re.search(alt_pattern, page_content, re.DOTALL)
            if match:
                term_text = match.group(1).strip()
                logging.info(f"Method 2 - Found policy term text: {term_text}")
                
                # Extract dates from the text
                dates = [date.strip() for date in term_text.split('-')]
                if len(dates) == 2:
                    details['effective_date'] = dates[0].strip()
                    details['expiration_date'] = dates[1].strip()
                    logging.info(f"Method 2 - Extracted dates from HTML: {details}")
                    return details
            
            # Method 3: General date pattern search (PROVEN TO WORK)
            general_date_pattern = r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})'
            matches = re.findall(general_date_pattern, page_content)
            if matches:
                logging.info(f"Method 3 - Found {len(matches)} date ranges")
                # Take the first reasonable match
                for i, match in enumerate(matches):
                    try:
                        from datetime import datetime
                        start_date = datetime.strptime(match[0], '%m/%d/%Y')
                        end_date = datetime.strptime(match[1], '%m/%d/%Y')
                        
                        # Basic validation
                        current_year = datetime.now().year
                        if (start_date.year >= current_year - 1 and 
                            end_date.year <= current_year + 2 and 
                            end_date > start_date):
                            details['effective_date'] = match[0]
                            details['expiration_date'] = match[1]
                            logging.info(f"Method 3 - Extracted dates via general pattern (match {i+1}): {details}")
                            return details
                    except Exception as date_error:
                        logging.warning(f"Date validation failed for match {i+1}: {date_error}")
                        continue
            
            # Debug: Log if we find Policy Term text at all
            if 'Policy Term:' in page_content:
                start_pos = page_content.find('Policy Term:')
                context = page_content[start_pos:start_pos+200]
                logging.warning(f"Found 'Policy Term:' in content but couldn't extract dates. Context: {context[:100]}...")
            else:
                logging.warning("'Policy Term:' text not found in page content at all")
            
            logging.warning("Could not extract policy term dates with any method")
            return details
            
        except Exception as e:
            logging.error(f"Detail extraction failed: {e}")
            return {}

    async def search_policy_with_page(self, policy_number: str, page) -> Optional[Dict]:
        """Search for a policy using a specific page (for concurrent operations)"""
        max_retries = 2
        row = None
        
        for attempt in range(max_retries + 1):
            try:
                # Navigate to search page with longer timeout for concurrent operations
                await page.goto("https://isc.onlinemga.com/amp/search/advancedsearch", timeout=30000)
                await page.fill('input[name="policy_number"]', policy_number)
                await page.click('button.submitAdvancedSearch.btn.btn-green.btn-success')
                
                # Wait for results with longer timeout for concurrent operations
                await page.wait_for_load_state("networkidle", timeout=20000)
                
                # Wait for and find the matching row
                row = await page.query_selector(f'tr.itemRow:has-text("{policy_number}")')
                if not row:
                    logging.warning(f"No results found for policy {policy_number}")
                    return None
                
                break  # Success, exit retry loop
                
            except Exception as e:
                if attempt < max_retries:
                    logging.warning(f"Attempt {attempt + 1} failed for {policy_number}: {e}. Retrying...")
                    await asyncio.sleep(3)  # Longer delay before retry for concurrent operations
                    continue
                else:
                    logging.error(f"All attempts failed for policy {policy_number}: {e}")
                    return None
        
        try:
            # Extract data from the row
            app_id = await row.get_attribute('data-id')
            status = await row.query_selector('td:nth-child(4)')
            status_text = await status.text_content() if status else ""
            
            company = await row.query_selector('td:nth-child(5)')
            company_text = await company.text_content() if company else ""
            
            state = await row.query_selector('td:nth-child(6)')
            state_text = await state.text_content() if state else ""
            
            program = await row.query_selector('td:nth-child(7)')
            program_text = await program.text_content() if program else ""
            
            cost = await row.query_selector('td:nth-child(8)')
            cost_text = await cost.text_content() if cost else ""
            
            # Navigate directly to the detail page using app_id
            detail_url = f"https://isc.onlinemga.com/amp/detail/view/{app_id}"
            logging.info(f"Navigating to detail page: {detail_url}")
            await page.goto(detail_url)
            await page.wait_for_load_state("networkidle")
            
            # Verify we're on the detail page
            current_url = page.url
            logging.info(f"Current URL after navigation: {current_url}")
            
            if "detail/view" not in current_url:
                logging.warning(f"Failed to navigate to detail page. Current URL: {current_url}")
                details = {}
            else:
                # Extract additional details from the detail page
                details = await self.extract_policy_details_from_page(page)
            
            # Combine search results with detail page data
            return {
                'policy_number': policy_number,
                'app_id': app_id,
                'status': status_text.strip(),
                'applicant_company': company_text.strip(),
                'state': state_text.strip(),
                'program': program_text.strip(),
                'total_cost': cost_text.strip(),
                'effective_date': details.get('effective_date', ''),
                'expiration_date': details.get('expiration_date', ''),
                'cancellation_date': details.get('cancellation_date', '')
            }
            
        except Exception as e:
            logging.error(f"Search failed for policy {policy_number}: {e}")
            return None

    async def extract_policy_details_from_page(self, page) -> Dict:
        """Extract detailed policy information from a specific page (for concurrent operations)"""
        try:
            details = {}
            
            # Wait for page to be fully loaded - be more patient
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(2000)  # Additional wait for dynamic content
            
            # Get the full page content
            page_content = await page.content()
            logging.info(f"Page content length: {len(page_content)} characters")
            
            # Extract cancellation date if present (check for cancelled policies)
            cancellation_pattern = r'Cancellation Date:\s*</dt>\s*<dd[^>]*>\s*(\d{2}/\d{2}/\d{4})'
            cancellation_match = re.search(cancellation_pattern, page_content, re.DOTALL)
            if cancellation_match:
                details['cancellation_date'] = cancellation_match.group(1).strip()
                logging.info(f"Extracted cancellation date: {details['cancellation_date']}")
            else:
                # Alternative pattern for different HTML structures
                alt_cancellation_pattern = r'Cancellation Date:\s*</dt>\s*<dd[^>]*>([^<]+)</dd>'
                alt_match = re.search(alt_cancellation_pattern, page_content, re.DOTALL)
                if alt_match:
                    cancellation_text = alt_match.group(1).strip()
                    # Extract date from the text (in case there's extra whitespace or formatting)
                    date_in_text = re.search(r'(\d{2}/\d{2}/\d{4})', cancellation_text)
                    if date_in_text:
                        details['cancellation_date'] = date_in_text.group(1)
                        logging.info(f"Extracted cancellation date (alternative): {details['cancellation_date']}")
            
            # Method 1: Primary regex - Policy Term with date pattern (PROVEN TO WORK)
            date_pattern = r'Policy Term:.*?(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})'
            match = re.search(date_pattern, page_content, re.DOTALL)
            if match:
                details['effective_date'] = match.group(1).strip()
                details['expiration_date'] = match.group(2).strip()
                logging.info(f"Method 1 - Extracted dates via Policy Term regex: {details}")
                return details
            
            # Method 2: Alternative HTML structure regex (PROVEN TO WORK)
            alt_pattern = r'<dt[^>]*>Policy Term:</dt>\s*<dd[^>]*>([^<]+)</dd>'
            match = re.search(alt_pattern, page_content, re.DOTALL)
            if match:
                term_text = match.group(1).strip()
                logging.info(f"Method 2 - Found policy term text: {term_text}")
                
                # Extract dates from the text
                dates = [date.strip() for date in term_text.split('-')]
                if len(dates) == 2:
                    details['effective_date'] = dates[0].strip()
                    details['expiration_date'] = dates[1].strip()
                    logging.info(f"Method 2 - Extracted dates from HTML: {details}")
                    return details
            
            # Method 3: General date pattern search (PROVEN TO WORK)
            general_date_pattern = r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})'
            matches = re.findall(general_date_pattern, page_content)
            if matches:
                logging.info(f"Method 3 - Found {len(matches)} date ranges")
                # Take the first reasonable match
                for i, match in enumerate(matches):
                    try:
                        from datetime import datetime
                        start_date = datetime.strptime(match[0], '%m/%d/%Y')
                        end_date = datetime.strptime(match[1], '%m/%d/%Y')
                        
                        # Basic validation
                        current_year = datetime.now().year
                        if (start_date.year >= current_year - 1 and 
                            end_date.year <= current_year + 2 and 
                            end_date > start_date):
                            details['effective_date'] = match[0]
                            details['expiration_date'] = match[1]
                            logging.info(f"Method 3 - Extracted dates via general pattern (match {i+1}): {details}")
                            return details
                    except Exception as date_error:
                        logging.warning(f"Date validation failed for match {i+1}: {date_error}")
                        continue
            
            # Debug: Log if we find Policy Term text at all
            if 'Policy Term:' in page_content:
                start_pos = page_content.find('Policy Term:')
                context = page_content[start_pos:start_pos+200]
                logging.warning(f"Found 'Policy Term:' in content but couldn't extract dates. Context: {context[:100]}...")
            else:
                logging.warning("'Policy Term:' text not found in page content at all")
            
            logging.warning("Could not extract policy term dates with any method")
            return details
            
        except Exception as e:
            logging.error(f"Detail extraction failed: {e}")
            return {}

    async def close(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
            # Force cleanup if needed
            if self.browser:
                try:
                    await self.browser.close()
                except:
                    pass
                self.browser = None
            if hasattr(self, 'playwright') and self.playwright:
                try:
                    await self.playwright.stop()
                except:
                    pass
                self.playwright = None