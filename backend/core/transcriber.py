"""
Faster-Whisper based audio transcription module.
Optimized for RTX 4070 Super with float16 precision.
"""
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

        The browser's MediaRecorder produces a container-encoded blob (webm/mp4/ogg),
        NOT raw PCM. We write the bytes to a temp file so faster-whisper can hand it
        to ffmpeg for proper container decoding before transcription.

        Args:
            audio_chunk: Container-encoded audio bytes (webm, mp4, ogg, wav)
            chunk_number: Sequential chunk identifier

        Returns:
            Transcribed text (None if chunk too short or empty)
        """
        import tempfile, os

        # Minimum viable chunk: anything under ~1 KB is too short to transcribe
        if len(audio_chunk) < 1024:
            logger.debug(f"Chunk {chunk_number} too small ({len(audio_chunk)} bytes), skipping")
            return None

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(audio_chunk)
                tmp_path = tmp.name

            segments, _ = self.model.transcribe(
                tmp_path,
                language="en",
                beam_size=3,
                temperature=0.0,
            )

            text = " ".join([segment.text for segment in segments]).strip()
            if text:
                logger.info(f"Stream chunk {chunk_number} transcribed: {len(text)} chars")
                return text

            return None

        except Exception as e:
            logger.warning(f"Stream transcription error on chunk {chunk_number}: {str(e)}")
            return None
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
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
