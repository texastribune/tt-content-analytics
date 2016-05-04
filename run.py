from content_analytics import ContentAnalytics
from gdocs import GoogleDriveAPI
from slack import SlackAPI

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
