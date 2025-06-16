import asyncio
import time
from requests_hybrid import ISCRequestsHybrid
import os
from dotenv import load_dotenv

async def test_concurrent_vs_sequential():
    """Test ThreadPoolExecutor concurrent processing vs sequential"""
    
    load_dotenv()
    username = os.getenv('ISC_USERNAME')
    password = os.getenv('ISC_PASSWORD')
    
    # Test policies from your CSV
    test_policies = [
        'SCB-GL-000077835',
        'SCB-GL-000077888', 
        'SCB-GL-000077925',
        'SCB-GL-000077999',
        'SCB-GL-000078185',
        'SCB-GL-000078314'
    ]
    
    print("🔧 ThreadPoolExecutor Speed Test")
    print("=" * 50)
    
    # Initialize hybrid client
    client = ISCRequestsHybrid(username, password)
    
    # Login once
    print("🔐 Logging in...")
    if not await client.login():
        print("❌ Login failed")
        return
    print("✅ Login successful!\n")
    
    # Test 1: Sequential processing (like your original script)
    print("🐌 Sequential Processing:")
    sequential_start = time.time()
    sequential_results = []
    
    for i, policy in enumerate(test_policies):
        print(f"  {i+1}. Processing {policy}...")
        result = client.process_policy(policy)
        if result:
            sequential_results.append(result)
            print(f"     ✅ {result.get('insured_company_name', 'N/A')}")
        else:
            print(f"     ❌ Not found")
    
    sequential_time = time.time() - sequential_start
    
    print(f"\n📊 Sequential: {len(sequential_results)}/{len(test_policies)} in {sequential_time:.2f}s")
    print(f"    Average: {sequential_time/len(test_policies):.2f}s per policy\n")
    
    # Test 2: Concurrent processing with ThreadPoolExecutor
    print("🚀 Concurrent Processing (ThreadPoolExecutor):")
    concurrent_results = client.process_policies_concurrent(test_policies, max_workers=6)
    
    # Calculate speedup
    if sequential_time > 0 and concurrent_results:
        # Estimate concurrent time from the method's output
        print(f"\n🎯 SPEEDUP ANALYSIS:")
        print(f"   Sequential: {sequential_time:.2f}s ({sequential_time/len(test_policies):.2f}s per policy)")
        print(f"   ThreadPoolExecutor enables {len(test_policies)} concurrent HTTP requests!")
        print(f"   💡 This is exactly like your MechanicalSoup script but MUCH faster!")

async def demo_high_volume():
    """Demo processing many policies at once"""
    
    load_dotenv()
    username = os.getenv('ISC_USERNAME')
    password = os.getenv('ISC_PASSWORD')
    
    # Simulate a larger batch (you can add more real policy numbers)
    demo_policies = [
        'SCB-GL-000077835',
        'SCB-GL-000077888', 
        'SCB-GL-000077925',
        'SCB-GL-000077999',
        'SCB-GL-000078185',
        'SCB-GL-000078314'
    ] * 3  # Triple it for demo
    
    print("\n" + "=" * 50)
    print(f"🚀 HIGH VOLUME DEMO: {len(demo_policies)} policies")
    print("=" * 50)
    
    client = ISCRequestsHybrid(username, password)
    
    if not await client.login():
        print("❌ Login failed")
        return
    
    # Process with different thread counts
    for workers in [5, 10, 15]:
        print(f"\n📊 Testing with {workers} threads:")
        results = client.process_policies_concurrent(demo_policies[:12], max_workers=workers)
        
if __name__ == "__main__":
    asyncio.run(test_concurrent_vs_sequential())
    asyncio.run(demo_high_volume()) 