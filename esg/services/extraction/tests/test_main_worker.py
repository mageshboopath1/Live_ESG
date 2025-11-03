"""
Tests for the main extraction worker.

This module tests the core functionality of the extraction worker including:
- RabbitMQ connection setup
- Message processing logic
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from main import (
    get_rabbitmq_connection,
    process_extraction_task,
    callback,
)


def test_get_rabbitmq_connection():
    """Test that RabbitMQ connection can be created with proper credentials."""
    with patch('main.pika.BlockingConnection') as mock_connection:
        with patch('main.pika.PlainCredentials') as mock_credentials:
            with patch('main.pika.ConnectionParameters') as mock_params:
                # Call the function
                get_rabbitmq_connection()
                
                # Verify credentials were created
                mock_credentials.assert_called_once()
                
                # Verify connection parameters were created
                mock_params.assert_called_once()
                
                # Verify connection was created
                mock_connection.assert_called_once()


def test_process_extraction_task_already_processed():
    """Test that already processed documents are skipped."""
    with patch('main.check_document_processed', return_value=True):
        with patch('main.logger') as mock_logger:
            # Process a document that's already processed
            result = process_extraction_task("RELIANCE/2024_BRSR.pdf")
            
            # Should return True (success)
            assert result is True
            
            # Should log that it's skipping
            mock_logger.info.assert_any_call(
                "Document RELIANCE/2024_BRSR.pdf already processed. Skipping."
            )


def test_process_extraction_task_invalid_object_key():
    """Test that invalid object keys are handled gracefully."""
    with patch('main.check_document_processed', return_value=False):
        with patch('main.parse_object_key', side_effect=ValueError("Invalid format")):
            with patch('main.logger') as mock_logger:
                # Process with invalid object key
                result = process_extraction_task("invalid_key")
                
                # Should return False (failure)
                assert result is False
                
                # Should log the error
                mock_logger.error.assert_called()


def test_callback_success():
    """Test that callback acknowledges message on successful processing."""
    # Mock channel and method
    mock_channel = Mock()
    mock_method = Mock()
    mock_method.delivery_tag = "test_tag"
    
    # Mock successful processing
    with patch('main.process_extraction_task', return_value=True):
        # Call callback
        callback(mock_channel, mock_method, None, b"RELIANCE/2024_BRSR.pdf")
        
        # Should acknowledge the message
        mock_channel.basic_ack.assert_called_once_with(delivery_tag="test_tag")
        
        # Should not reject the message
        mock_channel.basic_nack.assert_not_called()


def test_callback_failure():
    """Test that callback rejects message on failed processing."""
    # Mock channel and method
    mock_channel = Mock()
    mock_method = Mock()
    mock_method.delivery_tag = "test_tag"
    
    # Mock failed processing
    with patch('main.process_extraction_task', return_value=False):
        # Call callback
        callback(mock_channel, mock_method, None, b"RELIANCE/2024_BRSR.pdf")
        
        # Should reject the message without requeue
        mock_channel.basic_nack.assert_called_once_with(
            delivery_tag="test_tag",
            requeue=False
        )
        
        # Should not acknowledge the message
        mock_channel.basic_ack.assert_not_called()


def test_callback_exception():
    """Test that callback handles exceptions gracefully."""
    # Mock channel and method
    mock_channel = Mock()
    mock_method = Mock()
    mock_method.delivery_tag = "test_tag"
    
    # Mock exception during processing
    with patch('main.process_extraction_task', side_effect=Exception("Test error")):
        # Call callback
        callback(mock_channel, mock_method, None, b"RELIANCE/2024_BRSR.pdf")
        
        # Should reject the message without requeue
        mock_channel.basic_nack.assert_called_once_with(
            delivery_tag="test_tag",
            requeue=False
        )
        
        # Should not acknowledge the message
        mock_channel.basic_ack.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
