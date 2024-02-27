import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


class GoogleDrive:
    def __init__(self):
        self.creds = None
        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(self.creds.to_json())

        self.service = build("drive", "v3", credentials=self.creds)

    def create_folder_in_drive(self, name, parent_id) -> str:
        """Create a new folder in Google Drive or return the ID of an existing folder with the same name."""
        # Search for a folder with the same name
        response = (
            self.service.files()
            .list(
                q=f"name='{name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents",
                spaces="drive",
                fields="files(id, name)",
            )
            .execute()
        )

        # If the folder exists, return its ID
        if response.get("files"):
            return response.get("files")[0].get("id")

        # If the folder doesn't exist, create a new folder and return its ID
        file_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        folder = self.service.files().create(body=file_metadata, fields="id").execute()
        return folder["id"]

    def upload_folder_to_drive(self, local_folder_path, drive_folder_id) -> str:
        """Uploads folder from a local folder to a Google Drive folder."""
        try:
            # Create a subfolder in the drive_folder_id
            subfolder_name = os.path.basename(local_folder_path)
            subfolder_id = self.create_folder_in_drive(subfolder_name, drive_folder_id)

            for file_name in os.listdir(local_folder_path):
                file_path = os.path.join(local_folder_path, file_name)
                media = MediaFileUpload(file_path, resumable=True)

                # Search for a file with the same name in the subfolder
                response = (
                    self.service.files()
                    .list(
                        q=f"name='{file_name}' and '{subfolder_id}' in parents",
                        spaces="drive",
                        fields="files(id, name)",
                    )
                    .execute()
                )

                # If the file exists, update it
                if response.get("files"):
                    file_id = response.get("files")[0].get("id")
                    request = self.service.files().update(
                        fileId=file_id,
                        media_body=media,
                        body={"name": file_name},
                    )
                # If the file doesn't exist, create a new file
                else:
                    request = self.service.files().create(
                        media_body=media,
                        body={"name": file_name, "parents": [subfolder_id]},
                    )

                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        print(f"Uploaded {int(status.progress() * 100)}%.")
                print(f"Upload of {file_name} complete.")
            return subfolder_id
        except HttpError as error:
            print(f"An error occurred: {error}")
