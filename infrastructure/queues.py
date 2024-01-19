from aws_cdk import aws_sqs as sqs, core

def create_sqs_queue(scope, app_name):
    return sqs.Queue(
        scope, f"{app_name}SQSQueue",
        visibility_timeout=core.Duration.seconds(5400),
        queue_name=f'{app_name}SQSQueue'
    )
