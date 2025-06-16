import streamlit as st
import pandas as pd
import asyncio
import os
import logging
from pathlib import Path
import sys
import time
import platform
import random

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.scraper import ISCScraper
from src.utils import validate_csv_input, create_csv_template, merge_data, save_output_csv
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fun Mr. Robot–style status lines ⚡
HACK_MESSAGES = [
    "🛜 Connecting to ISC mainframe...",
    "🔐 Cracking sysadmin password hash...",
    "💾 Dumping database tables...",
    "📈 Accessing hidden Swiss bank records...",
    "🗝️ Escalating privileges...",
    "🛰️ Hijacking satellite uplink...",
    "💣 Planting logic bomb...",
    "👁️‍🗨️ Bypassing 2-factor authentication...",
    "📂 Leaking files to darknet...",
    "✅ Rootkit installed. All your data are belong to us."
]

async def process_data(scraper: ISCScraper, df: pd.DataFrame, progress_bar, status_text, hack_text, batch_size: int = 5):
    """Legacy sequential processing - kept for compatibility"""
    results = []
    total_rows = len(df)
    failed_policies = []
    
    for i in range(0, total_rows, batch_size):
        batch_end = min(i + batch_size, total_rows)
        batch_df = df.iloc[i:batch_end]
        
        # Update progress and status
        progress = i / total_rows
        progress_bar.progress(progress)
        status_text.text(f"Processing batch {i//batch_size + 1} of {(total_rows-1)//batch_size + 1} (policies {i+1}-{batch_end}/{total_rows})")
        
        # Fun hacking status update
        if hack_text:
            hack_text.text(random.choice(HACK_MESSAGES))
        
        # Process batch
        for index, row in batch_df.iterrows():
            policy_number = row['policy_number'].strip()
            
            try:
                search_result = await scraper.search_policy(policy_number)
                if search_result:
                    results.append(search_result)
                    logging.info(f"Successfully processed: {policy_number}")
                else:
                    failed_policies.append(policy_number)
                    logging.warning(f"No results found for: {policy_number}")
                    
            except Exception as e:
                failed_policies.append(policy_number)
                logging.error(f"Error processing {policy_number}: {str(e)}")
                continue
    
    # Final progress update
    progress_bar.progress(1.0)
    status_text.text(f"Completed processing {total_rows} policies. Found {len(results)} results, {len(failed_policies)} failed.")
    
    if failed_policies:
        logging.warning(f"Failed to process {len(failed_policies)} policies: {failed_policies[:10]}...")  # Log first 10
    
    return results

async def process_data_concurrent(scraper: ISCScraper, df: pd.DataFrame, progress_bar, status_text, hack_text, batch_size: int = 20, concurrency_limit: int = 4):
    """Process dataframe with concurrent async operations - optimized with shorter delays"""
    results = []
    total_rows = len(df)
    failed_policies = []
    completed_count = 0
    
    # Create semaphore to limit concurrent operations
    semaphore = asyncio.Semaphore(concurrency_limit)
    
    async def search_single_policy_with_semaphore(policy_number: str):
        """Search a single policy with semaphore control"""
        nonlocal completed_count
        
        async with semaphore:
            try:
                result = await scraper.search_policy(policy_number)
                if result:
                    logging.info(f"✅ Successfully processed: {policy_number}")
                    return result
                else:
                    failed_policies.append(policy_number)
                    logging.warning(f"❌ No results found for: {policy_number}")
                    return None
                    
            except Exception as e:
                failed_policies.append(policy_number)
                logging.error(f"❌ Error processing {policy_number}: {str(e)}")
                return None
            finally:
                # Update progress
                completed_count += 1
                progress = completed_count / total_rows
                progress_bar.progress(min(progress, 1.0))
                status_text.text(f"Processed {completed_count}/{total_rows} policies (✅ {len(results)} found, ❌ {len(failed_policies)} failed)")
                if hack_text and completed_count % 5 == 0:
                    hack_text.text(random.choice(HACK_MESSAGES))
    
    # Process in batches for better progress tracking and memory management
    for i in range(0, total_rows, batch_size):
        batch_end = min(i + batch_size, total_rows)
        batch_df = df.iloc[i:batch_end]
        
        status_text.text(f"Starting concurrent batch {i//batch_size + 1} of {(total_rows-1)//batch_size + 1} (policies {i+1}-{batch_end}/{total_rows})")
        
        # Create concurrent tasks for this batch
        tasks = []
        for _, row in batch_df.iterrows():
            policy_number = row['policy_number'].strip()
            task = search_single_policy_with_semaphore(policy_number)
            tasks.append(task)
        
        # Execute all tasks in this batch concurrently
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect successful results
        for result in batch_results:
            if result and not isinstance(result, Exception):
                results.append(result)
        
        # Shorter delay between batches - main optimization  
        if i + batch_size < total_rows:
            await asyncio.sleep(0.5)  # Reduced from 2.0 seconds for better speed
    
    # Final status update
    progress_bar.progress(1.0)
    status_text.text(f"🎉 Completed! Processed {total_rows} policies: ✅ {len(results)} found, ❌ {len(failed_policies)} failed")
    
    if failed_policies:
        logging.warning(f"Failed policies: {failed_policies[:10]}...")  # Log first 10
    
    return results

