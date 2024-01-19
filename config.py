import os
from aws_cdk import core

APP_NAME = "MeetingSummarizer"
SSM_PARAMETER_NAMES = [
    "/meeting_summarizer/slack_bot_token", 
    "/meeting_summarizer/slack_signing_secret", 
    "/meeting_summarizer/openai_api_key",
    "/meeting_summarizer/input_queue_name"
]

ENV = core.Environment(account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION"))