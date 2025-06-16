import asyncio
import time
import pandas as pd
import logging
from pathlib import Path
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.scraper import ISCScraper
from src.ui import process_data, process_data_concurrent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_test.log'),
        logging.StreamHandler()
    ]
)

class DummyProgressBar:
    def progress(self, value):
        pass

class DummyStatusText:
    def text(self, value):
        pass

async def run_performance_test(username: str, password: str, test_policies: list, batch_size: int = 20, concurrency_limit: int = 4):
    """Run performance test comparing sequential vs concurrent processing"""
    
    # Initialize scraper
    scraper = ISCScraper(username=username, password=password, headless=True)
    await scraper.initialize()
    
    if not await scraper.login():
        logging.error("Login failed. Cannot proceed with tests.")
        await scraper.close()
        return
    
    # Create test dataframe
    df = pd.DataFrame({'policy_number': test_policies})
    
    # Test sequential processing
    logging.info("Starting sequential processing test...")
    start_time = time.time()
    results_seq = await process_data(
        scraper, 
        df, 
        DummyProgressBar(), 
        DummyStatusText(), 
        None, 
        batch_size
    )
    seq_time = time.time() - start_time
    
    # Reset scraper for concurrent test
    await scraper.close()
    scraper = ISCScraper(username=username, password=password, headless=True)
    await scraper.initialize()
    await scraper.login()
    
    # Test concurrent processing
    logging.info("Starting concurrent processing test...")
    start_time = time.time()
    results_conc = await process_data_concurrent(
        scraper, 
        df, 
        DummyProgressBar(), 
        DummyStatusText(), 
        None, 
        batch_size, 
        concurrency_limit
    )
    conc_time = time.time() - start_time
    
    # Cleanup
    await scraper.close()
    
    # Calculate metrics
    total_policies = len(test_policies)
    seq_success = len(results_seq) if results_seq else 0
    conc_success = len(results_conc) if results_conc else 0
    
    metrics = {
        'sequential': {
            'total_time': seq_time,
            'avg_time_per_policy': seq_time / total_policies,
            'success_rate': (seq_success / total_policies) * 100,
            'success_count': seq_success,
            'error_count': total_policies - seq_success
        },
        'concurrent': {
            'total_time': conc_time,
            'avg_time_per_policy': conc_time / total_policies,
            'success_rate': (conc_success / total_policies) * 100,
            'success_count': conc_success,
            'error_count': total_policies - conc_success
        }
    }
    
    # Calculate speedup
    speedup = seq_time / conc_time if conc_time > 0 else 0
    
    # Log results
    logging.info("\n=== Performance Test Results ===")
    logging.info(f"Total policies tested: {total_policies}")
    logging.info(f"\nSequential Processing:")
    logging.info(f"Total time: {metrics['sequential']['total_time']:.2f} seconds")
    logging.info(f"Average time per policy: {metrics['sequential']['avg_time_per_policy']:.2f} seconds")
    logging.info(f"Success rate: {metrics['sequential']['success_rate']:.1f}%")
    logging.info(f"Successful: {metrics['sequential']['success_count']}")
    logging.info(f"Failed: {metrics['sequential']['error_count']}")
    
    logging.info(f"\nConcurrent Processing:")
    logging.info(f"Total time: {metrics['concurrent']['total_time']:.2f} seconds")
    logging.info(f"Average time per policy: {metrics['concurrent']['avg_time_per_policy']:.2f} seconds")
    logging.info(f"Success rate: {metrics['concurrent']['success_rate']:.1f}%")
    logging.info(f"Successful: {metrics['concurrent']['success_count']}")
    logging.info(f"Failed: {metrics['concurrent']['error_count']}")
    
    logging.info(f"\nSpeedup (sequential/concurrent): {speedup:.2f}x")
    
    return metrics

async def main():
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    username = os.getenv('ISC_USERNAME')
    password = os.getenv('ISC_PASSWORD')
    
    if not username or not password:
        logging.error("Please set ISC_USERNAME and ISC_PASSWORD environment variables")
        return
    
    # Test with real policy numbers
    test_policies = [
        "SCB-GL-000077835",
        "SCB-GL-000077888",
        "SCB-GL-000077925",
        "SCB-GL-000077999",
        "SCB-GL-000078185"
    ]
    
    logging.info("Starting performance test with 5 real policies...")
    metrics = await run_performance_test(username, password, test_policies, batch_size=5, concurrency_limit=2)
    
    # Save results to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_df = pd.DataFrame({
        'mode': ['sequential', 'concurrent'],
        'total_time': [metrics['sequential']['total_time'], metrics['concurrent']['total_time']],
        'avg_time_per_policy': [metrics['sequential']['avg_time_per_policy'], metrics['concurrent']['avg_time_per_policy']],
        'success_rate': [metrics['sequential']['success_rate'], metrics['concurrent']['success_rate']],
        'success_count': [metrics['sequential']['success_count'], metrics['concurrent']['success_count']],
        'error_count': [metrics['sequential']['error_count'], metrics['concurrent']['error_count']]
    })
    
    results_df.to_csv(f'performance_test_results_{timestamp}.csv', index=False)
    logging.info(f"Results saved to performance_test_results_{timestamp}.csv")

if __name__ == "__main__":
    asyncio.run(main()) 