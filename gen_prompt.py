import glob
import json

SEGMENTS_PROMPT = open("prompts/segments.txt").read()

for file in glob.glob("data/*/transcript.json"):
    data = json.load(open(file))

    # Load the transcript
    transcript = data["text"]

    # Compute the duration of each word
    durations = []
    for segment in data["segments"]:
        for word in segment["words"]:
            durations.append(word["end"] - word["start"])
    avg_duration = sum(durations) / len(durations)

    segments_prompt = SEGMENTS_PROMPT.format(
        transcript=transcript, avg_duration=avg_duration, video_length=30
    )
    print(segments_prompt)
