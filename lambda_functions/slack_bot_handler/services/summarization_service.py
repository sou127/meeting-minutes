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
                    "content": "You are a highly skilled AI trained in language comprehension and summarization. I would like you to read the following text and summarize it into a concise abstract paragraph. Aim to retain the most important points, providing a coherent and readable summary that could help a person understand the main points of the discussion without needing to read the entire text. Please avoid unnecessary details or tangential points."
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
                    "content": "You are a proficient AI with a specialty in distilling information into key points. Based on the following text, identify and list the main points that were discussed or brought up. These should be the most important ideas, findings, or topics that are crucial to the essence of the discussion. Your goal is to provide a list that someone could read to quickly understand what was talked about."
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
                    "content": "You are an AI expert in analyzing conversations and extracting action items. Please review the text and identify any tasks, assignments, or actions that were agreed upon or mentioned as needing to be done. These could be tasks assigned to specific individuals, or general actions that the group has decided to take. Please list these action items clearly and concisely."
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
                    "content": "You are a skilled AI who is adept at distilling information down to the essentials. Please refine the text and summarise it to the point. Remove redundancies, ensure consistency and brevity, and improve overall readability."
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
            'summary': cleaned_summary,
            'key_points': cleaned_key_points,
            'action_items': cleaned_action_items,
        }

    def save_as_text_file(self, minutes, filename):
        with open(filename, 'w', encoding='utf-8') as txt_file:
            for key, value in minutes.items():
                # Write the section heading
                heading = ' '.join(word.capitalize() for word in key.split('_'))
                txt_file.write(heading + "\n")
                # Write the content
                txt_file.write(value + "\n\n")