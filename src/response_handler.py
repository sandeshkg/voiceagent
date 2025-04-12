import pyttsx3

class ResponseHandler:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Speed of speech
        self.engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)

    def speak(self, text):
        """Convert text to speech."""
        print(f"Speaking: {text}")
        self.engine.say(text)
        self.engine.runAndWait()