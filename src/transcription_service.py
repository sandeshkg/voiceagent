import os
import logging
import whisper

class TranscriptionService:
    """Service for transcribing speech to text using Whisper."""
    
    def __init__(self, model_size: str = "base", language: str = "en"):
        """Initialize the transcription service.
        
        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
            language: Language code for transcription (e.g., "en" for English)
        """
        # Initialize logger first so it can be used in other methods
        self.logger = logging.getLogger(__name__)
        
        self.model_size = model_size
        self.language = language
        self.model = self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            self.logger.info(f"Loading Whisper model: {self.model_size}")
            return whisper.load_model(self.model_size)
        except Exception as e:
            self.logger.error(f"Error loading Whisper model: {e}")
            raise RuntimeError(f"Failed to load Whisper model: {e}")
    
    def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio file to text.
        
        Args:
            audio_file_path: Path to the audio file to transcribe
            
        Returns:
            Transcribed text or error message
        """
        if not os.path.exists(audio_file_path):
            self.logger.error(f"Audio file '{audio_file_path}' does not exist.")
            return "Error: Audio file not found."

        try:
            self.logger.info(f"Starting transcription for file: {audio_file_path}")
            result = self.model.transcribe(
                audio_file_path, 
                language=self.language  # Force specified language
            )
            self.logger.info("Transcription completed successfully.")
            return result["text"]
        except Exception as e:
            self.logger.error(f"An error occurred during transcription: {e}")
            return f"An error occurred during transcription: {e}"