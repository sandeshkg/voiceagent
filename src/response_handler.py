import pyttsx3
import re

class ResponseHandler:
    def __init__(self):
        self.engine = pyttsx3.init('espeak')
        
        # Get available voices and set the best available one
        voices = self.engine.getProperty('voices')

        for voice in voices:
            print(f"Voice ID: {voice.id}")
            print(f"Voice Name: {voice.name}")
            print(f"Voice Languages: {voice.languages}")
            print("------------------------")

        # Try to find US English voice
        us_voice = next((voice for voice in voices if 'en-us' in voice.languages), None)
        if us_voice:
            self.engine.setProperty('voice', us_voice.id)
            print(f"Using US English voice: {us_voice.name}")
        elif voices:  # If no US voice, use the first available voice
            self.engine.setProperty('voice', voices[0].id)
            print(f"Using default voice: {voices[0].name}")


        # Try to find a female voice for better customer service experience
        #female_voice = next((voice for voice in voices if 'female' in voice.name.lower()), None)
        #if female_voice:
        #    self.engine.setProperty('voice', female_voice.id)
        #elif voices:  # If no female voice, use the first available voice
        #    self.engine.setProperty('voice', voices[0].id)
            
        # Optimize speech parameters
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 0.9)
        self.engine.setProperty('pitch', 100)
    
    def clean_text(self, text):
        """Remove special characters that cause speech issues."""
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[*`#@$%^&+=<>~|]', '', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize basic punctuation for better speech flow
        text = text.replace('...', '.')
        text = re.sub(r'\.+', '.', text)
        text = re.sub(r'!+', '!', text)
        text = re.sub(r'\?+', '?', text)
        
        return text.strip()
        
    def speak(self, text):
        """Convert text to speech with cleaned text."""
        print(f"Speaking: {text}")
        
        # Clean the text before speaking
        cleaned_text = self.clean_text(text)
        
        # Speak the cleaned text
        self.engine.say(cleaned_text)
        self.engine.runAndWait()