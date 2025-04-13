import streamlit as st
from gemini_client import GeminiClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, AIMessage
import os
from dotenv import load_dotenv

load_dotenv()

st.title("🦜🔗 Quickstart App")

gemini_api_key = st.sidebar.text_input("Google Gemini API Key", type="password")

messages = []
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
    global messages  # Declare messages as global to avoid UnboundLocalError

    # Create prompt with system instructions and context
    prompt_messages = [
        {"role": "system", "content": system_prompt}  # Correctly format the system message
    ]

    # Add conversation history
    if messages:
        prompt_messages.append({"role": "user", "content": messages[-1].content})

    # Add user input to the prompt
    prompt_messages.append({"role": "user", "content": input_text})

    # Get response from Gemini
    model = get_model()
    response = model.invoke(prompt_messages)

    # Create AI message from response
    ai_message = AIMessage(content=response.content) # Access the content field of the response

    # Update state with new message
    messages = messages + [ai_message]

    st.info(ai_message.content)

with st.form("my_form"):
    text = st.text_area(
        "Enter text:",
        "What are the three key pieces of advice for learning how to code?",
    )
    submitted = st.form_submit_button("Submit")
    if not gemini_api_key:
        st.warning("Please enter your Google Gemini API key!", icon="⚠")
    if submitted and gemini_api_key:
        generate_response(text)

