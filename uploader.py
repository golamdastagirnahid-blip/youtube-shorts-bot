# ============================================================
# YOUTUBE SHORTS AUTO UPLOADER v3.0
# Features:
# - AI Generated Titles (Groq + Llama 3.3 70B)
# - Google Trends Integration
# - Anti Shadow Ban System
# - Self Learning AI
# - Google Sheets Logging
# - Telegram Notifications
# - Email Alerts
# - Human-like Random Delays
# - Auto Retry on Failure
# - Video Duplicate Checker
# - Auto Category Detection
# - Competitor Title Spy
# ============================================================

import os
import json
import sys
import random
import tempfile
import smtplib
import hashlib
import time
import urllib.request
import urllib.parse
import re
from email.mime.text import MIMEText
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from groq import Groq


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================
CLIENT_ID = os.environ.get('YOUTUBE_CLIENT_ID')
CLIENT_SECRET = os.environ.get('YOUTUBE_CLIENT_SECRET')
REFRESH_TOKEN = os.environ.get('YOUTUBE_REFRESH_TOKEN')
DRIVE_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID')
SERVICE_ACCOUNT_JSON = os.environ.get('GOOGLE_SERVICE_ACCOUNT')
ALERT_EMAIL = os.environ.get('ALERT_EMAIL', '')
ALERT_APP_PASSWORD = os.environ.get('ALERT_APP_PASSWORD', '')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')


# ============================================================
# YOUTUBE CATEGORY MAP
# ============================================================
CATEGORY_MAP = {
    "film": "1", "animation": "1", "movie": "1",
    "car": "2", "vehicle": "2", "auto": "2", "driving": "2",
    "music": "10", "song": "10", "singing": "10", "dance": "10", "dj": "10",
    "pet": "15", "animal": "15", "dog": "15", "cat": "15", "wildlife": "15", "nature": "15",
    "sport": "17", "fitness": "17", "gym": "17", "workout": "17", "football": "17", "basketball": "17", "soccer": "17", "cricket": "17",
    "travel": "19", "village": "19", "city": "19", "tourism": "19", "destination": "19", "landscape": "19",
    "gaming": "20", "game": "20", "minecraft": "20", "fortnite": "20", "gta": "20",
    "vlog": "22", "blog": "22", "daily": "22", "lifestyle": "22",
    "comedy": "23", "funny": "23", "humor": "23", "meme": "23", "joke": "23",
    "entertainment": "24", "challenge": "24", "reaction": "24",
    "news": "25", "politics": "25",
    "howto": "26", "tutorial": "26", "diy": "26", "tips": "26", "hack": "26", "learn": "26",
    "education": "27", "science": "27", "history": "27", "fact": "27", "knowledge": "27",
    "tech": "28", "technology": "28", "phone": "28", "computer": "28", "ai": "28", "robot": "28",
    "food": "26", "cooking": "26", "recipe": "26", "kitchen": "26", "chef": "26",
    "fashion": "26", "beauty": "26", "makeup": "26", "style": "26",
    "motivation": "22", "inspire": "22", "quote": "22", "success": "22",
    "horror": "1", "scary": "1", "ghost": "1",
    "asmr": "22", "satisfying": "22", "relaxing": "22",
}


# ============================================================
# ANTI SHADOW BAN CONFIG
# ============================================================
HASHTAG_POOLS = [
    ["shorts", "viral", "trending", "fyp", "explore"],
    ["shorts", "viralvideo", "trend", "foryou", "discover"],
    ["shortvideo", "viral", "trending2024", "fypage", "recommended"],
    ["shorts", "viralshorts", "trendingshorts", "fypシ", "mustwatch"],
    ["ytshorts", "viral", "trending", "foryoupage", "entertainment"],
    ["shorts", "viralcontent", "trending", "foryoupageシ", "watchthis"],
    ["shortsvideo", "viral", "trendingnow", "fyp", "videooftheday"],
]

