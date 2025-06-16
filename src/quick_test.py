import asyncio
import logging
from scraper import ISCScraper
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_fast_method():
    """Quick test of the fixed fast method"""
    
    load_dotenv()
    username = os.getenv('ISC_USERNAME')
    password = os.getenv('ISC_PASSWORD')
    
    scraper = ISCScraper(username, password, headless=True)
    await scraper.initialize()
    
    if not await scraper.login():
        print("❌ Login failed")
        return
    
    print("✅ Testing simplified fast method...")
    
    # Test the policy we know works
    test_policy = 'SCB-GL-000078314'
    app_id = await scraper.search_by_policy_fast(test_policy)
    
    if app_id:
        print(f"🚀 SUCCESS! Fast method found app_id: {app_id}")
        
        # Test getting full data
        result = await scraper.get_application_fast(app_id)
        if result:
            print(f"✅ Got company: {result.get('insured_company_name', 'N/A')}")
        else:
            print("⚠️ App_id found but couldn't get details")
    else:
        print("❌ Fast method still failed")
    
    await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_fast_method()) 