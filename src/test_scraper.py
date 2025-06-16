import asyncio
import os
import logging
from dotenv import load_dotenv
from scraper import ISCScraper
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment
    username = os.getenv('ISC_USERNAME')
    password = os.getenv('ISC_PASSWORD')
    
    if not username or not password:
        print("Please set ISC_USERNAME and ISC_PASSWORD in .env file")
        return
    
    # Initialize scraper
    scraper = ISCScraper(username, password, headless=False)
    await scraper.initialize()
    
    # Login
    if not await scraper.login():
        print("Login failed")
        await scraper.close()
        return
    
    # Test policy numbers
    policy_numbers = [
        'ISCPC04000058472',
        'ISCPC04000058215',
        'ISCPC04000058337',
        'SCB-GL-000092901'  # Cancelled policy
    ]
    
    results = []
    for policy_number in policy_numbers:
        print(f"Searching for policy {policy_number}...")
        result = await scraper.search_policy(policy_number)
        if result:
            results.append(result)
            print(f"Found policy: {result['applicant_company']}")
        else:
            print(f"No results found for {policy_number}")
    
    # Save results to CSV
    if results:
        df = pd.DataFrame(results)
        df.to_csv('data/output/policy_results.csv', index=False)
        print(f"\nResults saved to data/output/policy_results.csv")
    
    await scraper.close()

if __name__ == "__main__":
    asyncio.run(main()) 