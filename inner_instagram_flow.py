import pandas as pd
import time
import re
from vetricio_ig_wrapper import (
    instagram_scraper, get_user_id, get_user_info, 
    get_user_posts, account_search
)

# Constants
WATCHLIST = [
    'https://www.instagram.com/itspressplayuk',
    'https://www.instagram.com/whatnycsoundslike',
    'https://www.instagram.com/ontheradarradio',
    'https://www.instagram.com/producergrind'
]

def process_and_extract(df, account):
    mentioned_accounts_regex = r'@(.*?)\s'
    df['mentioned_accounts'] = df['caption.text'].apply(lambda x: list(set(re.findall(mentioned_accounts_regex, str(x)))))
    df['source'] = account
    df['post_link'] = df['code'].apply(lambda x: f'https://www.instagram.com/p/{x}')
    
    columns_to_keep = ['source', 'post_link', 'caption.text', 'mentioned_accounts', 'caption.created_at', 'usertags.in',
                       'has_shared_to_fb', 'play_count', 'view_count', 'video_duration', 'comment_count', 'preview_comments', 'taken_at']
    df = df[df.columns.intersection(columns_to_keep)]
    
    df['usertags_accounts'] = df['usertags.in'].apply(lambda x: [tag['user']['username'] for tag in x] if isinstance(x, list) else [])
    df['combined_accounts'] = df.apply(lambda row: list(set(row.get('mentioned_accounts', []) + row.get('usertags_accounts', []))), axis=1)
    df = df.explode('combined_accounts')
    df['combined_accounts'] = df['combined_accounts'].apply(lambda x: f'https://www.instagram.com/{x}' if isinstance(x, str) else None)
    
    df = df[['source', 'combined_accounts', 'post_link']].dropna(subset=['combined_accounts'])
    return df

def get_user_info_batch(accounts):
    user_dfs = []
    for account in accounts:
        user_df = get_user_info(account)
        if not user_df.empty:
            user_dfs.append(user_df)
        time.sleep(0.5)  # To avoid rate limiting
    return pd.concat(user_dfs, ignore_index=True) if user_dfs else pd.DataFrame()

def scrape_account(account, limit=50):
    posts_df = get_user_posts(account, limit=limit)
    processed_df = process_and_extract(posts_df, account)
    return processed_df

def main_workflow():
    all_data = []
    for account in WATCHLIST:
        print(f"Processing account: {account}")
        account_data = scrape_account(account)
        all_data.append(account_data)
        time.sleep(1)  # Avoid rate limiting
    
    combined_df = pd.concat(all_data, ignore_index=True)
    unique_accounts = combined_df['combined_accounts'].unique()
    user_info_df = get_user_info_batch(unique_accounts)
    
    final_df = pd.merge(combined_df, user_info_df, left_on='combined_accounts', right_on='source_user', how='left')
    final_df = final_df.drop_duplicates(subset=['source_user', 'post_link'])
    
    return final_df

if __name__ == "__main__":
    result_df = main_workflow()
    print(f"Total contacts scraped: {len(result_df)}")
    # result_df.to_csv('instagram_scrape_results.csv', index=False)