from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
from google.ai import generativelanguage as genai
from google.api_core import client_options
from google.auth.credentials import Credentials
import base64

load_dotenv()

class SimpleCredentials(Credentials):
    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key

    def refresh(self, request):
        """Refresh credentials. In this case, the API key doesn't need refreshing."""
        pass

    def apply(self, headers):
        """Apply the credentials to the headers."""
        headers['Authorization'] = f'Bearer {self.api_key}'

    def before_request(self, request, method, url, headers):
        """Apply credentials to request before it is made."""
        self.apply(headers)

class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
            
        # Configure the client
        client_opts = client_options.ClientOptions(
            api_endpoint="generativelanguage.googleapis.com"
        )
        self.model = genai.ModelServiceClient(
            client_options=client_opts,
            credentials=SimpleCredentials(api_key)
        )
        
        # Initialize LangChain components
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=api_key,
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
                audio_bytes = audio_file.read()
                audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            request = genai.GenerateContentRequest(
                model='models/gemini-pro-vision',
                contents=[
                    genai.Content(
                        parts=[
                            genai.Part(text="Please transcribe this audio file accurately. Only return the transcription text."),
                            genai.Part(
                                inline_data=genai.Blob(
                                    mime_type="audio/wav",
                                    data=audio_bytes
                                )
                            )
                        ]
                    )
                ]
            )
            
            response = self.model.generate_content(request)
            return response.candidates[0].content.parts[0].text
            
        except Exception as e:
            print(f"Transcription error: {e}")
            return None