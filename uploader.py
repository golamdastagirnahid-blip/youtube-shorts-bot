# ================================================================
# YouTube Shorts Bot v6.0 — BULLETPROOF / SELF-HEALING
# ================================================================
import os
import json
import sys
import random
import tempfile
import smtplib
import hashlib
import urllib.request
import urllib.parse
import base64
import re
import time
import traceback
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
from groq import Groq

# ================================================================
CLIENT_ID         = os.environ.get('YOUTUBE_CLIENT_ID')
CLIENT_SECRET     = os.environ.get('YOUTUBE_CLIENT_SECRET')
REFRESH_TOKEN     = os.environ.get('YOUTUBE_REFRESH_TOKEN')
DRIVE_FOLDER_ID   = os.environ.get('DRIVE_FOLDER_ID')
SA_JSON           = os.environ.get('GOOGLE_SERVICE_ACCOUNT')
ALERT_EMAIL       = os.environ.get('ALERT_EMAIL', '')
ALERT_PASSWORD    = os.environ.get('ALERT_APP_PASSWORD', '')
GROQ_API_KEY      = os.environ.get('GROQ_API_KEY', '')
SPREADSHEET_ID    = os.environ.get('SPREADSHEET_ID', '')
TG_TOKEN          = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TG_CHAT           = os.environ.get('TELEGRAM_CHAT_ID', '')
GH_TOKEN          = os.environ.get('GH_TOKEN', '')
GITHUB_REPO       = os.environ.get('GITHUB_REPOSITORY', '')

MAX_VIDEO_RETRIES = 3   # After this many failures, video moves to failed/
RETRY_PREFIX_RE   = re.compile(r'^retry(\d+)_')

# ================================================================
CATEGORY_MAP = {
    "film": "1", "animation": "1", "movie": "1", "cinema": "1",
    "car": "2", "vehicle": "2", "driving": "2", "motorcycle": "2",
    "music": "10", "song": "10", "singing": "10", "dance": "10",
    "concert": "10", "dj": "10", "beat": "10",
    "pet": "15", "animal": "15", "dog": "15", "cat": "15",
    "wildlife": "15", "nature": "15", "bird": "15", "fish": "15",
    "sport": "17", "fitness": "17", "gym": "17", "workout": "17",
    "football": "17", "basketball": "17", "soccer": "17",
    "cricket": "17", "tennis": "17", "yoga": "17",
    "travel": "19", "village": "19", "city": "19", "tourism": "19",
    "destination": "19", "landscape": "19", "monsoon": "19",
    "highland": "19", "scottish": "19", "medieval": "19",
    "riverside": "19", "mountain": "19", "forest": "19",
    "beach": "19", "island": "19", "desert": "19",
    "gaming": "20", "game": "20", "minecraft": "20",
    "fortnite": "20", "gta": "20", "playstation": "20",
    "vlog": "22", "blog": "22", "daily": "22", "lifestyle": "22",
    "motivation": "22", "inspire": "22", "success": "22",
    "asmr": "22", "satisfying": "22", "relaxing": "22",
    "comedy": "23", "funny": "23", "humor": "23",
    "meme": "23", "joke": "23", "prank": "23",
    "entertainment": "24", "challenge": "24", "reaction": "24",
    "news": "25", "politics": "25", "world": "25",
    "howto": "26", "tutorial": "26", "diy": "26",
    "tips": "26", "hack": "26", "food": "26",
    "cooking": "26", "recipe": "26", "kitchen": "26",
    "fashion": "26", "beauty": "26", "makeup": "26",
    "education": "27", "science": "27", "history": "27",
    "fact": "27", "knowledge": "27", "learning": "27",
    "tech": "28", "technology": "28", "phone": "28",
    "computer": "28", "ai": "28", "robot": "28", "iphone": "28",
}

CATEGORY_NAMES = {
    "1": "Film & Animation",    "2": "Autos & Vehicles",
    "10": "Music",              "15": "Pets & Animals",
    "17": "Sports",             "19": "Travel & Events",
    "20": "Gaming",             "22": "People & Blogs",
    "23": "Comedy",             "24": "Entertainment",
    "25": "News & Politics",    "26": "Howto & Style",
    "27": "Education",          "28": "Science & Technology",
}

