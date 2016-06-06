# TT Content Analytics

### What is this?

Scripts and a Dockerfile for running analytics. Currently contains two main scripts that we run at once: content analytics, and search analytics.

### Why the scripts?

*Content analytics* give regular updates on the quantity and quality of our content; how many stories get published, who they're authored by, how they're tagged, and so on. This script is subject to change if we decide we want different data or formats.

*Search analytics* display query terms that users (and bots) have searched for on our main site. This is also subject to change if we decide to add richer data, such as metadata on the user and context.

### Why the Dockerfile?

These scripts hook up to Google Docs (in order to upload analytics spreadsheets) and Slack (in order to post them to the #analytics channel). So the Dockerfile sets up an image that includes python packages to help with the Google and Slack auth and integrations.

### How can I use it?

You can use it as-is, but you need a couple things:

- Supply Google service account credentials in the form of a JSON file that lives at `/etc/ssl/certs/tt-googledrive-credentials.json` inside Docker. For more details about the service account JSON file, see [their docs](https://developers.google.com/identity/protocols/OAuth2ServiceAccount) (the Trib's credentials live in Rundeck).
- Supply the Tribune's Scalyr API token as a Docker env var, which you can find at https://www.scalyr.com/keys, or in our Rundeck/Ansible repo.

Once you have the creds, you can run the Docker like so:

    docker pull texastribune/tt-content-analytics
    export SCALYR_API_KEY='<my-api-key-here>'
    docker run --rm --env=SCALYR_API_KEY --volume=/path/to/your/credentials.json:/etc/ssl/certs/tt-googledrive-credentials.json texastribune/tt-content-analytics
