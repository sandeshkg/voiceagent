import pyttsx3
import re
import subprocess
import tempfile
import os
import signal
import threading

class BaseTTSHandler:
    """Base class for text-to-speech handlers with common functionality."""
    
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


class EspeakTTSHandler(BaseTTSHandler):
    """TTS Handler that uses pyttsx3 with espeak backend."""
    
    def __init__(self):
        self.engine = pyttsx3.init('espeak')
        
        # Get available voices and set to US English if available
        voices = self.engine.getProperty('voices')
        
        # Try to find US English voice
        us_voice = next((voice for voice in voices if 'en-us' in str(voice.languages).lower()), None)
        if us_voice:
            self.engine.setProperty('voice', us_voice.id)
            print(f"Using US English voice: {us_voice.name}")
        elif voices:  # If no US voice, use the first available voice
            self.engine.setProperty('voice', voices[0].id)
            print(f"Using default voice: {voices[0].name}")
            
        # Optimize speech parameters
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 0.9)
        self.engine.setProperty('pitch', 100)
    
    def speak(self, text):
        """Convert text to speech with cleaned text."""
        print(f"Speaking with pyttsx3/espeak: {text}")
        
        # Clean the text before speaking
        cleaned_text = self.clean_text(text)
        
        # Speak the cleaned text
        self.engine.say(cleaned_text)
        self.engine.runAndWait()


class SVOXPicoTTSHandler(BaseTTSHandler):
    """TTS Handler that uses SVOX Pico for better quality speech."""
    
    def __init__(self):
        # Check if pico2wave is installed
        try:
            subprocess.run(['which', 'pico2wave'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("SVOX Pico TTS is available")
        except subprocess.CalledProcessError:
            print("SVOX Pico TTS not found. Install with: sudo apt-get install libttspico-utils")
            raise RuntimeError("SVOX Pico TTS not installed")
        
        # Set default language to US English
        self.language = "en-US"
        print(f"Using SVOX Pico with language: {self.language}")
        
        # Audio playback process tracking
        self.current_process = None
        self.is_speaking = False
        self.play_thread = None
    
    def speak(self, text):
        """Convert text to speech with SVOX Pico."""
        print(f"Speaking with SVOX Pico: {text}")
        
        # Clean the text before speaking
        cleaned_text = self.clean_text(text)
        
        # Create a temporary wav file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        try:
            # Generate speech with pico2wave
            subprocess.run([
                'pico2wave',
                '--wave', temp_filename,
                '--lang', self.language,
                cleaned_text
            ], check=True)
            
            # Play the audio with aplay in a separate thread
            self.is_speaking = True
            self.play_thread = threading.Thread(
                target=self._play_audio_file,
                args=(temp_filename,)
            )
            self.play_thread.start()
            
        except Exception as e:
            print(f"Error generating speech: {e}")
            self.is_speaking = False
            # Clean up the temporary file in case of error
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    def _play_audio_file(self, filename):
        """Play audio file and handle cleanup."""
        try:
            self.current_process = subprocess.Popen(['aplay', filename])
            self.current_process.wait()
        finally:
            self.is_speaking = False
            self.current_process = None
            # Clean up the temporary file
            if os.path.exists(filename):
                os.unlink(filename)
    
    def stop(self):
        """Stop the currently playing audio."""
        if self.is_speaking and self.current_process:
            print("Stopping audio playback")
            self.current_process.terminate()
            self.current_process = None
            self.is_speaking = False
            return True
        return False


# Default ResponseHandler class for backward compatibility
class ResponseHandler(SVOXPicoTTSHandler):
    """Default TTS implementation using SVOX Pico for better quality.
    
    This class maintains the original interface for backwards compatibility.
    Change the parent class to EspeakTTSHandler to use the original implementation.
    """
    pass