DESCRIPTION_TEMPLATES = [
    "🔥 Watch till the end!\n\nLike & Subscribe for more! 👍\n\n{hashtags}",
    "😱 You won't believe this!\n\nSubscribe for daily content! 🔔\n\n{hashtags}",
    "💯 This is amazing!\n\nDrop a ❤️ if you agree!\n\n{hashtags}",
    "⚡ Wait for it...\n\nFollow for more! 🚀\n\n{hashtags}",
    "🎯 Don't miss this!\n\nShare with friends! 🔄\n\n{hashtags}",
    "👀 Watch this!\n\nNew content daily! ✨\n\n{hashtags}",
    "🤯 Mind blowing!\n\nTap ❤️ and Subscribe! 🔔\n\n{hashtags}",
    "🌟 This made my day!\n\nDouble tap if you loved it! ❤️\n\n{hashtags}",
    "🎬 Best video today!\n\nSave this for later! 🔖\n\n{hashtags}",
    "💥 Incredible!\n\nTag someone who needs to see this! 👇\n\n{hashtags}",
]

TITLE_STYLES = [
    "catchy and curiosity-driven with emoji",
    "shocking and surprising with emoji",
    "question-based that makes people curious",
    "bold statement that creates debate",
    "emotional and relatable with emoji",
    "funny and entertaining with emoji",
    "inspiring and motivational with emoji",
    "mysterious and intriguing with emoji",
    "educational but exciting with emoji",
    "storytelling hook that draws people in",
]


# ============================================================
# TELEGRAM NOTIFICATION
# ============================================================
def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured, skipping")
        return
    try:
        text = urllib.parse.quote(message)
        url = (
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
            f"/sendMessage?chat_id={TELEGRAM_CHAT_ID}"
            f"&text={text}&parse_mode=Markdown"
        )
        urllib.request.urlopen(url, timeout=10)
        print("✅ Telegram notification sent")
    except Exception as e:
        print(f"Telegram failed: {e}")


# ============================================================
# EMAIL + TELEGRAM ALERT
# ============================================================
def send_alert(subject, message):
    if ALERT_EMAIL and ALERT_APP_PASSWORD:
        try:
            msg = MIMEText(message)
            msg['Subject'] = f"YouTube Bot: {subject}"
            msg['From'] = ALERT_EMAIL
            msg['To'] = ALERT_EMAIL
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(ALERT_EMAIL, ALERT_APP_PASSWORD)
            server.send_message(msg)
            server.quit()
            print(f"✅ Email alert sent: {subject}")
        except Exception as e:
            print(f"Email alert failed: {e}")
    send_telegram(f"⚠️ *{subject}*\n\n{message}")


