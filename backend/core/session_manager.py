"""
Session Manager for state persistence and recovery.
Uses LangGraph MemorySaver for checkpointing.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from models.schemas import RequirementAnalysisState, AnalysisStatus
from core.agents import get_agent

logger = logging.getLogger("session_manager")


class SessionManager:
    """
    Manages session lifecycle and persistence.
    - Creates new sessions
    - Recovers sessions from checkpoints
    - Cleans up expired sessions
    """
    
    def __init__(self, session_timeout_minutes: int = 60):
        """
        Initialize session manager.
        
        Args:
            session_timeout_minutes: How long to keep sessions after last activity
        """
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        logger.info(f"Session Manager initialized (timeout: {session_timeout_minutes} min)")
    
    def create_session(self, session_id: str, context_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new analysis session.
        
        Args:
            session_id: Unique session ID
            context_file: Optional context file path
            
        Returns:
            Session metadata
        """
        session_meta = {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "status": "active",
            "context_file": context_file,
            "accumulated_text": "",
            "iterations": 0,
        }
        
        self.active_sessions[session_id] = session_meta
        logger.info(f"Session created: {session_id}")
        return session_meta
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get active session metadata."""
        if session_id not in self.active_sessions:
            # Try to recover from checkpoint
            return self._recover_from_checkpoint(session_id)
        
        session = self.active_sessions[session_id]
        
        # Check if session expired
        last_activity = datetime.fromisoformat(session["last_activity"])
        if datetime.utcnow() - last_activity > self.session_timeout:
            logger.warning(f"Session {session_id} expired")
            del self.active_sessions[session_id]
            return None
        
        return session
    
    def update_session(self, session_id: str, **kwargs) -> bool:
        """
        Update session metadata.
        
        Args:
            session_id: Session ID
            **kwargs: Fields to update
            
        Returns:
            True if successful
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return False
        
        session = self.active_sessions[session_id]
        session.update(kwargs)
        session["last_activity"] = datetime.utcnow().isoformat()
        
        logger.debug(f"Session {session_id} updated")
        return True
    
    def _recover_from_checkpoint(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Try to recover session from LangGraph checkpoint.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session metadata if recovered, None otherwise
        """
        try:
            agent = get_agent()
            
            # Try to get checkpoint state
            config = {"configurable": {"thread_id": session_id}}
            try:
                checkpoint_state = agent.app.get_state(config)
                if checkpoint_state and checkpoint_state.values:
                    logger.info(f"Recovered session {session_id} from checkpoint")
                    
                    state = checkpoint_state.values
                    session_meta = {
                        "session_id": session_id,
                        "created_at": datetime.utcnow().isoformat(),
                        "last_activity": datetime.utcnow().isoformat(),
                        "status": state.get("status", "active"),
                        "accumulated_text": state.get("input_text", ""),
                        "iterations": state.get("iteration_count", 0),
                        "recovered": True,
                    }
                    
                    self.active_sessions[session_id] = session_meta
                    return session_meta
            except Exception as e:
                logger.debug(f"Could not recover from checkpoint: {e}")
                return None
        
        except Exception as e:
            logger.error(f"Checkpoint recovery error: {e}")
            return None
    
    def end_session(self, session_id: str) -> bool:
        """
        End a session and save final state.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful
        """
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        session["status"] = "closed"
        session["closed_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Session {session_id} ended")
        return True
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        expired = []
        now = datetime.utcnow()
        
        for session_id, session in self.active_sessions.items():
            last_activity = datetime.fromisoformat(session["last_activity"])
            if now - last_activity > self.session_timeout:
                expired.append(session_id)
        
        for session_id in expired:
            del self.active_sessions[session_id]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        
        return len(expired)
    
    def get_active_count(self) -> int:
        """Get number of active sessions."""
        return len(self.active_sessions)
    
    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active sessions."""
        return self.active_sessions.copy()


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or initialize global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(session_timeout_minutes=60)
    return _session_manager