# ================================================================
HASHTAG_POOLS = [
    ["shorts", "viral", "trending", "fyp", "explore"],
    ["shorts", "viralvideo", "trend", "foryou", "discover"],
    ["shortvideo", "viral", "trending2024", "fypage", "recommended"],
    ["shorts", "viralshorts", "trendingshorts", "fypシ", "mustwatch"],
    ["ytshorts", "viral", "trending", "foryoupage", "entertainment"],
    ["shorts", "viralcontent", "trending", "foryoupageシ", "watchthis"],
    ["shortsvideo", "viral", "trendingnow", "fyp", "videooftheday"],
    ["shorts", "viralpost", "trending", "fyppage", "viral2024"],
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
    "🙌 Absolutely love this!\n\nHit Subscribe! 🔔\n\n{hashtags}",
    "😮 Did you see that?!\n\nLike if this surprised you! ❤️\n\n{hashtags}",
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
    "number-based listicle style with emoji",
    "cliffhanger style that demands watching",
]

# ================================================================
def send_telegram(message):
    if not TG_TOKEN or not TG_CHAT:
        return
    try:
        if len(message) > 4000:
            message = message[:3997] + "..."
        text = urllib.parse.quote(message)
        url = (
            f"https://api.telegram.org/bot{TG_TOKEN}"
            f"/sendMessage?chat_id={TG_CHAT}"
            f"&text={text}&parse_mode=Markdown"
            f"&disable_web_page_preview=true"
        )
        urllib.request.urlopen(url, timeout=15)
        print("✅ Telegram sent")
    except Exception as e:
        print(f"Telegram failed: {e}")


def telegram_success(video_name, title, video_url, category, tags, remaining,
                    trending, next_schedule, upload_seconds, file_size_mb):
    tag_str   = " ".join([f"#{t}" for t in tags[:5]])
    trend_str = ", ".join(trending[:3]) if trending else "None"
    indicator = "🟢" if remaining > 10 else "🟡" if remaining > 3 else "🔴"
    days_left = remaining // 8
    now       = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    msg = (
        f"╔══════════════════════════╗\n"
        f"║  ✅ UPLOAD SUCCESSFUL     ║\n"
        f"╚══════════════════════════╝\n\n"
        f"📹 *VIDEO INFO*\n"
        f"┣ File: `{video_name[:35]}`\n"
        f"┣ Size: `{file_size_mb:.1f} MB`\n"
        f"┣ Category: `{category}`\n"
        f"┗ Duration: `{upload_seconds:.0f} sec`\n\n"
        f"📝 *AI TITLE*\n┗ {title}\n\n"
        f"🏷️ *TAGS*\n┗ {tag_str}\n\n"
        f"📈 *TRENDS*\n┗ `{trend_str}`\n\n"
        f"🔗 *URL*\n┗ {video_url}\n\n"
        f"📊 *QUEUE*\n"
        f"┣ {indicator} Remaining: `{remaining} videos`\n"
        f"┣ Est. Days Left: `{days_left} days`\n"
        f"┗ Next Upload: `{next_schedule} UTC`\n\n"
        f"🕐 `{now}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _Shorts Bot v6.0 BULLETPROOF_"
    )
    send_telegram(msg)


def telegram_scheduled(next_schedule, remaining, note=""):
    extra = f"\n\nℹ️ {note}" if note else ""
    msg = (
        f"╔══════════════════════════╗\n"
        f"║  📅 SCHEDULE UPDATED      ║\n"
        f"╚══════════════════════════╝\n\n"
        f"⏰ Next Run: `{next_schedule} UTC`\n"
        f"📊 Remaining: `{remaining} videos`{extra}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _Shorts Bot v6.0 BULLETPROOF_"
    )
    send_telegram(msg)


def telegram_no_videos():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    msg = (
        f"╔══════════════════════════╗\n"
        f"║  📭 NO VIDEOS LEFT        ║\n"
        f"╚══════════════════════════╝\n\n"
        f"⚠️ *Action Required!*\n\n"
        f"📁 Add videos to:\n┗ Drive → YouTubeShorts → pending\n\n"
        f"💡 *Requirements:*\n"
        f"┣ Under 60 seconds\n┣ Vertical format (9:16)\n┗ MP4 format\n\n"
        f"🕐 `{now}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _Shorts Bot v6.0 BULLETPROOF_"
    )
    send_telegram(msg)


def telegram_error(video_name, error_msg, retry_info=""):
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    msg = (
        f"╔══════════════════════════╗\n"
        f"║  ❌ UPLOAD FAILED         ║\n"
        f"╚══════════════════════════╝\n\n"
        f"📹 `{video_name[:40]}`\n\n"
        f"🔴 *Error:*\n┗ `{str(error_msg)[:200]}`\n\n"
        f"🔁 {retry_info}\n\n"
        f"🕐 `{now}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _Shorts Bot v6.0 BULLETPROOF_"
    )
    send_telegram(msg)


