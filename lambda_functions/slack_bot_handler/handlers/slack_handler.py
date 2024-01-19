import json
import os
import re
import requests
import sys
sys.path.append("services")
from transcription_service import Transcriber
from summarization_service import Summarizer
from youtube_service import download_youtube_video
sys.path.append("utils")
from slack_utils import post_message

def handle_slack_event(event, slack_client):
  body_text = json.loads(event["Records"][0]["body"])

  channel = body_text["channel"]
  user = body_text["user"]
  thread_ts = body_text.get("thread_ts", None) or body_text.get("ts")

  if "files" in body_text:
    file = body_text.get("files")[0]
    filetype = file["filetype"]
    if filetype in ["mp3", "mp4", "mpeg", "m4a", "mpga", "webm", "wav"]:
      handle_file_upload(file, channel, thread_ts, slack_client)
    else:
      post_invalid_file_message(channel, thread_ts, slack_client)
  else:
    handle_text_message(body_text, channel, thread_ts, slack_client)

def handle_file_upload(file, channel, thread_ts, slack_client):
  title = file["title"]
  url = file["url_private"]
  filename = "temp." + file["filetype"]
  download_file(url, filename)

  post_message(slack_client, channel, thread_ts, f"{title}ファイルの文字起こしを行います。")

  transcriber = Transcriber()
  summarizer = Summarizer()

  transcription = transcriber.transcribe(filename)
  post_message(slack_client, channel, thread_ts, transcription)

  summarized_data = summarizer.meeting_minutes(transcription)
  post_summary_message(summarized_data, title, channel, thread_ts, slack_client)
  os.remove(filename)

def download_file(url, filename):
  resp = requests.get(url, headers={'Authorization': f'Bearer {os.environ["SLACK_BOT_TOKEN"]}'})
  with open(filename, 'wb') as f:
    f.write(resp.content)

def post_invalid_file_message(channel, thread_ts, slack_client):
  output = "適合するファイルではありません。以下、いずれかの形式のファイルを添付してください。\nmp3, mp4, mpeg, mpga, m4a, wav, webm"
  post_message(slack_client, channel, thread_ts, output)

def handle_text_message(body_text, channel, thread_ts, slack_client):
  message_received = body_text['text']
  youtube_url_match = re.search(r'(https?://[^\s]+)', message_received)
  if youtube_url_match:
    process_youtube_url(youtube_url_match.group(0), message_received, channel, thread_ts, slack_client)
  else:
    post_no_file_message(channel, thread_ts, slack_client)

def process_youtube_url(youtube_url, message_received, channel, thread_ts, slack_client):
  try:
    output = "YoutubeのURLを受け取りました。処理完了までしばらくお待ちください"
    post_message(slack_client, channel, thread_ts, output)

    filename = download_youtube_video(youtube_url, '/tmp/', 'youtube_video.mp4')

    transcriber = Transcriber()
    summarizer = Summarizer()
    process_video(filename, message_received, transcriber, summarizer, channel, thread_ts, slack_client)
  except Exception as e:
    post_message(slack_client, channel, thread_ts, f"エラーが発生しました: {e}")

def process_video(filename, message_received, transcriber, summarizer, channel, thread_ts, slack_client):
  transcription = transcriber.transcribe(filename)
  if "文字起こし" in message_received and "要約" in message_received:
    summarized_data = summarizer.meeting_minutes(transcription)
    post_summary_message(summarized_data, filename, channel, thread_ts, slack_client)
  elif "要約" in message_received:
    summarized_data = summarizer.meeting_minutes(transcription)
    post_message(slack_client, channel, thread_ts, summarized_data)
  elif "文字起こし" in message_received:
    post_message(slack_client, channel, thread_ts, transcription)
  os.remove(filename)

def post_no_file_message(channel, thread_ts, slack_client):
  output = "ファイルが見つかりません。\n私はspeech to text AIです。以下、いずれかの形式のファイルを添付してください。\nmp3, mp4, mpeg, mpga, m4a, wav, webm。または、YoutubeのURLを送ってください。"
  post_message(slack_client, channel, thread_ts, output)

def post_summary_message(summarized_data, title, channel, thread_ts, slack_client):
  summary_output = f"要約しました：{title} \n *会議の要約* \n {summarized_data['会議の要約']} \n *要点* \n {summarized_data['要点']} \n *行動項目* \n {summarized_data['行動項目']}"
  post_message(slack_client, channel, thread_ts, summary_output)
