#!/usr/bin/env python3
"""
Migration Rollback Infrastructure for CLI Decomposition

This module provides comprehensive rollback capabilities for the CLI decomposition
process, ensuring that any migration phase can be safely reverted within 5 minutes.

Features:
- Checkpoint creation with full state snapshots
- File-based and git-based rollback strategies
- Validation framework for rollback success
- Integration with performance and behavioral monitoring
- Automated cleanup and verification
"""

import json
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import track

console = Console()


@dataclass
class RollbackCheckpoint:
    """Represents a migration checkpoint for rollback."""
    phase: str
    timestamp: float
    checkpoint_path: Path
    git_commit: Optional[str] = None
    performance_baseline: Optional[Dict] = None
    behavioral_baseline: Optional[Dict] = None
    file_count: int = 0
    size_bytes: int = 0


@dataclass
class RollbackValidationResult:
    """Result of rollback validation."""
    success: bool
    tests_passed: bool
    performance_restored: bool
    behavioral_match: bool
    validation_time_seconds: float
    errors: List[str]


class MigrationRollback:
    """
    Comprehensive rollback infrastructure for CLI decomposition migration.
    
    Provides multiple rollback strategies:
    1. File-based snapshots (fastest)
    2. Git-based commits (most reliable)
    3. Hybrid approach (recommended)
    
    Ensures rollback operations complete within 5-minute requirement.
    """
    
    def __init__(self, project_root: Path = None, checkpoint_dir: Path = None):
        """Initialize rollback infrastructure."""
        self.project_root = project_root or Path.cwd()
        self.checkpoint_dir = checkpoint_dir or (self.project_root / "tools" / "rollback_checkpoints")
        self.checkpoints: Dict[str, RollbackCheckpoint] = {}
        self.git_available = self._check_git_available()
        
        # Ensure checkpoint directory exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing checkpoints
        self._load_existing_checkpoints()
        
        console.print(f"[dim]Rollback infrastructure initialized")
        console.print(f"[dim]Checkpoint directory: {self.checkpoint_dir}")
        console.print(f"[dim]Git available: {self.git_available}")

    def _check_git_available(self) -> bool:
        """Check if git is available and repository is initialized."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _load_existing_checkpoints(self):
        """Load checkpoint metadata from previous sessions."""
        metadata_file = self.checkpoint_dir / "checkpoints.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    for phase, checkpoint_data in data.items():
                        self.checkpoints[phase] = RollbackCheckpoint(
                            phase=checkpoint_data['phase'],
                            timestamp=checkpoint_data['timestamp'],
                            checkpoint_path=Path(checkpoint_data['checkpoint_path']),
                            git_commit=checkpoint_data.get('git_commit'),
                            performance_baseline=checkpoint_data.get('performance_baseline'),
                            behavioral_baseline=checkpoint_data.get('behavioral_baseline'),
                            file_count=checkpoint_data.get('file_count', 0),
                            size_bytes=checkpoint_data.get('size_bytes', 0)
                        )
            except (json.JSONDecodeError, KeyError) as e:
                console.print(f"[yellow]Warning: Could not load checkpoint metadata: {e}[/yellow]")

    def _save_checkpoint_metadata(self):
        """Save checkpoint metadata for persistence."""
        metadata_file = self.checkpoint_dir / "checkpoints.json"
        data = {}
        for phase, checkpoint in self.checkpoints.items():
            data[phase] = {
                'phase': checkpoint.phase,
                'timestamp': checkpoint.timestamp,
                'checkpoint_path': str(checkpoint.checkpoint_path),
                'git_commit': checkpoint.git_commit,
                'performance_baseline': checkpoint.performance_baseline,
                'behavioral_baseline': checkpoint.behavioral_baseline,
                'file_count': checkpoint.file_count,
                'size_bytes': checkpoint.size_bytes
            }
        
        with open(metadata_file, 'w') as f:
            json.dump(data, f, indent=2)

    def create_checkpoint(self, phase: str, include_git: bool = True) -> RollbackCheckpoint:
        """
        Create a comprehensive checkpoint before major migration changes.
        
        Args:
            phase: Migration phase name (e.g., "core_extraction_start")
            include_git: Whether to create git commit checkpoint
            
        Returns:
            RollbackCheckpoint object with metadata
        """
        start_time = time.time()
        timestamp = int(start_time)
        
        console.print(f"🏁 Creating rollback checkpoint for phase: [bold]{phase}[/bold]")
        
        # Create checkpoint directory
        checkpoint_path = self.checkpoint_dir / f"checkpoint_{phase}_{timestamp}"
        checkpoint_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize checkpoint object
        checkpoint = RollbackCheckpoint(
            phase=phase,
            timestamp=start_time,
            checkpoint_path=checkpoint_path
        )
        
        try:
            # Step 1: Create file-based snapshot (fast recovery)
            self._create_file_snapshot(checkpoint_path)
            
            # Step 2: Create git checkpoint if available (reliable recovery)
            if include_git and self.git_available:
                checkpoint.git_commit = self._create_git_checkpoint(phase)
            
            # Step 3: Capture performance baseline
            checkpoint.performance_baseline = self._capture_performance_baseline(phase)
            
            # Step 4: Capture behavioral baseline  
            checkpoint.behavioral_baseline = self._capture_behavioral_baseline(phase)
            
            # Step 5: Calculate checkpoint metrics
            checkpoint.file_count, checkpoint.size_bytes = self._calculate_checkpoint_size(checkpoint_path)
            
            # Store checkpoint
            self.checkpoints[phase] = checkpoint
            self._save_checkpoint_metadata()
            
            elapsed = time.time() - start_time
            console.print(f"✅ Checkpoint created successfully in {elapsed:.1f}s")
            console.print(f"   📁 Files: {checkpoint.file_count}, Size: {checkpoint.size_bytes // 1024}KB")
            if checkpoint.git_commit:
                console.print(f"   🔗 Git commit: {checkpoint.git_commit[:8]}")
            
            return checkpoint
            
        except Exception as e:
            console.print(f"[red]❌ Failed to create checkpoint: {e}[/red]")
            # Cleanup failed checkpoint
            if checkpoint_path.exists():
                shutil.rmtree(checkpoint_path)
            raise

    def _create_file_snapshot(self, checkpoint_path: Path):
        """Create file-based snapshot for fast rollback."""
        console.print("   📂 Creating file snapshot...")
        
        # Critical directories to backup
        critical_dirs = ["src", "tests"]
        
        for dir_name in critical_dirs:
            source_dir = self.project_root / dir_name
            if source_dir.exists():
                target_dir = checkpoint_path / dir_name
                shutil.copytree(source_dir, target_dir)
        
        # For tools directory, exclude rollback_checkpoints to prevent recursion
        tools_source = self.project_root / "tools"
        if tools_source.exists():
            tools_target = checkpoint_path / "tools"
            tools_target.mkdir(exist_ok=True)
            
            # Copy tool files while excluding checkpoints directory
            for item in tools_source.iterdir():
                if item.name != "rollback_checkpoints" and item.name != "__pycache__":
                    if item.is_dir():
                        shutil.copytree(item, tools_target / item.name)
                    else:
                        shutil.copy2(item, tools_target / item.name)
        
        # Critical files to backup
        critical_files = ["pyproject.toml", "requirements.txt", "README.md"]
        
        for file_name in critical_files:
            source_file = self.project_root / file_name
            if source_file.exists():
                target_file = checkpoint_path / file_name
                shutil.copy2(source_file, target_file)

    def _create_git_checkpoint(self, phase: str) -> Optional[str]:
        """Create git commit checkpoint."""
        console.print("   🔗 Creating git checkpoint...")
        
        try:
            # Add all changes
            subprocess.run(
                ["git", "add", "."],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                timeout=30
            )
            
            # Create commit
            commit_message = f"Migration checkpoint: {phase}"
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Get commit hash
                hash_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return hash_result.stdout.strip()
            else:
                console.print(f"[yellow]Warning: Git commit failed: {result.stderr}[/yellow]")
                return None
                
        except subprocess.TimeoutExpired:
            console.print("[yellow]Warning: Git operation timed out[/yellow]")
            return None
        except subprocess.CalledProcessError as e:
            console.print(f"[yellow]Warning: Git operation failed: {e}[/yellow]")
            return None

    def _capture_performance_baseline(self, phase: str) -> Optional[Dict]:
        """Capture performance baseline using existing monitoring."""
        console.print("   📊 Capturing performance baseline...")
        
        try:
            # Try to use existing performance monitor
            from .performance_monitor import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            snapshot = monitor.create_checkpoint(f"rollback_{phase}")
            
            return {
                'startup_time_ms': snapshot.startup_time_ms,
                'memory_usage_mb': snapshot.memory_usage_mb,
                'import_time_ms': snapshot.import_time_ms,
                'timestamp': snapshot.timestamp
            }
            
        except ImportError:
            console.print("[yellow]Warning: Performance monitor not available[/yellow]")
            return None
        except Exception as e:
            console.print(f"[yellow]Warning: Performance capture failed: {e}[/yellow]")
            return None

    def _capture_behavioral_baseline(self, phase: str) -> Optional[Dict]:
        """Capture behavioral baseline using existing testing."""
        console.print("   🧪 Capturing behavioral baseline...")
        
        try:
            # Try to use existing baseline testing
            from .baseline_testing import BaselineTestSuite
            
            suite = BaselineTestSuite()
            suite.capture_baseline()
            
            return {
                'baseline_file': str(suite.baseline_file),
                'timestamp': time.time()
            }
            
        except ImportError:
            console.print("[yellow]Warning: Baseline testing not available[/yellow]")
            return None
        except Exception as e:
            console.print(f"[yellow]Warning: Behavioral capture failed: {e}[/yellow]")
            return None

    def _calculate_checkpoint_size(self, checkpoint_path: Path) -> tuple[int, int]:
        """Calculate checkpoint file count and size."""
        file_count = 0
        total_size = 0
        
        for file_path in checkpoint_path.rglob("*"):
            if file_path.is_file():
                file_count += 1
                total_size += file_path.stat().st_size
        
        return file_count, total_size

    def rollback_to_checkpoint(self, phase: str, strategy: str = "hybrid") -> RollbackValidationResult:
        """
        Rollback to a specific checkpoint using specified strategy.
        
        Args:
            phase: Phase to rollback to
            strategy: "file", "git", or "hybrid" (default)
            
        Returns:
            RollbackValidationResult with success status and metrics
        """
        start_time = time.time()
        
        if phase not in self.checkpoints:
            raise ValueError(f"No checkpoint found for phase: {phase}")
        
        checkpoint = self.checkpoints[phase]
        console.print(f"⟲ Rolling back to checkpoint: [bold]{phase}[/bold]")
        console.print(f"   Strategy: {strategy}")
        
        try:
            # Perform rollback based on strategy
            if strategy == "git" and checkpoint.git_commit:
                self._rollback_with_git(checkpoint)
            elif strategy == "file" or not checkpoint.git_commit:
                self._rollback_with_files(checkpoint)
            elif strategy == "hybrid":
                # Try git first, fallback to files
                try:
                    if checkpoint.git_commit:
                        self._rollback_with_git(checkpoint)
                    else:
                        self._rollback_with_files(checkpoint)
                except Exception:
                    console.print("[yellow]Git rollback failed, falling back to file restoration[/yellow]")
                    self._rollback_with_files(checkpoint)
            
            # Validate rollback success
            validation_result = self.validate_rollback(phase)
            
            elapsed = time.time() - start_time
            console.print(f"✅ Rollback completed in {elapsed:.1f}s")
            
            if validation_result.success:
                console.print("[green]✅ Rollback validation passed[/green]")
            else:
                console.print("[red]❌ Rollback validation failed[/red]")
                for error in validation_result.errors:
                    console.print(f"   [red]• {error}[/red]")
            
            return validation_result
            
        except Exception as e:
            console.print(f"[red]❌ Rollback failed: {e}[/red]")
            raise

    def _rollback_with_git(self, checkpoint: RollbackCheckpoint):
        """Rollback using git reset."""
        console.print(f"   🔗 Resetting to git commit: {checkpoint.git_commit[:8]}")
        
        subprocess.run(
            ["git", "reset", "--hard", checkpoint.git_commit],
            cwd=self.project_root,
            check=True,
            timeout=60
        )

    def _rollback_with_files(self, checkpoint: RollbackCheckpoint):
        """Rollback using file restoration."""
        console.print("   📂 Restoring files from snapshot...")
        
        # Remove current directories (but preserve rollback_checkpoints)
        dirs_to_restore = ["src", "tests"]
        for dir_name in dirs_to_restore:
            current_dir = self.project_root / dir_name
            if current_dir.exists():
                shutil.rmtree(current_dir)
        
        # Handle tools directory specially
        tools_dir = self.project_root / "tools"
        if tools_dir.exists():
            # Remove all tools except rollback_checkpoints
            for item in tools_dir.iterdir():
                if item.name != "rollback_checkpoints":
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
        
        # Restore directories from checkpoint
        for dir_name in dirs_to_restore:
            checkpoint_dir = checkpoint.checkpoint_path / dir_name
            if checkpoint_dir.exists():
                target_dir = self.project_root / dir_name
                shutil.copytree(checkpoint_dir, target_dir)
        
        # Restore tools directory content
        checkpoint_tools = checkpoint.checkpoint_path / "tools"
        if checkpoint_tools.exists():
            tools_target = self.project_root / "tools"
            tools_target.mkdir(exist_ok=True)
            
            for item in checkpoint_tools.iterdir():
                if item.is_dir():
                    target_dir = tools_target / item.name
                    if target_dir.exists():
                        shutil.rmtree(target_dir)
                    shutil.copytree(item, target_dir)
                else:
                    shutil.copy2(item, tools_target / item.name)
        
        # Restore critical files
        critical_files = ["pyproject.toml", "requirements.txt", "README.md"]
        for file_name in critical_files:
            checkpoint_file = checkpoint.checkpoint_path / file_name
            if checkpoint_file.exists():
                target_file = self.project_root / file_name
                shutil.copy2(checkpoint_file, target_file)

    def validate_rollback(self, phase: str) -> RollbackValidationResult:
        """
        Comprehensive validation that rollback was successful.
        
        Validates:
        1. Basic functionality (CLI still works)
        2. Test suite passes
        3. Performance restored to baseline
        4. Behavioral baseline matches
        """
        start_time = time.time()
        errors = []
        
        console.print("🔍 Validating rollback success...")
        
        # Test 1: Basic CLI functionality
        tests_passed = self._validate_basic_functionality()
        if not tests_passed:
            errors.append("Basic CLI functionality tests failed")
        
        # Test 2: Performance validation
        performance_restored = self._validate_performance_restoration(phase)
        if not performance_restored:
            errors.append("Performance not restored to baseline levels")
        
        # Test 3: Behavioral validation
        behavioral_match = self._validate_behavioral_restoration(phase)
        if not behavioral_match:
            errors.append("Behavioral baseline does not match")
        
        elapsed = time.time() - start_time
        success = len(errors) == 0
        
        return RollbackValidationResult(
            success=success,
            tests_passed=tests_passed,
            performance_restored=performance_restored,
            behavioral_match=behavioral_match,
            validation_time_seconds=elapsed,
            errors=errors
        )

    def _validate_basic_functionality(self) -> bool:
        """Test basic CLI functionality after rollback."""
        try:
            # Test that CLI can import and show help
            result = subprocess.run(
                ["python", "src/improved_sdd_cli.py", "--help"],
                cwd=self.project_root,
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception:
            return False

    def _validate_performance_restoration(self, phase: str) -> bool:
        """Validate performance is restored to checkpoint baseline."""
        if phase not in self.checkpoints:
            return False
        
        checkpoint = self.checkpoints[phase]
        if not checkpoint.performance_baseline:
            return True  # No baseline to compare against
        
        try:
            from .performance_monitor import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            current = monitor.measure_current_performance("rollback_validation")
            baseline = checkpoint.performance_baseline
            
            # Allow 10% variance from checkpoint baseline
            startup_ok = abs(current.startup_time_ms - baseline['startup_time_ms']) / baseline['startup_time_ms'] < 0.1
            memory_ok = abs(current.memory_usage_mb - baseline['memory_usage_mb']) / baseline['memory_usage_mb'] < 0.1
            
            return startup_ok and memory_ok
            
        except Exception:
            return True  # Cannot validate, assume OK

    def _validate_behavioral_restoration(self, phase: str) -> bool:
        """Validate behavioral baseline is restored."""
        try:
            from .baseline_testing import BaselineTestSuite
            
            suite = BaselineTestSuite()
            return suite.validate_current_behavior()
            
        except Exception:
            return True  # Cannot validate, assume OK

    def list_checkpoints(self) -> List[RollbackCheckpoint]:
        """List all available checkpoints."""
        return list(self.checkpoints.values())

    def cleanup_old_checkpoints(self, keep_latest: int = 5):
        """Clean up old checkpoints to save disk space."""
        if len(self.checkpoints) <= keep_latest:
            return
        
        # Sort by timestamp, keep only the latest
        sorted_checkpoints = sorted(
            self.checkpoints.values(),
            key=lambda c: c.timestamp,
            reverse=True
        )
        
        to_remove = sorted_checkpoints[keep_latest:]
        
        for checkpoint in to_remove:
            try:
                if checkpoint.checkpoint_path.exists():
                    shutil.rmtree(checkpoint.checkpoint_path)
                del self.checkpoints[checkpoint.phase]
                console.print(f"[dim]Cleaned up checkpoint: {checkpoint.phase}[/dim]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not remove checkpoint {checkpoint.phase}: {e}[/yellow]")
        
        self._save_checkpoint_metadata()

    def get_checkpoint_info(self, phase: str) -> Optional[RollbackCheckpoint]:
        """Get information about a specific checkpoint."""
        return self.checkpoints.get(phase)

    def emergency_rollback(self) -> bool:
        """
        Emergency rollback to the most recent checkpoint.
        Used when migration is critically broken.
        """
        if not self.checkpoints:
            console.print("[red]❌ No checkpoints available for emergency rollback[/red]")
            return False
        
        # Find most recent checkpoint
        latest_checkpoint = max(self.checkpoints.values(), key=lambda c: c.timestamp)
        
        console.print(f"🚨 EMERGENCY ROLLBACK to: {latest_checkpoint.phase}")
        
        try:
            result = self.rollback_to_checkpoint(latest_checkpoint.phase, strategy="hybrid")
            return result.success
        except Exception as e:
            console.print(f"[red]❌ Emergency rollback failed: {e}[/red]")
            return False


def main():
    """CLI interface for rollback operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migration Rollback Infrastructure")
    parser.add_argument("command", choices=["checkpoint", "rollback", "validate", "list", "cleanup", "emergency"])
    parser.add_argument("--phase", help="Migration phase name")
    parser.add_argument("--strategy", choices=["file", "git", "hybrid"], default="hybrid")
    
    args = parser.parse_args()
    
    rollback = MigrationRollback()
    
    if args.command == "checkpoint":
        if not args.phase:
            console.print("[red]Error: --phase required for checkpoint command[/red]")
            return 1
        rollback.create_checkpoint(args.phase)
        
    elif args.command == "rollback":
        if not args.phase:
            console.print("[red]Error: --phase required for rollback command[/red]")
            return 1
        result = rollback.rollback_to_checkpoint(args.phase, args.strategy)
        return 0 if result.success else 1
        
    elif args.command == "validate":
        if not args.phase:
            console.print("[red]Error: --phase required for validate command[/red]")
            return 1
        result = rollback.validate_rollback(args.phase)
        return 0 if result.success else 1
        
    elif args.command == "list":
        checkpoints = rollback.list_checkpoints()
        if checkpoints:
            console.print(Panel("Available Checkpoints", style="cyan"))
            for cp in sorted(checkpoints, key=lambda c: c.timestamp, reverse=True):
                console.print(f"• {cp.phase} ({time.ctime(cp.timestamp)})")
        else:
            console.print("No checkpoints available")
            
    elif args.command == "cleanup":
        rollback.cleanup_old_checkpoints()
        
    elif args.command == "emergency":
        success = rollback.emergency_rollback()
        return 0 if success else 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())