def telegram_failed_permanently(video_name):
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    msg = (
        f"╔══════════════════════════╗\n"
        f"║  ⛔ VIDEO GIVEN UP        ║\n"
        f"╚══════════════════════════╝\n\n"
        f"📹 `{video_name[:40]}`\n\n"
        f"Failed {MAX_VIDEO_RETRIES}× — moved to `failed/` folder.\n"
        f"Queue continues with next video.\n\n"
        f"🕐 `{now}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _Shorts Bot v6.0 BULLETPROOF_"
    )
    send_telegram(msg)


def telegram_token_expired():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    msg = (
        f"╔══════════════════════════╗\n"
        f"║  🚨 TOKEN EXPIRED         ║\n"
        f"╚══════════════════════════╝\n\n"
        f"⛔ YouTube token expired!\n\n"
        f"🔧 *Fix (3 steps):*\n"
        f"┣ 1️⃣ Open Google Colab\n"
        f"┣ 2️⃣ Run token code\n"
        f"┗ 3️⃣ Update GitHub Secret\n\n"
        f"✅ Bot keeps polling every 6h until fixed.\n\n"
        f"🕐 `{now}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _Shorts Bot v6.0 BULLETPROOF_"
    )
    send_telegram(msg)


def telegram_duplicate(video_name, remaining):
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    msg = (
        f"╔══════════════════════════╗\n"
        f"║  ⚠️ DUPLICATE SKIPPED     ║\n"
        f"╚══════════════════════════╝\n\n"
        f"📹 `{video_name[:40]}`\n"
        f"Already uploaded before!\nMoved to duplicates folder.\n\n"
        f"📊 Remaining: `{remaining} videos`\n"
        f"🕐 `{now}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _Shorts Bot v6.0 BULLETPROOF_"
    )
    send_telegram(msg)


# ================================================================
def send_email(subject, body):
    if not ALERT_EMAIL or not ALERT_PASSWORD:
        return
    try:
        msg = MIMEText(body)
        msg['Subject'] = f"YouTube Bot: {subject}"
        msg['From']    = ALERT_EMAIL
        msg['To']      = ALERT_EMAIL
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(ALERT_EMAIL, ALERT_PASSWORD)
        s.send_message(msg)
        s.quit()
        print(f"✅ Email: {subject}")
    except Exception as e:
        print(f"Email failed: {e}")


