"""Unit tests for console management functionality."""

from io import StringIO
from unittest.mock import Mock, call, patch

import pytest

from src.ui.console import ConsoleManager


class TestConsoleManager:
    """Test suite for ConsoleManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.console_manager = ConsoleManager()

    def test_initialization(self):
        """Test ConsoleManager initialization."""
        assert self.console_manager.console is not None
        assert hasattr(self.console_manager.console, "print")

    @patch("src.ui.console.Console")
    def test_print_with_style(self, mock_console_class):
        """Test print method with styling."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        console_manager = ConsoleManager()
        console_manager.print("Test message", "red")

        mock_console.print.assert_called_once_with("Test message", style="red")

    @patch("src.ui.console.Console")
    def test_print_without_style(self, mock_console_class):
        """Test print method without styling."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        console_manager = ConsoleManager()
        console_manager.print("Test message")

        mock_console.print.assert_called_once_with("Test message", style=None)

    @patch("src.ui.console.Console")
    def test_print_success(self, mock_console_class):
        """Test success message printing."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        console_manager = ConsoleManager()
        console_manager.print_success("Operation completed")

        mock_console.print.assert_called_once_with("[green][OK][/green] Operation completed")

    @patch("src.ui.console.Console")
    def test_print_error(self, mock_console_class):
        """Test error message printing."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        console_manager = ConsoleManager()
        console_manager.print_error("Something went wrong")

        mock_console.print.assert_called_once_with("[red][ERROR][/red] Something went wrong")

    @patch("src.ui.console.Console")
    def test_print_warning(self, mock_console_class):
        """Test warning message printing."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        console_manager = ConsoleManager()
        console_manager.print_warning("This is a warning")

        mock_console.print.assert_called_once_with("[yellow][WARN][/yellow] This is a warning")

    @patch("src.ui.console.Console")
    def test_print_info(self, mock_console_class):
        """Test info message printing."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        console_manager = ConsoleManager()
        console_manager.print_info("Information message")

        mock_console.print.assert_called_once_with("[cyan]Information message[/cyan]")

    @patch("src.ui.console.Console")
    def test_print_status_found(self, mock_console_class):
        """Test status printing when tool is found."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        console_manager = ConsoleManager()
        console_manager.print_status("python", True, "Install hint")

        mock_console.print.assert_called_once_with("[green][OK][/green] python found")

    @patch("src.ui.console.Console")
    def test_print_status_not_found_required(self, mock_console_class):
        """Test status printing when required tool is not found."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        console_manager = ConsoleManager()
        console_manager.print_status("python", False, "Install from python.org", False)

        expected_calls = [
            (("[red][ERROR][/red]  python not found",), {}),
            (("   Install with: [cyan]Install from python.org[/cyan]",), {}),
        ]
        mock_console.print.assert_has_calls([call(*args, **kwargs) for args, kwargs in expected_calls])

    @patch("src.ui.console.Console")
    def test_print_status_not_found_optional(self, mock_console_class):
        """Test status printing when optional tool is not found."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        console_manager = ConsoleManager()
        console_manager.print_status("tool", False, "Install hint", True)

        expected_calls = [
            (("[yellow][WARN][/yellow]  tool not found",), {}),
            (("   Install with: [cyan]Install hint[/cyan]",), {}),
        ]
        mock_console.print.assert_has_calls([call(*args, **kwargs) for args, kwargs in expected_calls])

    @patch("src.ui.console.Console")
    def test_print_status_no_hint(self, mock_console_class):
        """Test status printing without install hint."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        console_manager = ConsoleManager()
        console_manager.print_status("tool", False)

        mock_console.print.assert_called_once_with("[red][ERROR][/red]  tool not found")

    @patch("src.ui.console.BANNER", "Test Banner")
    @patch("src.ui.console.TAGLINE", "Test Tagline")
    @patch("src.ui.console.Console")
    def test_show_banner(self, mock_console_class):
        """Test banner display functionality."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        console_manager = ConsoleManager()
        console_manager.show_banner()

        # Verify that print was called for banner lines and tagline
        assert mock_console.print.call_count >= 3  # At least empty line, banner, tagline, empty line

        # Check that tagline was printed with italic bright_yellow style
        tagline_call = [call for call in mock_console.print.call_args_list if "Test Tagline" in str(call)]
        assert len(tagline_call) > 0

    @patch("src.ui.console.Panel")
    @patch("src.ui.console.Console")
    def test_show_panel(self, mock_console_class, mock_panel_class):
        """Test panel display functionality."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        mock_panel = Mock()
        mock_panel_class.fit.return_value = mock_panel

        console_manager = ConsoleManager()
        console_manager.show_panel("Test content", "Test title", "blue")

        mock_panel_class.fit.assert_called_once_with("Test content", title="Test title", border_style="blue")
        mock_console.print.assert_called_once_with(mock_panel)

    @patch("src.ui.console.Align")
    @patch("src.ui.console.Console")
    def test_show_centered_message(self, mock_console_class, mock_align_class):
        """Test centered message display."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        mock_centered = Mock()
        mock_align_class.center.return_value = mock_centered

        console_manager = ConsoleManager()
        console_manager.show_centered_message("Centered text")

        mock_align_class.center.assert_called_once_with("Centered text")
        mock_console.print.assert_called_once_with(mock_centered)

    @patch("src.ui.console.Console")
    def test_print_newline(self, mock_console_class):
        """Test newline printing."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        console_manager = ConsoleManager()
        console_manager.print_newline()

        mock_console.print.assert_called_once_with()

    @patch("src.ui.console.Console")
    def test_print_dim(self, mock_console_class):
        """Test dim text printing."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        console_manager = ConsoleManager()
        console_manager.print_dim("Dimmed text")

        mock_console.print.assert_called_once_with("[dim]Dimmed text[/dim]")


def test_global_console_manager_import():
    """Test that global console_manager instance can be imported."""
    from src.ui.console import console_manager

    assert console_manager is not None
    assert isinstance(console_manager, ConsoleManager)
    assert hasattr(console_manager, "console")


class TestConsoleManagerIntegration:
    """Integration tests for ConsoleManager with real Rich console."""

    def test_real_console_output(self):
        """Test that ConsoleManager produces output with real Rich console."""
        # Create a console manager with output to string
        from rich.console import Console

        output = StringIO()
        console_manager = ConsoleManager()
        console_manager.console = Console(file=output, width=80)

        # Test various output methods
        console_manager.print_success("Test success")
        console_manager.print_error("Test error")
        console_manager.print_warning("Test warning")
        console_manager.print_info("Test info")

        output_str = output.getvalue()

        # Verify output contains expected text
        assert "Test success" in output_str
        assert "Test error" in output_str
        assert "Test warning" in output_str
        assert "Test info" in output_str

        # Verify styling markers are present
        assert "[OK]" in output_str
        assert "[ERROR]" in output_str
        assert "[WARN]" in output_str
