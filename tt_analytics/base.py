from datetime import datetime
from content import TexasTribuneAPI
import csv
import StringIO


class Analytics(object):
    def __init__(self, start=None, end=None, filename=None):
        self.start = start
        self.end = end
        self.filename = filename or 'outfile.csv'

    def get_rows(self):
        """
        Get the rows for CSV output.
        """
        raise NotImplementedError('Subclass this to make the rows')

    def to_csv_file(self, rows):
        with open(self.filename, 'w+') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    def to_csv_file_obj(self, rows):
        """
        Take the rows (e.g. from `get_rows`) and write them to a CSV file-like
        object.

        :param rows: List of rows to write to the CSV.
        """
        output = StringIO.StringIO()
        writer = csv.writer(output)
        writer.writerows(rows)
        return output


class TTAnalytics(Analytics):
    def get_rows(self):
        # Get the content data in JSON, e.g.:
        tt_api = TexasTribuneAPI(start=self.start, end=self.end)
        content = tt_api.content()
        # Transform it from JSON to a list of lists
        rows = [[c['id'], c['url']] for c in content]
        return rows


def run():
    start = datetime(2016, 1, 1)    # python date, e.g. datetime(2016, 1, 1)
    end = datetime(2016, 1, 7)      # python date
    filename = None

    analytics = TTAnalytics(start, end, filename)
    rows = analytics.get_rows()
    analytics.to_csv_file(rows)

if __name__ == '__main__':
    run()
