import glob
import json
import os
import re
import subprocess
from collections import Counter

from dotenv import load_dotenv

from src.llm.zero_shot import ZeroShot
from src.utils.preprocess import Preprocessor

load_dotenv()


def best_match_overlap_score(given_array, candidate_arrays):
    """
    Finds the candidate array with the highest overlap score for a sub-array
    compared to the given array.

    Args:
      given_array: The given array.
      candidate_arrays: List of candidate arrays.

    Returns:
      A tuple of (best_match_candidate, best_match_index, start_index, end_index, overlap_score), or None if no match.
    """

    best_match = None
    best_match_index = None
    max_overlap_score = 0
    best_start_index = None
    best_end_index = None

    for index, candidate in enumerate(candidate_arrays):
        # Count occurrences of each element in the candidate array
        candidate_element_counts = Counter(candidate)

        # Check for intersection and iterate through possible sub-arrays within the candidate
        if set(given_array).issubset(candidate_element_counts):
            for i in range(len(candidate) - len(given_array) + 1):
                sub_array = candidate[i : i + len(given_array)]
                sub_array_counts = Counter(sub_array)

                # Calculate overlap score based on matching elements and counts
                matched_elements = len(set(given_array).intersection(set(sub_array)))
                matched_counts = sum(
                    min(c1, c2)
                    for c1, c2 in zip(
                        sub_array_counts.values(), Counter(given_array).values()
                    )
                )
                overlap_score = matched_elements + matched_counts

                if overlap_score > max_overlap_score:
                    max_overlap_score = overlap_score
                    best_match = candidate
                    best_match_index = index
                    best_start_index = i
                    best_end_index = i + len(given_array) - 1

    return (
        best_match,
        best_match_index,
        best_start_index,
        best_end_index,
        max_overlap_score,
    )


def trim_video(source_file, start_time, end_time, buffer, output_file):
    """
    Trims a video based on start and end time arguments and saves it to a new file.

    Args:
      source_file: Path to the input video file (.mp4).
      start_time: Start time of the clip in seconds (e.g., 10.5 for 10 seconds and 0.5 seconds).
      end_time: End time of the clip in seconds.
      buffer: Buffer time in seconds to add before and after the clip.
      output_file: Path to the output video file (.mp4).
    """

    # Construct the ffmpeg command using f-strings
    start_time = max(0, start_time - buffer)
    end_time += buffer
    command = (
        f"ffmpeg -i {source_file} -ss {start_time} -to {end_time} -c copy {output_file}"
    )
    print(command)

    # Execute the command using subprocess
    if os.path.exists(output_file):
        os.remove(output_file)
    process = subprocess.run(command.split(), capture_output=True)

    # Check for any errors
    if process.returncode != 0:
        print("Error during trimming:", process.stderr.decode("utf-8"))
    else:
        print(f"Video trimmed successfully! Saved to: {output_file}")


def main():
    for request_file in glob.glob("requests/*/request.json"):
        # Prepare the file directories
        video_file = request_file.replace("request.json", "video.mp4")
        transcript_file = request_file.replace("request.json", "transcript.json")
        zero_shot_file = request_file.replace("request.json", "zero_shot.txt")

        # Preprocess the video
        Preprocessor.transcribe_audio(video_file)

        # Invoke the zero-shot agent
        agent = ZeroShot(llm_model=os.getenv("LLM_MODEL"))
        agent.invoke(transcript_file)

        # Trim the video
        transcript = json.load(open(transcript_file))

        # Locate the sections
        with open(zero_shot_file, "r") as f:
            content = f.read()
            sections = re.findall(r'Section \d+: "(.*?)"', content, re.DOTALL)
            for idx, section in enumerate(sections):
                # Find the best matching segment
                segments = [
                    segment["text"].strip().split()
                    for segment in transcript["segments"]
                ]
                (
                    _,
                    best_match_index,
                    start_index,
                    end_index,
                    _,
                ) = best_match_overlap_score(section.split(), segments)

                # Trim the video
                start_time = transcript["segments"][best_match_index]["words"][
                    start_index
                ]["start"]
                end_time = transcript["segments"][best_match_index]["words"][end_index][
                    "end"
                ]
                trim_video(
                    video_file,
                    start_time,
                    end_time,
                    0.50,
                    zero_shot_file.replace(
                        "zero_shot.txt", "trimmed_{}.mp4".format(idx + 1)
                    ),
                )


if __name__ == "__main__":
    main()
