import json
import os

import librosa
import soundfile as sf
import torch
import whisper_timestamped as whisper

device = "cuda:0" if torch.cuda.is_available() else "cpu"


class Preprocessor:
    @staticmethod
    def transcribe_audio(video_path: str):
        # Extract audio
        parent_path = os.path.dirname(video_path)
        audio_path = os.path.join(parent_path, "audio.wav")

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

        with open(os.path.join(parent_path, "transcript.json"), "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
