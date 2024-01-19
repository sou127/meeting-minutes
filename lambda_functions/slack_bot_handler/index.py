import os
import re
import boto3
import json
import requests
from openai import OpenAI
from pytube import YouTube
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from summarizer import Summarizer
from transcriber import Transcriber

ssm = boto3.client("ssm")
slack_bot_token, slack_signing_secret, openai_api_key = (
    ssm.get_parameter(Name=f"/meeting_summarizer/{name}", WithDecryption=True)["Parameter"]["Value"]
    for name in [
        "slack_bot_token", 
        "slack_signing_secret", 
        "openai_api_key"
    ]
)

os.environ["OPENAI_API_KEY"] = openai_api_key

slack_client = WebClient(token=slack_bot_token)

def sendSummary(event):
    body_text = json.loads(event["Records"][0]["body"])

    channel = body_text["channel"]
    user = body_text["user"]
    thread_ts = body_text.get("thread_ts", None) or body_text.get("ts")

    if "files" in body_text:
        file = body_text.get("files")[0]
        filetype = file["filetype"]
        if filetype == "mp3" or filetype == "mp4" or filetype == "mpeg" or filetype == "m4a" or \
        filetype == "mpga" or filetype == "webm" or filetype == "wav":
            title = file["title"]
            url = file["url_private"]
            filename = "temp." + filetype
            resp = requests.get(url, headers={'Authorization': 'Bearer %s' % os.environ["SLACK_BOT_TOKEN"]})

            with open(filename, 'wb') as f:
                f.write(resp.content)

            slack_client.chat_postMessage(text=f"{title}ファイルの文字起こしを行います。", thread_ts=thread_ts, channel=channel)

            transcriber = Transcriber()
            summarizer = Summarizer()

            transcription = transcriber.transcribe(filename)
            slack_client.chat_postMessage(text=transcription, thread_ts=thread_ts, channel=channel)
            
            summarized_data = summarizer.meeting_minutes(transcription)
            slack_client.chat_postMessage(text="要約が完了するまでしばらくお待ちください。", thread_ts=thread_ts, channel=channel)

            summary_output = f"要約しました：{title} \n *会議の要約* \n {summarized_data['会議の要約']} \n *要点* \n {summarized_data['要点']} \n *行動項目* \n {summarized_data['行動項目']}"
            slack_client.chat_postMessage(text=summary_output, thread_ts=thread_ts, channel=channel)
            os.remove(filename)
        else:
            output = "適合するファイルではありません。以下、いずれかの形式のファイルを添付してください。\nmp3, mp4, mpeg, mpga, m4a, wav, webm"
            slack_client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=output
            )
    else:
        message_received = body_text['text']
        youtube_url_match = re.search(r'(https?://[^\s]+)', message_received)
        if youtube_url_match:
            youtube_url = youtube_url_match.group(0)
            try:
                output = "YoutubeのURLを受け取りました。処理完了までしばらくお待ちください"
                slack_client.chat_postMessage(text=output, thread_ts=thread_ts, channel=channel)
                yt = YouTube(youtube_url)
                video = yt.streams.filter(file_extension='mp4').first()
                filename = '/tmp/' + video.default_filename
                video.download(output_path='/tmp/', filename=filename)
                # Pass the downloaded video to transcriber and summarizer
                transcriber = Transcriber()
                summarizer = Summarizer()
                
                if "文字起こし" in message_received and "要約" in message_received:
                    transcription = transcriber.transcribe(filename)
                    summarized_data = summarizer.meeting_minutes(transcription)
                    summary_output = f"要約しました：{filename} \n *会議の要約* \n {summarized_data['会議の要約']} \n *要点* \n {summarized_data['要点']} \n *行動項目* \n {summarized_data['行動項目']}"
                    slack_client.chat_postMessage(text=transcription, thread_ts=thread_ts, channel=channel)
                    slack_client.chat_postMessage(text=summary_output, thread_ts=thread_ts, channel=channel)
                elif "要約" in message_received:
                    transcription = transcriber.transcribe(filename)
                    summarized_data = summarizer.meeting_minutes(transcription)
                    slack_client.chat_postMessage(text=summary_output, thread_ts=thread_ts, channel=channel)
                elif "文字起こし" in message_received:
                    transcription = transcriber.transcribe(filename)
                    slack_client.chat_postMessage(text=transcription, thread_ts=thread_ts, channel=channel)

                os.remove(filename)
            except Exception as e:
                slack_client.chat_postMessage(text=f"エラーが発生しました: {e}", thread_ts=thread_ts, channel=channel)
        else:
            output = "ファイルが見つかりません。\n私はspeech to text AIです。以下、いずれかの形式のファイルを添付してください。\nmp3, mp4, mpeg, mpga, m4a, wav, webm。または、YoutubeのURLを送ってください。"
            slack_client.chat_postMessage(text=output, thread_ts=thread_ts, channel=channel)
    # try:
    #     chat_response = slack_client.chat_postMessage(
    #         channel=channel,
    #         thread_ts=thread_ts,
    #         text=f"<@{user}> 処理lambdaからのメッセージ"
    #     )
    # except SlackApiError as e:
    #     print(e)
    #     print(e.__str__())

def handler(event, context):
    sendSummary(event)