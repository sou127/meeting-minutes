import os
from handlers.slack_handler import handle_slack_event
from utils.slack_utils import create_slack_client
from utils.ssm_utils import get_ssm_parameters

def handler(event, context):
    slack_bot_token, slack_signing_secret, openai_api_key = get_ssm_parameters([
        "slack_bot_token", "slack_signing_secret", "openai_api_key"
    ])

    os.environ["OPENAI_API_KEY"] = openai_api_key
    slack_client = create_slack_client(slack_bot_token)

    handle_slack_event(event, slack_client)