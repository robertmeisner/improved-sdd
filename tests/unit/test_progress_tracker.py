"""Unit tests for ProgressTracker UI component.

This module tests the ProgressTracker class which provides centralized progress
tracking operations for the CLI application using Rich library.
"""

import pytest
from unittest.mock import Mock, patch, call
from rich.console import Console
from rich.progress import Progress

from src.ui.progress import ProgressTracker, progress_tracker
from src.core.models import ProgressInfo


class TestProgressTracker:
    """Test cases for ProgressTracker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_console = Mock(spec=Console)
        self.tracker = ProgressTracker(console=self.mock_console)
    
    def test_init_with_console(self):
        """Test ProgressTracker initialization with provided console."""
        console = Mock(spec=Console)
        tracker = ProgressTracker(console=console)
        assert tracker.console is console
    
    def test_init_without_console(self):
        """Test ProgressTracker initialization creates default console."""
        tracker = ProgressTracker()
        assert tracker.console is not None
        assert isinstance(tracker.console, Console)
    
    @patch('src.ui.progress.Progress')
    def test_create_download_progress(self, mock_progress_class):
        """Test creating download-specific progress instance."""
        mock_progress = Mock(spec=Progress)
        mock_progress_class.return_value = mock_progress
        
        result = self.tracker.create_download_progress()
        
        assert result is mock_progress
        mock_progress_class.assert_called_once()
        call_args = mock_progress_class.call_args
        assert call_args.kwargs['console'] is self.mock_console
    
    @patch('src.ui.progress.Progress')
    def test_create_extraction_progress(self, mock_progress_class):
        """Test creating extraction-specific progress instance."""
        mock_progress = Mock(spec=Progress)
        mock_progress_class.return_value = mock_progress
        
        result = self.tracker.create_extraction_progress()
        
        assert result is mock_progress
        mock_progress_class.assert_called_once()
        call_args = mock_progress_class.call_args
        assert call_args.kwargs['console'] is self.mock_console
    
    @patch('src.ui.progress.Progress')
    def test_create_generic_progress(self, mock_progress_class):
        """Test creating generic progress instance."""
        mock_progress = Mock(spec=Progress)
        mock_progress_class.return_value = mock_progress
        
        result = self.tracker.create_generic_progress()
        
        assert result is mock_progress
        mock_progress_class.assert_called_once()
        call_args = mock_progress_class.call_args
        assert call_args.kwargs['console'] is self.mock_console
    
    def test_update_progress_from_info_with_bytes(self):
        """Test updating progress using ProgressInfo with byte information."""
        mock_progress = Mock(spec=Progress)
        task_id = 1
        
        progress_info = ProgressInfo(
            phase="download",
            bytes_completed=500,
            bytes_total=1000,
            percentage=50.0
        )
        
        self.tracker.update_progress_from_info(mock_progress, task_id, progress_info)
        
        mock_progress.update.assert_called_once_with(
            task_id,
            completed=500,
            total=1000,
            description="Downloading..."
        )
    
    def test_update_progress_from_info_with_percentage_only(self):
        """Test updating progress using ProgressInfo with bytes."""
        mock_progress = Mock(spec=Progress)
        task_id = 1
        
        progress_info = ProgressInfo(
            phase="extract",
            bytes_completed=75,
            bytes_total=100,
            percentage=75.0
        )
        
        self.tracker.update_progress_from_info(mock_progress, task_id, progress_info)
        
        mock_progress.update.assert_called_once_with(
            task_id,
            completed=75,
            total=100,
            description="Extracting..."
        )
    
    def test_update_progress_from_info_with_percentage_and_total(self):
        """Test updating progress using ProgressInfo with bytes and total."""
        mock_progress = Mock(spec=Progress)
        task_id = 1
        
        progress_info = ProgressInfo(
            phase="processing",
            bytes_completed=500,
            bytes_total=2000,
            percentage=25.0
        )
        
        self.tracker.update_progress_from_info(mock_progress, task_id, progress_info)
        
        mock_progress.update.assert_called_once_with(
            task_id,
            completed=500,
            total=2000,
            description="Processing..."
        )
    
    def test_update_progress_from_info_indeterminate(self):
        """Test updating progress for indeterminate progress (no bytes total)."""
        mock_progress = Mock(spec=Progress)
        task_id = 1
        
        progress_info = ProgressInfo(
            phase="initializing",
            bytes_completed=0,
            bytes_total=0,
            percentage=0.0
        )
        
        self.tracker.update_progress_from_info(mock_progress, task_id, progress_info)
        
        mock_progress.update.assert_called_once_with(
            task_id,
            description="Initializing..."
        )
    
    def test_update_progress_from_info_no_phase(self):
        """Test updating progress without phase information."""
        mock_progress = Mock(spec=Progress)
        task_id = 1
        
        progress_info = ProgressInfo(
            phase="",  # Empty phase
            bytes_completed=300,
            bytes_total=600,
            percentage=50.0
        )
        
        self.tracker.update_progress_from_info(mock_progress, task_id, progress_info)
        
        mock_progress.update.assert_called_once_with(
            task_id,
            completed=300,
            total=600,
            description="Processing..."
        )
    
    def test_create_callback_for_progress(self):
        """Test creating progress callback function."""
        mock_progress = Mock(spec=Progress)
        task_id = 1
        
        callback = self.tracker.create_callback_for_progress(mock_progress, task_id)
        
        # Test the callback function
        progress_info = ProgressInfo(
            phase="test",
            bytes_completed=100,
            bytes_total=200,
            percentage=50.0
        )
        callback(progress_info)
        
        mock_progress.update.assert_called_once_with(
            task_id,
            completed=100,
            total=200,
            description="Testing..."
        )
    
    @patch('src.ui.progress.Progress')
    def test_run_with_progress_download_type(self, mock_progress_class):
        """Test running operation with download progress type."""
        mock_progress_instance = Mock()
        mock_progress_context = Mock()
        mock_progress_context.__enter__ = Mock(return_value=mock_progress_instance)
        mock_progress_context.__exit__ = Mock(return_value=None)
        mock_progress_class.return_value = mock_progress_context
        
        mock_progress_instance.add_task.return_value = 1
        
        # Mock operation function
        def mock_operation(callback):
            return "operation_result"
        
        result = self.tracker.run_with_progress(
            mock_operation, 
            description="Downloading files...",
            progress_type="download"
        )
        
        assert result == "operation_result"
        mock_progress_instance.add_task.assert_called_once_with("Downloading files...", total=None)
        mock_progress_instance.update.assert_called_once_with(
            1, description="Complete!", completed=100, total=100
        )
    
    @patch('src.ui.progress.Progress')
    def test_run_with_progress_extraction_type(self, mock_progress_class):
        """Test running operation with extraction progress type."""
        mock_progress_instance = Mock()
        mock_progress_context = Mock()
        mock_progress_context.__enter__ = Mock(return_value=mock_progress_instance)
        mock_progress_context.__exit__ = Mock(return_value=None)
        mock_progress_class.return_value = mock_progress_context
        
        mock_progress_instance.add_task.return_value = 2
        
        def mock_operation(callback):
            return "extraction_result"
        
        result = self.tracker.run_with_progress(
            mock_operation,
            description="Extracting...",
            progress_type="extraction"
        )
        
        assert result == "extraction_result"
        mock_progress_instance.add_task.assert_called_once_with("Extracting...", total=None)
        mock_progress_instance.update.assert_called_once_with(
            2, description="Complete!", completed=100, total=100
        )
    
    @patch('src.ui.progress.Progress')
    def test_run_with_progress_generic_type(self, mock_progress_class):
        """Test running operation with generic progress type."""
        mock_progress_instance = Mock()
        mock_progress_context = Mock()
        mock_progress_context.__enter__ = Mock(return_value=mock_progress_instance)
        mock_progress_context.__exit__ = Mock(return_value=None)
        mock_progress_class.return_value = mock_progress_context
        
        mock_progress_instance.add_task.return_value = 3
        
        def mock_operation(callback):
            progress_info = ProgressInfo(
                phase="testing",
                bytes_completed=50,
                bytes_total=100,
                percentage=50.0
            )
            callback(progress_info)
            return "generic_result"
        
        result = self.tracker.run_with_progress(mock_operation, progress_type="generic")
        
        assert result == "generic_result"
        mock_progress_instance.add_task.assert_called_once_with("Processing...", total=None)
        # Should be called twice: once for the callback, once for completion
        assert mock_progress_instance.update.call_count == 2
    
    def test_run_with_progress_operation_with_callback(self):
        """Test that operation receives callback and can use it."""
        # Use a real Progress instance for integration test
        mock_progress_instance = Mock()
        mock_progress_context = Mock()
        mock_progress_context.__enter__ = Mock(return_value=mock_progress_instance)
        mock_progress_context.__exit__ = Mock(return_value=None)
        
        with patch('src.ui.progress.Progress', return_value=mock_progress_context):
            mock_progress_instance.add_task.return_value = 1
            
            callback_received = None
            
            def mock_operation(callback):
                nonlocal callback_received
                callback_received = callback
                return "test_result"
            
            result = self.tracker.run_with_progress(mock_operation)
            
            assert result == "test_result"
            assert callback_received is not None
            
            # Test that the callback works
            progress_info = ProgressInfo(
                phase="test",
                bytes_completed=25,
                bytes_total=100,
                percentage=25.0
            )
            callback_received(progress_info)
            
            # Verify the callback updated progress
            expected_calls = [
                call("Processing...", total=None),
            ]
            mock_progress_instance.add_task.assert_has_calls(expected_calls)


class TestProgressTrackerIntegration:
    """Integration tests for ProgressTracker with real Rich components."""
    
    def test_real_progress_creation(self):
        """Test creating real Progress instances."""
        tracker = ProgressTracker()
        
        # Test each progress type creates without errors
        download_progress = tracker.create_download_progress()
        extraction_progress = tracker.create_extraction_progress()
        generic_progress = tracker.create_generic_progress()
        
        assert isinstance(download_progress, Progress)
        assert isinstance(extraction_progress, Progress)
        assert isinstance(generic_progress, Progress)
    
    def test_progress_callback_integration(self):
        """Test progress callback integration with real Progress."""
        tracker = ProgressTracker()
        progress = tracker.create_generic_progress()
        
        with progress:
            task_id = progress.add_task("Test task", total=100)
            callback = tracker.create_callback_for_progress(progress, task_id)
            
            # Test callback updates progress
            progress_info = ProgressInfo(
                phase="test",
                bytes_completed=50,
                bytes_total=100,
                percentage=50.0
            )
            
            # Should not raise errors
            callback(progress_info)
    
    def test_global_progress_tracker_instance(self):
        """Test that global progress_tracker instance is properly configured."""
        assert progress_tracker is not None
        assert isinstance(progress_tracker, ProgressTracker)
        assert isinstance(progress_tracker.console, Console)
    
    def test_progress_tracker_imports(self):
        """Test that ProgressTracker can be imported from ui module."""
        from src.ui import ProgressTracker as ImportedProgressTracker
        from src.ui import progress_tracker as imported_progress_tracker
        
        assert ImportedProgressTracker is ProgressTracker
        assert imported_progress_tracker is progress_tracker


if __name__ == "__main__":
    pytest.main([__file__])