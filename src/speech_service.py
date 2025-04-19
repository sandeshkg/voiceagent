"""
Text-to-speech service module.
This module handles all text-to-speech functionality, using SVOX Pico for high-quality speech.
"""

import os
import logging
import re
import subprocess
import tempfile
import threading
import shutil
from typing import List, Optional

class SpeechService:
    """Service for text-to-speech conversion with high quality audio."""
    
    def __init__(self, audio_quality: str = "medium", language: str = "en-US"):
        """Initialize the speech service.
        
        Args:
            audio_quality: Quality level ("low", "medium", "high", "ultra")
            language: Language code for speech (e.g., "en-US" for US English)
        """
        self.logger = logging.getLogger(__name__)
        self.language = language
        self.audio_quality = audio_quality
        
        # Verify SVOX Pico is installed
        self._verify_pico_installation()
        
        # Find available audio players
        self.players = self._find_available_players()
        if self.players:
            self.logger.info(f"Using audio player: {self.players[0]}")
        else:
            self.logger.warning("No suitable audio players found")
            
        # Audio playback process tracking
        self.current_process = None
        self.is_speaking = False
        self.play_thread = None
        self.temp_files = []  # Track all temporary files
    
    def _verify_pico_installation(self):
        """Verify that SVOX Pico is installed."""
        try:
            subprocess.run(['which', 'pico2wave'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("SVOX Pico TTS is available")
        except subprocess.CalledProcessError:
            self.logger.error("SVOX Pico TTS not found. Install with: sudo apt-get install libttspico-utils")
            raise RuntimeError("SVOX Pico TTS not installed")
    
    def _find_available_players(self) -> List[str]:
        """Find available audio players in order of preference."""
        players = []
        for player in ['play', 'mpv', 'ffplay', 'aplay']:
            try:
                subprocess.run(['which', player], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                players.append(player)
            except subprocess.CalledProcessError:
                pass
        return players
    
    def clean_text(self, text: str) -> str:
        """Clean text for better speech synthesis.
        
        Args:
            text: Input text to clean
            
        Returns:
            Cleaned text ready for speech synthesis
        """
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
    
    def speak(self, text: str) -> None:
        """Convert text to speech with high-quality voice.
        
        Args:
            text: Text to convert to speech
        """
        self.logger.info(f"Speaking with SVOX Pico: {text}")
        
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
            self.logger.error(f"Error generating speech: {e}")
            self.is_speaking = False
            self._cleanup_temp_files()

    def _enhance_audio(self, input_file: str, output_file: str) -> None:
        """Enhance audio quality based on selected quality level.
        
        Args:
            input_file: Path to the input audio file
            output_file: Path to save the enhanced audio file
        """
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
                    self.logger.error(f"ffmpeg processing failed: {e}")
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
            self.logger.error(f"Audio enhancement failed: {e}")
            # Fall back to original file if enhancement fails
            if not os.path.exists(output_file):
                shutil.copy2(input_file, output_file)
    
    def _play_audio_file(self, filename: str) -> None:
        """Play audio file with the best available player.
        
        Args:
            filename: Path to the audio file to play
        """
        try:
            if not self.players:
                self.logger.error("No audio players available")
                return
                
            player = self.players[0]
            
            if player == 'play':  # SoX
                self.current_process = subprocess.Popen(['play', '-q', filename])
            elif player == 'mpv':
                self.current_process = subprocess.Popen(['mpv', '--no-terminal', filename])
            elif player == 'ffplay':
                self.current_process = subprocess.Popen([
                    'ffplay', '-nodisp', '-autoexit', 
                    '-hide_banner', '-loglevel', 'quiet', filename
                ])
            else:  # Default to aplay
                self.current_process = subprocess.Popen(['aplay', filename])
                
            self.current_process.wait()
        finally:
            self.is_speaking = False
            self.current_process = None
            self._cleanup_temp_files()
    
    def _cleanup_temp_files(self) -> None:
        """Clean up all temporary files created by this instance."""
        for filename in self.temp_files:
            if os.path.exists(filename):
                try:
                    os.unlink(filename)
                    self.logger.debug(f"Deleted temporary file: {filename}")
                except Exception as e:
                    self.logger.error(f"Error deleting temporary file {filename}: {e}")
        self.temp_files = []
    
    def stop(self) -> bool:
        """Stop the currently playing audio.
        
        Returns:
            True if audio was stopped, False if no audio was playing
        """
        if self.is_speaking and self.current_process:
            self.logger.info("Stopping audio playback")
            self.current_process.terminate()
            self.current_process = None
            self.is_speaking = False
            self._cleanup_temp_files()  # Clean up immediately when stopped
            return True
        return False