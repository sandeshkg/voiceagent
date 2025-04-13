#a simple console app to check if we can use langchain and google gemini to transcribe audio
#This will read the recorded_audio.wav file and transcribe it using the google gemini api
#and print the response in the console


import os
from dotenv import load_dotenv

# Import the whisper library
import whisper

load_dotenv()

# Load the Whisper model (you can use 'base', 'small', 'medium', or 'large')
model = whisper.load_model("base")

# Path to the audio file
audio_file = "./recorded_audio.wav"  # Adjust the path if needed

# Check if the audio file exists
if not os.path.exists(audio_file):
    print(f"Error: The audio file '{audio_file}' does not exist. Please check the file path.")
    exit(1)

# Transcribe the audio
try:
    print("Transcribing audio...")
    result = model.transcribe(audio_file)
    print("Transcription:")
    print(result["text"])
except Exception as e:
    print(f"An error occurred during transcription: {e}")


