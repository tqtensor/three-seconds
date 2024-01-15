from typing import Optional

import ffmpy


class FramesExtractor:
    def __init__(self):
        # Ensure that ffmpeg is installed
        ffmpy.FFmpeg().run()

    @staticmethod
    def extract_frames(video_path: str, output_dir: Optional[str], fps: int = 1):
        if output_dir is None:
            output_dir = "tmp"
        ff = ffmpy.FFmpeg(
            inputs={video_path: None},
            outputs={f"{output_dir}/frame_%d.jpg": f"-vf fps={fps}"},
        )
        ff.run()
