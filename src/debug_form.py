import asyncio
import logging
from scraper import ISCScraper
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def debug_and_save_response():
    """Authenticate, make request, save response to temp file"""
    
    load_dotenv()
    username = os.getenv('ISC_USERNAME')
    password = os.getenv('ISC_PASSWORD')
    
    if not username or not password:
        print("Please set ISC_USERNAME and ISC_PASSWORD in .env file")
        return
    
    # Test with a policy from your CSV
    test_policy = 'SCB-GL-000078314'
    
    print(f"🔍 Debugging GET request for policy: {test_policy}")
    print("=" * 60)
    
    # Initialize scraper
    scraper = ISCScraper(username, password, headless=True)
    await scraper.initialize()
    
    # Login
    print("🔐 Logging in...")
    if not await scraper.login():
        print("❌ Login failed")
        await scraper.close()
        return
    print("✅ Login successful!")
    
    # Make the GET request
    print(f"🚀 Making GET request for {test_policy}...")
    
    search_url = "https://isc.onlinemga.com/amp/search/advancedsearch"
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
        'policy_number': test_policy,
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
    
    response = await scraper.page.request.get(search_url, params=params)
    
    if response.status == 200:
        content = await response.text()
        
        # Save response to temp file
        temp_file = f"debug_response_{test_policy.replace('-', '_')}.html"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📁 Response saved to: {temp_file}")
        print(f"📊 Response length: {len(content)} characters")
        print(f"🔍 Contains policy number: {test_policy in content}")
        
        # Quick check for common patterns
        import re
        data_ids = re.findall(r'data-id="(\d+)"', content)
        print(f"🔢 Found {len(data_ids)} data-id attributes")
        
        if "login" in content.lower():
            print("⚠️ Response contains 'login' - might be redirected")
        
        if "no results" in content.lower():
            print("⚠️ Response contains 'no results'")
            
    else:
        print(f"❌ HTTP error: {response.status}")
    
    await scraper.close()
    print(f"\n✅ Debug complete! Check {temp_file} for full response")

if __name__ == "__main__":
    asyncio.run(debug_and_save_response()) 