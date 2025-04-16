import pyttsx3
import re
import subprocess
import tempfile
import os
import signal
import threading
import shutil

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
    
    def __init__(self, audio_quality="medium"):
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
        
        # Set audio quality (low, medium, high, ultra)
        self.audio_quality = audio_quality
        
        # Audio players in preference order
        self.players = self._find_available_players()
        if not self.players:
            print("No suitable audio players found. Installing sox...")
            try:
                subprocess.run(['apt-get', 'install', '-y', 'sox'], check=True)
                self.players = ['play']
            except:
                print("Falling back to aplay...")
                self.players = ['aplay']
                
        print(f"Using audio player: {self.players[0]}")
        
        # Audio playback process tracking
        self.current_process = None
        self.is_speaking = False
        self.play_thread = None
        self.temp_files = []  # Track all temporary files
    
    def _find_available_players(self):
        """Find available audio players in order of preference."""
        players = []
        for player in ['play', 'mpv', 'ffplay', 'aplay']:
            try:
                subprocess.run(['which', player], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                players.append(player)
            except subprocess.CalledProcessError:
                pass
        return players
    
    def speak(self, text):
        """Convert text to speech with SVOX Pico."""
        print(f"Speaking with SVOX Pico: {text}")
        
        # Clean the text before speaking
        cleaned_text = self.clean_text(text)
        
        # Clean up any lingering temp files from previous calls
        self._cleanup_temp_files()
        
        # Create a temporary wav file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        # Create a processed file name
        processed_filename = temp_filename + '.processed.wav'
        
        # Add to tracked temp files
        self.temp_files = [temp_filename, processed_filename]
        
        try:
            # Generate speech with pico2wave
            subprocess.run([
                'pico2wave',
                '--wave', temp_filename,
                '--lang', self.language,
                cleaned_text
            ], check=True)
            
            # Process the audio for better quality
            self._enhance_audio(temp_filename, processed_filename)
            
            # Play the audio with selected player in a separate thread
            self.is_speaking = True
            self.play_thread = threading.Thread(
                target=self._play_audio_file,
                args=(processed_filename if os.path.exists(processed_filename) else temp_filename,)
            )
            self.play_thread.start()
            
        except Exception as e:
            print(f"Error generating speech: {e}")
            self.is_speaking = False
            self._cleanup_temp_files()
    
    def _enhance_audio(self, input_file, output_file):
        """Enhance audio quality based on selected quality level."""
        try:
            if self.audio_quality == "low":
                # Just copy the file - no enhancements
                shutil.copy2(input_file, output_file)
                return
                
            # Check if we have sox
            sox_available = False
            try:
                subprocess.run(['which', 'sox'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                sox_available = True
            except subprocess.CalledProcessError:
                pass
            
            if not sox_available:
                # Try with ffmpeg
                try:
                    subprocess.run(['which', 'ffmpeg'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    if self.audio_quality == "medium":
                        # Convert to stereo and apply basic processing
                        subprocess.run([
                            'ffmpeg', '-y', '-i', input_file,
                            '-ac', '2', '-ar', '22050',
                            output_file
                        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    elif self.audio_quality == "high":
                        # Better quality with higher sample rate
                        subprocess.run([
                            'ffmpeg', '-y', '-i', input_file,
                            '-ac', '2', '-ar', '44100', '-b:a', '192k',
                            output_file
                        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    elif self.audio_quality == "ultra":
                        # Maximum quality
                        subprocess.run([
                            'ffmpeg', '-y', '-i', input_file,
                            '-ac', '2', '-ar', '48000', '-b:a', '256k',
                            output_file
                        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    return
                except Exception as e:
                    print(f"ffmpeg processing failed: {e}")
                    shutil.copy2(input_file, output_file)
                    return
            
            # Use sox for the best audio enhancement
            if self.audio_quality == "medium":
                # Convert to stereo and apply basic enhancements
                subprocess.run([
                    'sox', input_file, output_file, 
                    'channels', '2', 'rate', '22050',
                    'norm', 'contrast'
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif self.audio_quality == "high":
                # Higher quality with more enhancements
                subprocess.run([
                    'sox', input_file, output_file,
                    'channels', '2', 'rate', '44100',
                    'norm', 'contrast', 'equalizer', '1k', '2q', '3',
                    'reverb', '10', '50', '100'
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif self.audio_quality == "ultra":
                # Maximum quality with comprehensive enhancements
                subprocess.run([
                    'sox', input_file, output_file,
                    'channels', '2', 'rate', '48000',
                    'norm', 'contrast', 'equalizer', '1k', '2q', '5',
                    'reverb', '15', '50', '100', 'bass', '+2'
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
        except Exception as e:
            print(f"Audio enhancement failed: {e}")
            # Fall back to original file if enhancement fails
            if not os.path.exists(output_file):
                shutil.copy2(input_file, output_file)
    
    def _play_audio_file(self, filename):
        """Play audio file with the best available player."""
        try:
            player = self.players[0]
            
            if player == 'play':  # SoX
                self.current_process = subprocess.Popen(['play', '-q', filename])
            elif player == 'mpv':
                self.current_process = subprocess.Popen(['mpv', '--no-terminal', filename])
            elif player == 'ffplay':
                self.current_process = subprocess.Popen(['ffplay', '-nodisp', '-autoexit', '-hide_banner', '-loglevel', 'quiet', filename])
            else:  # Default to aplay
                self.current_process = subprocess.Popen(['aplay', filename])
                
            self.current_process.wait()
        finally:
            self.is_speaking = False
            self.current_process = None
            self._cleanup_temp_files()
    
    def _cleanup_temp_files(self):
        """Clean up all temporary files created by this instance."""
        for filename in self.temp_files:
            if os.path.exists(filename):
                try:
                    os.unlink(filename)
                    print(f"Deleted temporary file: {filename}")
                except Exception as e:
                    print(f"Error deleting temporary file {filename}: {e}")
        self.temp_files = []
    
    def stop(self):
        """Stop the currently playing audio."""
        if self.is_speaking and self.current_process:
            print("Stopping audio playback")
            self.current_process.terminate()
            self.current_process = None
            self.is_speaking = False
            self._cleanup_temp_files()  # Clean up immediately when stopped
            return True
        return False

# Default ResponseHandler class for backward compatibility
class ResponseHandler(SVOXPicoTTSHandler):
    """Default TTS implementation using SVOX Pico for better quality.
    
    This class maintains the original interface for backwards compatibility.
    Change the parent class to EspeakTTSHandler to use the original implementation.
    
    Parameters:
    audio_quality -- The audio quality level: "low", "medium", "high", or "ultra"
    """
    def __init__(self, audio_quality="medium"):
        super().__init__(audio_quality=audio_quality)