def main():
    st.title("ISC Slayer - Policy Data Scraper")
    
    # Input section
    with st.sidebar:
        st.header("Login")
        username = st.text_input("Username", value=os.getenv('ISC_USERNAME', ''))
        password = st.text_input("Password", value=os.getenv('ISC_PASSWORD', ''), type="password")
        st.markdown("**Processing parameters are auto-tuned for best speed & reliability.**")

    # Optimised defaults (no user interaction required)
    headless = True  # always run headless for performance & stability
    batch_size = 20  # sweet-spot between speed and server load
    use_concurrent = False  # sequential processing is most reliable
    concurrency_limit = 1

    # File upload
    uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
    
    # Template download
    if st.button("Download CSV Template"):
        template = create_csv_template()
        st.download_button(
            label="Download Template",
            data=template.to_csv(index=False),
            file_name="isc_template.csv",
            mime="text/csv"
        )
    
    # Start processing
    if st.button("Start Sync"):
        if username and password and uploaded_file:
            try:
                # Read and validate CSV
                df = pd.read_csv(uploaded_file)
                if not validate_csv_input(df):
                    st.error("Invalid CSV format. Please ensure your CSV has a 'policy_number' column.")
                    return
                
                # Preprocess policy numbers - clean whitespace and quotes
                st.info("Preprocessing policy numbers...")
                original_count = len(df)
                df['policy_number'] = df['policy_number'].astype(str).str.strip().str.strip('"\'')
                df = df[df['policy_number'].str.len() > 0]  # Remove empty rows
                df = df[~df['policy_number'].isin(['nan', 'NaN', 'None'])]  # Remove invalid entries
                df = df.drop_duplicates(subset=['policy_number'])  # Remove duplicates
                cleaned_count = len(df)
                
                if cleaned_count == 0:
                    st.error("No valid policy numbers found after preprocessing.")
                    return
                
                if cleaned_count < original_count:
                    st.warning(f"Cleaned data: {original_count} → {cleaned_count} rows (removed {original_count - cleaned_count} invalid/duplicate entries)")
                
                st.success(f"Ready to process {cleaned_count} policy numbers")
                
                # Store policy count for time estimation
                st.session_state.policy_count = cleaned_count
                
                # 🔥 Start stopwatch for performance metrics
                start_time = time.time()
                
                # Set up asyncio event loop & UI elements
                if platform.system() == "Windows":
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                progress_bar = st.progress(0)
                status_text = st.empty()
                hack_text = st.empty()

                try:
                    # 🚀 Run the async scraping process
                    results = loop.run_until_complete(
                        run_scraping_process(
                            username,
                            password,
                            headless,
                            df,
                            progress_bar,
                            status_text,
                            hack_text,
                            batch_size,
                            concurrency_limit,
                            use_concurrent,
                        )
                    )

                    # ⏱️ Compute performance metrics
                    elapsed = time.time() - start_time  # seconds
                    avg_auto = elapsed / cleaned_count
                    manual_avg = 60  # seconds per policy (conservative manual estimate)
                    manual_total = manual_avg * cleaned_count
                    time_saved = manual_total - elapsed

                    # Show metrics with some flair
                    st.markdown(
                        f"🚀 **Automation speed:** {avg_auto:.1f}s / policy &nbsp;&nbsp;|&nbsp;&nbsp; Total: {elapsed/60:.1f} min"
                    )
                    st.markdown(
                        f"📝 **Manual estimate:** {manual_avg}s / policy &nbsp;&nbsp;|&nbsp;&nbsp; Total: {manual_total/60:.1f} min"
                    )
                    st.success(
                        f"🤖 **Time saved:** ≈ {time_saved/60:.1f} min  (~{time_saved/3600:.2f} h) 🎉"
                    )

                    # Process results in main thread
                    if results:
                        merged_df = merge_data(df, results)
                        # Ensure output directory exists
                        output_dir = os.path.join('data', 'output')
                        os.makedirs(output_dir, exist_ok=True)
                        output_path = os.path.join(output_dir, 'enriched_data.csv')
                        if save_output_csv(merged_df, output_path):
                            st.success(f"Results saved to {output_path}")
                            st.download_button(
                                label="Download Results",
                                data=merged_df.to_csv(index=False),
                                file_name="enriched_data.csv",
                                mime="text/csv",
                            )
                        else:
                            st.error("Failed to save results.")
                    else:
                        st.warning("No results found.")

                except Exception as e:
                    st.error(f"Processing failed: {str(e)}")
                    logging.error(f"Processing error: {e}")
                finally:
                    # Ensure all pending tasks are cancelled and loop closed
                    try:
                        pending = asyncio.all_tasks(loop)
                        for task in pending:
                            task.cancel()
                        if pending:
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    except Exception as cleanup_error:
                        logging.warning(f"Task cleanup warning: {cleanup_error}")

                    try:
                        loop.close()
                    except Exception as loop_error:
                        logging.warning(f"Loop close warning: {loop_error}")

            except Exception as outer_e:
                st.error(f"An unexpected error occurred: {outer_e}")
                logging.error(f"Unhandled error: {outer_e}")
            
        else:
            st.error("Please provide all required inputs")



async def run_scraping_process(username: str, password: str, headless: bool, df: pd.DataFrame, progress_bar, status_text, hack_text, batch_size: int = 5, concurrency_limit: int = 3, use_concurrent: bool = True):
    """Async function to handle the scraping process - optimized delays"""
    # Initialize scraper
    scraper = ISCScraper(username=username, password=password, headless=headless)
    
    try:
        # Process data
        status_text.text("Initializing browser...")
        await scraper.initialize()
        
        status_text.text("Logging in...")
        if not await scraper.login():
            st.error("Login failed. Please check your credentials.")
            return None
        
        status_text.text("Processing data...")
        if use_concurrent and concurrency_limit > 1:
            results = await process_data_concurrent(scraper, df, progress_bar, status_text, hack_text, batch_size, concurrency_limit)
        else:
            # Use original sequential processing for better reliability
            results = await process_data(scraper, df, progress_bar, status_text, hack_text, batch_size)
        
        return results
        
    finally:
        # Cleanup
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())