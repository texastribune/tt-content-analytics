import os
import apiclient
import httplib2
from oauth2client.service_account import ServiceAccountCredentials


class GoogleDriveAPI(object):
    """
    Class for interacting with the Google Drive API.

    :param credential_file: path+filename of the JSON credentials keyfile.
    :param scopes: Authentication scopes (probably should not change).
    :param parent_folder_id: Google Drive ID of the parent folder.
    """
    credential_file = 'tt-googledrive-credentials.json'
    scopes = 'https://www.googleapis.com/auth/drive.file'
    parent_folder_id = '0Byoew92ZDFFtazB2TlA1a3g4OGc'

    _service = None

    def __init__(self, credential_file=None, scopes=None, parent_folder_id=None):
        if credential_file:
            self.credential_file = credential_file
        if scopes:
            self.scopes = scopes
        if parent_folder_id:
            self.parent_folder_id = parent_folder_id

    @property
    def service(self):
        """
        Gets an authorized Drive service account from the credential file.

        :returns: a Drive service object
        """
        if self._service is None:
            if os.path.exists(self.credential_file):
                cred_path = self.credential_file
            else:
                cred_path = '/etc/ssl/certs/' + self.credential_file

            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                cred_path, scopes=self.scopes)

            http_auth = credentials.authorize(httplib2.Http())
            self._service = apiclient.discovery.build('drive', 'v3', http=http_auth)
        return self._service

    def get_file_url(self, file_id):
        """
        Get a Google Drive file's full web view URL from its ID.

        :param file_id: The file's ID in Google Drive.
        :returns: Full URL of the file.
        """
        result = self.service.files().get(
            fileId=file_id, fields='webViewLink'
        ).execute()
        return result['webViewLink']

    def share_folder_with_user(self, email):
        """
        Share the parent folder with a specific user.

        :param email: Email address of the user to share the folder with.
        """
        body = {
            'role': 'writer',
            'type': 'user',
            'emailAddress': email
        }
        self.service.permissions().create(
            fileId=self.parent_folder_id, body=body).execute()

    def share_with_texastribune(self, file_id):
        """
        Share a file with the entire texastribune.org domain.

        :param file_id: The file's ID in Google Drive.
        """
        body = {
            'role': 'writer',
            'type': 'domain',
            'domain': 'texastribune.org',
            'allowFileDiscovery': True
        }
        self.service.permissions().create(
            fileId=file_id, body=body).execute()

    def upload_csv(self, file_obj, doc_title=None):
        """
        Uploads a CSV file to Google Drive, makes it writeable by the entire
        Texas Tribune staff, and returns the resulting file's URL.

        :param file_obj: A CSV-formatted file object.
        :param doc_title: The name of the document in Google Drive.
        :returns: Full web view URL of the uploaded file.
        """
        media = apiclient.http.MediaIoBaseUpload(
            file_obj, mimetype='text/csv', resumable=True)
        result = self.service.files().create(
            fields='id',
            media_body=media,
            body={
                'name': doc_title or 'untitled',
                'parents': [self.parent_folder_id],
                'mimeType': 'application/vnd.google-apps.spreadsheet'
            }
        ).execute()
        file_obj.close()
        if 'id' in result:
            # Make it viewable by the Texas Tribune
            self.share_with_texastribune(result['id'])
            # Get the full URL of the file and return it
            return self.get_file_url(result['id'])
        raise
