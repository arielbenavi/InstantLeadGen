import requests
import pandas as pd
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import re
import time


with open('vetricio_api_key.txt', 'r') as file:
        VERTIC_API_KEY = file.read().strip()


class VetricIOBase:
    base = "https://api.vetric.io"
    platform = ""
    api_version = "v1"

    def __init__(self, auth_key: str = VERTIC_API_KEY):
        self.auth_key = auth_key
        self.headers = self._set_headers(auth_key)
        self.session = self._get_session()

    def _set_headers(self, auth_key: str):
        return {
            'user-agent': "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Mobile Safari/537.36",
            'referrer-policy': 'no-referrer',
            'x-api-key': auth_key
        }

    def _get_session(self, max_retries=3, timeout=30):
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.timeout = timeout
        session.headers.update(self.headers)
        return session

    def fetch(self, endpoint: str, payload: dict = None, method: str = "GET"):
        url = f"{self.base}/{self.platform}/{self.api_version}/{endpoint}"
        if method == "GET":
            return self.session.get(url, params=payload)
        elif method == "POST":
            return self.session.post(url, data=payload)
        else:
            raise ValueError(f"Invalid HTTP method {method}, please choose GET|POST")

    def get_usage(self):
        return self.session.get(f"{self.base}/usage").json()

class VetricIOInstagram(VetricIOBase):
    platform = "instagram"

    def __init__(self, auth_key: str = VERTIC_API_KEY):
        super().__init__(auth_key)

    def get_user_info(self, user_id: str):
        endpoint = f"users/{user_id}/info"
        return self.fetch(endpoint=endpoint).json()

    def get_user_posts(self, user_id: str, params=None, limit=50):
        if params is None:
            params = {}
        endpoint = f"feed/user/{user_id}"
        master_df = pd.DataFrame()
        while True:
            res = self.fetch(endpoint=endpoint, payload=params).json()
            if 'items' not in res:
                print(f"Items not in response: {res}")
                if 'Endpoint request timed out' in str(res):
                    time.sleep(1)
                    continue
                break
            df = pd.json_normalize(res['items'])
            master_df = pd.concat([master_df, df], ignore_index=True)
            if 'next_max_id' not in res or len(master_df) >= limit:
                break
            params['max_id'] = res['next_max_id']
            time.sleep(0.5)
        return master_df

    def get_user_following_followers(self, user_id: str, method='following_followers', limit=999):
        master_df = pd.DataFrame()
        endpoints = []
        if 'followers' in method:
            endpoints.append(f"friendships/{user_id}/followers")
        if 'following' in method:
            endpoints.append(f"friendships/{user_id}/following?rank_token=13e81127-39d3-4c32-9dbf-a346009bfd41")

        for endpoint in endpoints:
            params = {}
            while True:
                res = self.fetch(endpoint=endpoint, payload=params).json()
                df = pd.json_normalize(res['users'])
                df['type'] = endpoint.split('/')[-1].split('?')[0]
                master_df = pd.concat([master_df, df], ignore_index=True)
                if 'next_max_id' not in res or len(master_df) >= limit:
                    break
                params['max_id'] = res['next_max_id']
        return master_df

    @staticmethod
    def get_profile_url(username: str):
        return f"https://instagram.com/{username}"

def extract_instagram_username(url):
    if 'instagram.com' in url:
        return url.split('/')[-1].split('?')[0]
    elif 'facebook.com' in url:
        if 'groups/' in url:
            return url.split('groups/')[-1].split('/')[0]
        elif 'profile/' in url:
            return url.split('profile/')[-1].split('/')[0]
        elif 'profile.php/?id/' in url:
            return url.split('?id=')[-1].split('/')[0]
        else:
            return url.split('/')[-1]
    return url

def get_uid_by_name(username):
    instagram = VetricIOInstagram()
    url = f'users/search?q={username}'
    response = instagram.fetch(url).json()
    if 'users' in response:
        for user in response['users']:
            if user['username'].lower() == username.lower():
                return user['pk']
    return None

def get_user_id(url):
    username = extract_instagram_username(url)
    print(f'[*] Fetching user id for {username}')
    return get_uid_by_name(username)

def get_user_info(account, pk=None):
    instagram = VetricIOInstagram()
    if 'instagram' not in str(account) and account:
        account_search_df = account_search(account)
        account = f'https://www.instagram.com/{account_search_df["username"].iloc[0]}'
        pk = account_search_df['pk'].iloc[0]

    id = get_user_id(account) if not pk else pk
    user_data = instagram.get_user_info(id)
    
    try:
        df = pd.json_normalize(user_data['user'])
    except Exception as e:
        print(e, user_data)
        return pd.DataFrame()

    columns_to_keep = ['follower_count', 'contact_phone_number', 'public_phone_number', 'public_email', 'category', 'biography']
    
    for col in columns_to_keep:
        if col not in df.columns:
            df[col] = None

    df = df[columns_to_keep]
    df['source_user'] = account

    return df[['source_user'] + columns_to_keep]

def account_search(name):
    instagram = VetricIOInstagram()
    url = f'users/search?q={name}'
    response = instagram.fetch(url).json()
    ig_search_df = pd.json_normalize(response['users'])

    def rank_score(id):
        user_data = get_user_info(None, pk=id)
        score = 0
        if user_data.empty:
            return 0

        follower_count = user_data['follower_count'].values[0] if 'follower_count' in user_data.columns else None
        if follower_count is None:
            return 0

        if int(follower_count) > 500:
            score += 1
        if user_data['category'].iloc[0] in ["Producer", "Artist", "Music Producer", "Music Composer", "Musician"]:
            score += 1
        if any(keyword in user_data["biography"].iloc[0].lower() for keyword in ["producer", "artist", "credits", "mgmt"]):
            score += 1
        return score

    ig_search_df['score'] = ig_search_df['pk'].apply(rank_score)
    max_score = ig_search_df['score'].max()
    top_profiles = ig_search_df[ig_search_df['score'] == max_score]

    return top_profiles

instagram_scraper = VetricIOInstagram()

# Additional utility functions
def get_user_posts(account, limit=50):
    id = get_user_id(account)
    return instagram_scraper.get_user_posts(id, limit=limit)

def get_user_following_followers(account):
    id = get_user_id(account)
    df = instagram_scraper.get_user_following_followers(id)
    df['source'] = account
    df['user_link'] = df['username'].apply(lambda x: f'https://www.instagram.com/{x}')
    return df[['source', 'user_link', 'type', 'username', 'full_name', 'profile_pic_url', 'is_private', 'latest_reel_media']]

