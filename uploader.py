import os
import json
import sys
import tempfile
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

CLIENT_ID = os.environ.get('YOUTUBE_CLIENT_ID')
CLIENT_SECRET = os.environ.get('YOUTUBE_CLIENT_SECRET')
REFRESH_TOKEN = os.environ.get('YOUTUBE_REFRESH_TOKEN')
DRIVE_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID')
SERVICE_ACCOUNT_JSON = os.environ.get('GOOGLE_SERVICE_ACCOUNT')
ALERT_EMAIL = os.environ.get('ALERT_EMAIL', '')
ALERT_APP_PASSWORD = os.environ.get('ALERT_APP_PASSWORD', '')

DEFAULT_TAGS = ["shorts", "viral", "trending", "fyp"]
DEFAULT_DESCRIPTION = """Watch till the end!

Like and Subscribe for more!

#Shorts #Viral #Trending"""


def send_alert(subject, message):
    if not ALERT_EMAIL or not ALERT_APP_PASSWORD:
        print("No alert email configured, skipping alert")
        return
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
        print(f"Alert email sent: {subject}")
    except Exception as e:
        print(f"Failed to send alert: {e}")


def get_drive_service():
    sa_info = json.loads(SERVICE_ACCOUNT_JSON)
    creds = service_account.Credentials.from_service_account_info(
        sa_info,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    service = build('drive', 'v3', credentials=creds)
    print("Drive authenticated")
    return service


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
        print("YouTube authenticated")
        return service
    except Exception as e:
        error_msg = str(e)
        print(f"YouTube auth FAILED: {error_msg}")
        send_alert(
            "TOKEN EXPIRED - ACTION NEEDED",
            f"YouTube refresh token expired!\n\n"
            f"Error: {error_msg}\n\n"
            f"Fix steps:\n"
            f"1. Go to Google Colab\n"
            f"2. Run the token generation code\n"
            f"3. Update YOUTUBE_REFRESH_TOKEN in GitHub Secrets\n"
            f"4. Bot will auto-resume next cycle\n\n"
            f"Time: {datetime.now()}"
        )
        sys.exit(1)


def get_pending_folder_id(drive_service):
    query = (
        f"'{DRIVE_FOLDER_ID}' in parents and "
        f"name = 'pending' and "
        f"mimeType = 'application/vnd.google-apps.folder' and "
        f"trashed = false"
    )
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    folders = results.get('files', [])
    if not folders:
        print("No pending folder found")
        return None
    return folders[0]['id']


def get_uploaded_folder_id(drive_service):
    query = (
        f"'{DRIVE_FOLDER_ID}' in parents and "
        f"name = 'uploaded' and "
        f"mimeType = 'application/vnd.google-apps.folder' and "
        f"trashed = false"
    )
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    folders = results.get('files', [])
    if not folders:
        folder_metadata = {
            'name': 'uploaded',
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [DRIVE_FOLDER_ID]
        }
        folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
        return folder['id']
    return folders[0]['id']


def get_next_video(drive_service, pending_folder_id):
    query = (
        f"'{pending_folder_id}' in parents and "
        f"trashed = false and "
        f"(mimeType contains 'video/')"
    )
    results = drive_service.files().list(
        q=query,
        fields="files(id, name, size)",
        orderBy="name",
        pageSize=1
    ).execute()
    files = results.get('files', [])
    if not files:
        return None
    return files[0]


def count_pending(drive_service, pending_folder_id):
    query = (
        f"'{pending_folder_id}' in parents and "
        f"trashed = false and "
        f"(mimeType contains 'video/')"
    )
    results = drive_service.files().list(
        q=query,
        fields="files(id)",
        pageSize=1000
    ).execute()
    return len(results.get('files', []))


def download_video(drive_service, file_info):
    request = drive_service.files().get_media(fileId=file_info['id'])
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file_info['name'])
    with open(temp_path, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Downloaded {int(status.progress() * 100)}%")
    print(f"Downloaded: {file_info['name']}")
    return temp_path


def upload_to_youtube(youtube_service, video_path, filename):
    title = filename.rsplit('.', 1)[0]
    title = title.replace('_', ' ').replace('-', ' ').title()
    if "#Shorts" not in title:
        title = f"{title} #Shorts"
    if len(title) > 100:
        title = title[:97] + "..."

    body = {
        'snippet': {
            'title': title,
            'description': DEFAULT_DESCRIPTION,
            'tags': DEFAULT_TAGS,
            'categoryId': '22',
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False,
        }
    }

    media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True, chunksize=1024*1024)
    request = youtube_service.videos().insert(part='snippet,status', body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    video_id = response['id']
    video_url = f"https://youtube.com/shorts/{video_id}"
    print(f"Uploaded: {video_url}")
    return video_id, video_url


def move_to_uploaded(drive_service, file_info, pending_folder_id, uploaded_folder_id):
    drive_service.files().update(
        fileId=file_info['id'],
        addParents=uploaded_folder_id,
        removeParents=pending_folder_id,
        fields='id, parents'
    ).execute()
    print("Moved to uploaded folder")


def main():
    print(f"Bot started: {datetime.now()}")
    print("=" * 50)

    required = ['YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET', 'YOUTUBE_REFRESH_TOKEN', 'DRIVE_FOLDER_ID', 'GOOGLE_SERVICE_ACCOUNT']
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"Missing: {', '.join(missing)}")
        sys.exit(1)

    drive_service = get_drive_service()
    youtube_service = get_youtube_service()

    pending_folder_id = get_pending_folder_id(drive_service)
    if not pending_folder_id:
        print("No pending folder. Exiting.")
        return

    video_info = get_next_video(drive_service, pending_folder_id)
    if not video_info:
        print("No videos to upload. Exiting.")
        send_alert(
            "No Videos Left",
            f"All videos uploaded!\n"
            f"Add more videos to Drive → YouTubeShorts → pending\n"
            f"Time: {datetime.now()}"
        )
        return

    remaining = count_pending(drive_service, pending_folder_id)
    print(f"Videos in queue: {remaining}")
    print(f"Next video: {video_info['name']}")

    temp_path = download_video(drive_service, video_info)

    try:
        video_id, video_url = upload_to_youtube(youtube_service, temp_path, video_info['name'])
        uploaded_folder_id = get_uploaded_folder_id(drive_service)
        move_to_uploaded(drive_service, video_info, pending_folder_id, uploaded_folder_id)

        print("=" * 50)
        print("SUCCESS!")
        print(f"Video: {video_info['name']}")
        print(f"URL: {video_url}")
        print(f"Remaining: {remaining - 1}")
        print("=" * 50)

    except Exception as e:
        error_msg = str(e)
        print(f"Upload failed: {error_msg}")
        send_alert(
            "Upload Failed",
            f"Video: {video_info['name']}\n"
            f"Error: {error_msg}\n"
            f"Time: {datetime.now()}"
        )
        sys.exit(1)

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            os.rmdir(os.path.dirname(temp_path))


if __name__ == '__main__':
    main()
