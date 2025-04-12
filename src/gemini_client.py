from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import google.generativeai as genai
import base64

load_dotenv()

class GeminiClient:
    def __init__(self):
        genai.configure(api_key="YOUR_GEMINI_API_KEY")
        self.model = genai.GenerativeModel('gemini-pro')
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful customer service agent. Provide concise, polite, and accurate responses."),
            ("human", "{input}")
        ])

    def get_response(self, user_input):
        """Send user input to Gemini and get a response."""
        if not user_input:
            return "I'm sorry, I didn't catch that. How can I assist you?"
        chain = self.prompt | self.llm
        response = chain.invoke({"input": user_input})
        return response.content

    def transcribe_audio(self, audio_file_path):
        """Transcribe audio using Gemini Vision."""
        try:
            with open(audio_file_path, 'rb') as audio_file:
                # Convert audio to base64
                audio_bytes = audio_file.read()
                audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Create a prompt that asks Gemini to transcribe the audio
            prompt = "Please transcribe this audio file accurately. Only return the transcription text."
            
            # Call Gemini with the audio file
            response = self.vision_model.generate_content([
                prompt,
                {"mime_type": "audio/wav", "data": audio_b64}
            ])
            
            return response.text
        except Exception as e:
            print(f"Transcription error: {e}")
            return None