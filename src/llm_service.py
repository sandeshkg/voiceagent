import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Dict

class LLMService:
    """Service for handling LLM interactions with Gemini API."""
    
    def __init__(self, system_prompt: str = None):
        """Initialize the LLM service.
        
        Args:
            system_prompt: Initial system prompt for the assistant.
        """
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        self.model_name = "gemini-2.0-flash"
        self.logger = logging.getLogger(__name__)
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt if none is provided."""
        return """You are a helpful, friendly assistant.
Be concise and provide accurate information. 
If you don't know something, say so rather than making up information."""
    
    def get_model(self):
        """Get the initialized LLM model."""
        # Get API key from environment or secrets
        api_key = os.getenv("GOOGLE_API_KEY") or ""
        if not api_key:
            self.logger.warning("Google API key not found in environment")
        
        return ChatGoogleGenerativeAI(model=self.model_name, google_api_key=api_key)
    
    def generate_response(self, input_text: str, message_history: List[Dict[str, str]]) -> str:
        """Generate a response from the LLM based on input and conversation history.
        
        Args:
            input_text: The user's input text
            message_history: List of previous conversation messages
            
        Returns:
            The generated response text
        """
        # Create prompt with system instructions and context
        prompt_messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Add recent messages from conversation history for context
        if message_history:
            # Take the last 10 messages for context
            history_messages = message_history[-10:]
            for msg in history_messages:
                prompt_messages.append({"role": msg["role"], "content": msg["content"]})

        # Add user input to the prompt
        prompt_messages.append({"role": "user", "content": input_text})
        
        try:
            # Get response from Gemini
            model = self.get_model()
            response = model.invoke(prompt_messages)
            return response.content
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return f"I'm sorry, I encountered an error: {e}"