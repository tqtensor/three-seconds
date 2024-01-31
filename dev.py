import json
import os

import librosa
import soundfile as sf
import torch
import whisper_timestamped as whisper
import youtube_dl

from src.utils.frames_extractor import FramesExtractor

URLS = ["https://www.youtube.com/shorts/HQc4E9hb7JQ"]
FPS = 2

device = "cuda:0" if torch.cuda.is_available() else "cpu"


if __name__ == "__main__":
    # Download the video
    video_output_path = "data"
    if not os.path.exists(video_output_path):
        os.makedirs(video_output_path)

    ydl_opts = {
        "format": "mp4",
        "extractor_retries": "auto",
        "outtmpl": video_output_path + "/%(id)s" + "/video.%(ext)s",
    }
    for video_url in URLS:
        # Download the video
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            video_info = ydl.extract_info(url=video_url, download=False)
            video_id = video_info["id"]

            if not os.path.exists(os.path.join(video_output_path, video_id)):
                os.makedirs(os.path.join(video_output_path, video_id))

            if not os.path.exists(
                os.path.join(video_output_path, video_id, "video.mp4")
            ):
                ydl.download([video_url])

            with open(os.path.join(video_output_path, video_id, "info.json"), "w") as f:
                video_info = {
                    k: v for k, v in video_info.items() if not isinstance(v, list)
                }
                json.dump(video_info, f, ensure_ascii=False)

        # Extract frames
        frames_output_path = os.path.join(video_output_path, video_id, "frames")
        if not os.path.exists(frames_output_path):
            os.makedirs(frames_output_path)
        FramesExtractor.extract_frames(
            video_path=os.path.join(video_output_path, video_id, "video.mp4"),
            output_dir=frames_output_path,
            fps=FPS,
        )

        # Extract audio
        audio_output_path = os.path.join(video_output_path, video_id, "audio")
        if not os.path.exists(audio_output_path):
            os.makedirs(audio_output_path)

        video_path = os.path.join(video_output_path, video_id, "video.mp4")
        audio_path = os.path.join(audio_output_path, "audio.wav")

        # Convert video to audio using librosa
        if not os.path.exists(audio_path):
            audio, sr = librosa.load(video_path)
            sf.write(audio_path, audio, sr)

        # Transcribe audio
        audio = whisper.load_audio(audio_path)
        model = whisper.load_model(
            name="mesolitica/malaysian-whisper-medium", device=device
        )
        result = whisper.transcribe(
            model, audio, language="malay", detect_disfluencies=True
        )

        with open("dev.json", "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
