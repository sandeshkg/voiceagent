import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import logging
from dotenv import load_dotenv
from audio_handler import AudioHandler
from tts_handlers import SVOXPicoTTSHandler
import whisper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

load_dotenv()

# Initialize voice components
if "audio_handler" not in st.session_state:
    st.session_state.audio_handler = AudioHandler(use_mock=False)
if "response_handler" not in st.session_state:
    # Use high quality audio - options: "low", "medium", "high", "ultra"
    st.session_state.response_handler = SVOXPicoTTSHandler(audio_quality="medium")
    
# Initialize is_speaking state if not already present
if "is_speaking" not in st.session_state:
    st.session_state.is_speaking = False

st.title("💬 Safe Bank of Antartica - Loan Division")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# System prompt for the assistant
system_prompt = """You are a helpful, friendly Customer service assistant working for the Auto Loan section with Safe Bank of Antartica.
You can answer questions about auto loans, interest rates, and loan applications.
Be concise and provide accurate information. Response should not exceed 100 words.
If you don't know something, say so rather than making up information."""

# Initialize Gemini model
@st.cache_resource
def get_model():
    # Use the API key from environment
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", "")
    if not api_key:
        st.warning("Please set your Google API key in environment or secrets")
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=api_key)

def generate_response(input_text):
    # Create prompt with system instructions and context
    prompt_messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Add recent messages from conversation history for context
    if st.session_state.messages:
        history_messages = st.session_state.messages[-10:]
        for msg in history_messages:
            prompt_messages.append({"role": msg["role"], "content": msg["content"]})

    # Add user input to the prompt
    prompt_messages.append({"role": "user", "content": input_text})

    # Get response from Gemini
    model = get_model()
    response = model.invoke(prompt_messages)

    return response.content

# Load the Whisper model
model = whisper.load_model("base")

def transcribe_audio(audio_file_path):
    """Transcribe audio using Whisper."""
    if not os.path.exists(audio_file_path):
        logging.error(f"Audio file '{audio_file_path}' does not exist.")
        return "Error: Audio file not found."

    try:
        logging.info(f"Starting transcription for file: {audio_file_path}")
        result = model.transcribe(audio_file_path, language="en")
        logging.info("Transcription completed successfully.")
        return result["text"]
    except Exception as e:
        logging.error(f"An error occurred during transcription: {e}")
        return f"An error occurred during transcription: {e}"

# Add spacing between chat messages and other UI elements
st.markdown("<style> .stChatMessage { margin-bottom: 20px; } </style>", unsafe_allow_html=True)

# Ensure proper alignment of chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Function to handle stopping audio playback
def stop_audio():
    if st.session_state.response_handler.stop():
        st.session_state.is_speaking = False
        st.success("Audio playback stopped")

# Create a row with two buttons side by side
col1, col2 = st.columns(2)

# Voice Input button
if col1.button("🎤 Voice Input", key="voice_button"):
    with st.spinner("Listening..."):
        # Record audio
        audio_file_path = "recorded_audio.wav"
        audio_file = st.session_state.audio_handler.record_dynamic_audio()

        if audio_file:
            # Transcribe audio using Whisper
            transcript = transcribe_audio(audio_file_path)

            if transcript:
                # Display user's transcribed message
                with st.chat_message("user"):
                    st.markdown(transcript)

                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": transcript})

                # Generate and display assistant response
                with st.chat_message("assistant"):
                    response = generate_response(transcript)
                    st.markdown(response)
                    # Update speaking state and speak the response
                    st.session_state.is_speaking = True
                    st.session_state.response_handler.speak(response)
                    st.session_state.is_speaking = False

                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                st.error("Sorry, I couldn't understand the audio. Please try again.")

# Stop button
if col2.button("🔇 Stop Audio", key="stop_button"):
    stop_audio()

# Accept text input
if prompt := st.chat_input("What would you like to know?"):   
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate and display assistant response
    with st.chat_message("assistant"):
        response = generate_response(prompt)
        st.markdown(response)
        # Update speaking state and speak the response
        st.session_state.is_speaking = True
        st.session_state.response_handler.speak(response)
        st.session_state.is_speaking = False
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

