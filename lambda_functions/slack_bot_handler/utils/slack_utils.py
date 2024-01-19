from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def create_slack_client(token):
    return WebClient(token=token)

def post_message(slack_client, channel, thread_ts, text):
    try:
        slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=text)
    except SlackApiError as e:
        print(f"Slack API Error: {e}")