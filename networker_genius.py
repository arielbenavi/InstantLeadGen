import json
import time
from datetime import datetime, timedelta
import requests
import pandas as pd
from typing import List, Dict, Union


from vetricio_ig_wrapper import get_user_info
from gsheet_handler import parse_to_sheet, client

# Constants
BASE_URL = "https://api.genius.com"
AUTH_TOKEN = "ZTejoT_ojOEasIkT9WrMBhBQOz6eYKK5QULCMECmOhvwqjRZ6WbpamFe3geHnvp3"
HEADERS = {
    'Authorization': f'Bearer {AUTH_TOKEN}',
    'User-Agent': 'Genius/7.2.0.4303 (Android; Android 13; Google sdk_gphone64_arm64)',
}

# Original Headers:
'''
'x-genius-app-background-request': '0',
'Host': 'api.genius.com',
'Connection': 'Keep-Alive',
'User-Agent': 'okhttp/4.10.0',
'User-Agent': 'Genius/7.2.0.4303 (Android; Android 13; Google sdk_gphone64_arm64)',
'Authorization': 'Bearer ZTejoT_ojOEasIkT9WrMBhBQOz6eYKK5QULCMECmOhvwqjRZ6WbpamFe3geHnvp3',
'X-Genius-Logged-Out': 'true',
'X-Genius-Android-Version': '7.2.0.4303',
'''
# Original Params:
'''
params = {
    'from_background': '0',
}
'''

