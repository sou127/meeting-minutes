import os
import re
import sys
import json
import requests
sys.path.append("utils")
sys.path.append("services")
from slack_utils import post_message
from transcription_service import Transcriber
from summarization_service import Summarizer
from youtube_service import download_youtube_video

def handle_slack_event(event, slack_client, slack_bot_token):
  '''
  Main Slack Handler Function
  '''
  body_text = json.loads(event["Records"][0]["body"])

  channel = body_text["channel"]
  user = body_text["user"]
  thread_ts = body_text.get("thread_ts", None) or body_text.get("ts")

  if "files" in body_text:
    file = body_text.get("files")[0]
    filetype = file["filetype"]
    title = file["title"]
    if filetype in ["mp3", "mp4", "mpeg", "m4a", "mpga", "webm", "wav"]:
      post_message(slack_client, channel, thread_ts, f"Processing {title}. Please wait a moment!")
      handle_file_upload(file, channel, thread_ts, slack_client, slack_bot_token)
    else:
      post_invalid_file_message(channel, thread_ts, slack_client)
  else:
    handle_text_message(body_text, channel, thread_ts, slack_client)

# file upload handlers
def download_file(url, filename, slack_bot_token):
  resp = requests.get(url, headers={'Authorization': f'Bearer {slack_bot_token}'})
  with open(filename, 'wb') as f:
    f.write(resp.content)

def handle_file_upload(file, channel, thread_ts, slack_client, slack_bot_token):
  '''
  File upload handler. This runs when user uploads a valid media file.
  '''
  title = file["title"]
  url = file["url_private"]
  filename = "/tmp/temp." + file["filetype"]
  download_file(url, filename, slack_bot_token)

  transcriber = Transcriber()
  summarizer = Summarizer()

  transcription = transcriber.transcribe(filename)
  post_message(slack_client, channel, thread_ts, transcription)

  summarized_data = summarizer.meeting_minutes(transcription)
  post_summary_message(summarized_data, title, channel, thread_ts, slack_client)
  # remove file from lambda environment after processing
  os.remove(filename)

# handler
def handle_text_message(body_text, channel, thread_ts, slack_client):
  message_received = body_text['text']
  youtube_url_match = re.search(r'(https?://[^\s]+)', message_received)
  if youtube_url_match:
    process_youtube_url(youtube_url_match.group(0), message_received, channel, thread_ts, slack_client)
  else:
    post_no_file_message(channel, thread_ts, slack_client)


def process_youtube_url(youtube_url, message_received, channel, thread_ts, slack_client):
  try:
    output = "Youtube URL received. Please wait a moment while the process is completed."
    post_message(slack_client, channel, thread_ts, output)

    filename = download_youtube_video(youtube_url, '/tmp/', 'youtube_video.mp4')

    transcriber = Transcriber()
    summarizer = Summarizer()
    process_video(filename, message_received, transcriber, summarizer, channel, thread_ts, slack_client)
  except Exception as e:
    post_message(slack_client, channel, thread_ts, f"Error occured: {e}")


def process_video(filename, message_received, transcriber, summarizer, channel, thread_ts, slack_client):
  transcription = transcriber.transcribe(filename)
  if "transcribe" in message_received and "summarize" in message_received:
    summarized_data = summarizer.meeting_minutes(transcription)
    post_summary_message(summarized_data, filename, channel, thread_ts, slack_client)
  elif "summarize" in message_received:
    summarized_data = summarizer.meeting_minutes(transcription)
    post_message(slack_client, channel, thread_ts, summarized_data)
  elif "transcribe" in message_received:
    post_message(slack_client, channel, thread_ts, transcription)
  os.remove(filename)

# Posting Messages Functions
def post_summary_message(summarized_data, title, channel, thread_ts, slack_client):
  '''
  posts summary
  '''
  summary_output = f"Summarized {title} \n *Summary* \n {summarized_data['summary']} \n *Key Points* \n {summarized_data['key_points']} \n *Action Items* \n {summarized_data['action_items']}"
  post_message(slack_client, channel, thread_ts, summary_output)

def post_invalid_file_message(channel, thread_ts, slack_client):
  '''
  posts invalid file message
  '''
  output = f"Invalid file. Please attach files in one of the following formats. \n mp3, mp4, mpeg, mpga, m4a, wav, webm"
  post_message(slack_client, channel, thread_ts, output)

def post_no_file_message(channel, thread_ts, slack_client):
  '''
  posts no file message
  '''
  output = "File not found. \n I am a speech to text AI Assistant. Please attach a file in one of the following formats. \nmp3, mp4, mpeg, mpga, m4a, wav, webm. or send me the Youtube URL."
  post_message(slack_client, channel, thread_ts, output)
