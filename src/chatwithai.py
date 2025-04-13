import streamlit as st
from gemini_client import GeminiClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, AIMessage
import os
from dotenv import load_dotenv
from audio_handler import AudioHandler
from response_handler import ResponseHandler

load_dotenv()

# Initialize voice components
if "audio_handler" not in st.session_state:
    st.session_state.audio_handler = AudioHandler(use_mock=False)
if "response_handler" not in st.session_state:
    st.session_state.response_handler = ResponseHandler()
if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = GeminiClient()

st.title("💬 Safe Bank of Antartica - Loan Division")

gemini_api_key = st.sidebar.text_input("Google Gemini API Key", type="password")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# System prompt for the assistant
system_prompt = """You are a helpful, friendly Customer service assistant working for the Auto Loan section with Safe Bank of Antartica.
You can answer questions about auto loans, interest rates, and loan applications.
Be concise and provide accurate information.
If you don't know something, say so rather than making up information."""

# Initialize Gemini model
@st.cache_resource
def get_model():
    # Use the API key from Streamlit secrets or environment
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", "")
    if not api_key:
        st.warning("Please set your Google API key in the sidebar")
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=api_key)

def generate_response(input_text):
    # Create prompt with system instructions and context
    prompt_messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Add last 5 messages from conversation history for better context
    if st.session_state.messages:
        history_messages = st.session_state.messages[-10:]  # Get last 5 pairs of messages (10 messages total)
        for msg in history_messages:
            prompt_messages.append({"role": msg["role"], "content": msg["content"]})

    # Add user input to the prompt
    prompt_messages.append({"role": "user", "content": input_text})

    # Get response from Gemini
    model = get_model()
    response = model.invoke(prompt_messages)

    return response.content

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Add voice input button
col1, col2 = st.columns([8, 2])
with col2:
    if st.button("🎤 Voice Input", key="voice_button"):
        with st.spinner("Listening..."):
            # Record audio
            audio_file = st.session_state.audio_handler.record_dynamic_audio()
            
            if audio_file:
                # Transcribe audio
                transcript = st.session_state.gemini_client.transcribe_audio(audio_file)
                
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
                        # Speak the response
                        st.session_state.response_handler.speak(response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    st.error("Sorry, I couldn't understand the audio. Please try again.")

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
        # Speak the response for text input as well
        st.session_state.response_handler.speak(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

