import json
import boto3
import logging
from aiohttp import ClientError
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ssm = boto3.client("ssm")
sqs = boto3.client('sqs', region_name="ap-northeast-1")

ssm = boto3.client("ssm")
slack_bot_token, input_queue_name = (
    ssm.get_parameter(Name=f"/meeting_summarizer/{name}", WithDecryption=True)["Parameter"]["Value"]
    for name in [
        "slack_bot_token", 
        "input_queue_name"
    ]
)

slack_client = WebClient(token=slack_bot_token)

def _sendToSqS(queue_url: str, event: dict):
    try:
        message_body = json.dumps(event)
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body
        )
    except ClientError as error:
        logger.exception("Send message failed: %s", message_body)
        raise error
    else:
        logger.info(f"SQS Response: {response}")
        return response

def push_file_info_to_sqs(event):
    # Extract the nested 'event' dictionary
    slack_event = event.get("event", {})

    print(slack_event)

    # Access channel and other information from the nested event
    channel = slack_event.get("channel")
    user_id = slack_event.get("user")
    thread_ts = slack_event.get("thread_ts") or slack_event.get("ts")
    message_received = slack_event.get("text")

    # Retrieve the SQS queue URL
    queue_url = sqs.get_queue_url(QueueName=input_queue_name).get('QueueUrl')

    # Send the entire event to SQS
    sqs_response = _sendToSqS(queue_url, slack_event)
    logger.info(f"SQS Response: {sqs_response}")

    return {"ok": True}

def handler(event, context):
    push_file_info_to_sqs(event)