import os
from collections import Counter
import datetime
import csv
import StringIO
import httplib2

import requests
import slacker
import apiclient
from oauth2client.service_account import ServiceAccountCredentials


class ContentAnalytics(object):
    num_days = 7
    _results = None
    api_url = 'https://www.texastribune.org/api/'

    def __init__(self, days=None, end=None):
        today = datetime.datetime.today().date()
        self.start = (today - datetime.timedelta(days=days or self.num_days)
                     ).strftime('%Y-%m-%d')
        self.end = end or today.strftime('%Y-%m-%d')
        self.data = {}

    @property
    def filename(self):
        if not getattr(self, '_filename', None):
            self._filename = 'content-analytics_%s_%s.csv' % (self.start, self.end)
        return self._filename

    def get_data(self):
        return self.data

    def flatten(self, nested_list, key):
        keyed_list = [i[key] for i in nested_list]
        try:
            keyed_list = [item.get('slug') or item.get('url') or item
                         for item in keyed_list]
        except AttributeError:
            # it's flat
            pass
        if not isinstance(keyed_list[0], (list, tuple)):
            # not a nested list, so just return as-is
            return keyed_list
        # slug is preferable, but use url as a backup
        return [item.get('slug') or item.get('url')
                for sublist in keyed_list for item in sublist]

    @property
    def results(self):
        if self._results is None:
            self._results = self.call_content_api()
        return self._results

    def call_api(self, endpoint, params):
        params['start_date'] = params.get('start_date') or self.start + 'T00:00'
        params['end_date'] = params.get('end_date') or self.end + 'T00:00'
        params['offset'] = params.get('offset') or 0
        params['limit'] = params.get('limit') or 100
        results = []
        while True:
            r = requests.get(self.api_url + endpoint, params=params)
            response = r.json()
            results += response['results']
            if not response['next']:
                break
            params['offset'] += params['limit']
        return results

    def call_story_api(self):
        params = {'fields': 'body'}
        return self.call_api('stories/', params)

    def call_content_api(self):
        params = {'content_type': 'story,video,audio,pointer', 'fields': 'all'}
        return self.call_api('content/', params)

    def _analyze(self, attr):
        if not self.results:
            print 'Could not find results!'
            return
        items = self.flatten(self.results, attr)
        item_ctr = Counter(items)
        items_per_result = float(sum(item_ctr.values())) / len(self.results)
        result = item_ctr.most_common() + [('PER STORY', '%.2f' % items_per_result)]
        self.data['%s per story' % attr.title().replace('_', ' ')] = '%.2f' % items_per_result
        return result

    def analyze_sections(self):
        results = self._analyze('sections')
        # exclude front-page from total counts
        totals = sum([r[1] for r in results[:-1] if r[0] != 'front-page'])
        items_per_result = float(totals) / len(self.results)
        results[-1] = (results[-1][0], '%.2f' % items_per_result)
        self.data['Sections per story'] = '%.2f' % items_per_result
        return results

    def analyze_tags(self):
        return self._analyze('tags')

    def analyze_location_tags(self):
        return self._analyze('location_tags')

    def analyze_primary_location(self):
        return self._analyze('primary_location')

    def analyze_tribpedia_entries(self):
        return self._analyze('tribpedia_entries')

    def analyze_authors(self):
        return self._analyze('authors')

    def analyze_related_content(self):
        results = self._analyze('related_content')
        # just limit results to those that have more than 2
        results = [r for r in results if not isinstance(r[1], int) or r[1] > 2]
        return results

    def analyze_pub_date(self):
        # bypass _analyze because this is a weird case
        items = [item['pub_date'][:10] for item in self.results]
        return Counter(items).most_common()

    def analyze_content_type(self):
        results = self._analyze('content_type')
        # just get the total count of all stories for this column
        results[-1] = ('TOTAL', len(self.results))
        self.data['Total links'] = len(self.results)
        return results

    def analyze_word_count(self):
        stories = [story['body'] for story in self.call_story_api()]
        total_word_count = sum([len(body.split(' ')) for body in stories])
        word_count_avg = total_word_count / len(self.results)
        self.data['Average word count'] = word_count_avg
        return [('AVERAGE', '%.2f' % word_count_avg),]

    def get_rows(self):
        rows = []
        methods = [m for m in dir(self) if m.startswith('analyze_')]
        for method_name in methods:
            method = getattr(self, method_name)
            result = method()
            # Add a blank row and the resource name
            cleaned_method = method_name[8:].upper().replace('_', ' ')
            rows += [('',), (cleaned_method,)]
            rows += result
        return rows

    def to_csv_file_obj(self, rows):
        output = StringIO.StringIO()
        writer = csv.writer(output)
        writer.writerows(rows)
        return output


class GoogleDriveAPI(object):
    SCOPES = 'https://www.googleapis.com/auth/drive.file'
    CREDENTIAL_FILE = 'tt-googledrive-credentials.json'
    PARENT_FOLDER = '0Byoew92ZDFFtazB2TlA1a3g4OGc'
    _service = None

    @property
    def service(self):
        """
        Gets valid Drive service account credentials from a JSON cred file.

        Returns:
            Service, the Drive service object
        """
        if self._service is None:
            if os.path.exists(self.CREDENTIAL_FILE):
                cred_path = self.CREDENTIAL_FILE
            else:
                cred_path = '/etc/ssl/certs/' + self.CREDENTIAL_FILE

            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                cred_path, scopes=self.SCOPES)

            http_auth = credentials.authorize(httplib2.Http())
            self._service = apiclient.discovery.build('drive', 'v3', http=http_auth)
        return self._service

    def get_file_url(self, file_id):
        result = self.service.files().get(
            fileId=file_id, fields='webViewLink'
        ).execute()
        return result['webViewLink']

    def share_with_texastribune(self, file_id):
        self.service.permissions().create(
            fileId=file_id,
            body={
                'role': 'writer',
                'type': 'domain',
                'domain': 'texastribune.org',
                'allowFileDiscovery': True
            }
        ).execute()

    def upload_csv(self, file_obj, doc_title=None):
        media = apiclient.http.MediaIoBaseUpload(
            file_obj, mimetype='text/csv', resumable=True)
        result = self.service.files().create(
            fields='id',
            media_body=media,
            body={
                'name': doc_title or 'untitled',
                'parents': [self.PARENT_FOLDER],
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


class SlackAPI(object):
    WEBHOOK_URL = 'https://hooks.slack.com/services/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'

    def __init__(self):
        self.client = slacker.Slacker('', incoming_webhook_url=self.WEBHOOK_URL)

    def to_webhook(self, url=None, filename=None, data=None):
        url, filename, data = url or '', filename or 'untitled', data or {}
        post_data = {
            'username': 'analyticsbot',
            'icon_emoji': ':hotbot:',
            'channel': '#analytics',
            'text': 'Here are the content analytics for this week.',
            'attachments': [{
                'fallback': '<%s|%s>' % (url,filename),
                'title': filename,
                'title_link': url,
                #'text': 'Foobar',
                'pretext': 'Click for more details.',
                'color': 'good',
                'fields': [{
                    'title': k,
                    'value': v,
                    'short': True
                } for k,v in data.items()]
            }]
        }
        self.client.incomingwebhook.post(post_data)


def run(days):
    analytics = ContentAnalytics(days=days)

    rows = analytics.get_rows()
    drive_url = GoogleDriveAPI().upload_csv(
        analytics.to_csv_file_obj(rows),
        doc_title=analytics.filename
    )
    SlackAPI().to_webhook(drive_url, analytics.filename, analytics.get_data())

if __name__ == '__main__':
    run(7)
