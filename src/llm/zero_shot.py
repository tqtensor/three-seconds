import json
import os

from langchain.chains import ConversationChain
from langchain_community.chat_models import BedrockChat
from langchain_openai import AzureChatOpenAI

SEGMENTS_PROMPT = open("prompts/segments.txt").read()


class ZeroShot:
    def __init__(self, llm_model: str) -> None:
        if llm_model == "gpt-35-turbo":
            llm = AzureChatOpenAI(
                deployment_name="gpt-35",
                openai_api_version=os.getenv("OPENAI_API_VERSION"),
                temperature=0.5,
            )
        elif llm_model == "claude-v2":
            llm = BedrockChat(
                credentials_profile_name="bedrock",
                region_name="us-east-1",
                model_id="anthropic.claude-v2",
                model_kwargs={"temperature": 0.5, "max_tokens_to_sample": 2048},
            )
        else:
            raise ValueError(f"Unknown LLM model: {llm_model}")

        self.qa = ConversationChain(llm=llm)

    def invoke(self, transcript_path: str, video_length: float) -> None:
        # Load the transcript
        data = json.load(open(transcript_path))
        transcript = data["text"]

        # Compute the duration of each word
        durations = []
        for segment in data["segments"]:
            for word in segment["words"]:
                durations.append(word["end"] - word["start"])
        avg_duration = sum(durations) / len(durations)

        segments_prompt = SEGMENTS_PROMPT.format(
            transcript=transcript, avg_duration=avg_duration, video_length=video_length
        )

        # Execute the zero-shot agent
        result = self.qa.invoke(segments_prompt)

        # Store the result
        with open(
            transcript_path.replace("transcript.json", "zero_shot.txt"), "w"
        ) as f:
            f.write(result["response"])
