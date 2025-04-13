from audio_handler import AudioHandler
from gemini_client import GeminiClient
from response_handler import ResponseHandler

def select_audio_device():
    """Let user select an audio input device."""
    temp_handler = AudioHandler(use_mock=False)  # Temporary instance to list devices
    while True:
        try:
            device_index = input("\nEnter the Device ID number to use (or press Enter for default): ").strip()
            if not device_index:  # Empty input - use default
                return None
            return int(device_index)
        except ValueError:
            print("Please enter a valid number")

def main():
    # Let user select audio device
    #device_index = select_audio_device()
    
    audio_handler = AudioHandler(use_mock=False, device_index=0)  # Use default device
    gemini_client = GeminiClient()
    response_handler = ResponseHandler()

    print("Voice-enabled customer service agent started. Press Ctrl+C to stop.")
    try:
        while True:
            print("Listening... (speak now)")
            # Step 1: Record audio dynamically
            audio_file = audio_handler.record_dynamic_audio()
            
            if audio_file:  # Only proceed if audio was recorded
                # Step 2: Transcribe audio using Gemini
                user_input = gemini_client.transcribe_audio(audio_file)
                
                if user_input:  # Only proceed if transcription was successful
                    print(f"You said: {user_input}")
                    
                    # Step 3: Get response from Gemini
                    response = gemini_client.get_response(user_input)
                    
                    # Step 4: Speak the response
                    response_handler.speak(response)
            
    except KeyboardInterrupt:
        print("\nStopping the agent. Goodbye!")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()