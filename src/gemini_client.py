from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
from google.genai.client import Client
from google.genai import types
import base64

load_dotenv()

class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        # Initialize the generative model client with the API key
        self.client = Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash-001"

    def get_response(self, user_input):
        """Send user input to Gemini and get a response."""
        if not user_input:
            return "I'm sorry, I didn't catch that. How can I assist you?"

        # Create content with text part
        content = types.Content(
            parts=[types.Part(text=user_input)]
        )

        # Generate response using the model
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=content,
            config=types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=256
            )
        )
        return response.text

    def transcribe_audio(self, audio_file_path):
        """Transcribe audio using Gemini 2.0 Flash."""
        try:
            # Read the audio file
            with open(audio_file_path, 'rb') as audio_file:
                audio_bytes = audio_file.read()

            if not audio_bytes:
                print("Error: Audio file is empty or could not be read.")
                return None

            print(f"Audio file {audio_file_path} read successfully. Size: {len(audio_bytes)} bytes.")

            # Create vision prompt with clear instructions
            prompt = """Please carefully transcribe the spoken words in this audio file.
            Focus only on the clear speech and ignore any background noise.
            Return only the transcribed text without any additional commentary.
            If you can't understand something clearly, use [...] to indicate unclear parts."""

            # Create content with text and audio parts
            content = types.Content(
                parts=[
                    types.Part(text=prompt),
                    types.Part(
                        inline_data=types.Blob(
                            mime_type="audio/wav",
                            data=base64.b64encode(audio_bytes).decode('utf-8')
                        )
                    )
                ]
            )

            # Generate response using the model
            print("Sending transcription request to Gemini model...")
            print(dir(types.GenerationConfig))



            response = self.client.models.generate_content(
                model=self.model_name,
                contents=content,
                config=types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2048
                )
            )

            if not response or not response.text:
                print("Error: No transcription result received from the model.")
                return None

            print("Transcription completed successfully.")
            # Extract the transcription text
            return response.text.strip()

        except Exception as e:
            print(f"Transcription error: {e}")
            return None