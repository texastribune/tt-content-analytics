import os
import json
import csv
import datetime
from collections import Counter
import requests

try:
    # Python 2 version
    import StringIO
except ImportError:
    # Python 3 version
    import io as StringIO


class ScalyrAPI(object):
    api_key = None
    base_url = 'https://www.scalyr.com'

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('SCALYR_API_TOKEN')

    def _call(self, endpoint, params):
        if 'token' not in params:
            params['token'] = self.api_key
        url = self.base_url + endpoint
        r = requests.post(url,
            data=json.dumps(params),
            headers={'content-type': 'application/json'}
        )
        return r.json()

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
        print results
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
