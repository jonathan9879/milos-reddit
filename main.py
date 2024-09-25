import praw
import os
import re
import json
from datetime import datetime, timedelta
from pushbullet import Pushbullet
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account


# Reddit API credentials
reddit = praw.Reddit(
    client_id=os.environ['REDDIT_CLIENT_ID'],
    client_secret=os.environ['REDDIT_CLIENT_SECRET'],
    user_agent="python:myRedditScraper:v1.0 (by /u/Firm_Homework2562)"
)

# Pushbullet API key
pb = Pushbullet(os.environ['PUSHBULLET_API_KEY'])

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Load service account credentials from environment variable
service_account_info = json.loads(os.environ['GOOGLE_SHEETS_CREDENTIALS'])
creds = service_account.Credentials.from_service_account_info(
    service_account_info, scopes=SCOPES)

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

SPREADSHEET_ID = os.environ['SPREADSHEET_ID']
RANGE_NAME = 'Sheet1!A4:G'

# Load keywords and subreddits from Google Sheets
def load_data_from_sheets():
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    
    keywords = set()
    subreddits = []
    
    for row in values:
        # Check if we've reached the end of the data
        if len(row) == 0:
            break
        
        # Read keywords from column A (index 0)
        if len(row) > 0 and row[0]:
            keywords.add(row[0].lower())
        
        # Read keywords from column C (index 2)
        if len(row) > 2 and row[2]:
            keywords.add(row[2].lower())
        
        # Read keywords from column E (index 4)
        if len(row) > 4 and row[4]:
            keywords.add(row[4].lower())
        
        # Read subreddits from column G (index 6)
        if len(row) > 6 and row[6]:
            subreddits.append(row[6])
    
    return keywords, subreddits

# Check if a post contains any of the keywords
def contains_keyword(text, keywords):
    text_lower = text.lower()
    found_keywords = []
    for keyword in keywords:
        # Create a regex pattern to match the keyword as a full word
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_lower):
            found_keywords.append(keyword)
    return found_keywords

# Send Pushbullet notification
def send_notification(title, body):
    pb.push_note(title, body)

# Main scraping function
def scrape_subreddits(keywords, subreddits):
    cutoff_time = datetime.utcnow() - timedelta(days=1)
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        for post in subreddit.new(limit=None):
            if datetime.fromtimestamp(post.created_utc) < cutoff_time:
                break
            found_keywords = contains_keyword(post.title + ' ' + post.selftext, keywords)
            if found_keywords:
                title = f"Keyword found in r/{subreddit_name}"
                body = f"Post: {post.title}\nLink: https://www.reddit.com{post.permalink}\nFound keywords: {', '.join(found_keywords)}"
                send_notification(title, body)

# Main execution
if __name__ == "__main__":
    keywords, subreddits = load_data_from_sheets()
    
    print(f"Script started at {datetime.now()}")
    print(f"Loaded {len(keywords)} keywords and {len(subreddits)} subreddits")
    scrape_subreddits(keywords, subreddits)
    print(f"Script completed at {datetime.now()}")