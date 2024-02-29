import glob
import json
import os
import re
import shutil
import subprocess
from collections import Counter

from dotenv import load_dotenv

from src.llm.zero_shot import ZeroShot
from src.utils.gdrive import GoogleDrive
from src.utils.preprocess import Preprocessor

load_dotenv()

gdrive = GoogleDrive()


def best_match_overlap_score(given_array, candidate_arrays):
    best_match = None
    best_match_index = None
    max_overlap_score = 0
    best_start_index = None
    best_end_index = None

    for index, candidate in enumerate(candidate_arrays):
        # Count occurrences of each element in the candidate array
        candidate_element_counts = Counter(candidate)

        # Calculate the percentage of elements in given_array that are
        # also in candidate_element_counts
        percentage = (
            len(set(given_array).intersection(candidate_element_counts))
            / len(given_array)
            * 100
        )
        if percentage > 50:
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


def main(request_id: str) -> str:
    request_file = f"requests/{request_id}/request.json"

    # Check if the request has been processed
    with open(request_file, "r") as f:
        request = json.load(f)
        if request.get("status") != "SUCCESS":
            # Prepare the file directories
            video_file = request_file.replace("request.json", "video.mp4")
            transcript_file = request_file.replace("request.json", "transcript.json")
            zero_shot_file = request_file.replace("request.json", "zero_shot.txt")

            if not os.path.exists(transcript_file):
                # Preprocess the video
                Preprocessor.transcribe_audio(video_file)

            success = False
            while not success:
                # Invoke the zero-shot agent
                agent = ZeroShot(llm_model=os.getenv("LLM_MODEL"))
                agent.invoke(
                    transcript_path=transcript_file,
                    video_length=float(request.get("length")),
                )

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

                        if start_index is None or end_index is None:
                            continue

                        # Trim the video
                        start_time = transcript["segments"][best_match_index]["words"][
                            start_index
                        ]["start"]
                        end_time = transcript["segments"][best_match_index]["words"][
                            end_index
                        ]["end"]

                        # Create output folder
                        dir_name, _ = os.path.split(request_file)
                        output_folder = os.path.join(
                            dir_name, dir_name.split("/")[-1] + "_output"
                        )
                        if not os.path.exists(output_folder):
                            os.makedirs(output_folder)

                        # Trim the video
                        trim_video(
                            video_file,
                            start_time,
                            end_time,
                            0.50,
                            os.path.join(output_folder, f"section_{idx}.mp4"),
                        )
                        shutil.copy(
                            zero_shot_file, os.path.join(output_folder, "readme.txt")
                        )

                    # Upload the output folder to Google Drive
                    gdrive_folder = gdrive.upload_folder_to_drive(
                        output_folder, os.getenv("DRIVE_FOLDER_ID")
                    )

                    # Write status SUCCESS to the request file
                    request["status"] = "SUCCESS"
                    request["gdrive_folder"] = gdrive_folder

                    # End the loop
                    success = True
        else:
            gdrive_folder = request.get("gdrive_folder")

        with open(request_file, "w") as f:
            json.dump(request, f)
        return gdrive_folder
