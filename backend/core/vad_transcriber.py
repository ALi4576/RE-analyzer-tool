"""
Voice Activity Detection (VAD) enabled transcriber with sliding window.
Provides real-time transcription with partial results and silence detection.
"""
import numpy as np
from collections import deque
from typing import Optional, Tuple, List
from faster_whisper import WhisperModel
from config import settings
from utils import get_logger

logger = get_logger("transcriber")


class SlidingWindowVADTranscriber:
    """
    Transcriber with Voice Activity Detection and sliding window buffering.
    
    Features:
    - Detects silence using energy-based VAD
    - Accumulates audio in sliding window (1.5s)
    - Sends partial results every 500ms
    - Triggers final transcription after 1.5s silence
    """
    
    def __init__(self):
        """Initialize transcriber with VAD."""
        logger.info(f"Initializing VAD Transcriber: {settings.WHISPER_MODEL_SIZE}")
        self.model = WhisperModel(
            settings.WHISPER_MODEL_SIZE,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
            num_workers=2,
        )
        
        # Audio parameters
        self.sample_rate = 16000  # Hz
        self.chunk_duration = 0.5  # seconds (500ms)
        self.silence_threshold_db = -40  # Energy threshold for silence detection
        self.silence_duration_threshold = 1.5  # seconds (1.5s of silence triggers finalize)
        
        # Buffers
        self.audio_buffer = deque(maxlen=int(self.sample_rate * 3))  # 3 second window
        self.silence_duration = 0.0
        self.last_speech_time = 0.0
        self.accumulated_text = ""
        self.chunk_count = 0
        
        logger.info("VAD Transcriber initialized")
    
    def add_audio_chunk(self, audio_bytes: bytes) -> Optional[Tuple[str, bool]]:
        """
        Add audio chunk to buffer and check for transcription trigger.
        
        Args:
            audio_bytes: Raw PCM audio bytes (mono, 16-bit, 16kHz)
            
        Returns:
            Tuple of (transcribed_text, is_final) or None if no transcription triggered
            - transcribed_text: Partial or final transcribed text
            - is_final: True if 1.5s silence detected (final), False if partial (500ms interval)
        """
        try:
            # Convert bytes to numpy array
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Add to buffer
            for sample in audio_data:
                self.audio_buffer.append(sample)
            
            # Detect if this chunk is silence
            is_silent = self._is_silence(audio_data)
            
            if is_silent:
                self.silence_duration += len(audio_data) / self.sample_rate
            else:
                self.silence_duration = 0.0
                self.last_speech_time = len(self.audio_buffer) / self.sample_rate
            
            # Check triggers
            if self.silence_duration >= self.silence_threshold_db:
                # Trigger final transcription (1.5s silence)
                result = self._transcribe_buffer(final=True)
                self.audio_buffer.clear()
                self.accumulated_text = ""
                self.silence_duration = 0.0
                return result
            
            # Periodic partial transcription (500ms intervals)
            self.chunk_count += 1
            if self.chunk_count % 2 == 0:  # Every 2 chunks (500ms at 250ms per chunk)
                result = self._transcribe_buffer(final=False)
                if result:
                    text, _ = result
                    return text, False
            
            return None
            
        except Exception as e:
            logger.error(f"VAD processing error: {str(e)}")
            return None
    
    def finalize(self) -> Optional[str]:
        """
        Finalize transcription and return any remaining audio.
        Call when stream ends explicitly.
        """
        if not self.audio_buffer:
            return None
        
        result = self._transcribe_buffer(final=True)
        self.audio_buffer.clear()
        self.accumulated_text = ""
        
        if result:
            text, _ = result
            return text
        return None
    
    def _is_silence(self, audio_chunk: np.ndarray) -> bool:
        """
        Detect if audio chunk is silence using energy-based VAD.
        
        Args:
            audio_chunk: Audio samples as float32 (-1.0 to 1.0)
            
        Returns:
            True if chunk is mostly silence
        """
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        
        # Convert to dB
        db = 20 * np.log10(rms + 1e-10)
        
        # Check if below threshold
        return db < self.silence_threshold_db
    
    def _transcribe_buffer(self, final: bool = False) -> Optional[Tuple[str, bool]]:
        """
        Transcribe current buffer contents.
        
        Args:
            final: Whether this is final transcription (1.5s silence)
            
        Returns:
            Tuple of (text, is_final) or None if insufficient audio
        """
        if len(self.audio_buffer) < self.sample_rate * 0.5:  # Less than 500ms
            return None
        
        try:
            # Convert buffer to bytes
            audio_array = np.array(self.audio_buffer, dtype=np.float32)
            
            # Transcribe
            segments, _ = self.model.transcribe(
                audio_array,
                language="en",
                beam_size=3 if not final else 5,  # Better quality for final
                temperature=0.0,
            )
            
            text = " ".join([segment.text for segment in segments])
            
            if text.strip():
                logger.debug(f"Transcribed ({'final' if final else 'partial'}): {text[:60]}...")
                return text.strip(), final
            
            return None
            
        except Exception as e:
            logger.warning(f"Transcription error: {str(e)}")
            return None
    
    def reset(self):
        """Reset transcriber state for new session."""
        self.audio_buffer.clear()
        self.silence_duration = 0.0
        self.accumulated_text = ""
        self.chunk_count = 0
        logger.info("VAD Transcriber reset")


# Global instance
_vad_transcriber = None


def get_vad_transcriber() -> SlidingWindowVADTranscriber:
    """Get or initialize VAD transcriber."""
    global _vad_transcriber
    if _vad_transcriber is None:
        _vad_transcriber = SlidingWindowVADTranscriber()
    return _vad_transcriber
