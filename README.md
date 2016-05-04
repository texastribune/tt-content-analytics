# TT Content Analytics

### What is this?

A script and Dockerfile for running content analytics.

### Why the script?

We wanted to get regular updates on the quantity and quality of our content; how many stories get published, who they're authored by, how they're tagged, and so on. This script is subject to change if we decide we want different data or formats.

### Why the Dockerfile?

Thanks to the Texas Tribune API, this script doesn't need to live directly in the main Texas Tribune app. But it does hook up to Google Docs (in order to upload analytics spreadsheets) and Slack (in order to post the spreadsheet to the #analytics channel). So this Dockerfile sets up an image that includes python packages to help with the Google and Slack auth and integrations.

### How can I use it?

You can use it as-is, but you need to supply Google service account credentials in the form of a JSON file that lives at `/etc/ssl/certs/tt-googledrive-credentials.json`. For more details about the service account JSON file, see [their docs](https://developers.google.com/identity/protocols/OAuth2ServiceAccount) (the Trib's credentials live in Rundeck). Once you have the credentials file, you can mount it as a volume inside the Docker image at runtime. For example:

    docker pull texastribune/tt-content-analytics
    docker run --rm --volume=/path/to/your/credentials.json:/etc/ssl/certs/tt-googledrive-credentials.json texastribune/tt-content-analytics
