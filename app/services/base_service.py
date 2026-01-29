"""Base service class with common functionality."""

import logging
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class BaseService:
    """Base service class with common database operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logger
    
    def commit_or_rollback(self, operation_name: str) -> None:
        """Commit transaction or rollback on error.
        
        Args:
            operation_name: Name of the operation for logging
        """
        try:
            self.db.commit()
            self.logger.debug(f"{operation_name} committed successfully")
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"{operation_name} failed, rolled back: {e}")
            raise Exception(f"Database error during {operation_name}: {e}") from e
    
    def create_success_response(
        self, 
        message: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create standardized success response.
        
        Args:
            message: Success message
            data: Optional response data
            
        Returns:
            Standardized success response
        """
        return {
            "success": True,
            "message": message,
            "data": data
        }
    
    def handle_database_error(self, operation: str, email: str, error: Exception) -> None:
        """Handle database errors with consistent logging and rollback.
        
        Args:
            operation: Name of the operation that failed
            email: User email for context
            error: The exception that occurred
        """
        self.db.rollback()
        self.logger.error(f"Database error during {operation} for {email}: {error}")
        raise Exception(f"Database error: {error}") from error
    
    def handle_unexpected_error(self, operation: str, email: str, error: Exception) -> None:
        """Handle unexpected errors with consistent logging and rollback.
        
        Args:
            operation: Name of the operation that failed
            email: User email for context
            error: The exception that occurred
        """
        self.db.rollback()
        self.logger.error(f"Unexpected error during {operation} for {email}: {error}")
        raise error