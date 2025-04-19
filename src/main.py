import streamlit as st
import os
import logging
from dotenv import load_dotenv

# Import the specialized service modules 
from llm_service import LLMService
from audio_input_service import AudioInputService
from transcription_service import TranscriptionService
from speech_service import SpeechService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# System prompt for the assistant
SYSTEM_PROMPT = """You are a helpful, friendly Customer service assistant working for the Auto Loan section with Safe Bank of Antartica.
You can answer questions about auto loans, interest rates, and loan applications.
Be concise and provide accurate information. Response should not exceed 100 words.
If you don't know something, say so rather than making up information."""

# Initialize services in session state
if "audio_input_service" not in st.session_state:
    st.session_state.audio_input_service = AudioInputService(use_mock=False)
    
if "speech_service" not in st.session_state:
    # Use high quality audio - options: "low", "medium", "high", "ultra"
    st.session_state.speech_service = SpeechService(audio_quality="high")
    
if "transcription_service" not in st.session_state:
    st.session_state.transcription_service = TranscriptionService(model_size="base", language="en")
    
if "llm_service" not in st.session_state:
    st.session_state.llm_service = LLMService(system_prompt=SYSTEM_PROMPT)
    
# Initialize is_speaking state if not already present
if "is_speaking" not in st.session_state:
    st.session_state.is_speaking = False

st.title("💬 Safe Bank of Antartica - Loan Division")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Add spacing between chat messages and other UI elements
st.markdown("<style> .stChatMessage { margin-bottom: 20px; } </style>", unsafe_allow_html=True)

# Ensure proper alignment of chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Function to handle stopping audio playback
def stop_audio():
    if st.session_state.speech_service.stop():
        st.session_state.is_speaking = False
        st.success("Audio playback stopped")

# Create a row with two buttons side by side
col1, col2 = st.columns(2)

# Voice Input button
if col1.button("🎤 Voice Input", key="voice_button"):
    with st.spinner("Listening..."):
        # Record audio using the audio input service
        audio_file_path = st.session_state.audio_input_service.record_audio()

        if audio_file_path:
            # Transcribe audio using the transcription service
            transcript = st.session_state.transcription_service.transcribe_audio(audio_file_path)

            if transcript:
                # Display user's transcribed message
                with st.chat_message("user"):
                    st.markdown(transcript)

                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": transcript})

                # Generate response using the LLM service
                with st.chat_message("assistant"):
                    response = st.session_state.llm_service.generate_response(
                        transcript, 
                        st.session_state.messages
                    )
                    st.markdown(response)
                    
                    # Update speaking state and speak the response using the speech service
                    st.session_state.is_speaking = True
                    st.session_state.speech_service.speak(response)
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

    # Generate response using the LLM service
    with st.chat_message("assistant"):
        response = st.session_state.llm_service.generate_response(
            prompt, 
            st.session_state.messages
        )
        st.markdown(response)
        
        # Update speaking state and speak the response using the speech service
        st.session_state.is_speaking = True
        st.session_state.speech_service.speak(response)
        st.session_state.is_speaking = False
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

