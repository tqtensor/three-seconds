import glob
import json
import os

from dotenv import load_dotenv
from langchain.chains import ConversationChain
from langchain_community.chat_models import BedrockChat
from langchain_openai import AzureChatOpenAI

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL")
SEGMENTS_PROMPT = open("prompts/segments.txt").read()

if __name__ == "__main__":
    if LLM_MODEL == "gpt-35-turbo":
        llm = AzureChatOpenAI(
            deployment_name="gpt-35",
            openai_api_version=os.getenv("OPENAI_API_VERSION"),
            temperature=1,
        )
    elif LLM_MODEL == "claude-v2":
        llm = BedrockChat(
            credentials_profile_name="bedrock",
            region_name="us-east-1",
            model_id="anthropic.claude-v2",
            model_kwargs={"temperature": 1},
        )
    else:
        raise ValueError(f"Unknown LLM model: {LLM_MODEL}")
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
