import pandas as pd
import os
from typing import List, Dict

def validate_csv_input(df: pd.DataFrame) -> bool:
    """Validate input CSV format - only policy_number column required"""
    try:
        return 'policy_number' in df.columns
    except Exception as e:
        print(f"Error validating CSV: {e}")
        return False

def create_csv_template() -> pd.DataFrame:
    """Create downloadable CSV template - only policy_number required"""
    template = pd.DataFrame({
        'policy_number': ['ISCPC04000058472', 'ISCPC04000058215', 'ISCPC04000058337']
    })
    return template

def merge_data(original_df: pd.DataFrame, scraped_data: List[Dict]) -> pd.DataFrame:
    """Merge original data with scraped results"""
    try:
        # Convert scraped data to DataFrame
        scraped_df = pd.DataFrame(scraped_data)
        
        # Merge with original data
        merged_df = pd.merge(
            original_df,
            scraped_df,
            left_on='policy_number',
            right_on='policy_number',
            how='left'
        )
        
        return merged_df
    except Exception as e:
        print(f"Error merging data: {e}")
        return original_df

def save_output_csv(df: pd.DataFrame, output_path: str) -> bool:
    """Save enriched data to CSV"""
    try:
        df.to_csv(output_path, index=False)
        return True
    except Exception as e:
        print(f"Error saving CSV: {e}")
        return False