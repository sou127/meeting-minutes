#!/usr/bin/env python3

import aws_cdk as cdk

from meeting_summarizer.meeting_summarizer_stack import MeetingSummarizerStack


app = cdk.App()
MeetingSummarizerStack(app, "MeetingSummarizerStack")

app.synth()
