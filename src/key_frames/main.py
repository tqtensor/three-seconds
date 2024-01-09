# DEMO
from __future__ import unicode_literals

import os

import youtube_dl
from Katna.video import Video
from Katna.writer import KeyFrameDiskWriter

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

    # Initialize video module
    vd = Video()

    # Number of images to be returned
    no_of_frames_to_returned = 12

    # Initialize diskwriter to save data at desired location
    diskwriter = KeyFrameDiskWriter(location="data/selected_frames")

    # Extract keyframes and process data with diskwriter
    vd.extract_keyframes_from_videos_dir(
        no_of_frames=no_of_frames_to_returned,
        dir_path=output_path,
        writer=diskwriter,
    )