# ============================================================
# HUMAN-LIKE RANDOM DELAY
# ============================================================
def human_delay():
    delay_seconds = random.randint(0, 3600)
    delay_minutes = delay_seconds // 60
    delay_secs = delay_seconds % 60

    print("=" * 50)
    print(f"🕐 Human-like delay: {delay_minutes}m {delay_secs}s")
    print("=" * 50)

    send_telegram(
        f"🤖 *Bot Activated*\n\n"
        f"⏳ Waiting {delay_minutes} min before upload\n"
        f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    remaining = delay_seconds
    while remaining > 0:
        chunk = min(300, remaining)
        time.sleep(chunk)
        remaining -= chunk
        if remaining > 0:
            print(f"   ⏳ {remaining // 60} min remaining...")

    print("✅ Delay complete!")


# ============================================================
# ANTI SHADOW BAN CONFIG GENERATOR
# ============================================================
def get_anti_ban_config(filename):
    seed = int(hashlib.md5(filename.encode()).hexdigest()[:8], 16)
    random.seed(seed + int(datetime.now().strftime('%Y%m%d%H')))

    hashtag_set = random.choice(HASHTAG_POOLS)
    description_template = random.choice(DESCRIPTION_TEMPLATES)
    title_style = random.choice(TITLE_STYLES)

    extra_tags = random.sample([
        "amazing", "wow", "unbelievable", "insane", "epic",
        "cool", "awesome", "incredible", "mindblowing", "satisfying",
        "beautiful", "perfect", "outstanding", "brilliant", "stunning"
    ], 4)

    all_tags = hashtag_set + extra_tags
    hashtags = " ".join([f"#{tag}" for tag in all_tags])
    description = description_template.format(hashtags=hashtags)

    return title_style, description, all_tags


# ============================================================
# AUTO CATEGORY DETECTION
# ============================================================
def detect_category(filename):
    clean_name = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').lower()
    words = clean_name.split()

    detected_category = "22"  # Default: People & Blogs
    detected_name = "People & Blogs"

    category_names = {
        "1": "Film & Animation", "2": "Autos & Vehicles",
        "10": "Music", "15": "Pets & Animals",
        "17": "Sports", "19": "Travel & Events",
        "20": "Gaming", "22": "People & Blogs",
        "23": "Comedy", "24": "Entertainment",
        "25": "News & Politics", "26": "Howto & Style",
        "27": "Education", "28": "Science & Technology",
    }

    for word in words:
        if word in CATEGORY_MAP:
            detected_category = CATEGORY_MAP[word]
            detected_name = category_names.get(detected_category, "People & Blogs")
            break

    # Also try two-word combinations
    for i in range(len(words) - 1):
        combo = words[i] + words[i + 1]
        if combo in CATEGORY_MAP:
            detected_category = CATEGORY_MAP[combo]
            detected_name = category_names.get(detected_category, "People & Blogs")
            break

    print(f"🏷️ Auto Category: {detected_name} (ID: {detected_category})")
    return detected_category, detected_name


# ============================================================
# VIDEO DUPLICATE CHECKER
# ============================================================
def check_duplicate(drive_service, file_info, uploaded_folder_id):
    try:
        # Check by filename in uploaded folder
        query = (
            f"'{uploaded_folder_id}' in parents and "
            f"name = '{file_info['name']}' and "
            f"trashed = false"
        )
        results = drive_service.files().list(
            q=query,
            fields="files(id, name)"
        ).execute()
        files = results.get('files', [])

        if files:
            print(f"⚠️ DUPLICATE FOUND: {file_info['name']} already uploaded!")
            return True

        # Check by file size (same size = likely same video)
        if 'size' in file_info:
            query = (
                f"'{uploaded_folder_id}' in parents and "
                f"trashed = false and "
                f"(mimeType contains 'video/')"
            )
            results = drive_service.files().list(
                q=query,
                fields="files(id, name, size)",
                pageSize=100
            ).execute()
            uploaded_files = results.get('files', [])

            for uploaded in uploaded_files:
                if uploaded.get('size') == file_info.get('size'):
                    print(f"⚠️ POSSIBLE DUPLICATE: {file_info['name']} has same size as {uploaded['name']}")
                    return True

        print(f"✅ No duplicate found for: {file_info['name']}")
        return False

    except Exception as e:
        print(f"Duplicate check failed (non-critical): {e}")
        return False


def move_to_duplicate(drive_service, file_info, pending_folder_id):
    """Move duplicate video to a 'duplicates' folder"""
    try:
        duplicate_folder_id = get_or_create_folder(drive_service, DRIVE_FOLDER_ID, 'duplicates')
        drive_service.files().update(
            fileId=file_info['id'],
            addParents=duplicate_folder_id,
            removeParents=pending_folder_id,
            fields='id, parents'
        ).execute()
        print(f"📁 Moved duplicate to 'duplicates' folder")
    except Exception as e:
        print(f"Move duplicate failed: {e}")


def get_non_duplicate_video(drive_service, pending_folder_id, uploaded_folder_id):
    """Find next video that is NOT a duplicate"""
    query = (
        f"'{pending_folder_id}' in parents and "
        f"trashed = false and "
        f"(mimeType contains 'video/')"
    )
    results = drive_service.files().list(
        q=query,
        fields="files(id, name, size)",
        orderBy="name",
        pageSize=50
    ).execute()
    files = results.get('files', [])

    if not files:
        return None

    for video in files:
        is_duplicate = check_duplicate(drive_service, video, uploaded_folder_id)
        if not is_duplicate:
            return video
        else:
            # Move duplicate out of pending
            move_to_duplicate(drive_service, video, pending_folder_id)
            send_telegram(f"⚠️ *Duplicate Skipped*\n\n📹 {video['name']}\nMoved to duplicates folder")

    return None


# ============================================================
# COMPETITOR TITLE SPY
# ============================================================
def spy_competitor_titles(youtube_service, filename):
    try:
        clean_name = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')

        # Extract key topic words
        stop_words = ['a', 'an', 'the', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'and', 'or', 'but', 'not', 'this', 'that']
        words = [w for w in clean_name.lower().split() if w not in stop_words and len(w) > 2]
        search_query = ' '.join(words[:4]) + ' shorts'

        print(f"🔍 Spying competitor titles for: {search_query}")

        # Search YouTube for similar shorts
        search_response = youtube_service.search().list(
            q=search_query,
            part='snippet',
            type='video',
            videoDuration='short',
            order='viewCount',
            maxResults=5
        ).execute()

        items = search_response.get('items', [])
        if not items:
            print("No competitor videos found")
            return ""

        competitor_titles = []
        for item in items:
            title = item['snippet']['title']
            competitor_titles.append(title)

        print(f"🕵️ Found {len(competitor_titles)} competitor titles:")
        for t in competitor_titles:
            print(f"   → {t}")

        spy_data = "\n\nTOP PERFORMING COMPETITOR TITLES FOR SIMILAR CONTENT:\n"
        for t in competitor_titles:
            spy_data += f"- \"{t}\"\n"
        spy_data += "\nAnalyze their patterns (emoji usage, word choice, hooks) and create something BETTER.\n"

        return spy_data

    except Exception as e:
        print(f"Competitor spy failed (non-critical): {e}")
        return ""


# ============================================================
# GOOGLE TRENDS
# ============================================================
def get_trending_topics():
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=360)
        trending = pytrends.trending_searches(pn='united_states')
        topics = trending[0].tolist()[:10]
        print(f"📈 Trending: {', '.join(topics[:5])}")
        return topics
    except Exception as e:
        print(f"Trends fetch failed (non-critical): {e}")
        return []


