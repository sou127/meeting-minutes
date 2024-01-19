from openai import OpenAI
import os

class Summarizer:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_KEY')
        )

    def transcribe_audio(self, audio_file_path):
        with open(audio_file_path, 'rb') as audio_file:
            transcription = self.client.audio.transcriptions.create("whisper-1", audio_file)
        return transcription['text']

    def abstract_summary_extraction(self, transcription):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "あなたは言語理解と要約の訓練を受けた高度に熟練したAIです。以下の文章を読み、簡潔に要約してほしい。最も重要な点を保持し、全文を読まなくても議論の要点を理解できるような、首尾一貫した読みやすい要約を目指してください。不必要な詳細や余談は避けてください。"
                },
                {
                    "role": "user",
                    "content": transcription
                }
            ]
        )
        return response.choices[0].message.content

    def key_points_extraction(self, transcription):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "あなたは、情報を要点に絞り込むことを得意とする熟練したAIです。以下の文章をもとに、議論された、あるいは提起された主なポイントを特定し、リストアップしてください。これらは、議論の本質に関わる最も重要なアイデア、発見、またはトピックでなければなりません。あなたのゴールは、誰かが読めば、何が話し合われたのかすぐに理解できるようなリストを提供することです。"
                },
                {
                    "role": "user",
                    "content": transcription
                }
            ]
        )
        return response.choices[0].message.content

    def action_item_extraction(self, transcription):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "あなたは会話を分析し、行動項目を抽出するAIの専門家です。テキストを確認し、合意された、または実行する必要があると言及されたタスク、割り当て、またはアクションを特定してください。これらは、特定の個人に割り当てられたタスクかもしれませんし、グループが決定した一般的なアクションかもしれません。これらの行動項目を明確かつ簡潔に列記してください。"
                },
                {
                    "role": "user",
                    "content": transcription
                }
            ]
        )
        return response.choices[0].message.content

    def clean_summary(self, summary):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            temperature=0.5,
            messages=[
                {
                    "role": "system",
                    "content": "あなたは、情報を要点に絞り込むことを得意とする熟練したAIです。以下の要約を洗練させ、ポイントにまとめてください。冗長な部分を削除し、一貫性と簡潔さを確保し、全体的な読みやすさを向上させてください"
                },
                {
                    "role": "user",
                    "content": summary
                }
            ]
        )
        return response.choices[0].message.content

    def meeting_minutes(self, transcription, chunk_size=500):
        # Split transcription into chunks of specified size
        words = transcription.split()
        chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

        # Initialize variables to store combined results
        combined_abstract_summary = ""
        combined_key_points = ""
        combined_action_items = ""

        # Process each chunk
        for chunk in chunks:
            abstract_summary = self.abstract_summary_extraction(chunk)
            key_points = self.key_points_extraction(chunk)
            action_items = self.action_item_extraction(chunk)

            combined_abstract_summary += abstract_summary + "\n"
            combined_key_points += key_points + "\n"
            combined_action_items += action_items + "\n"

        cleaned_summary = self.clean_summary(combined_abstract_summary)
        cleaned_key_points = self.clean_summary(combined_key_points)
        cleaned_action_items = self.clean_summary(combined_action_items)

        # Combine the results from all chunks
        return {
            '会議の要約': cleaned_summary,
            '要点': cleaned_key_points,
            '行動項目': cleaned_action_items,
        }

    def save_as_text_file(self, minutes, filename):
        with open(filename, 'w', encoding='utf-8') as txt_file:
            for key, value in minutes.items():
                # Write the section heading
                heading = ' '.join(word.capitalize() for word in key.split('_'))
                txt_file.write(heading + "\n")
                # Write the content
                txt_file.write(value + "\n\n")