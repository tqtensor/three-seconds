import ast
import json
import os

import gdown
from dotenv import load_dotenv

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

    # Download the video
    try:
        gdown.download(id=user_input["video_id"], output="video.mp4", quiet=False)
    except Exception as e:
        update.message.reply_text(f"Error downloading the video: {e}")
        return

    # Define Request ID
    request_id = user_input["video_id"]

    # Write the user input to a file
    with open(f"request_{request_id}.json", "w") as file:
        file.write(json.dumps(user_input))

    # Send a response message
    update.message.reply_text(f"Your request ID is {request_id}, please wait")


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
