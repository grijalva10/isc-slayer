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

def prepare_input_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure all required columns exist in the input DataFrame, creating empty ones if missing"""
    # Define all expected columns that the scraper will return
    expected_columns = [
        'policy_number',
        'app_id', 
        'status',
        'applicant_company',
        'state',
        'program',
        'total_cost',
        'effective_date',
        'expiration_date',
        'cancellation_date'
    ]
    
    # Create a copy to avoid modifying the original
    result_df = df.copy()
    
    # Add any missing columns with empty string values
    for column in expected_columns:
        if column not in result_df.columns:
            result_df[column] = ''
    
    return result_df

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
            how='left',
            suffixes=('_original', '_scraped')
        )
        
        # For columns that exist in both DataFrames, prefer scraped data if it's not empty
        # This handles cases where input CSV might have some data we want to preserve
        for col in scraped_df.columns:
            if col != 'policy_number' and f'{col}_original' in merged_df.columns and f'{col}_scraped' in merged_df.columns:
                # Use scraped data if available, otherwise keep original
                merged_df[col] = merged_df[f'{col}_scraped'].fillna(merged_df[f'{col}_original'])
                # Drop the suffixed columns
                merged_df.drop([f'{col}_original', f'{col}_scraped'], axis=1, inplace=True)
            elif f'{col}_scraped' in merged_df.columns:
                # If only scraped version exists, rename it
                merged_df[col] = merged_df[f'{col}_scraped']
                merged_df.drop(f'{col}_scraped', axis=1, inplace=True)
        
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