"""FileTracker service for tracking file operations during installation.

This service implements the FileTrackerProtocol and provides functionality
to track file creations, modifications, and directory creations with
rich formatted summaries.
"""

from pathlib import Path

from core.interfaces import FileTrackerProtocol


class FileTracker(FileTrackerProtocol):
    """Track files that are created or modified during installation."""

    def __init__(self):
        self.created_files = []
        self.modified_files = []
        self.created_dirs = []

    def track_file_creation(self, filepath: Path) -> None:
        """Track a file that was created."""
        self.created_files.append(str(filepath))

    def track_file_modification(self, filepath: Path) -> None:
        """Track a file that was modified."""
        self.modified_files.append(str(filepath))

    def track_dir_creation(self, dirpath: Path) -> None:
        """Track a directory that was created."""
        self.created_dirs.append(str(dirpath))

    def get_summary(self) -> str:
        """Get a formatted summary of all tracked changes."""
        lines = []

        if self.created_dirs:
            lines.append("[bold cyan]Directories Created:[/bold cyan]")
            for dir_path in sorted(self.created_dirs):
                lines.append(f"  📁 {dir_path}")
            lines.append("")

        if self.created_files:
            lines.append("[bold green]Files Created:[/bold green]")
            # Group files by type
            file_groups = self._group_files_by_type(self.created_files)
            for file_type, files in file_groups.items():
                lines.append(f"  [dim]{file_type}: [/dim]")
                for file_path in sorted(files):
                    lines.append(f"    📄 {file_path}")
                lines.append("")
            lines.append("")

        if self.modified_files:
            lines.append("[bold yellow]Files Modified:[/bold yellow]")
            # Group files by type
            file_groups = self._group_files_by_type(self.modified_files)
            for file_type, files in file_groups.items():
                lines.append(f"  [dim]{file_type}: [/dim]")
                for file_path in sorted(files):
                    lines.append(f"    ✏️  {file_path}")
                lines.append("")
            lines.append("")

        total_changes = len(self.created_dirs) + len(self.created_files) + len(self.modified_files)
        if total_changes > 0:
            lines.append(
                f"[dim]Total: {len(self.created_dirs)} directories, "
                f"{len(self.created_files)} files created, "
                f"{len(self.modified_files)} files modified[/dim]"
            )
        else:
            lines.append("[dim]No files were created or modified[/dim]")

        return "\n".join(lines)

    def _group_files_by_type(self, files: list) -> dict:
        """Group files by their type based on directory structure."""
        groups = {"Chatmodes": [], "Instructions": [], "Prompts": [], "Commands": []}

        for file_path in files:
            # Convert to string and normalize path separators
            path_str = str(file_path).replace("\\", "/")

            if "chatmodes" in path_str:
                groups["Chatmodes"].append(file_path)
            elif "instructions" in path_str:
                groups["Instructions"].append(file_path)
            elif "prompts" in path_str:
                groups["Prompts"].append(file_path)
            elif "commands" in path_str:
                groups["Commands"].append(file_path)
            else:
                # Fallback for any files not in the expected structure
                groups["Other"] = groups.get("Other", [])
                groups["Other"].append(file_path)

        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
