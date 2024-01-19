import json
import os
import boto3
from slack_bolt import App

ssm = boto3.client("ssm")
lambda_client = boto3.client("lambda")

slack_bot_token, slack_signing_secret = (
    ssm.get_parameter(Name=f"/meeting_summarizer/{name}", WithDecryption=True)["Parameter"]["Value"]
    for name in [
        "slack_bot_token", 
        "slack_signing_secret"
    ]
)

app = App(
    signing_secret=slack_signing_secret,
    token=slack_bot_token,
    process_before_response=True,
)

@app.event("app_mention")
def handler(event, context):
    payload = json.loads(event['body'])

    if 'type' in payload and payload['type'] == 'url_verification':
        return {
            'statusCode': 200,
            'body': payload['challenge']
        }
    
    try:
        event_handler_lambda = lambda_client.get_function(
            FunctionName="MeetingSummarizer-MeetingSummarizerPushToSqsLambda-RlRdhKXEqaxk"
        )
        event_handler_lambda_arn = event_handler_lambda.get("Configuration")["FunctionArn"]
        lambda_client.invoke(
            FunctionName=event_handler_lambda_arn,
            InvocationType='Event',
            Payload=json.dumps(payload)
        )
        return {
            'statusCode': 200,
            'body': json.dumps({})
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'response': 'Error processing request'
            })
        }