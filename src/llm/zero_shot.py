import glob
import json
import os

from dotenv import load_dotenv
from langchain.chains import ConversationChain
from langchain_openai import AzureChatOpenAI

load_dotenv()

SEGMENTS_PROMPT = open("prompts/segments.txt").read()

if __name__ == "__main__":
    llm = AzureChatOpenAI(
        deployment_name="gpt-35",
        openai_api_version=os.getenv("OPENAI_API_VERSION"),
        temperature=0,
    )
    qa = ConversationChain(llm=llm)

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
            transcript=transcript, avg_duration=avg_duration, video_length=15
        )

        # Execute the zero-shot agent
        result = qa.invoke(segments_prompt)
        print(result["response"])
