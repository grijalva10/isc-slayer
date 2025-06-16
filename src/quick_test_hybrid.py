import asyncio
from requests_hybrid import ISCRequestsHybrid
import os
from dotenv import load_dotenv

async def quick_test():
    load_dotenv()
    client = ISCRequestsHybrid(os.getenv('ISC_USERNAME'), os.getenv('ISC_PASSWORD'))
    
    print("🔐 Logging in...")
    await client.login()
    
    print("🔎 Testing policy extraction...")
    result = client.process_policy('SCB-GL-000078314')
    
    if result:
        print("🎯 SUCCESS! Extracted data:")
        for key, value in result.items():
            print(f"   {key}: {value}")
    else:
        print("❌ Failed to extract data")

if __name__ == "__main__":
    asyncio.run(quick_test()) 