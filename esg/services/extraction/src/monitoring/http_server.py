"""
HTTP server for health check and metrics endpoints.

This module provides a simple HTTP server that exposes:
- /health - Health check endpoint
- /metrics - Metrics endpoint

Requirements: 9.4
"""

import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable, Dict
import threading

logger = logging.getLogger(__name__)


class HealthMetricsHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health and metrics endpoints."""
    
    # Class variables to store callback functions
    health_callback: Callable[[], Dict] = None
    metrics_callback: Callable[[], Dict] = None
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/health":
            self._handle_health()
        elif self.path == "/metrics":
            self._handle_metrics()
        elif self.path == "/":
            self._handle_root()
        else:
            self._send_404()
    
    def _handle_health(self):
        """Handle health check endpoint."""
        try:
            if self.__class__.health_callback is None:
                self._send_error_response(500, "Health callback not configured")
                return
            
            health_status = self.__class__.health_callback()
            status_code = 200 if health_status.get("status") == "healthy" else 503
            
            self._send_json_response(status_code, health_status)
            
        except Exception as e:
            logger.error(f"Error in health endpoint: {e}", exc_info=True)
            self._send_error_response(500, f"Internal server error: {str(e)}")
    
    def _handle_metrics(self):
        """Handle metrics endpoint."""
        try:
            if self.__class__.metrics_callback is None:
                self._send_error_response(500, "Metrics callback not configured")
                return
            
            metrics = self.__class__.metrics_callback()
            self._send_json_response(200, metrics)
            
        except Exception as e:
            logger.error(f"Error in metrics endpoint: {e}", exc_info=True)
            self._send_error_response(500, f"Internal server error: {str(e)}")
    
    def _handle_root(self):
        """Handle root endpoint."""
        response = {
            "service": "ESG Extraction Service",
            "endpoints": {
                "/health": "Health check endpoint",
                "/metrics": "Metrics endpoint",
            }
        }
        self._send_json_response(200, response)
    
    def _send_json_response(self, status_code: int, data: Dict):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def _send_error_response(self, status_code: int, message: str):
        """Send error response."""
        self._send_json_response(status_code, {"error": message})
    
    def _send_404(self):
        """Send 404 response."""
        self._send_error_response(404, "Not found")
    
    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        logger.debug(f"{self.address_string()} - {format % args}")


class HealthMetricsServer:
    """
    HTTP server for health check and metrics endpoints.
    
    Runs in a separate thread to not block the main worker.
    """
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        health_callback: Callable[[], Dict] = None,
        metrics_callback: Callable[[], Dict] = None,
    ):
        """
        Initialize HTTP server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            health_callback: Callback function to get health status
            metrics_callback: Callback function to get metrics
        """
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        
        # Set callbacks on handler class
        HealthMetricsHandler.health_callback = health_callback
        HealthMetricsHandler.metrics_callback = metrics_callback
    
    def start(self):
        """Start the HTTP server in a background thread."""
        try:
            self.server = HTTPServer((self.host, self.port), HealthMetricsHandler)
            
            self.thread = threading.Thread(
                target=self.server.serve_forever,
                daemon=True,
                name="HealthMetricsServer"
            )
            self.thread.start()
            
            logger.info(
                f"Health and metrics server started on http://{self.host}:{self.port}"
            )
            logger.info(f"  - Health check: http://{self.host}:{self.port}/health")
            logger.info(f"  - Metrics: http://{self.host}:{self.port}/metrics")
            
        except Exception as e:
            logger.error(f"Failed to start health/metrics server: {e}", exc_info=True)
            raise
    
    def stop(self):
        """Stop the HTTP server."""
        if self.server:
            logger.info("Stopping health and metrics server...")
            self.server.shutdown()
            self.server.server_close()
            if self.thread:
                self.thread.join(timeout=5)
            logger.info("Health and metrics server stopped")
