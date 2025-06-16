import asyncio
import time
import logging
from scraper import ISCScraper
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def speed_comparison_test():
    """Compare speed between fast HTTP method vs browser method"""
    
    # Load environment variables
    load_dotenv()
    
    username = os.getenv('ISC_USERNAME')
    password = os.getenv('ISC_PASSWORD')
    
    if not username or not password:
        print("Please set ISC_USERNAME and ISC_PASSWORD in .env file")
        return
    
    # Test policy numbers (replace with actual ones from your system)
    test_policies = [
        'SCB-GL-000077835',
        'SCB-GL-000077888', 
        'SCB-GL-000077925',
        'SCB-GL-000077999',
        'SCB-GL-000078185'
    ]
    
    # Initialize scraper
    scraper = ISCScraper(username, password, headless=True)
    await scraper.initialize()
    
    # Login once
    print("🔐 Logging in...")
    if not await scraper.login():
        print("❌ Login failed")
        await scraper.close()
        return
    
    print("✅ Login successful!\n")
    
    # Test fast method (similar to MechanicalSoup)
    print("🚀 Testing FAST HTTP method (like MechanicalSoup)...")
    fast_start = time.time()
    fast_results = []
    
    for policy in test_policies:
        print(f"  📋 Processing {policy}...")
        
        # Use the fast method directly
        app_id = await scraper.search_by_policy_fast(policy)
        if app_id:
            result = await scraper.get_application_fast(app_id)
            if result:
                fast_results.append(result)
                print(f"    ✅ Found: {result.get('insured_company_name', 'N/A')}")
            else:
                print(f"    ⚠️ Found app_id but couldn't get details")
        else:
            print(f"    ❌ Not found")
    
    fast_time = time.time() - fast_start
    
    print(f"\n⚡ Fast method: {len(fast_results)} policies in {fast_time:.2f} seconds")
    print(f"   📊 Average: {fast_time/len(test_policies):.2f} seconds per policy\n")
    
    # Test browser fallback method 
    print("🐌 Testing BROWSER fallback method...")
    browser_start = time.time()
    browser_results = []
    
    for policy in test_policies:
        print(f"  📋 Processing {policy}...")
        result = await scraper.search_policy_browser_fallback(policy)
        if result:
            browser_results.append(result)
            print(f"    ✅ Found: {result.get('applicant_company', 'N/A')}")
        else:
            print(f"    ❌ Not found")
    
    browser_time = time.time() - browser_start
    
    print(f"\n🐌 Browser method: {len(browser_results)} policies in {browser_time:.2f} seconds")
    print(f"   📊 Average: {browser_time/len(test_policies):.2f} seconds per policy\n")
    
    # Comparison
    if fast_time > 0:
        speedup = browser_time / fast_time
        print(f"🎯 SPEED IMPROVEMENT: {speedup:.1f}x faster with HTTP method!")
        print(f"💡 For 100 policies, this saves ~{(browser_time - fast_time) * 20:.0f} seconds")
    
    await scraper.close()
    
    # Show sample results
    if fast_results:
        print("\n📋 Sample result from fast method:")
        sample = fast_results[0]
        for key, value in sample.items():
            print(f"   {key}: {value}")

async def mechanicalsoup_style_workflow():
    """Demonstrate the MechanicalSoup-style workflow with Playwright"""
    
    load_dotenv()
    username = os.getenv('ISC_USERNAME')
    password = os.getenv('ISC_PASSWORD')
    
    print("🔧 MechanicalSoup-style workflow with Playwright:")
    print("   1. Login with browser (one-time)")
    print("   2. Switch to fast HTTP requests for data")
    print("   3. Process multiple policies quickly\n")
    
    scraper = ISCScraper(username, password, headless=True)
    await scraper.initialize()
    
    # Step 1: Login (browser required)
    print("🔐 Step 1: Browser login...")
    start = time.time()
    if not await scraper.login():
        print("❌ Login failed")
        return
    login_time = time.time() - start
    print(f"✅ Logged in ({login_time:.2f}s)\n")
    
    # Step 2: Fast data processing (HTTP only)
    print("⚡ Step 2: Fast HTTP data processing...")
    policies = ['SCB-GL-000077835', 'SCB-GL-000077888', 'SCB-GL-000077925']
    
    results = []
    for i, policy in enumerate(policies):
        start = time.time()
        
        # This is just like mechanicalsoup.browser.get(url)
        app_id = await scraper.search_by_policy_fast(policy)
        if app_id:
            result = await scraper.get_application_fast(app_id)
            if result:
                results.append(result)
        
        elapsed = time.time() - start
        print(f"   {i+1}. {policy}: {elapsed:.2f}s")
    
    print(f"\n🎯 Processed {len(policies)} policies with HTTP requests only!")
    print(f"💡 This is the same pattern as your MechanicalSoup script")
    
    await scraper.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 ISC Scraper Speed Test")
    print("=" * 60)
    
    # Run both tests
    asyncio.run(speed_comparison_test())
    print("\n" + "=" * 60)
    asyncio.run(mechanicalsoup_style_workflow()) 