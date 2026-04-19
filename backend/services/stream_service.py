"""
Real-time audio stream service for WebSocket-based audio processing.
Handles PCM binary audio chunks from client.
"""
import asyncio
import io
from typing import Optional, Callable, List
import numpy as np
from config import settings
from utils import get_logger
from core import get_transcriber

logger = get_logger("stream")


class StreamAudioService:
    """
    Real-time audio streaming and transcription.
    
    Receives PCM audio chunks via WebSocket, buffers them,
    and transcribes when meaningful chunks are ready.
    """
    
    def __init__(self):
        """Initialize stream service."""
        self.active_streams = {}
        logger.info("Stream Audio Service initialized")
    
    async def create_stream(
        self, session_id: str, on_transcription: Callable[[str], None]
    ) -> "AudioStreamBuffer":
        """
        Create a new audio stream for session.
        
        Args:
            session_id: Session ID
            on_transcription: Callback when transcription is ready
            
        Returns:
            StreamBuffer instance
        """
        logger.info(f"Creating audio stream for session {session_id}")
        
        buffer = AudioStreamBuffer(
            session_id=session_id,
            sample_rate=settings.SAMPLE_RATE,
            chunk_size=settings.AUDIO_CHUNK_SIZE,
            on_transcription=on_transcription,
        )
        
        self.active_streams[session_id] = buffer
        logger.info(f"Stream created for session {session_id}")
        
        return buffer
    
    async def add_chunk(
        self, session_id: str, audio_data: bytes
    ) -> Optional[str]:
        """
        Add audio chunk to stream.
        
        Args:
            session_id: Session ID
            audio_data: Raw PCM audio bytes
            
        Returns:
            Transcription if ready, else None
        """
        if session_id not in self.active_streams:
            logger.warning(f"Stream not found for session {session_id}")
            return None
        
        buffer = self.active_streams[session_id]
        transcription = await buffer.add_chunk(audio_data)
        
        return transcription
    
    async def finalize_stream(
        self, session_id: str
    ) -> Optional[str]:
        """
        Finalize stream and get final transcription.
        
        Args:
            session_id: Session ID
            
        Returns:
            Final transcription
        """
        if session_id not in self.active_streams:
            return None
        
        logger.info(f"Finalizing stream for session {session_id}")
        
        buffer = self.active_streams[session_id]
        transcription = await buffer.finalize()
        
        # Cleanup
        del self.active_streams[session_id]
        logger.info(f"Stream finalized and cleaned up for session {session_id}")
        
        return transcription
    
    async def close_stream(self, session_id: str) -> None:
        """Force close a stream."""
        if session_id in self.active_streams:
            del self.active_streams[session_id]
            logger.info(f"Stream closed for session {session_id}")


class AudioStreamBuffer:
    """
    Buffer for audio stream chunks.
    Accumulates chunks and triggers transcription when ready.
    """
    
    def __init__(
        self,
        session_id: str,
        sample_rate: int,
        chunk_size: int,
        on_transcription: Optional[Callable] = None,
    ):
        """
        Initialize audio buffer.
        
        Args:
            session_id: Session ID
            sample_rate: Audio sample rate (Hz)
            chunk_size: Chunk size in samples
            on_transcription: Callback for transcriptions
        """
        self.session_id = session_id
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.on_transcription = on_transcription
        
        self.audio_data = bytearray()
        self.chunk_count = 0
        self.transcriptions = []
        self.total_duration = 0.0
        
        logger.info(f"AudioStreamBuffer created for {session_id}")
    
    async def add_chunk(self, audio_bytes: bytes) -> Optional[str]:
        """
        Add audio chunk to buffer.
        
        Args:
            audio_bytes: Raw PCM audio bytes
            
        Returns:
            Transcription if triggered, else None
        """
        try:
            self.audio_data.extend(audio_bytes)
            self.chunk_count += 1
            
            # Calculate duration
            num_samples = len(audio_bytes) // 2  # Assuming 16-bit PCM
            duration = num_samples / self.sample_rate
            self.total_duration += duration
            
            logger.debug(
                f"[{self.session_id}] Chunk {self.chunk_count}: "
                f"{len(audio_bytes)} bytes, "
                f"total duration: {self.total_duration:.1f}s"
            )
            
            # Transcribe if buffer reaches threshold (5 seconds)
            if self.total_duration >= 5.0:
                return await self.transcribe_buffered()
            
            return None
            
        except Exception as e:
            logger.error(f"Error adding chunk: {str(e)}")
            return None
    
    async def transcribe_buffered(self) -> Optional[str]:
        """Transcribe accumulated audio buffer."""
        try:
            if len(self.audio_data) < 1000:  # Minimum size
                logger.debug("Buffer too small to transcribe")
                return None
            
            logger.info(
                f"[{self.session_id}] Transcribing {len(self.audio_data)} bytes "
                f"({self.total_duration:.1f}s)"
            )
            
            # Create temporary file for transcription
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(self.audio_data)
                tmp_path = tmp.name
            
            try:
                transcriber = get_transcriber()
                
                # Transcribe using Faster-Whisper
                text = await asyncio.to_thread(
                    transcriber.transcribe_file,
                    tmp_path,
                    "en"
                )
                
                self.transcriptions.append(text)
                logger.info(f"[{self.session_id}] Transcribed: {len(text)} chars")
                
                # Call callback
                if self.on_transcription:
                    await asyncio.to_thread(self.on_transcription, text)
                
                # Clear buffer for next batch
                self.audio_data = bytearray()
                self.total_duration = 0.0
                
                return text
                
            finally:
                import os
                os.unlink(tmp_path)
                
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return None
    
    async def finalize(self) -> Optional[str]:
        """
        Finalize stream and transcribe remaining buffer.
        
        Returns:
            Final combined transcription
        """
        if self.audio_data:
            final_text = await self.transcribe_buffered()
            if final_text:
                self.transcriptions.append(final_text)
        
        # Combine all transcriptions
        combined = " ".join(self.transcriptions)
        
        logger.info(
            f"[{self.session_id}] Stream finalized. "
            f"Total transcription: {len(combined)} chars"
        )
        
        return combined if combined else None


# Global stream service instance
_stream_service = None


def get_stream_service() -> StreamAudioService:
    """Get or initialize the global stream service."""
    global _stream_service
    if _stream_service is None:
        _stream_service = StreamAudioService()
    return _stream_service
