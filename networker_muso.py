import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from vetricio_ig_wrapper import get_user_info
from gsheet_handler import parse_to_sheet, client
from request_wrapper import af_request

# Constants
MUSO_BASE_URL = 'https://credits.muso.ai'
RISING_PROFILES_URL = f'{MUSO_BASE_URL}/home/rising-profiles'
RESULTS_SHEET_ID = 48647465

# Headers and cookies (consider moving these to a separate configuration file)
HEADERS = {
    'authority': 'credits.muso.ai',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'dnt': '1',
    'sec-ch-ua': '"Chromium";v="121", "Not A(Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
}

COOKIES = {
    'intercom-device-id-dwjzhcge': 'c54f1a81-fd5a-46ea-a184-30c03c94a83f',
    'ms-store': '%22%7B%5C%22auth%5C%22%3A%7B%5C%22activeAccountId%5C%22%3Anull%2C%5C%22activeRosterMemberId%5C%22%3Anull%2C%5C%22emailConfirmed%5C%22%3Afalse%2C%5C%22welcomeScreen%5C%22%3Afalse%7D%2C%5C%22claim%5C%22%3A%7B%5C%22isShowClaimModal%5C%22%3Afalse%2C%5C%22claimingRosterId%5C%22%3Anull%2C%5C%22claimWorkspaceId%5C%22%3Anull%2C%5C%22claimPopupOpenedOn%5C%22%3Anull%2C%5C%22claimPopupDataToSend%5C%22%3Anull%2C%5C%22isShowClaimChooseAccountView%5C%22%3Afalse%7D%7D%22',
    'i18n_redirected': 'en',
    'amp_018470': 'g4Cl890eeRLglSQtA_hR4P.ODE2MDY=..1hmlvj1sp.1hmlvldmq.f.0.f',
}

def get_rising_profiles():
    """Scrapes muso.ai for rising profiles and returns a list of profile URLs."""
    print('[*] Scraping muso.ai for rising profiles...')
    response = requests.get(RISING_PROFILES_URL, cookies=COOKIES, headers=HEADERS)
    pattern = r'/profile/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    matches = [f'{MUSO_BASE_URL}{x}' for x in set(re.findall(pattern, response.text))]
    print(f'[+] Found {len(matches)} profiles')
    return matches

def scrape_muso_profile(profile_url):
    """Scrapes a single muso.ai profile and returns the data as a dictionary."""
    print(f'[*] Scraping profile {profile_url}...')
    response = af_request(profile_url, cookies=COOKIES, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')

    profile_name = soup.find('h1', class_='title-entity')
    profile_name = profile_name.get_text(strip=True) if profile_name else 'N/A'

    role_elements = soup.find_all('div', text='Engineer')
    role = ', '.join([elem.get_text(strip=True) for elem in role_elements])

    location = soup.find('div', class_='mr-4')
    location = location.text.strip() if location else 'N/A'

    spotify = instagram = 'N/A'
    for link in soup.find_all('a', href=True):
        href = link['href']
        if "instagram" in href:
            instagram = href
        elif "spotify" in href:
            spotify = href

    return {
        'Profile Name': profile_name,
        'url': profile_url,
        'Role': role,
        'song_url': 'TODO',  # TODO: Implement song URL extraction
        'Location': location,
        'Instagram': instagram,
        'Spotify': spotify,
        'Source': 'Muso.ai'
    }

def process_profile_data(profile_data):
    """Processes the profile data, enriches it with Instagram info, and returns a DataFrame."""
    df = pd.DataFrame([profile_data])
    df['Instagram'] = df['Instagram'].fillna(df['Profile Name'])
    df = df.drop_duplicates(subset=['Instagram'])

    ig_df = pd.concat([get_user_info(account) for account in set(df['Instagram'].to_list())], ignore_index=True)
    merged_df = df.merge(ig_df, left_on='Instagram', right_on='source_user', how='left')
    merged_df = merged_df.drop(columns=['Instagram']).rename(columns={'source_user': 'Instagram'})

    return merged_df

def main():
    results_sheet = client.open("Placements Email & Phones").get_worksheet_by_id(RESULTS_SHEET_ID)
    profiles = get_rising_profiles()
    
    for profile in profiles[:4]:  # Limiting to 4 profiles for testing
        print(f'[*] Scraping profile: {profile}')
        profile_data = scrape_muso_profile(profile)
        df = process_profile_data(profile_data)
        parse_to_sheet(df, results_sheet)

if __name__ == "__main__":
    main()