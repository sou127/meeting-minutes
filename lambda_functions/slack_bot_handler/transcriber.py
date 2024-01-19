import os
from openai import OpenAI
import subprocess
import math

class Transcriber:
    MAX_FILE_SIZE_MB = 25
    AUDIO_CHUNK_LENGTH_MS = 10 * 60 * 1000
    FFMPEG_STATIC = "/opt/python/ffmpeg/bin/ffmpeg"
    FFPROBE_STATIC = "/opt/python/ffmpeg/bin/ffprobe"

    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_KEY')
        )

    def convert_video_to_audio(self, video_path, audio_path):
        # video = VideoFileClip(video_path)
        # video.audio.write_audiofile(audio_path, codec='mp3')
        subprocess.call([self.FFMPEG_STATIC, "-i", video_path, "-q:a", "0", "-map", "a", audio_path])
        # os.remove(video_path)

    def get_audio_duration(self, file_path):
        result = subprocess.check_output(
            [self.FFPROBE_STATIC, "-v", "error", "-show_entries", 
             "format=duration", "-of", 
             "default=noprint_wrappers=1:nokey=1", file_path]
        )
        return float(result.strip())

    def split_audio_file(self, file_path):
        file_duration = self.get_audio_duration(file_path)
        chunk_duration = self.AUDIO_CHUNK_LENGTH_MS / 1000  # Convert ms to seconds
        audio_chunks = []

        # Calculate the number of chunks needed
        num_chunks = math.ceil(file_duration / chunk_duration)

        for i in range(num_chunks):
            start_time = i * chunk_duration
            end_time = min((i + 1) * chunk_duration, file_duration)
            chunk_file_name = f"chunk_{i}.mp3"
            
            subprocess.call([
                self.FFMPEG_STATIC, "-i", file_path, 
                "-ss", str(start_time), "-to", str(end_time),
                "-c", "copy", chunk_file_name
            ])
            audio_chunks.append(chunk_file_name)

        return audio_chunks

    def transcribe_chunk(self, chunk, prompt=""):
        with open(chunk, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format='text',
                language='ja'
            )
        
        os.remove(chunk)
        
        return transcript

    def transcribe(self, file_path):
        # Convert to audio if the file is a video
        if file_path.endswith('.mp4'):
            audio_file_path = os.path.splitext(file_path)[0] + '.mp3'
            self.convert_video_to_audio(file_path, audio_file_path)
            file_path = audio_file_path  # Update file_path to the converted audio file

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        full_transcription = ""

        if file_size_mb > self.MAX_FILE_SIZE_MB:
            audio_chunks = self.split_audio_file(file_path)
            transcriptions = []
            previous_transcript = ""
            
            for chunk in audio_chunks:
                transcript_chunk = self.transcribe_chunk(chunk, prompt=previous_transcript)
                transcriptions.append(transcript_chunk)
                previous_transcript = transcript_chunk
            
            full_transcription = ' '.join(transcriptions)
        else:
            with open(file_path, "rb") as audio_file:
                full_transcription = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format='text',
                    language='ja'
                )
        # os.remove(file_path)
        return full_transcription

    def save_as_text_file(self, transcription, filename):
        with open(filename, 'w', encoding='utf-8') as txt_file:
            txt_file.write(transcription)
