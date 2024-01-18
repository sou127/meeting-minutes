import aws_cdk as core
import aws_cdk.assertions as assertions
from meeting_summarizer.meeting_summarizer_stack import MeetingSummarizerStack


def test_sqs_queue_created():
    app = core.App()
    stack = MeetingSummarizerStack(app, "meeting-summarizer")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::SQS::Queue", {
        "VisibilityTimeout": 300
    })


def test_sns_topic_created():
    app = core.App()
    stack = MeetingSummarizerStack(app, "meeting-summarizer")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::SNS::Topic", 1)
