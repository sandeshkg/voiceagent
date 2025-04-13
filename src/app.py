# LangChain + LangGraph + Gemini Chatbot with Streamlit UI
# Prerequisites: pip install langchain langchain-google-genai langgraph graphviz streamlit

import os
import streamlit as st
from typing import Dict, TypedDict, List, Annotated
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv


load_dotenv()

# Set page config
st.set_page_config(
    page_title="Gemini Chat Assistant",
    page_icon="🤖",
    layout="wide"
)

# Define the state structure
class AgentState(TypedDict):
    messages: Annotated[List, "The chat history"]
    context: Dict

# Initialize Gemini model
@st.cache_resource
def get_model():
    # Use the API key from Streamlit secrets or environment
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", "")
    if not api_key:
        st.warning("Please set your Google API key in the sidebar")
    
    
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=api_key)

# System prompt for the assistant
system_prompt = """You are a helpful, friendly AI assistant. 
Be concise and provide accurate information.
If you don't know something, say so rather than making up information."""

# Create function to handle conversation
def conversation_agent(state):
    messages = state["messages"]
    context = state["context"]

    # Only process if the last message is from the user
    if not messages or not isinstance(messages[-1], HumanMessage):
        return state

    # Create prompt with system instructions and context
    prompt_messages = [SystemMessage(content=system_prompt)]

    if context and "relevant_info" in context:
        prompt_messages.append(SystemMessage(content=f"Relevant context: {context['relevant_info']}"))

    # Add conversation history
    prompt_messages.extend(messages[-2:])  # Only include last exchange for context

    # Get response from Gemini
    model = get_model()
    response = model.invoke(prompt_messages)

    # Create AI message from response
    ai_message = AIMessage(content=response.content)

    # Update state with new message
    new_messages = messages + [ai_message]

    # Update Streamlit display for the assistant's response
    #with st.chat_message("assistant"):
    #    st.write(ai_message.content)

    return {"messages": new_messages, "context": context}

# Function to check if we should end conversation
def should_end(state):
    messages = state["messages"]
    if not messages:
        return False

    # End the conversation after the AI responds
    last_message = messages[-1]
    return isinstance(last_message, AIMessage)

# Create and compile the graph
@st.cache_resource
def create_workflow():
    workflow = StateGraph(AgentState)

    # Add the conversation node
    workflow.add_node("conversation", conversation_agent)

    # Set the entry point
    workflow.set_entry_point("conversation")

    # Add edges with the end condition
    workflow.add_conditional_edges(
        "conversation",
        should_end,
        {
            True: END,
            False: "conversation"  # This will not loop since should_end ends after AI response
        }
    )

    return workflow.compile()

# Visualize the graph (for documentation purposes)
def generate_graph_image():
    workflow = StateGraph(AgentState)
    workflow.add_node("conversation", conversation_agent)
    workflow.set_entry_point("conversation")
    workflow.add_conditional_edges(
        "conversation",
        should_end,
        {
            True: END,
            False: "conversation"
        }
    )
    try:
        workflow.to_graph().draw("conversation_graph.png", format="png")
        return "conversation_graph.png"
    except:
        return None

# Initialize session state
def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "app" not in st.session_state:
        st.session_state.app = create_workflow()
    if "state" not in st.session_state:
        st.session_state.state = {
            "messages": [],
            "context": {"relevant_info": "User is interacting through a Streamlit interface."}
        }

# Main app
def main():
    st.title("🤖 Gemini Chat Assistant")
    st.subheader("Powered by LangChain + LangGraph")

    # Initialize session
    init_session()

    # Sidebar
    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input("Google API Key", value=os.getenv("GOOGLE_API_KEY", ""), type="password")
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key

        st.divider()

        # Context settings
        st.subheader("Conversation Context")
        context = st.text_area(
            "Add context for the assistant",
            value=st.session_state.state["context"].get("relevant_info", ""),
            help="This information will be provided to the model as context"
        )

        if st.button("Update Context"):
            st.session_state.state["context"]["relevant_info"] = context
            st.success("Context updated!")

        st.divider()

        # Display graph visualization if available
        st.subheader("Conversation Graph")
        graph_path = generate_graph_image()
        if graph_path and os.path.exists(graph_path):
            st.image(graph_path, caption="Conversation Flow Graph")
        else:
            st.info("Graph visualization requires Graphviz. Install with: pip install graphviz")

        if st.button("Clear Conversation"):
            st.session_state.messages = []
            st.session_state.state["messages"] = []
            st.rerun()

    # Display chat messages
    for message in st.session_state.state["messages"]:
        if isinstance(message, (AIMessage, HumanMessage)):
            role = "assistant" if isinstance(message, AIMessage) else "user"
            with st.chat_message(role):
                st.write(message.content)

    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        human_message = HumanMessage(content=prompt)
        with st.chat_message("user"):
            st.write(prompt)

        # Update state with user message
        st.session_state.state["messages"].append(human_message)

        with st.spinner("Thinking..."):
            # Process the message through our graph
            result = st.session_state.app.invoke(st.session_state.state)
            st.session_state.state = result

            # Display the AI response
            if result["messages"] and isinstance(result["messages"][-1], AIMessage):
                with st.chat_message("assistant"):
                    st.write(result["messages"][-1].content)

if __name__ == "__main__":
    main()