# ============================================================
# SELF LEARNING - READ PAST PERFORMANCE
# ============================================================
def get_learning_data():
    if not SPREADSHEET_ID or not SERVICE_ACCOUNT_JSON:
        return ""
    try:
        sa_info = json.loads(SERVICE_ACCOUNT_JSON)
        creds = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        sheets = build('sheets', 'v4', credentials=creds)

        result = sheets.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A:I'
        ).execute()

        rows = result.get('values', [])
        if len(rows) < 3:
            return ""

        data_rows = rows[1:]
        best_videos = sorted(
            data_rows,
            key=lambda x: int(x[6]) if len(x) > 6 and x[6].isdigit() else 0,
            reverse=True
        )[:3]

        if not best_videos:
            return ""

        learning = "\n\nLEARNING FROM YOUR BEST PERFORMING VIDEOS:\n"
        for v in best_videos:
            if len(v) > 6:
                learning += f"- Title: '{v[2]}' got {v[6]} views\n"

        print(f"🧠 Learning from {len(best_videos)} top videos")
        return learning

    except Exception as e:
        print(f"Learning data failed (non-critical): {e}")
        return ""


# ============================================================
# GOOGLE SHEETS LOGGING
# ============================================================
def log_to_sheets(video_name, title, video_url, tags, trending, category_name):
    if not SPREADSHEET_ID:
        print("No spreadsheet configured, skipping log")
        return
    try:
        sa_info = json.loads(SERVICE_ACCOUNT_JSON)
        creds = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        sheets = build('sheets', 'v4', credentials=creds)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        trends_used = ', '.join(trending[:3]) if trending else 'None'
        tags_str = ', '.join(tags)

        row = [[
            now,              # A: Date
            video_name,       # B: Filename
            title,            # C: Title
            video_url,        # D: URL
            tags_str,         # E: Tags
            trends_used,      # F: Trends Used
            "0",              # G: Views
            "0",              # H: Likes
            "0",              # I: Comments
            category_name,    # J: Category
        ]]

        sheets.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A:J',
            valueInputOption='RAW',
            body={'values': row}
        ).execute()
        print("📊 Logged to Google Sheets")
    except Exception as e:
        print(f"Sheets logging failed (non-critical): {e}")


