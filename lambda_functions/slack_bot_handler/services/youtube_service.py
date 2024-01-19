from pytube import YouTube

def download_youtube_video(url, output_path, output_filename):
    yt = YouTube(url)
    video = yt.streams.filter(file_extension='mp4').first()
    filename = output_path + output_filename
    video.download(output_path=output_path, filename=filename)
    return filename