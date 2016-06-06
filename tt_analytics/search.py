import sys
import os
import json
import csv
import datetime
from collections import Counter

try:
    # Python 2 versions
    import httplib
    import StringIO
except ImportError:
    # Python 3 versions
    import http.client as httplib
    import io as StringIO


class ScalyrAPI(object):
    api_key = None
    base_url = None

    def __init__(self, api_key=None, base_url='www.scalyr.com'):
        self.api_key = api_key or os.environ.get('SCALYR_API_TOKEN')
        self.base_url = base_url

    def _call(self, endpoint, params):
        if 'token' not in params:
            params['token'] = self.api_key
        headers = {'Content-Type': 'application/json'}
        json_params = json.dumps(params)

        conn = httplib.HTTPSConnection(self.base_url)
        conn.request('POST', endpoint, json_params, headers)

        # Retrieve and parse the response.
        response = conn.getresponse()
        body = response.read().decode('utf8')

        try:
            parsed_response = json.loads(body)
        except ValueError:
            sys.stderr.write('Scalyr server returned invalid response:\n%s' % body)
            return
        return parsed_response

    def query(self, filter='', start='', end='', count=10, mode='', columns='',
                    output='json', priority='high'):
        params = {
            'filter': filter,
            'queryType': 'log',
            'startTime': start,
            'endTime': end,
            'maxCount': count,
            'pageMode': mode,
            'columns': columns,
            'output': output,
            'priority': priority
        }
        return self._call('/api/query', params)


class SearchAnalytics(object):
    num_days = 7

    def __init__(self, days=None):
        if days is not None:
            self.num_days = days
        today = datetime.datetime.today().date()
        self.start = (today - datetime.timedelta(days=self.num_days)
                     ).strftime('%Y-%m-%d')
        self.end = today.strftime('%Y-%m-%d')
        self._api = ScalyrAPI()

    @property
    def filename(self):
        if not getattr(self, '_filename', None):
            self._filename = 'search-analytics_%s_%s.csv' % (self.start, self.end)
        return self._filename

    def get_data(self):
        if not getattr(self, '_data', None):
            return {}
        return {k: v for k, v in self._data[:10]}

    def query(self, params=None):
        params = params or {}
        defaults = {
            'start': '%s days' % self.num_days,
            'filter': "$logfile='/var/log/nginx/access.log' ' /search/?'",
            'count': 5000,
            'columns': 'uriQ'
        }
        for k, v in defaults.items():
            if k not in params:
                params[k] = v

        self._results = self._api.query(**params)
        return self._results

    def process(self, results):
        searches = [unicode(match['attributes']['uriQ']).encode('utf8')
                    for match in results['matches']
                    if 'uriQ' in match['attributes']]
        # kill tinfoil searches
        searches = [s for s in searches if not 'tinfoil' in s]
        ctr = Counter(searches)
        self._data = ctr.most_common()
        return self._data

    def get_rows(self, params=None):
        results = self.query(params=params)
        rows = self.process(results)
        return rows

    def to_csv_file_obj(self, rows):
        output = StringIO.StringIO()
        writer = csv.writer(output)
        writer.writerow(['SEARCHES', ''])
        writer.writerows(rows)
        return output