# ============================================================
# AI METADATA GENERATION WITH ALL FEATURES
# ============================================================
def generate_ai_metadata(filename, youtube_service):
    if not GROQ_API_KEY:
        print("No Groq API key, using fallback")
        category_id, category_name = detect_category(filename)
        title, desc, tags = fallback_metadata(filename)
        return title, desc, tags, category_id, category_name

    try:
        client = Groq(api_key=GROQ_API_KEY)
        clean_name = (
            filename.rsplit('.', 1)[0]
            .replace('_', ' ')
            .replace('-', ' ')
        )

        # Get all intelligence
        title_style, description_base, base_tags = get_anti_ban_config(filename)
        trending = get_trending_topics()
        learning = get_learning_data()
        competitor_data = spy_competitor_titles(youtube_service, filename)
        category_id, category_name = detect_category(filename)

        trends_text = ""
        if trending:
            trends_text = (
                f"\n\nToday's trending topics: {', '.join(trending[:5])}"
                f"\nIf any trend relates to the video naturally, include it."
            )

        prompt = f"""You are a world-class YouTube Shorts viral content expert.

Video filename: "{clean_name}"
Video category: {category_name}
Title style needed: {title_style}{trends_text}{learning}{competitor_data}

TITLE RULES:
- Use style: {title_style}
- Maximum 80 characters
- Must end with #Shorts
- Make viewers NEED to click immediately
- Use 1-2 relevant emojis only
- Be specific to video content
- BEAT the competitor titles above

DESCRIPTION RULES:
- Write 2-3 engaging lines
- Include strong call to action
- Do NOT add hashtags (added separately)
- Make it personal and human
- Relate to {category_name} category

TAGS RULES:
- Exactly 5 tags
- Specific to {category_name} and video content
- Mix of broad and niche tags

Respond ONLY in valid JSON format:
{{"title": "your title #Shorts", "description": "your description", "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]}}"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=400,
        )

        result = response.choices[0].message.content.strip()

        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()

        metadata = json.loads(result)
        title = metadata.get("title", "")
        ai_description = metadata.get("description", "")
        ai_tags = metadata.get("tags", [])

        if not title or len(title) < 5:
            raise ValueError("Invalid title generated")

        if "#Shorts" not in title:
            title = f"{title} #Shorts"
        if len(title) > 100:
            title = title[:97] + "..."

        all_tags = list(set(ai_tags + base_tags))[:30]
        hashtags = " ".join([f"#{tag}" for tag in base_tags])
        full_description = f"{ai_description}\n\n{hashtags}"

        print(f"🤖 AI Title: {title}")
        print(f"🎨 Style: {title_style}")
        print(f"🏷️ Category: {category_name}")
        print(f"🏷️ Tags: {', '.join(all_tags[:8])}")
        return title, full_description, all_tags, category_id, category_name

    except Exception as e:
        print(f"AI generation failed: {e}")
        category_id, category_name = detect_category(filename)
        title, desc, tags = fallback_metadata(filename)
        return title, desc, tags, category_id, category_name


def fallback_metadata(filename):
    title = filename.rsplit('.', 1)[0]
    title = title.replace('_', ' ').replace('-', ' ').title()
    if "#Shorts" not in title:
        title = f"{title} #Shorts"
    if len(title) > 100:
        title = title[:97] + "..."
    _, description, tags = get_anti_ban_config(filename)
    return title, description, tags


# ============================================================
# GOOGLE SERVICES
# ============================================================
def get_drive_service():
    try:
        sa_info = json.loads(SERVICE_ACCOUNT_JSON)
        creds = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        service = build('drive', 'v3', credentials=creds)
        print("✅ Google Drive authenticated")
        return service
    except Exception as e:
        print(f"Drive auth failed: {e}")
        send_alert("Drive Auth Failed", f"Error: {e}\nTime: {datetime.now()}")
        sys.exit(1)


def get_youtube_service():
    try:
        creds = Credentials(
            token=None,
            refresh_token=REFRESH_TOKEN,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_uri='https://oauth2.googleapis.com/token',
        )
        creds.refresh(Request())
        service = build('youtube', 'v3', credentials=creds)
        print("✅ YouTube authenticated")
        return service
    except Exception as e:
        error_msg = str(e)
        print(f"YouTube auth FAILED: {error_msg}")
        send_alert(
            "🚨 TOKEN EXPIRED - ACTION NEEDED",
            f"YouTube refresh token expired!\n\n"
            f"Error: {error_msg}\n\n"
            f"Fix steps:\n"
            f"1. Open Google Colab\n"
            f"2. Run the token generation code\n"
            f"3. Update YOUTUBE_REFRESH_TOKEN in GitHub Secrets\n"
            f"4. Bot resumes automatically next cycle\n\n"
            f"Time: {datetime.now()}"
        )
        sys.exit(1)


# ============================================================
# DRIVE FOLDER OPERATIONS
# ============================================================
def get_folder_id(drive_service, parent_id, folder_name):
    query = (
        f"'{parent_id}' in parents and "
        f"name = '{folder_name}' and "
        f"mimeType = 'application/vnd.google-apps.folder' and "
        f"trashed = false"
    )
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    folders = results.get('files', [])
    return folders[0]['id'] if folders else None


def create_folder(drive_service, parent_id, folder_name):
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
    return folder['id']


def get_or_create_folder(drive_service, parent_id, folder_name):
    folder_id = get_folder_id(drive_service, parent_id, folder_name)
    if not folder_id:
        folder_id = create_folder(drive_service, parent_id, folder_name)
        print(f"📁 Created folder: {folder_name}")
    return folder_id


def count_pending(drive_service, pending_folder_id):
    query = (
        f"'{pending_folder_id}' in parents and "
        f"trashed = false and "
        f"(mimeType contains 'video/')"
    )
    results = drive_service.files().list(
        q=query, fields="files(id)", pageSize=1000
    ).execute()
    return len(results.get('files', []))


def download_video(drive_service, file_info):
    print(f"⬇️ Downloading: {file_info['name']}")
    request = drive_service.files().get_media(fileId=file_info['id'])
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file_info['name'])

    with open(temp_path, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"   Downloaded {int(status.progress() * 100)}%")

    size_mb = os.path.getsize(temp_path) / (1024 * 1024)
    print(f"✅ Downloaded: {file_info['name']} ({size_mb:.1f} MB)")
    return temp_path


def move_to_uploaded(drive_service, file_info, pending_folder_id, uploaded_folder_id):
    drive_service.files().update(
        fileId=file_info['id'],
        addParents=uploaded_folder_id,
        removeParents=pending_folder_id,
        fields='id, parents'
    ).execute()
    print("📁 Moved to uploaded folder")


# ============================================================
# YOUTUBE UPLOAD WITH AUTO RETRY
# ============================================================
def upload_to_youtube(youtube_service, video_path, filename, retry=3):
    title, description, tags, category_id, category_name = generate_ai_metadata(filename, youtube_service)

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id,
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False,
        }
    }

    for attempt in range(1, retry + 1):
        try:
            print(f"📤 Upload attempt {attempt}/{retry}...")
            media = MediaFileUpload(
                video_path,
                mimetype='video/mp4',
                resumable=True,
                chunksize=1024 * 1024
            )
            request = youtube_service.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"   Uploading... {int(status.progress() * 100)}%")

            video_id = response['id']
            video_url = f"https://youtube.com/shorts/{video_id}"
            print(f"✅ Uploaded: {video_url}")
            return video_id, video_url, title, tags, category_name

        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
            if attempt < retry:
                wait = attempt * 30
                print(f"   Retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                raise e


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("🤖 YOUTUBE SHORTS BOT v3.0")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Validate required secrets
    required = [
        'YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET',
        'YOUTUBE_REFRESH_TOKEN', 'DRIVE_FOLDER_ID',
        'GOOGLE_SERVICE_ACCOUNT'
    ]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"❌ Missing secrets: {', '.join(missing)}")
        sys.exit(1)

    # Initialize services
    drive_service = get_drive_service()
    youtube_service = get_youtube_service()

    # Get folders
    pending_folder_id = get_or_create_folder(drive_service, DRIVE_FOLDER_ID, 'pending')
    uploaded_folder_id = get_or_create_folder(drive_service, DRIVE_FOLDER_ID, 'uploaded')

    # Get next non-duplicate video
    print("\n🔍 Checking for duplicates...")
    video_info = get_non_duplicate_video(drive_service, pending_folder_id, uploaded_folder_id)

    if not video_info:
        print("📭 No videos to upload (all duplicates or empty)")
        send_alert(
            "📭 No Videos Left",
            f"All videos uploaded or duplicates!\n"
            f"Add more videos to Google Drive → YouTubeShorts → pending\n\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return

    remaining = count_pending(drive_service, pending_folder_id)
    print(f"\n📹 Videos in queue: {remaining}")
    print(f"🎬 Next video: {video_info['name']}")

    # Get trending topics
    trending = get_trending_topics()

    # Download video
    temp_path = download_video(drive_service, video_info)

    try:
        # Upload to YouTube
        video_id, video_url, title, tags, category_name = upload_to_youtube(
            youtube_service, temp_path, video_info['name']
        )

        # Move to uploaded folder
        move_to_uploaded(
            drive_service, video_info,
            pending_folder_id, uploaded_folder_id
        )

        # Log to Google Sheets
        log_to_sheets(
            video_info['name'], title, video_url,
            tags, trending, category_name
        )

        # Success summary
        print("=" * 60)
        print("🎉 SUCCESS!")
        print(f"📹 File: {video_info['name']}")
        print(f"📝 Title: {title}")
        print(f"🏷️ Category: {category_name}")
        print(f"🔗 URL: {video_url}")
        print(f"📊 Remaining: {remaining - 1}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Telegram success notification
        send_telegram(
            f"🎉 *Upload Successful!*\n\n"
            f"📹 *{title}*\n\n"
            f"🏷️ Category: {category_name}\n"
            f"🔗 {video_url}\n\n"
            f"📊 Videos remaining: {remaining - 1}\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Upload failed: {error_msg}")
        send_alert(
            "❌ Upload Failed",
            f"Video: {video_info['name']}\n"
            f"Error: {error_msg}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        sys.exit(1)

    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                os.rmdir(os.path.dirname(temp_path))
                print("🧹 Temp files cleaned")
        except:
            pass


# ============================================================
# ENTRY POINT WITH HUMAN-LIKE DELAY
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("⏳ HUMAN-LIKE DELAY SYSTEM")
    print("=" * 60)

    delay_seconds = random.randint(0, 3600)
    delay_minutes = delay_seconds // 60
    delay_secs = delay_seconds % 60

    print(f"🎲 Random delay: {delay_minutes}m {delay_secs}s")
    print(f"🕐 Upload starts after delay")

    send_telegram(
        f"🤖 *Bot Activated*\n\n"
        f"⏳ Waiting {delay_minutes} min before upload\n"
        f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    remaining = delay_seconds
    while remaining > 0:
        chunk = min(300, remaining)
        time.sleep(chunk)
        remaining -= chunk
        if remaining > 0:
            print(f"   ⏳ {remaining // 60} min remaining...")

    print("✅ Delay complete!\n")
    main()
