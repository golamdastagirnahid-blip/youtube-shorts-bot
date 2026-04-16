import os
import json
import sys
import tempfile
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

DEFAULT_TAGS = ["shorts", "viral", "trending", "fyp"]
DEFAULT_DESCRIPTION = """Watch till the end!

Like and Subscribe for more!

#Shorts #Viral #Trending"""


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
    print(f"Uploaded: https://youtube.com/shorts/{video_id}")
    return video_id


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
        return

    print(f"Next video: {video_info['name']}")
    temp_path = download_video(drive_service, video_info)

    try:
        video_id = upload_to_youtube(youtube_service, temp_path, video_info['name'])
        uploaded_folder_id = get_uploaded_folder_id(drive_service)
        move_to_uploaded(drive_service, video_info, pending_folder_id, uploaded_folder_id)
        print("SUCCESS!")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            os.rmdir(os.path.dirname(temp_path))


if __name__ == '__main__':
    main()