# ================================================================
def update_schedule(next_run_dt, remaining, note=""):
    """Rewrite upload.yml cron. Safe to call multiple times / always."""
    if not GH_TOKEN or not GITHUB_REPO:
        print("⚠️ GH_TOKEN or GITHUB_REPO missing — cannot self-schedule")
        return False
    try:
        new_cron      = f"{next_run_dt.minute} {next_run_dt.hour} * * *"
        next_time_str = f"{next_run_dt.hour:02d}:{next_run_dt.minute:02d}"
        path    = ".github/workflows/upload.yml"
        url     = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
        headers = {
            "Authorization": f"token {GH_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            data    = json.loads(r.read().decode())
            sha     = data['sha']
            content = base64.b64decode(data['content']).decode('utf-8')

        # Replace the (single) primary cron line.
        updated = re.sub(r"cron: '[^']*'", f"cron: '{new_cron}'", content, count=1)

        if updated == content:
            print("⚠️ Cron unchanged (already same value)")
            telegram_scheduled(next_time_str, remaining, note)
            return True

        payload = json.dumps({
            "message": f"🤖 Bot scheduled: {next_time_str} UTC",
            "content": base64.b64encode(updated.encode('utf-8')).decode('utf-8'),
            "sha": sha,
        }).encode('utf-8')
        req_put = urllib.request.Request(url, data=payload, headers=headers, method='PUT')
        with urllib.request.urlopen(req_put, timeout=30):
            print(f"✅ Cron updated → {new_cron}")
        telegram_scheduled(next_time_str, remaining, note)
        return True
    except Exception as e:
        print(f"❌ Schedule update failed: {e}")
        send_telegram(f"⚠️ Self-reschedule failed: `{str(e)[:200]}`\nFailing job so workflow's emergency reschedule step takes over.")
        # Re-raise so main() exits non-zero → workflow `if: failure()` step
        # rewrites cron to ~24h from now (otherwise bot would never wake again).
        raise


# ================================================================
def get_anti_ban_config(filename):
    seed = int(hashlib.md5(filename.encode()).hexdigest()[:8], 16)
    random.seed(seed + int(datetime.utcnow().strftime('%Y%m%d%H')))
    hashtag_set = random.choice(HASHTAG_POOLS)
    desc_tmpl   = random.choice(DESCRIPTION_TEMPLATES)
    title_style = random.choice(TITLE_STYLES)
    extra = random.sample([
        "amazing", "wow", "unbelievable", "insane", "epic",
        "cool", "awesome", "incredible", "mindblowing", "satisfying",
        "beautiful", "perfect", "outstanding", "brilliant", "stunning",
    ], 4)
    all_tags  = list(set(hashtag_set + extra))
    hashtags  = " ".join([f"#{t}" for t in hashtag_set])
    desc      = desc_tmpl.format(hashtags=hashtags)
    print(f"🛡️ Style: {title_style[:45]}")
    return title_style, desc, all_tags


# ================================================================
def detect_category(filename):
    clean = (
        strip_retry_prefix(filename).rsplit('.', 1)[0]
        .replace('_', ' ').replace('-', ' ').lower()
    )
    words = clean.split()
    cat_id = "22"
    for word in words:
        if word in CATEGORY_MAP:
            cat_id = CATEGORY_MAP[word]
            break
    cat_name = CATEGORY_NAMES.get(cat_id, "People & Blogs")
    print(f"🏷️ Category: {cat_name} ({cat_id})")
    return cat_id, cat_name


# ================================================================
def get_trends():
    try:
        from pytrends.request import TrendReq
        pt      = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        topics  = pt.trending_searches(pn='united_states')[0].tolist()[:10]
        print(f"📈 Trends: {', '.join(topics[:5])}")
        return topics
    except Exception as e:
        print(f"Trends unavailable (non-critical): {e}")
        return []


def get_learning_data():
    if not SPREADSHEET_ID or not SA_JSON:
        return ""
    try:
        creds  = service_account.Credentials.from_service_account_info(
            json.loads(SA_JSON),
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        sheets = build('sheets', 'v4', credentials=creds)
        result = sheets.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range='Sheet1!A:J'
        ).execute()
        rows = result.get('values', [])
        if len(rows) < 3:
            return ""
        data = rows[1:]
        best = sorted(
            [r for r in data if len(r) > 6],
            key=lambda x: int(x[6]) if x[6].isdigit() else 0,
            reverse=True
        )[:3]
        if not best:
            return ""
        out = "\n\nLEARN FROM BEST PERFORMING TITLES:\n"
        for r in best:
            out += f"- '{r[2]}' → {r[6]} views\n"
        print(f"🧠 Learning from {len(best)} videos")
        return out
    except Exception as e:
        print(f"Learning failed (non-critical): {e}")
        return ""


def spy_competitors(yt_service, filename):
    try:
        clean = strip_retry_prefix(filename).rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
        stopwords = {'a','an','the','in','on','at','to','for','of','with','by','from','is','are','was','and','or'}
        words = [w for w in clean.lower().split() if w not in stopwords and len(w) > 2]
        query = ' '.join(words[:3]) + ' shorts'
        print(f"🕵️ Competitor search: {query}")
        res = yt_service.search().list(
            q=query, part='snippet', type='video',
            videoDuration='short', order='viewCount', maxResults=3
        ).execute()
        titles = [i['snippet']['title'] for i in res.get('items', [])]
        if not titles:
            return ""
        out = "\n\nTOP COMPETITOR TITLES (Create something BETTER):\n"
        for t in titles:
            out += f'- "{t}"\n'
        return out
    except Exception as e:
        print(f"Competitor spy failed (non-critical): {e}")
        return ""


def log_to_sheets(video_name, title, url, tags, trending, category_name):
    if not SPREADSHEET_ID or not SA_JSON:
        return
    try:
        creds  = service_account.Credentials.from_service_account_info(
            json.loads(SA_JSON),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        sheets = build('sheets', 'v4', credentials=creds)
        row = [[
            datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
            strip_retry_prefix(video_name),
            title, url,
            ', '.join(tags[:10]),
            ', '.join(trending[:3]) if trending else 'None',
            "0", "0", "0", category_name,
        ]]
        sheets.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A:J',
            valueInputOption='RAW',
            body={'values': row}
        ).execute()
        print("📊 Logged to Sheets")
    except Exception as e:
        print(f"Sheets log failed (non-critical): {e}")


# ================================================================
def generate_metadata(filename, yt_service, trending):
    cat_id, cat_name = detect_category(filename)
    title_style, base_desc, base_tags = get_anti_ban_config(filename)
    clean_name = strip_retry_prefix(filename)

    if not GROQ_API_KEY:
        title = clean_name.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
        if "#Shorts" not in title:
            title = f"{title} #Shorts"
        return title[:100], base_desc, base_tags, cat_id, cat_name

    try:
        clean    = clean_name.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
        learning = get_learning_data()
        spy_data = spy_competitors(yt_service, clean_name)
        trend_text = ""
        if trending:
            trend_text = (
                f"\n\nToday's trending: {', '.join(trending[:5])}"
                "\nInclude relevant trend ONLY if it naturally fits."
            )
        prompt = f"""You are a world-class YouTube Shorts viral expert.

Video filename: "{clean}"
Category: {cat_name}
Title style: {title_style}{trend_text}{learning}{spy_data}

TITLE RULES:
- Use style: {title_style}
- Max 80 characters total
- Must end with #Shorts
- 1-2 emojis maximum
- Make viewer NEED to click instantly

DESCRIPTION RULES:
- 2-3 lines only
- Strong call to action
- NO hashtags in description

TAGS RULES:
- Exactly 5 tags
- Relevant to video + category
- No spaces in tags

Reply ONLY valid JSON (no extra text):
{{"title":"title here #Shorts","description":"description here","tags":["t1","t2","t3","t4","t5"]}}"""

        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.85, max_tokens=350,
        )
        raw = response.choices[0].message.content.strip()
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        meta  = json.loads(raw)
        title = meta.get("title", "").strip()
        desc  = meta.get("description", "").strip()
        tags  = meta.get("tags", [])
        if not title or len(title) < 5:
            raise ValueError("Empty/short title")
        if "#Shorts" not in title:
            title = f"{title} #Shorts"
        if len(title) > 100:
            title = title[:97] + "..."
        all_tags = list(dict.fromkeys(tags + base_tags))[:30]
        hashtag_block = " ".join([f"#{t}" for t in base_tags[:6]])
        full_desc     = f"{desc}\n\n{hashtag_block}"
        print(f"🤖 Title: {title}")
        return title, full_desc, all_tags, cat_id, cat_name
    except Exception as e:
        print(f"AI failed ({e}) → fallback")
        title = clean_name.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
        if "#Shorts" not in title:
            title = f"{title} #Shorts"
        if len(title) > 100:
            title = title[:97] + "..."
        return title, base_desc, base_tags, cat_id, cat_name


