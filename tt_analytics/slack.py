from slacker import Slacker


class SlackAPI(object):
    """
    Client for integrating with the Slack API.

    :param webhook_url: URL of the Slack webhook to post to.
    :param channel: Name of the Slack channel to post to.
    """
    webhook_url = ('https://hooks.slack.com/services/'
                   'T0252VA3B/B12TZ1X2P/oxfEYPOjyWFjA4vPUISHQsdF')
    channel = '#analytics'

    def __init__(self, type='', webhook_url=None, channel=None):
        self.type = type
        if webhook_url:
            self.webhook_url = webhook_url
        if channel:
            self.channel = channel
        self.client = Slacker('', incoming_webhook_url=self.webhook_url)

    def to_webhook(self, url=None, filename=None, data=None):
        """
        Post a URL to the content analytics CSV in a Slack channel.

        :param url: URL of the CSV file to link to.
        :param filename: Name of the CSV file for presentation.
        :param data: Dict of field:value pairs to present in the Slack channel.
                     For instance, "num_stories: 70" or "average_tags: 1.2".
        """
        url, filename, data = url or '', filename or 'untitled', data or {}
        post_data = {
            'username': 'analyticsbot',
            'icon_emoji': ':hotbot:',
            'channel': self.channel,
            'text': 'Here are the %s analytics.' % self.type,
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
