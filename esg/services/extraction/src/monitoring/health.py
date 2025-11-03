"""
Health check functionality for extraction service.

This module provides health check endpoints and status monitoring.

Requirements: 9.4
"""

import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


@dataclass
class ComponentHealth:
    """Health status for a service component."""
    
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: Optional[str] = None
    last_check: Optional[datetime] = None
    response_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "response_time_ms": self.response_time_ms,
        }


class HealthChecker:
    """
    Health checker for extraction service.
    
    Monitors the health of various components:
    - Database connectivity
    - RabbitMQ connectivity
    - Google GenAI API availability
    - Overall service status
    """
    
    def __init__(self):
        """Initialize health checker."""
        self._lock = threading.Lock()
        self._component_health: Dict[str, ComponentHealth] = {}
        self._service_start_time = time.time()
        self._last_successful_extraction: Optional[datetime] = None
        self._last_failed_extraction: Optional[datetime] = None
    
    def check_database(self, connection_string: str) -> ComponentHealth:
        """
        Check database connectivity.
        
        Args:
            connection_string: PostgreSQL connection string
            
        Returns:
            ComponentHealth: Database health status
        """
        start_time = time.time()
        
        try:
            import psycopg2
            
            conn = psycopg2.connect(connection_string)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            response_time = (time.time() - start_time) * 1000
            
            health = ComponentHealth(
                name="database",
                status="healthy",
                message="Database connection successful",
                last_check=datetime.now(),
                response_time_ms=response_time,
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            health = ComponentHealth(
                name="database",
                status="unhealthy",
                message=f"Database connection failed: {str(e)}",
                last_check=datetime.now(),
                response_time_ms=response_time,
            )
            
            logger.error(f"Database health check failed: {e}")
        
        with self._lock:
            self._component_health["database"] = health
        
        return health
    
    def check_rabbitmq(self, host: str, user: str, password: str) -> ComponentHealth:
        """
        Check RabbitMQ connectivity.
        
        Args:
            host: RabbitMQ host
            user: RabbitMQ username
            password: RabbitMQ password
            
        Returns:
            ComponentHealth: RabbitMQ health status
        """
        start_time = time.time()
        
        try:
            import pika
            
            credentials = pika.PlainCredentials(user, password)
            parameters = pika.ConnectionParameters(
                host=host,
                credentials=credentials,
                connection_attempts=1,
                retry_delay=1,
            )
            
            connection = pika.BlockingConnection(parameters)
            connection.close()
            
            response_time = (time.time() - start_time) * 1000
            
            health = ComponentHealth(
                name="rabbitmq",
                status="healthy",
                message="RabbitMQ connection successful",
                last_check=datetime.now(),
                response_time_ms=response_time,
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            health = ComponentHealth(
                name="rabbitmq",
                status="unhealthy",
                message=f"RabbitMQ connection failed: {str(e)}",
                last_check=datetime.now(),
                response_time_ms=response_time,
            )
            
            logger.error(f"RabbitMQ health check failed: {e}")
        
        with self._lock:
            self._component_health["rabbitmq"] = health
        
        return health
    
    def check_google_genai(self, api_key: str) -> ComponentHealth:
        """
        Check Google GenAI API availability.
        
        Args:
            api_key: Google API key
            
        Returns:
            ComponentHealth: Google GenAI health status
        """
        start_time = time.time()
        
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            # Try to initialize the model (doesn't make API call yet)
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=api_key,
                temperature=0.1,
            )
            
            # Make a simple test call
            response = llm.invoke("test")
            
            response_time = (time.time() - start_time) * 1000
            
            health = ComponentHealth(
                name="google_genai",
                status="healthy",
                message="Google GenAI API accessible",
                last_check=datetime.now(),
                response_time_ms=response_time,
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            health = ComponentHealth(
                name="google_genai",
                status="unhealthy",
                message=f"Google GenAI API failed: {str(e)}",
                last_check=datetime.now(),
                response_time_ms=response_time,
            )
            
            logger.error(f"Google GenAI health check failed: {e}")
        
        with self._lock:
            self._component_health["google_genai"] = health
        
        return health
    
    def update_extraction_status(self, success: bool):
        """
        Update extraction status tracking.
        
        Args:
            success: Whether the extraction succeeded
        """
        with self._lock:
            if success:
                self._last_successful_extraction = datetime.now()
            else:
                self._last_failed_extraction = datetime.now()
    
    def get_health_status(self) -> Dict:
        """
        Get overall health status.
        
        Returns:
            Dict: Health status including all components
        """
        with self._lock:
            # Determine overall status
            component_statuses = [
                comp.status for comp in self._component_health.values()
            ]
            
            if not component_statuses:
                overall_status = "unknown"
            elif all(status == "healthy" for status in component_statuses):
                overall_status = "healthy"
            elif any(status == "unhealthy" for status in component_statuses):
                overall_status = "unhealthy"
            else:
                overall_status = "degraded"
            
            uptime_seconds = time.time() - self._service_start_time
            
            return {
                "status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": uptime_seconds,
                "components": {
                    name: comp.to_dict()
                    for name, comp in self._component_health.items()
                },
                "last_successful_extraction": (
                    self._last_successful_extraction.isoformat()
                    if self._last_successful_extraction
                    else None
                ),
                "last_failed_extraction": (
                    self._last_failed_extraction.isoformat()
                    if self._last_failed_extraction
                    else None
                ),
            }
    
    def is_healthy(self) -> bool:
        """
        Check if service is healthy.
        
        Returns:
            bool: True if all components are healthy
        """
        with self._lock:
            return all(
                comp.status == "healthy"
                for comp in self._component_health.values()
            )
    
    def log_health_status(self):
        """Log health status at INFO level."""
        status = self.get_health_status()
        logger.info(
            f"Service health status: {status['status']}",
            extra={"health_status": status}
        )


# Global health checker instance
health_checker = HealthChecker()
