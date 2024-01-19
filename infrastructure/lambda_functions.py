from aws_cdk import core, aws_lambda as lambda_
from aws_cdk.aws_lambda_python import PythonFunction, PythonLayerVersion

def create_payload_handler_lambda(scope, app_name):
  return PythonFunction(
    scope, f"{app_name}PayloadLambda", 
    entry="lambda_functions/payload_handler", 
    handler="handler", 
    runtime=lambda_.Runtime.PYTHON_3_8,
    timeout=core.Duration.seconds(900)
  )

def create_push_to_sqs_handler_lambda(scope, app_name):
  return PythonFunction(
    scope, f"{app_name}PushToSqsLambda", 
    entry="lambda_functions/push_to_sqs_handler", 
    handler="handler", 
    runtime=lambda_.Runtime.PYTHON_3_8,
    timeout=core.Duration.seconds(900),
  )

def create_slack_bot_handler_lambda(scope, app_name):
  return PythonFunction(
    scope, f"{app_name}SlackbotLambda", 
    entry="lambda_functions/slack_bot_handler", 
    handler="handler", 
    runtime=lambda_.Runtime.PYTHON_3_8,
    timeout=core.Duration.seconds(900),
  )

def create_ffmpeg_layer(scope, app_name):
  return PythonLayerVersion(
    scope, f"{app_name}FFMPEGLayer",
    entry="lambda_layers/ffmpeg_layer",
    compatible_runtimes=[lambda_.Runtime.PYTHON_3_8]
  )