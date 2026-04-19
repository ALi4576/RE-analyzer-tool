"""
Faster-Whisper based audio transcription module.
Optimized for RTX 4070 Super with float16 precision.
"""
import io
from typing import Optional, Tuple
import numpy as np
from faster_whisper import WhisperModel
from config import settings
from utils import get_logger

logger = get_logger("transcriber")


class TranscriberEngine:
    """High-performance audio transcription using Faster-Whisper."""
    
    def __init__(self):
        """Initialize Whisper model with GPU optimization."""
        logger.info(f"Loading Whisper model: {settings.WHISPER_MODEL_SIZE}")
        self.model = WhisperModel(
            settings.WHISPER_MODEL_SIZE,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
            num_workers=2,
        )
        logger.info("Whisper model loaded successfully")
    
    def transcribe_file(
        self, file_path: str, language: Optional[str] = None
    ) -> str:
        """
        Transcribe an audio file to text.
        
        Args:
            file_path: Path to audio file
            language: ISO 639-1 language code (e.g., 'en', 'es')
            
        Returns:
            Transcribed text
        """
        try:
            logger.info(f"Transcribing file: {file_path}")
            segments, info = self.model.transcribe(
                file_path,
                language=language,
                beam_size=5,
                best_of=5,
                patience=1.0,
                temperature=0.0,
                compression_ratio_threshold=2.4,
            )
            
            # Collect all segments
            text = " ".join([segment.text for segment in segments])
            logger.info(f"Transcription complete. Length: {len(text)} chars")
            return text
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise
    
    def transcribe_stream(
        self, audio_chunk: bytes, chunk_number: int = 0
    ) -> Optional[str]:
        """
        Transcribe a single audio chunk from a stream.
        Used for real-time processing.
        
        Args:
            audio_chunk: Raw PCM audio bytes
            chunk_number: Sequential chunk identifier
            
        Returns:
            Transcribed text (None if chunk too short)
        """
        try:
            # Convert bytes to numpy array for Whisper
            audio_data = np.frombuffer(audio_chunk, dtype=np.float32)
            
            # Resample to 16kHz if needed
            current_rate = 16000  # Assuming standard rate
            if len(audio_data) < current_rate * 0.5:  # Less than 500ms
                logger.debug(f"Chunk {chunk_number} too short, skipping")
                return None
            
            # Create temporary buffer
            audio_io = io.BytesIO(audio_chunk)
            
            segments, _ = self.model.transcribe(
                audio_io,
                language="en",
                beam_size=3,  # Smaller for real-time
                temperature=0.0,
            )
            
            text = " ".join([segment.text for segment in segments])
            if text.strip():
                logger.info(f"Stream chunk {chunk_number} transcribed: {len(text)} chars")
                return text
            
            return None
            
        except Exception as e:
            logger.warning(f"Stream transcription error on chunk {chunk_number}: {str(e)}")
            return None
    
    def transcribe_with_timestamps(
        self, file_path: str, language: Optional[str] = None
    ) -> list:
        """
        Transcribe with segment timestamps for synchronization.
        
        Args:
            file_path: Path to audio file
            language: ISO 639-1 language code
            
        Returns:
            List of (start_time, end_time, text) tuples
        """
        try:
            logger.info(f"Transcribing with timestamps: {file_path}")
            segments, info = self.model.transcribe(
                file_path,
                language=language,
                beam_size=5,
            )
            
            result = []
            for segment in segments:
                result.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                })
            
            logger.info(f"Transcription segments: {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"Transcription with timestamps error: {str(e)}")
            raise


# Global transcriber instance
_transcriber = None


def get_transcriber() -> TranscriberEngine:
    """Get or initialize the global transcriber instance."""
    global _transcriber
    if _transcriber is None:
        _transcriber = TranscriberEngine()
    return _transcriber
