"""
Quota Failure Logger for RTI Summarization System
Provides audit trail for API failures and fallback activations.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class QuotaLogger:
    """
    Logger for tracking API quota failures and system events.
    Stores logs in JSON format for easy parsing and audit trails.
    """
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize the quota logger.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / "quota_failures.json"
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        """Create log directory if it doesn't exist."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize log file if it doesn't exist
        if not self.log_file.exists():
            self._write_logs([])
    
    def _read_logs(self) -> List[Dict]:
        """Read existing logs from file."""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _write_logs(self, logs: List[Dict]):
        """Write logs to file."""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    
    def log_quota_failure(
        self,
        error_type: str,
        error_message: str,
        endpoint: str = "gemini",
        context: Optional[Dict] = None,
        fallback_used: bool = False
    ) -> Dict:
        """
        Log an API quota failure.
        
        Args:
            error_type: Type of error (e.g., "429", "quota_exceeded", "rate_limit")
            error_message: Full error message
            endpoint: API endpoint that failed
            context: Additional context (e.g., summary type requested)
            fallback_used: Whether local fallback was activated
            
        Returns:
            The log entry that was created
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "quota_failure",
            "error_type": error_type,
            "error_message": str(error_message)[:500],  # Truncate long messages
            "endpoint": endpoint,
            "fallback_used": fallback_used,
            "context": context or {}
        }
        
        logs = self._read_logs()
        logs.append(log_entry)
        
        # Keep only last 1000 entries to prevent file bloat
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        self._write_logs(logs)
        
        return log_entry
    
    def log_fallback_activation(
        self,
        reason: str,
        summary_type: str,
        success: bool = True
    ) -> Dict:
        """
        Log when fallback summarizer is activated.
        
        Args:
            reason: Why fallback was triggered
            summary_type: Type of summary being generated
            success: Whether fallback succeeded
            
        Returns:
            The log entry that was created
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "fallback_activation",
            "reason": reason,
            "summary_type": summary_type,
            "success": success
        }
        
        logs = self._read_logs()
        logs.append(log_entry)
        self._write_logs(logs)
        
        return log_entry
    
    def log_api_success(self, endpoint: str, summary_type: str) -> Dict:
        """
        Log successful API call (for comparison/stats).
        
        Args:
            endpoint: API endpoint used
            summary_type: Type of summary generated
            
        Returns:
            The log entry that was created
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "api_success",
            "endpoint": endpoint,
            "summary_type": summary_type
        }
        
        logs = self._read_logs()
        logs.append(log_entry)
        self._write_logs(logs)
        
        return log_entry
    
    def get_audit_trail(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get audit trail of logged events.
        
        Args:
            event_type: Filter by event type (None for all)
            limit: Maximum number of entries to return
            
        Returns:
            List of log entries (most recent first)
        """
        logs = self._read_logs()
        
        if event_type:
            logs = [l for l in logs if l.get('event_type') == event_type]
        
        # Return most recent first
        return logs[-limit:][::-1]
    
    def get_failure_stats(self) -> Dict:
        """
        Get statistics about quota failures.
        
        Returns:
            Dictionary with failure statistics
        """
        logs = self._read_logs()
        
        failures = [l for l in logs if l.get('event_type') == 'quota_failure']
        fallbacks = [l for l in logs if l.get('event_type') == 'fallback_activation']
        successes = [l for l in logs if l.get('event_type') == 'api_success']
        
        # Count by error type
        error_types = {}
        for f in failures:
            error_type = f.get('error_type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_failures": len(failures),
            "total_fallbacks": len(fallbacks),
            "total_successes": len(successes),
            "failure_rate": len(failures) / (len(failures) + len(successes)) if (failures or successes) else 0,
            "error_types": error_types,
            "fallback_success_rate": len([f for f in fallbacks if f.get('success')]) / len(fallbacks) if fallbacks else 1.0
        }
    
    def clear_logs(self):
        """Clear all logs (use with caution)."""
        self._write_logs([])


# Global logger instance
_logger_instance = None


def get_logger(log_dir: str = "logs") -> QuotaLogger:
    """
    Get or create the global logger instance.
    
    Args:
        log_dir: Directory for log files
        
    Returns:
        QuotaLogger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = QuotaLogger(log_dir)
    return _logger_instance


# Convenience functions
def log_quota_failure(error_type: str, error_message: str, **kwargs) -> Dict:
    """Convenience function to log quota failure."""
    return get_logger().log_quota_failure(error_type, error_message, **kwargs)


def log_fallback_activation(reason: str, summary_type: str, **kwargs) -> Dict:
    """Convenience function to log fallback activation."""
    return get_logger().log_fallback_activation(reason, summary_type, **kwargs)


def log_api_success(endpoint: str, summary_type: str) -> Dict:
    """Convenience function to log API success."""
    return get_logger().log_api_success(endpoint, summary_type)


# Test
if __name__ == "__main__":
    logger = QuotaLogger("test_logs")
    
    # Test logging
    logger.log_quota_failure(
        error_type="429",
        error_message="You exceeded your current quota",
        endpoint="gemini",
        context={"summary_type": "ultra_short"},
        fallback_used=True
    )
    
    logger.log_fallback_activation(
        reason="API quota exceeded",
        summary_type="ultra_short",
        success=True
    )
    
    # Get stats
    stats = logger.get_failure_stats()
    print("Stats:", json.dumps(stats, indent=2))
    
    # Get audit trail
    trail = logger.get_audit_trail(limit=5)
    print("\nAudit Trail:")
    for entry in trail:
        print(f"  {entry['timestamp']}: {entry['event_type']}")
