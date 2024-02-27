import ast
import hashlib
import json
import os

import gdown
from dotenv import load_dotenv

from src.main import main as three_seconds
from telegram.ext import CommandHandler, Updater

load_dotenv()


# Define the command handler for the /process command
def process(update, context):
    # Get the user input
    user_input = update.message.text

    # Validate the user input
    user_input = user_input.replace("/process ", "").strip()
    try:
        user_input = ast.literal_eval(user_input)
    except Exception as e:
        update.message.reply_text(f"Invalid input: {e}")
        return

    # Define Request ID
    request_id = hashlib.sha256(user_input["video_id"].encode("utf-8")).hexdigest()[:12]

    # Download the video
    if not os.path.exists(f"requests/{request_id}"):
        os.makedirs(f"requests/{request_id}")

    try:
        gdown.download(
            id=user_input["video_id"],
            output=f"requests/{request_id}/video.mp4",
            quiet=False,
        )
    except Exception as e:
        update.message.reply_text(f"Error downloading the video: {e}")
        return

    # Write the user input to a file
    with open(f"requests/{request_id}/request.json", "w") as f:
        f.write(json.dumps(user_input))

    # Run the main function
    output = three_seconds(request_id=request_id)

    # Send a response message
    update.message.reply_text(
        f"Your short video is ready! https://drive.google.com/drive/folders/{output}"
    )


def main():
    # Create an instance of the Updater class
    updater = Updater(token=os.getenv("BOT_TOKEN"), use_context=True)

    # Create an instance of the Dispatcher class
    dp = updater.dispatcher

    # Register the /process command handler
    dp.add_handler(CommandHandler("process", process))

    # Start the bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == "__main__":
    main()
