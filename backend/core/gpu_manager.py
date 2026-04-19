"""
GPU Resource Management and VRAM Optimization for RTX 4070 Super.
Implements model quantization, concurrent session limiting, and memory monitoring.
"""
import asyncio
import psutil
import torch
import logging
from typing import Optional
from config import settings

logger = logging.getLogger("gpu_manager")


class GPUResourceManager:
    """
    Manages GPU resources for concurrent model inference.
    
    Constraints:
    - RTX 4070 Super: 12GB VRAM
    - Llama 3 + Whisper must share VRAM
    - Keep 30% free for OS and Python overhead
    """
    
    def __init__(self, max_concurrent_sessions: int = 3):
        """
        Initialize GPU resource manager.
        
        Args:
            max_concurrent_sessions: Max number of concurrent inference sessions
        """
        self.max_concurrent_sessions = max_concurrent_sessions
        self.active_sessions = 0
        self.session_semaphore = asyncio.Semaphore(max_concurrent_sessions)
        self.total_vram_mb = self._get_total_vram()
        self.warning_threshold = self.total_vram_mb * 0.70  # Warn at 70%
        self.critical_threshold = self.total_vram_mb * 0.85  # Critical at 85%
        
        logger.info(f"GPU Resource Manager initialized")
        logger.info(f"Total VRAM: {self.total_vram_mb}MB")
        logger.info(f"Warning threshold: {self.warning_threshold}MB (70%)")
        logger.info(f"Critical threshold: {self.critical_threshold}MB (85%)")
        logger.info(f"Max concurrent sessions: {max_concurrent_sessions}")
    
    def _get_total_vram(self) -> int:
        """Get total GPU VRAM in MB."""
        try:
            if torch.cuda.is_available():
                return torch.cuda.get_device_properties(0).total_memory // (1024 * 1024)
            return 0
        except Exception as e:
            logger.error(f"Failed to get VRAM info: {e}")
            return 12288  # Assume RTX 4070 Super (12GB)
    
    def get_current_vram_usage(self) -> int:
        """Get current GPU VRAM usage in MB."""
        try:
            if torch.cuda.is_available():
                return torch.cuda.memory_allocated() // (1024 * 1024)
            return 0
        except Exception as e:
            logger.error(f"Failed to get VRAM usage: {e}")
            return 0
    
    def get_vram_percentage(self) -> float:
        """Get current VRAM usage as percentage."""
        used = self.get_current_vram_usage()
        return (used / self.total_vram_mb) * 100 if self.total_vram_mb > 0 else 0
    
    async def acquire_session_slot(self, session_id: str) -> bool:
        """
        Acquire a session slot.
        Blocks if max concurrent sessions reached.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if slot acquired
        """
        try:
            vram_pct = self.get_vram_percentage()
            
            if vram_pct > self.critical_threshold:
                logger.warning(f"CRITICAL: VRAM at {vram_pct:.1f}% - Rejecting session {session_id}")
                return False
            
            if vram_pct > self.warning_threshold:
                logger.warning(f"WARNING: VRAM at {vram_pct:.1f}% - Consider reducing concurrent sessions")
            
            await self.session_semaphore.acquire()
            self.active_sessions += 1
            logger.info(f"Session {session_id} acquired slot ({self.active_sessions}/{self.max_concurrent_sessions})")
            return True
        
        except Exception as e:
            logger.error(f"Error acquiring session slot: {e}")
            return False
    
    def release_session_slot(self, session_id: str) -> None:
        """
        Release a session slot.
        
        Args:
            session_id: Session ID
        """
        try:
            self.session_semaphore.release()
            self.active_sessions -= 1
            logger.info(f"Session {session_id} released slot ({self.active_sessions}/{self.max_concurrent_sessions})")
        except Exception as e:
            logger.error(f"Error releasing session slot: {e}")
    
    def clear_cache(self) -> None:
        """Clear GPU cache to free memory."""
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info(f"GPU cache cleared. VRAM usage: {self.get_vram_percentage():.1f}%")
        except Exception as e:
            logger.error(f"Error clearing GPU cache: {e}")
    
    def get_stats(self) -> dict:
        """Get current GPU statistics."""
        return {
            "total_vram_mb": self.total_vram_mb,
            "used_vram_mb": self.get_current_vram_usage(),
            "usage_percentage": self.get_vram_percentage(),
            "active_sessions": self.active_sessions,
            "max_sessions": self.max_concurrent_sessions,
        }


# Global GPU resource manager instance
_gpu_manager: Optional[GPUResourceManager] = None


def get_gpu_manager() -> GPUResourceManager:
    """Get or initialize global GPU resource manager."""
    global _gpu_manager
    if _gpu_manager is None:
        _gpu_manager = GPUResourceManager(max_concurrent_sessions=3)
    return _gpu_manager