def fetch_genius_data(endpoint: str, params: Dict = None) -> Dict:
    """
    Generic function to fetch data from Genius API.
    """
    response = requests.get(f"{BASE_URL}/{endpoint}", headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

def extract_artists(artist_list: List[Dict], relationship: str, song_url: str) -> List[Dict]:
    """
    Extract relevant fields from artist list.
    """
    extracted_artists = []
    seen_urls = set()
    for artist in artist_list:
        if not artist:
            continue
        artist_info = {
            'name': artist.get('name'),
            'url': artist.get('url'),
            'id': artist.get('id'),
            'relationship': relationship,
            'song_url': song_url,
            'Location': 'TODO',
            'Instagram': None,
            'Spotify': None,
            'Source': 'Genius.com'
        }
        if artist_info['url'] not in seen_urls:
            extracted_artists.append(artist_info)
            seen_urls.add(artist_info['url'])
    return extracted_artists

def get_artist_info(artist_id: int) -> Dict:
    """
    Fetch artist information from Genius API.
    """
    print(f'[*] Fetching info for artist ID {artist_id}...')
    return fetch_genius_data(f"artists/{artist_id}")

def get_song_info(song_id: int) -> Dict:
    """
    Fetch song information from Genius API.
    """
    print(f'[*] Fetching info for song ID {song_id}...')
    return fetch_genius_data(f"songs/{song_id}")

def process_song(song_id: int) -> pd.DataFrame:
    """
    Process a single song and return a DataFrame with artist information.
    """
    song_data = get_song_info(song_id)
    song = song_data.get('response', {}).get('song', {})
    song_url = song.get('url', '')

    print(f'[*] Processing song: {song_url}')

    all_artists = []
    for relationship, artist_list in [
        ('producer', song.get('producer_artists', [])),
        ('writer', song.get('writer_artists', [])),
        ('featured', song.get('featured_artists', [])),
        ('primary', [song.get('primary_artist')] + song.get('primary_artists', []))
    ]:
        all_artists.extend(extract_artists(artist_list, relationship, song_url))

    df = pd.DataFrame(all_artists)
    df = df.drop_duplicates(subset=['url'], keep='first')

    for index, row in df.iterrows():
        artist_data = get_artist_info(row['id'])
        instagram_name = artist_data.get('response', {}).get('artist', {}).get('instagram_name')
        if instagram_name:
            print(f'[*] Found Instagram for {row["name"]}: {instagram_name}')
            df.at[index, 'Instagram'] = f'https://instagram.com/{instagram_name}'
        else:
            print(f'[-] No Instagram found for {row["name"]}')

    df = df.drop(['id'], axis=1)
    df['Instagram'] = df['Instagram'].fillna(df['name'])

    print(f'[+] Processed {len(df)} artists for song: {song_url}')
    return df

def enrich_with_instagram(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich the DataFrame with Instagram information.
    """
    print('[*] Enriching data with Instagram information...')
    ig_df = pd.concat([get_user_info(account) for account in set(df['Instagram'].to_list())], ignore_index=True)
    merged_df = df.merge(ig_df, left_on='Instagram', right_on='source_user', how='left')
    merged_df = merged_df.drop(columns=['Instagram'])
    merged_df = merged_df.rename(columns={'source_user': 'Instagram'})
    print(f'[+] Enriched {len(merged_df)} entries with Instagram data')
    return merged_df

def get_song_ids(calendar_id: int) -> List[int]:
    """
    Fetch song IDs from a specific release calendar.
    """
    print(f'[*] Fetching song IDs for calendar ID {calendar_id}...')
    calendar_data = get_song_info(calendar_id)
    df = pd.json_normalize(calendar_data['response']['song']['lyrics']['dom']['children'])
    df = df.explode('children')
    api_paths = df[df['children'].apply(lambda x: isinstance(x, dict) and 'data' in x and 'api_path' in x['data'])]
    song_ids = api_paths['children'].apply(lambda x: x['data']['api_path'].split('/')[-1]).astype(int).tolist()
    print(f'[+] Found {len(song_ids)} song IDs')
    return song_ids

def get_release_calendar_id(year: int, month: int, release_type: str) -> int:
    """
    Dynamically generate the release calendar ID based on year, month, and type.
    Handles both past and future dates relative to May 2024.
    """
    base_id = 9345566  # May 2024 singles ID
    base_date = datetime(2024, 5, 1)
    target_date = datetime(year, month, 1)
    months_diff = (target_date.year - base_date.year) * 12 + (target_date.month - base_date.month)
    type_offset = 0 if release_type == 'singles' else 1
    calendar_id = base_id + months_diff - type_offset
    print(f'[*] Generated calendar ID for {year}-{month} {release_type}: {calendar_id}')
    return calendar_id

def scrape_genius(start_year: int, start_month: int, end_year: int = None, end_month: int = None, 
                  release_type: str = 'singles', limit: int = None) -> pd.DataFrame:
    """
    Main function to scrape Genius data for a given time range and release type.
    Handles both past and future dates.
    """
    print(f'[*] Starting Genius scraper for {release_type} from {start_year}-{start_month} to {end_year}-{end_month}')
    end_year = end_year or datetime.now().year
    end_month = end_month or datetime.now().month
    
    all_dfs = []
    current_date = datetime(start_year, start_month, 1)
    end_date = datetime(end_year, end_month, 1)

    while current_date <= end_date:
        print(f'[*] Processing {current_date.strftime("%B %Y")}...')
        calendar_id = get_release_calendar_id(current_date.year, current_date.month, release_type)
        try:
            song_ids = get_song_ids(calendar_id)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"[-] No data available for {current_date.strftime('%B %Y')}. Skipping...")
                current_date += timedelta(days=32)
                current_date = current_date.replace(day=1)
                continue
            else:
                raise

        if limit:
            song_ids = song_ids[:limit]
            print(f'[*] Limiting to {limit} songs')
        
        for song_id in song_ids:
            df = process_song(song_id)
            if not df.empty:
                all_dfs.append(df)
        
        current_date += timedelta(days=32)
        current_date = current_date.replace(day=1)

    if not all_dfs:
        print("[-] No data found for the specified date range.")
        return pd.DataFrame()

    master_df = pd.concat(all_dfs, ignore_index=True)
    master_df = enrich_with_instagram(master_df)
    print(f'[+] Scraping complete. Total contacts scraped: {len(master_df)}')
    return master_df

if __name__ == "__main__":
    # Example usage
    results_sheet = client.open("Placements Email & Phones").get_worksheet_by_id(48647465)
    
    print('[*] Starting Genius.com scraper...')
    # Scrape data for July 2024 singles
    df = scrape_genius(2024, 7, release_type='singles', limit=3)
    
    if not df.empty:
        print('[*] Parsing data to Google Sheet...')
        parse_to_sheet(df, results_sheet)
        print(f"[+] Total contacts scraped and parsed to sheet: {len(df)}")
    else:
        print("[-] No data to parse to sheet.")
    
    print('[+] Thanks for using networker!')