# ================================================================
def get_drive():
    creds = service_account.Credentials.from_service_account_info(
        json.loads(SA_JSON),
        scopes=['https://www.googleapis.com/auth/drive']
    )
    svc = build('drive', 'v3', credentials=creds)
    print("✅ Drive ready")
    return svc


def get_youtube():
    creds = Credentials(
        token=None, refresh_token=REFRESH_TOKEN,
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
        token_uri='https://oauth2.googleapis.com/token',
    )
    creds.refresh(Request())
    svc = build('youtube', 'v3', credentials=creds)
    print("✅ YouTube ready")
    return svc


# ================================================================
def get_or_create_folder(drive, parent, name):
    q = (f"'{parent}' in parents and name='{name}' and "
         f"mimeType='application/vnd.google-apps.folder' and trashed=false")
    res = drive.files().list(q=q, fields="files(id)").execute()
    lst = res.get('files', [])
    if lst:
        return lst[0]['id']
    f = drive.files().create(
        body={'name': name, 'mimeType': 'application/vnd.google-apps.folder',
              'parents': [parent]},
        fields='id'
    ).execute()
    print(f"📁 Created: {name}")
    return f['id']


def count_videos(drive, folder_id):
    res = drive.files().list(
        q=(f"'{folder_id}' in parents and trashed=false and (mimeType contains 'video/')"),
        fields="files(id)", pageSize=1000,
    ).execute()
    return len(res.get('files', []))


def get_next_video(drive, folder_id):
    res = drive.files().list(
        q=(f"'{folder_id}' in parents and trashed=false and (mimeType contains 'video/')"),
        fields="files(id, name, size)", orderBy="name", pageSize=1,
    ).execute()
    files = res.get('files', [])
    return files[0] if files else None


