# Voice Agent with Gemini AI

A voice-enabled customer service agent powered by Google's Gemini AI.

## Installation

Install dependencies using Poetry:

```bash
poetry install --no-root
```

## Running the Applications

### Chat Interface (chatwithai.py)

Run the Streamlit chat interface using Poetry:

```bash
poetry run streamlit run src/chatwithai.py
```

### Voice Agent (main.py)

Run the voice-enabled agent:

```bash
poetry run python src/main.py
```

## Debugging in VS Code

The repository includes launch configurations for VS Code. To debug:

1. Open the project in VS Code
2. Go to the Run and Debug view (Ctrl+Shift+D)
3. Select one of the following launch configurations:
   - "Streamlit: Debug chat with ai.py" - Debug the chat interface
   - "Streamlit: Debug app.py" - Debug the app interface
   - "Streamlit: Debug Current File" - Debug the currently open file
   - "Streamlit: Remote Attach" - Attach to a running Streamlit process

### Remote Debugging

To start the application in remote debugging mode:

```bash
poetry run python -m debugpy --listen 5678 --wait-for-client -m streamlit run src/main.py
```

Then use the "Streamlit: Remote Attach" configuration to attach the debugger.