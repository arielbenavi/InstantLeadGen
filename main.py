import pandas as pd
from datetime import datetime
from telegram_wrapper import telegram_noti
from networker_genius import scrape_genius
from inner_instagram_flow import main_workflow as instagram_workflow
from networker_muso import main as muso_workflow
from gsheet_handler import parse_to_sheet, client

# Constants
RESULTS_SHEET_ID = 48647465
MAX_RECORDS_PER_SOURCE = 100  # Adjust as needed

# Standard column names in the correct order
STANDARD_COLUMNS = [
    'Profile Name', 'url', 'Role', 'song_url', 'Location', 'Spotify', 'Source',
    'Instagram', 'follower_count', 'public_email', 'contact_phone_number',
    'public_phone_number', 'category', 'biography', 'time collected'
]

def standardize_dataframe(df, source):
    """Standardize the DataFrame structure across all sources."""
    df = df.copy()
    df['Source'] = source
    df['time collected'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Rename columns to match standard format if necessary
    column_mapping = {
        'name': 'Profile Name',
        'instagram': 'Instagram',
        # Add more mappings as needed
    }
    df = df.rename(columns=column_mapping)
    
    # Ensure all standard columns exist, fill with None if missing
    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = None
    
    # Reorder columns to match STANDARD_COLUMNS
    df = df[STANDARD_COLUMNS]
    
    return df

def run_genius_workflow():
    print("Starting Genius.com scraper...")
    df = scrape_genius(2024, 7, release_type='singles', limit=MAX_RECORDS_PER_SOURCE)
    return standardize_dataframe(df, 'Genius.com')

def run_instagram_workflow():
    print("Starting Instagram scraper...")
    df = instagram_workflow()
    return standardize_dataframe(df, 'Instagram')

def run_muso_workflow():
    print("Starting Muso.ai scraper...")
    df = muso_workflow()  # Assuming muso_workflow returns a DataFrame
    return standardize_dataframe(df, 'Muso.ai')

def main():
    start_time = datetime.now()
    all_data = []
    error_messages = []

    workflows = [
        ("Genius", run_genius_workflow),
        ("Instagram", run_instagram_workflow),
        ("Muso", run_muso_workflow)
    ]

    for name, workflow in workflows:
        try:
            df = workflow()
            all_data.append(df)
            message = f"[+] {name} scraping completed. Records found: {len(df)}"
            print(message)
            telegram_noti(message)
        except Exception as e:
            error_message = f"[-] Error in {name} workflow: {str(e)}"
            print(error_message)
            error_messages.append(error_message)
            telegram_noti(error_message)

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        results_sheet = client.open("Placements Email & Phones").get_worksheet_by_id(RESULTS_SHEET_ID)
        parse_to_sheet(combined_df, results_sheet)
        
        summary = f"""
        Networker Scraping Summary:
        Total records: {len(combined_df)}
        Genius records: {len(combined_df[combined_df['Source'] == 'Genius.com'])}
        Instagram records: {len(combined_df[combined_df['Source'] == 'Instagram'])}
        Muso records: {len(combined_df[combined_df['Source'] == 'Muso.ai'])}
        Time taken: {datetime.now() - start_time}
        """
        print(summary)
        telegram_noti(summary)
    
    if error_messages:
        error_summary = "Errors encountered:\n" + "\n".join(error_messages)
        print(error_summary)
        telegram_noti(error_summary)

if __name__ == "__main__":
    main()