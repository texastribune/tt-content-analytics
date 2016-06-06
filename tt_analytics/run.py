from content import ContentAnalytics
from search import SearchAnalytics

from gdocs import GoogleDriveAPI
from slack import SlackAPI

def _to_drive_and_slack(name, analytics):
    # Upload the rows to a CSV file in Google Drive
    drive_url = GoogleDriveAPI().upload_csv(
        analytics.to_csv_file_obj(analytics.get_rows()),
        doc_title=analytics.filename
    )
    # Finally post aggregate data and a link to the CSV in Slack
    SlackAPI(name).to_webhook(drive_url, analytics.filename, analytics.get_data())

def run_content(days):
    # Run content analytics for the last n days
    analytics = ContentAnalytics(days=days)
    # Now push to output channels
    _to_drive_and_slack('content', analytics)

def run_search(days):
    # Run search analytics for the last n days
    analytics = SearchAnalytics(days=days)
    # Now push to output channels
    _to_drive_and_slack('search', analytics)

if __name__ == '__main__':
    run_content(7)
    run_search(7)
