"""CacheManager service for managing temporary cache directories.

This service provides secure cache directory creation and management with automatic cleanup.
Ensures cache directories are created in system temp directory with unique naming.
"""

import atexit
import glob
import os
import platform
import re
import shutil
import tempfile
from pathlib import Path
from typing import List

from core.interfaces import CacheManagerProtocol


class CacheManager(CacheManagerProtocol):
    """Manages temporary cache directories for template downloads.

    Provides secure cache directory creation and management with automatic cleanup.
    Ensures cache directories are created in system temp directory with unique naming.
    """

    def __init__(self):
        """Initialize cache manager."""
        self.process_id = os.getpid()
        self._active_caches: List[Path] = []

        # Register atexit handler for cleanup on normal termination
        atexit.register(self.cleanup_all_caches)

    def create_cache_dir(self) -> Path:
        """Create a temporary cache directory in system temp location.

        Creates directory outside current working directory and all parent directories
        using system temp directory with process ID for uniqueness.

        Returns:
            Path: Path to created cache directory

        Raises:
            OSError: If cache directory creation fails
        """
        # Create cache directory with unique naming including process ID
        cache_prefix = f"sdd_templates_{self.process_id}_"
        cache_dir = Path(tempfile.mkdtemp(prefix=cache_prefix))

        # Track active cache for cleanup
        self._active_caches.append(cache_dir)

        return cache_dir

    def cleanup_cache(self, cache_dir: Path) -> None:
        """Clean up a specific cache directory.

        Args:
            cache_dir: Path to cache directory to cleanup
        """
        try:
            if cache_dir.exists():
                shutil.rmtree(cache_dir, ignore_errors=True)
        except Exception as e:
            # Log warning but don't fail operation
            from rich.console import Console

            console = Console()
            console.print(f"[yellow]⚠ Warning: Could not cleanup cache directory {cache_dir}: {e}[/yellow]")
        finally:
            # Always remove from active caches, regardless of cleanup success/failure
            if cache_dir in self._active_caches:
                self._active_caches.remove(cache_dir)

    def cleanup_all_caches(self) -> None:
        """Clean up all active cache directories."""
        for cache_dir in self._active_caches.copy():
            self.cleanup_cache(cache_dir)

    def cleanup_orphaned_caches(self) -> int:
        """Clean up orphaned cache directories from interrupted runs.

        Scans system temp directory for sdd_templates_* directories and removes
        those belonging to processes that are no longer running.

        Returns:
            int: Number of orphaned caches cleaned up
        """
        import tempfile

        cleaned_count = 0
        temp_dir = Path(tempfile.gettempdir())

        try:
            # Find all sdd_templates_* directories in temp
            pattern = temp_dir / "sdd_templates_*"
            orphan_candidates = [Path(p) for p in glob.glob(str(pattern)) if Path(p).is_dir()]

            for cache_dir in orphan_candidates:
                try:
                    # Extract process ID from directory name
                    match = re.search(r"sdd_templates_(\d+)_", cache_dir.name)
                    if not match:
                        continue

                    pid = int(match.group(1))

                    # Skip if it's our own cache
                    if pid == self.process_id:
                        continue

                    # Check if process is still running
                    if self._is_process_running(pid):
                        continue

                    # Process not running, clean up orphaned cache
                    shutil.rmtree(cache_dir, ignore_errors=True)
                    cleaned_count += 1

                except (ValueError, OSError, Exception) as e:
                    # Log warning for individual failures but continue
                    from rich.console import Console

                    console = Console()
                    console.print(f"[yellow]⚠ Warning: Could not cleanup orphaned cache {cache_dir}: {e}[/yellow]")
                    continue

            if cleaned_count > 0:
                from rich.console import Console

                console = Console()
                console.print(
                    f"[cyan]🧩 Cleaned up {cleaned_count} orphaned cache "
                    f"director{'y' if cleaned_count == 1 else 'ies'}[/cyan]"
                )

        except Exception as e:
            # Log warning for overall failure but don't fail operation
            from rich.console import Console

            console = Console()
            console.print(f"[yellow]⚠ Warning: Could not scan for orphaned caches: {e}[/yellow]")

        return cleaned_count

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running.

        Args:
            pid: Process ID to check

        Returns:
            bool: True if process is running, False otherwise
        """
        try:
            # On Windows, use different approach
            if platform.system() == "Windows":
                try:
                    # Lazy import subprocess for Windows process checking
                    import subprocess

                    # Use tasklist to check if process exists
                    result = subprocess.run(
                        ["tasklist", "/FI", f"PID eq {pid}"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    return str(pid) in result.stdout
                except Exception:  # Catch any subprocess-related errors
                    return False
            else:
                # On Unix-like systems, use os.kill with signal 0
                os.kill(pid, 0)
                return True

        except (OSError, ProcessLookupError):
            return False
        except Exception:
            # If we can't determine, assume it's running to be safe
            return True

    def get_cache_info(self, cache_dir: Path) -> dict:
        """Get information about a cache directory.

        Args:
            cache_dir: Path to cache directory

        Returns:
            dict: Cache information including size and file count
        """
        if not cache_dir.exists():
            return {"exists": False, "size_bytes": 0, "file_count": 0}

        total_size = 0
        file_count = 0

        try:
            for file_path in cache_dir.rglob("*"):
                if file_path.is_file():
                    file_count += 1
                    total_size += file_path.stat().st_size
        except Exception:
            pass  # Ignore errors during size calculation

        return {
            "exists": True,
            "size_bytes": total_size,
            "file_count": file_count,
            "path": str(cache_dir),
        }