def strip_retry_prefix(name):
    return RETRY_PREFIX_RE.sub('', name)


def get_retry_count(name):
    m = RETRY_PREFIX_RE.match(name)
    return int(m.group(1)) if m else 0


def bump_retry_prefix(drive, file_info):
    """Rename file in Drive to retry<N+1>_<original>. Used after a failure
    so subsequent runs know how many times this video has failed."""
    try:
        n = get_retry_count(file_info['name'])
        base = strip_retry_prefix(file_info['name'])
        new_name = f"retry{n + 1}_{base}"
        drive.files().update(fileId=file_info['id'], body={'name': new_name}).execute()
        print(f"🔁 Renamed → {new_name}")
        return n + 1
    except Exception as e:
        print(f"⚠️ Could not bump retry count: {e}")
        return get_retry_count(file_info['name']) + 1


def is_duplicate(drive, file_info, uploaded_id):
    try:
        real_name = strip_retry_prefix(file_info['name'])
        res = drive.files().list(
            q=(f"'{uploaded_id}' in parents and name='{real_name}' and trashed=false"),
            fields="files(id)"
        ).execute()
        if res.get('files'):
            return True
        my_size = file_info.get('size', '0')
        if my_size != '0':
            res2 = drive.files().list(
                q=(f"'{uploaded_id}' in parents and trashed=false and (mimeType contains 'video/')"),
                fields="files(id, size)", pageSize=200,
            ).execute()
            for f in res2.get('files', []):
                if f.get('size') == my_size:
                    return True
        return False
    except Exception:
        return False


def move_file(drive, file_id, from_id, to_id, new_name=None):
    body = {}
    if new_name:
        body['name'] = new_name
    drive.files().update(
        fileId=file_id, addParents=to_id, removeParents=from_id,
        body=body if body else None, fields='id'
    ).execute()


# ================================================================
def download_video(drive, file_info):
    last_err = None
    for attempt in range(1, 4):
        try:
            print(f"⬇️ Downloading (attempt {attempt}/3): {file_info['name']}")
            req    = drive.files().get_media(fileId=file_info['id'])
            tmp    = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            loader = MediaIoBaseDownload(tmp, req)
            done   = False
            while not done:
                status, done = loader.next_chunk()
                if status:
                    print(f"   {int(status.progress() * 100)}%")
            tmp.close()
            mb = os.path.getsize(tmp.name) / (1024 * 1024)
            print(f"✅ Downloaded: {mb:.1f} MB")
            return tmp.name, mb
        except Exception as e:
            last_err = e
            print(f"❌ Download attempt {attempt} failed: {e}")
            time.sleep(attempt * 10)
    raise RuntimeError(f"Download failed after 3 attempts: {last_err}")


# ================================================================
NON_RETRYABLE_REASONS = {
    'quotaExceeded', 'dailyLimitExceeded', 'rateLimitExceeded',
    'authError', 'forbidden', 'youtubeSignupRequired',
}


def classify_error(exc):
    """Return ('retryable'|'quota'|'auth'|'permanent', message)."""
    msg = str(exc)
    if isinstance(exc, HttpError):
        try:
            content = json.loads(exc.content.decode())
            reason  = content.get('error', {}).get('errors', [{}])[0].get('reason', '')
            status  = exc.resp.status
            if reason in ('quotaExceeded', 'dailyLimitExceeded', 'rateLimitExceeded'):
                return 'quota', f"{reason} (HTTP {status})"
            if status in (401, 403) and reason in ('authError', 'forbidden'):
                return 'auth', f"{reason} (HTTP {status})"
            if status >= 500:
                return 'retryable', f"server error {status}"
            if status == 400:
                return 'permanent', f"bad request: {msg[:120]}"
        except Exception:
            pass
    if 'invalid_grant' in msg.lower() or 'token has been expired' in msg.lower():
        return 'auth', 'refresh token invalid/expired'
    if 'timed out' in msg.lower() or 'connection' in msg.lower():
        return 'retryable', msg[:120]
    return 'retryable', msg[:120]


