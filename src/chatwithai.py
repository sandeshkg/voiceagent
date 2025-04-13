import streamlit as st
from gemini_client import GeminiClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, AIMessage
import os
from dotenv import load_dotenv

load_dotenv()

st.title("💬 Gemini Chat")

gemini_api_key = st.sidebar.text_input("Google Gemini API Key", type="password")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# System prompt for the assistant
system_prompt = """You are a helpful, friendly AI assistant. 
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

    # Add conversation history
    if st.session_state.messages:
        prompt_messages.append({"role": "user", "content": st.session_state.messages[-1]["content"]})

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

# Accept user input
if prompt := st.chat_input("What would you like to know?"):
    if not gemini_api_key:
        st.warning("Please enter your Google Gemini API key!", icon="⚠")
    else:
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate and display assistant response
        with st.chat_message("assistant"):
            response = generate_response(prompt)
            st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

