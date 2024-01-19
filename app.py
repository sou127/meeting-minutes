import os
from infrastructure.queues import create_sqs_queue
from infrastructure.permissions import setup_lambda_permissions
from infrastructure.api_gateway import create_api_gateway
from infrastructure.ssm_parameters import setup_ssm_parameters
from infrastructure.lambda_functions import (
    create_payload_handler_lambda, 
    create_push_to_sqs_handler_lambda,
    create_slack_bot_handler_lambda,
    create_ffmpeg_layer
)
from aws_cdk import (
    core,
    aws_lambda_event_sources as lambda_event_sources
)

APP_NAME = "MeetingSummarizer"
SSM_PARAMETER_NAMES = [
    "/meeting_summarizer/slack_bot_token", 
    "/meeting_summarizer/slack_signing_secret", 
    "/meeting_summarizer/openai_api_key",
    "/meeting_summarizer/input_queue_name"
]

class MeetingSummarizerStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.sqs_queue = create_sqs_queue(self, APP_NAME)

        self.ffmpeg_layer = create_ffmpeg_layer(self, APP_NAME)

        self.payload_handler_lambda = create_payload_handler_lambda(self, APP_NAME)
        self.push_to_sqs_handler_lambda = create_push_to_sqs_handler_lambda(self, APP_NAME)
        self.slack_bot_handler_lambda = create_slack_bot_handler_lambda(self, APP_NAME)

        # target_lambda_arn = "arn:aws:lambda:ap-northeast-1:006860306333:function:MeetingSummarizer-MeetingSummarizerPushToSqsLambda-RlRdhKXEqaxk"
        setup_lambda_permissions(self, self.payload_handler_lambda)

        sqs_trigger = lambda_event_sources.SqsEventSource(self.sqs_queue)
        self.slack_bot_handler_lambda.add_event_source(sqs_trigger)

        # API Gateway
        self.api_gateway = create_api_gateway(self, APP_NAME, self.payload_handler_lambda)

        # IAM Permissions
        self.sqs_queue.grant_send_messages(self.push_to_sqs_handler_lambda)
        self.sqs_queue.grant_consume_messages(self.push_to_sqs_handler_lambda)

        # SSM Parameters
        lambda_identifiers = [
            "payloadHandler",
            "pushToSqsHandler",
            "slackBotHandler"
        ]
        setup_ssm_parameters(
            self, APP_NAME,
            lambda_identifiers, 
            [
                self.payload_handler_lambda, 
                self.push_to_sqs_handler_lambda,
                self.slack_bot_handler_lambda
            ]
        )
            
app = core.App()
env = core.Environment(account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION"))
MeetingSummarizerStack(app, APP_NAME, env=env)
app.synth()