def upload_to_youtube(yt_service, path, filename, trending):
    title, desc, tags, cat_id, cat_name = generate_metadata(filename, yt_service, trending)
    body = {
        'snippet': {'title': title, 'description': desc, 'tags': tags, 'categoryId': cat_id},
        'status':  {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False},
    }
    last_exc = None
    for attempt in range(1, 4):
        try:
            print(f"📤 Upload attempt {attempt}/3 ...")
            media = MediaFileUpload(path, mimetype='video/mp4', resumable=True,
                                    chunksize=2 * 1024 * 1024)
            req      = yt_service.videos().insert(part='snippet,status', body=body, media_body=media)
            response = None
            while response is None:
                status, response = req.next_chunk()
                if status:
                    print(f"   {int(status.progress() * 100)}%")
            vid_id  = response['id']
            vid_url = f"https://youtube.com/shorts/{vid_id}"
            print(f"✅ Live: {vid_url}")
            return vid_url, title, tags, cat_name
        except Exception as e:
            last_exc = e
            kind, why = classify_error(e)
            print(f"❌ Attempt {attempt} failed [{kind}]: {why}")
            if kind in ('quota', 'auth', 'permanent'):
                # Don't burn more attempts on non-retryable errors.
                raise
            if attempt < 3:
                wait = attempt * 30
                print(f"   Retrying in {wait}s ...")
                time.sleep(wait)
    raise last_exc


# ================================================================
def pick_next_run(kind='normal'):
    """Returns (datetime, note). Different windows for different scenarios."""
    if kind == 'quota':
        # Quota resets ~midnight Pacific = 08:00 UTC. Wait ~12h.
        minutes = random.randint(11 * 60, 13 * 60)
        return datetime.utcnow() + timedelta(minutes=minutes), "Quota cooldown ~12h"
    if kind == 'auth':
        # Token broken — retry in ~6h so user has a chance to refresh it.
        minutes = random.randint(5 * 60, 7 * 60)
        return datetime.utcnow() + timedelta(minutes=minutes), "Token issue — retry in ~6h"
    if kind == 'empty':
        # No videos in queue. Poll once a day.
        minutes = random.randint(22 * 60, 26 * 60)
        return datetime.utcnow() + timedelta(minutes=minutes), "Queue empty — polling in ~24h"
    # normal — 1 upload per ~24h, randomized across the full day so the
    # time-of-day shifts every cycle (humanized, anti-spam pacing).
    minutes = random.randint(20 * 60, 28 * 60)
    return datetime.utcnow() + timedelta(minutes=minutes), "1/day humanized pacing"


