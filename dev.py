import youtube_dl
from src.utils.frames_extractor import FramesExtractor
import os

if __name__ == "__main__":
    # Download the video
    output_path = "data"
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    ydl_opts = {
        "format": "mp4",
        "extractor_retries": "auto",
        "outtmpl": output_path + "/%(title)s.%(ext)s",
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download(["https://www.youtube.com/watch?v=xTeknnJXTB8"])

    # Extract frames
    FramesExtractor.extract_frames(
        video_path="data/China viral influencer - Xiao Yang Ge live streaming to sell baby diaper #chinaviralshortvideo.mp4",
        output_dir="data",
        fps=2,
    )
