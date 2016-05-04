import datetime
import csv
import json
from collections import Counter
from urllib import urlopen
from urllib2 import urlencode
import StringIO


class TexasTribuneAPI(object):
    api_url = 'https://www.texastribune.org/api/'

    def __init__(self, api_url=None, start=None, end=None):
        if api_url:
            self.api_url = api_url
        self.start = start
        self.end = end

    def call(self, endpoint, params):
        params['start_date'] = params.get('start_date') or self.start + 'T00:00'
        params['end_date'] = params.get('end_date') or self.end + 'T00:00'
        params['offset'] = params.get('offset') or 0
        params['limit'] = params.get('limit') or 100
        results = []
        while True:
            r = urlopen(self.api_url + endpoint + '?' + urlencode(params))
            response = json.loads(r.read())
            results += response['results']
            if not response['next']:
                break
            params['offset'] += params['limit']
        return results

    def story(self):
        params = {'fields': 'body'}
        return self.call('stories/', params)

    def content(self):
        params = {'content_type': 'story,video,audio,pointer', 'fields': 'all'}
        return self.call('content/', params)


class ContentAnalytics(object):
    num_days = 7
    _results = None

    def __init__(self, days=None, end=None):
        today = datetime.datetime.today().date()
        start = (today - datetime.timedelta(days=days or self.num_days)
                ).strftime('%Y-%m-%d')
        end = end or today.strftime('%Y-%m-%d')
        self._api = TexasTribuneAPI(start=start, end=end)
        self.data = {}

    @property
    def results(self):
        if self._results is None:
            self._results = self._api.content()
        return self._results

    @property
    def filename(self):
        if not getattr(self, '_filename', None):
            self._filename = 'content-analytics_%s_%s.csv' % (
                self._api.start, self._api.end)
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
        stories = [story['body'] for story in self._api.story()]
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