# ================================================================
def run_once():
    """Returns a tuple (next_run_kind, remaining_count). Never raises."""
    print("=" * 60)
    print("🤖 YOUTUBE SHORTS BOT v6.0 BULLETPROOF")
    print(f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)

    missing = [v for v in [
        'YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET',
        'YOUTUBE_REFRESH_TOKEN', 'DRIVE_FOLDER_ID', 'GOOGLE_SERVICE_ACCOUNT',
    ] if not os.environ.get(v)]
    if missing:
        msg = f"Missing secrets: {', '.join(missing)}"
        print(f"❌ {msg}")
        send_telegram(f"❌ Bot cannot start!\n{msg}")
        return 'auth', 0

    # ── Drive auth ──
    try:
        drive = get_drive()
    except Exception as e:
        print(f"❌ Drive auth failed: {e}")
        send_email("Drive Auth Failed", str(e))
        send_telegram(f"❌ Drive auth failed: `{str(e)[:200]}`")
        return 'auth', 0

    # ── YouTube auth ──
    try:
        yt = get_youtube()
    except Exception as e:
        print(f"❌ YouTube auth failed: {e}")
        telegram_token_expired()
        send_email("TOKEN EXPIRED", str(e))
        return 'auth', 0

    # ── Folders ──
    try:
        pending_id   = get_or_create_folder(drive, DRIVE_FOLDER_ID, 'pending')
        uploaded_id  = get_or_create_folder(drive, DRIVE_FOLDER_ID, 'uploaded')
        duplicate_id = get_or_create_folder(drive, DRIVE_FOLDER_ID, 'duplicates')
        failed_id    = get_or_create_folder(drive, DRIVE_FOLDER_ID, 'failed')
    except Exception as e:
        print(f"❌ Folder setup failed: {e}")
        send_telegram(f"⚠️ Folder setup failed: `{str(e)[:200]}`")
        return 'normal', 0

    trending = get_trends()

    video = get_next_video(drive, pending_id)
    if not video:
        print("📭 Pending folder is empty")
        telegram_no_videos()
        send_email("No Videos Left", "Add more to Drive → pending")
        return 'empty', 0

    total_pending = count_videos(drive, pending_id)
    print(f"📹 Queue: {total_pending} | Next: {video['name']}")

    # ── Duplicate check ──
    try:
        if is_duplicate(drive, video, uploaded_id):
            print(f"⚠️ Duplicate: {video['name']}")
            move_file(drive, video['id'], pending_id, duplicate_id,
                      new_name=strip_retry_prefix(video['name']))
            remaining = count_videos(drive, pending_id)
            telegram_duplicate(video['name'], remaining)
            return 'normal', remaining
    except Exception as e:
        print(f"⚠️ Duplicate check failed: {e}")

    retry_n = get_retry_count(video['name'])

    # ── Download ──
    t0 = time.time()
    try:
        temp_path, file_mb = download_video(drive, video)
    except Exception as e:
        err = str(e)
        print(f"❌ Download failed: {err}")
        new_n = bump_retry_prefix(drive, video)
        if new_n >= MAX_VIDEO_RETRIES:
            move_file(drive, video['id'], pending_id, failed_id,
                      new_name=strip_retry_prefix(video['name']))
            telegram_failed_permanently(video['name'])
        else:
            telegram_error(video['name'], err,
                           retry_info=f"Will retry next run ({new_n}/{MAX_VIDEO_RETRIES}).")
        send_email("Download Failed", f"{video['name']}\n{err}")
        return 'normal', count_videos(drive, pending_id)

    # ── Upload ──
    try:
        vid_url, title, tags, cat_name = upload_to_youtube(yt, temp_path, video['name'], trending)
        upload_seconds = time.time() - t0
        move_file(drive, video['id'], pending_id, uploaded_id,
                  new_name=strip_retry_prefix(video['name']))
        remaining = count_videos(drive, pending_id)
        log_to_sheets(video['name'], title, vid_url, tags, trending, cat_name)
        # Telegram + schedule are handled in main() after this returns.
        # Stash success info on the function for main() to pick up.
        run_once.last_success = {
            'video_name': video['name'], 'title': title, 'video_url': vid_url,
            'category': cat_name, 'tags': tags, 'remaining': remaining,
            'trending': trending, 'upload_seconds': upload_seconds, 'file_size_mb': file_mb,
        }
        return 'normal', remaining
    except Exception as e:
        err = str(e)
        kind, why = classify_error(e)
        print(f"❌ Upload failed [{kind}]: {err}")
        traceback.print_exc()

        if kind == 'quota':
            send_telegram(f"⏳ YouTube quota hit: `{why}`\nWaiting ~12h before retry.")
            send_email("Quota Hit", err)
            # Don't bump retry count — not the video's fault.
            return 'quota', count_videos(drive, pending_id)

        if kind == 'auth':
            telegram_token_expired()
            send_email("TOKEN EXPIRED", err)
            return 'auth', count_videos(drive, pending_id)

        # retryable / permanent → bump count, maybe move to failed/
        new_n = bump_retry_prefix(drive, video)
        if new_n >= MAX_VIDEO_RETRIES or kind == 'permanent':
            move_file(drive, video['id'], pending_id, failed_id,
                      new_name=strip_retry_prefix(video['name']))
            telegram_failed_permanently(video['name'])
            send_email("Video Given Up", f"{video['name']}\n{err}")
        else:
            telegram_error(video['name'], err,
                           retry_info=f"Will retry next run ({new_n}/{MAX_VIDEO_RETRIES}).")
            send_email("Upload Failed", f"{video['name']}\n{err}")
        return 'normal', count_videos(drive, pending_id)
    finally:
        try:
            os.unlink(temp_path)
            print("🧹 Temp cleaned")
        except Exception:
            pass


# ================================================================
def main():
    kind, remaining = 'normal', 0
    try:
        kind, remaining = run_once()
    except Exception as e:
        # Absolute last-resort safety net — should not normally fire,
        # since run_once() swallows everything.
        print(f"💥 Unexpected top-level error: {e}")
        traceback.print_exc()
        send_telegram(f"💥 Bot crashed unexpectedly: `{str(e)[:200]}`\nWill auto-retry in ~24h.")
        kind = 'normal'

    # ── ALWAYS reschedule, no matter what happened ──
    next_run_dt, note = pick_next_run(kind)

    success = getattr(run_once, 'last_success', None)
    if success:
        next_time_str = f"{next_run_dt.hour:02d}:{next_run_dt.minute:02d}"
        telegram_success(
            next_schedule=next_time_str,
            **{k: v for k, v in success.items()},
        )

    update_schedule(next_run_dt, remaining, note=note)
    print("✅ Run finished cleanly.")


# ================================================================
if __name__ == '__main__':
    main()
