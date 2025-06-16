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

from src.requests_hybrid import ISCRequestsHybrid, ensure_playwright_browsers
from src.utils import validate_csv_input, create_csv_template, merge_data, save_output_csv
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Session state will be initialized in main() function

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

async def process_data(scraper: ISCRequestsHybrid, df: pd.DataFrame, progress_bar, status_text, hack_text, batch_size: int = 5):
    """Process dataframe with our new hybrid approach"""
    results = []
    total_rows = len(df)
    failed_policies = []
    completed_count = 0
    
    def update_progress(current, total, successful, failed):
        """Callback to update UI progress"""
        nonlocal completed_count
        completed_count = current
        progress = current / total
        progress_bar.progress(min(progress, 1.0))
        status_text.text(f"Processed {current}/{total} policies (✅ {successful} found, ❌ {failed} failed)")
        if hack_text and current % 5 == 0:
            hack_text.text(random.choice(HACK_MESSAGES))
    
    # Process in batches for better progress tracking
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
        batch_policies = batch_df['policy_number'].tolist()
        batch_results = scraper.process_policies_concurrent(
            batch_policies, 
            max_workers=5,
            progress_callback=update_progress
        )
        
        # Track failed policies
        successful_policies = {result.get('policy_number') for result in batch_results if result}
        batch_failed = [p for p in batch_policies if p not in successful_policies]
        failed_policies.extend(batch_failed)
        
        # Update results
        results.extend(batch_results)
    
    # Final progress update
    progress_bar.progress(1.0)
    status_text.text(f"Completed processing {total_rows} policies. Found {len(results)} results, {len(failed_policies)} failed.")
    
    if failed_policies:
        logging.warning(f"Failed to process {len(failed_policies)} policies: {failed_policies[:10]}...")  # Log first 10
    
    return results, failed_policies

async def run_scraping_process(username: str, password: str, headless: bool, df: pd.DataFrame, progress_bar, status_text, hack_text, batch_size: int = 5, concurrency_limit: int = 3, use_concurrent: bool = True):
    """Run the scraping process with our new hybrid approach"""
    try:
        # Initialize scraper
        scraper = ISCRequestsHybrid(username, password)
        
        # Login
        status_text.text("🔐 Logging in...")
        if not await scraper.login():
            st.error("❌ Login failed. Please check your credentials.")
            return [], []
        
        # Process data
        return await process_data(scraper, df, progress_bar, status_text, hack_text, batch_size)
        
    except Exception as e:
        st.error(f"❌ Error during scraping: {str(e)}")
        return [], []

def main():
    # Initialize session state for results if not exists
    if 'last_results' not in st.session_state:
        st.session_state.last_results = None
    if 'last_failed' not in st.session_state:
        st.session_state.last_failed = None
    if 'last_sync_time' not in st.session_state:
        st.session_state.last_sync_time = None
    if 'browsers_initialized' not in st.session_state:
        st.session_state.browsers_initialized = False
    
    st.title("ISC Slayer - Policy Data Scraper")
    
    # Initialize browsers on first run
    if not st.session_state.browsers_initialized:
        with st.spinner("🔧 Initializing browser components..."):
            success = ensure_playwright_browsers()
            st.session_state.browsers_initialized = success
            if success:
                st.success("✅ Browser components ready!")
            else:
                st.error("❌ Failed to initialize browser components")
    
    # Input section
    with st.sidebar:
        st.header("Login")
        username = st.text_input("Username", value=os.getenv('ISC_USERNAME', ''))
        password = st.text_input("Password", value=os.getenv('ISC_PASSWORD', ''), type="password")
        st.markdown("**Processing parameters are auto-tuned for best speed & reliability.**")

    # Optimised defaults (no user interaction required)
    headless = True  # always run headless for performance & stability
    batch_size = 20  # sweet-spot between speed and server load
    use_concurrent = True  # our new approach is concurrent by default
    concurrency_limit = 5  # optimal for our hybrid approach

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
    
    # Show last sync results if they exist
    if st.session_state.last_results is not None:
        st.markdown("---")
        st.subheader("📊 Last Sync Results")
        st.markdown(f"Last sync completed at: {st.session_state.last_sync_time}")
        
        # Show successful results
        if not st.session_state.last_results.empty:
            st.success(f"✅ Found {len(st.session_state.last_results)} successful results")
            st.download_button(
                label="Download Results",
                data=st.session_state.last_results.to_csv(index=False),
                file_name="enriched_data.csv",
                mime="text/csv"
            )
            st.dataframe(st.session_state.last_results.head())
        
        # Show failed policies
        if st.session_state.last_failed:
            st.warning(f"❌ {len(st.session_state.last_failed)} policies failed")
            failed_df = pd.DataFrame({'policy_number': st.session_state.last_failed})
            st.download_button(
                label="Download Failed Policies",
                data=failed_df.to_csv(index=False),
                file_name="failed_policies.csv",
                mime="text/csv"
            )
    
    # Start processing
    if st.button("Start Sync"):
        if not st.session_state.browsers_initialized:
            st.error("❌ Browser components not initialized. Please refresh the page.")
            return
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
                    results, failed_policies = loop.run_until_complete(
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
                    
                    # Show performance metrics
                    st.success(f"""
                    🎯 Performance Metrics:
                    - Time saved: {manual_total/3600:.1f} hours
                    - Speedup: {manual_avg/avg_auto:.1f}x faster than manual
                    - Rate: {cleaned_count/elapsed:.1f} policies/minute
                    """)
                    
                    # Save results
                    if results:
                        # Ensure output directory exists
                        output_dir = os.path.join('data', 'output')
                        os.makedirs(output_dir, exist_ok=True)
                        
                        # Save successful results
                        output_df = pd.DataFrame(results)
                        output_path = os.path.join(output_dir, 'enriched_data.csv')
                        if save_output_csv(output_df, output_path):
                            st.success(f"✅ Results saved to: {output_path}")
                            
                            # Store results in session state
                            st.session_state.last_results = output_df
                            st.session_state.last_failed = failed_policies
                            st.session_state.last_sync_time = time.strftime("%Y-%m-%d %H:%M:%S")
                            
                            # Show preview
                            st.dataframe(output_df.head())
                        else:
                            st.error("Failed to save results.")
                        
                        # Save failed policies
                        if failed_policies:
                            failed_df = pd.DataFrame({'policy_number': failed_policies})
                            failed_path = os.path.join(output_dir, 'failed_policies.csv')
                            if save_output_csv(failed_df, failed_path):
                                st.warning(f"❌ Failed policies saved to: {failed_path}")
                    else:
                        st.warning("No results found.")
                        
                except Exception as e:
                    st.error(f"❌ Error during processing: {str(e)}")
                finally:
                    loop.close()
                    
            except Exception as e:
                st.error(f"❌ Error reading CSV: {str(e)}")
        else:
            st.warning("Please provide username, password, and upload a CSV file.")

if __name__ == "__main__":
    main()