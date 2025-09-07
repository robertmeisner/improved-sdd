#!/usr/bin/env python3
"""
Behavioral Baseline Testing Infrastructure for CLI Decomposition

This module captures complete CLI behavior snapshots to ensure migration safety.
It records outputs, error messages, exit codes, and performance metrics for
regression detection during the refactoring process.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

# Performance monitoring integration removed - baseline testing can work independently
PERFORMANCE_MONITORING_AVAILABLE = False


@dataclass
class CommandResult:
    """Capture complete command execution results."""

    command: List[str]
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    memory_peak_mb: float
    working_directory: str
    environment_snapshot: Dict[str, str]


@dataclass
class PerformanceBaseline:
    """Performance metrics baseline."""

    startup_time_ms: float
    memory_usage_mb: float
    import_time_ms: float
    command_response_time_ms: Dict[str, float]


class BaselineTestSuite:
    """Captures behavioral snapshots for migration safety."""

    def __init__(self, cli_path: Path, baseline_dir: Path = None, enable_performance_monitoring: bool = True):
        self.cli_path = cli_path.resolve()
        self.baseline_dir = baseline_dir or Path("tools/baseline_data")
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dirs: List[Path] = []

        # Initialize performance monitoring if available
        self.performance_monitor = None
        if PERFORMANCE_MONITORING_AVAILABLE and enable_performance_monitoring:
            try:
                self.performance_monitor = PerformanceMonitor(cli_path)
                self.performance_monitor.load_baseline_metrics()
                print("✅ Performance monitoring enabled")
            except Exception as e:
                print(f"Warning: Could not initialize performance monitoring: {e}")
                self.performance_monitor = None

    def create_temp_project(self) -> Path:
        """Create isolated temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp(prefix="baseline_test_"))
        self.temp_dirs.append(temp_dir)
        return temp_dir

    def cleanup_temp_dirs(self):
        """Clean up all temporary directories."""
        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
        self.temp_dirs.clear()

    def run_command(
        self, args: List[str], cwd: Path = None, input_data: str = None, timeout: int = 30
    ) -> CommandResult:
        """Execute CLI command and capture complete results."""

        # Prepare command
        cmd = [sys.executable, str(self.cli_path)] + args
        env = os.environ.copy()

        # Track memory usage
        process = None
        memory_peak = 0.0
        start_time = time.time()

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE if input_data else None,
                text=True,
                cwd=cwd,
                env=env,
            )

            # Monitor memory usage during execution (less frequent to avoid hanging)
            try:
                ps_process = psutil.Process(process.pid)
                check_count = 0
                max_checks = timeout * 10  # Maximum checks based on timeout
                while process.poll() is None and check_count < max_checks:
                    try:
                        memory_info = ps_process.memory_info()
                        memory_peak = max(memory_peak, memory_info.rss / 1024 / 1024)  # MB
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        break
                    time.sleep(0.1)  # Check every 100ms instead of 10ms
                    check_count += 1
            except Exception:
                pass  # Memory monitoring is best-effort

            stdout, stderr = process.communicate(input=input_data, timeout=timeout)
            execution_time = time.time() - start_time

            return CommandResult(
                command=args,
                exit_code=process.returncode,
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time,
                memory_peak_mb=memory_peak,
                working_directory=str(cwd or Path.cwd()),
                environment_snapshot={k: v for k, v in env.items() if k.startswith(("PYTHON", "PATH", "IMPROVED_SDD"))},
            )

        except subprocess.TimeoutExpired:
            if process:
                process.kill()
            raise Exception(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        except Exception as e:
            raise Exception(f"Failed to execute command {' '.join(cmd)}: {e}")

    def capture_help_behaviors(self) -> Dict[str, CommandResult]:
        """Capture all help-related command behaviors."""
        help_commands = [
            [],  # No args - shows banner + help tip
            ["--help"],
            ["-h"],
            ["init", "--help"],
            ["delete", "--help"],
            ["check", "--help"],
            ["--invalid-option"],  # Error case
            ["invalid-command"],  # Error case
        ]

        results = {}
        for cmd_args in help_commands:
            key = "no_args" if not cmd_args else "_".join(cmd_args)
            try:
                # Help commands should be fast - use shorter timeout
                result = self.run_command(cmd_args, timeout=10)
                results[f"help_{key}"] = result
            except Exception as e:
                print(f"Warning: Failed to capture help for {cmd_args}: {e}")

        return results

    def capture_check_command_behaviors(self) -> Dict[str, CommandResult]:
        """Capture check command behaviors."""
        results = {}

        # Basic check command - run in CI mode to avoid interactive prompts
        env = os.environ.copy()
        env["CI"] = "true"  # Set CI environment to make check non-interactive

        cmd = [sys.executable, str(self.cli_path), "check"]
        start_time = time.time()

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
            stdout, stderr = process.communicate(timeout=15)
            execution_time = time.time() - start_time

            result = CommandResult(
                command=["check"],
                exit_code=process.returncode,
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time,
                memory_peak_mb=0.0,  # Skip memory monitoring for check
                working_directory=str(Path.cwd()),
                environment_snapshot={"CI": "true"},
            )
            results["check_basic"] = result

        except subprocess.TimeoutExpired:
            print("Warning: Check command timed out - skipping baseline capture")

        return results

    def capture_init_command_behaviors(self) -> Dict[str, CommandResult]:
        """Capture init command behaviors with various scenarios."""
        results = {}

        # Test scenarios in isolated directories
        scenarios = [
            # Basic scenarios
            (["init", "--help"], "init_help"),
            (
                [
                    "init",
                    "test-project",
                    "--new-dir",
                    "--force",
                    "--offline",
                    "--app-type",
                    "python-cli",
                    "--ai-tools",
                    "github-copilot",
                ],
                "init_new_project_offline",
            ),
            (
                ["init", "--here", "--force", "--offline", "--app-type", "mcp-server", "--ai-tools", "github-copilot"],
                "init_here_offline",
            ),
            # Error scenarios
            (["init"], "init_no_args_no_here"),  # Should error - no project name, no --here
            (
                ["init", "--app-type", "invalid-type", "--force", "--offline", "--ai-tools", "github-copilot"],
                "init_invalid_app_type",
            ),
            (
                ["init", "--ai-tools", "invalid-tool", "--force", "--offline", "--app-type", "python-cli"],
                "init_invalid_ai_tool",
            ),
        ]

        for cmd_args, test_name in scenarios:
            temp_dir = self.create_temp_project()
            try:
                result = self.run_command(cmd_args, cwd=temp_dir)
                results[test_name] = result
            except Exception as e:
                print(f"Warning: Failed to capture init scenario {test_name}: {e}")

        return results

    def capture_delete_command_behaviors(self) -> Dict[str, CommandResult]:
        """Capture delete command behaviors."""
        results = {}

        # Test in clean temp directory
        temp_dir = self.create_temp_project()

        scenarios = [
            (["delete", "--help"], "delete_help"),
            (["delete", "mcp-server", "--force"], "delete_mcp_server"),
            (["delete", "python-cli", "--force"], "delete_python_cli"),
            (["delete", "invalid-type", "--force"], "delete_invalid_type"),
            (["delete"], "delete_no_args"),  # Interactive mode
        ]

        for cmd_args, test_name in scenarios:
            try:
                result = self.run_command(cmd_args, cwd=temp_dir)
                results[test_name] = result
            except Exception as e:
                print(f"Warning: Failed to capture delete scenario {test_name}: {e}")

        return results

    def measure_performance_baselines(self) -> PerformanceBaseline:
        """Establish performance baselines."""

        # Measure startup time
        startup_times = []
        for _ in range(3):
            start = time.time()
            result = self.run_command(["--help"], timeout=10)
            startup_times.append((time.time() - start) * 1000)  # Convert to ms

        avg_startup = sum(startup_times) / len(startup_times)

        # Measure import time (Python -c "import improved_sdd_cli")
        import_times = []
        for _ in range(3):
            start = time.time()
            subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"import sys; sys.path.insert(0, '{self.cli_path.parent}'); import improved_sdd_cli",
                ],
                capture_output=True,
                timeout=10,
            )
            import_times.append((time.time() - start) * 1000)

        avg_import = sum(import_times) / len(import_times)

        # Measure command response times (excluding check due to interactivity)
        command_times = {}
        commands_to_test = [
            (["--help"], "help"),
            (["init", "--help"], "init_help"),
            (["delete", "--help"], "delete_help"),
        ]

        for cmd_args, cmd_name in commands_to_test:
            times = []
            for _ in range(3):
                start = time.time()
                self.run_command(cmd_args, timeout=10)
                times.append((time.time() - start) * 1000)
            command_times[cmd_name] = sum(times) / len(times)

        # Memory usage baseline (rough estimate)
        memory_result = self.run_command(["--help"], timeout=10)

        return PerformanceBaseline(
            startup_time_ms=avg_startup,
            memory_usage_mb=memory_result.memory_peak_mb or 0.0,
            import_time_ms=avg_import,
            command_response_time_ms=command_times,
        )

    def capture_complete_baseline(self) -> Dict[str, Any]:
        """Capture complete behavioral baseline."""
        print("🔍 Capturing behavioral baseline for CLI...")

        baseline = {
            "metadata": {
                "cli_path": str(self.cli_path),
                "python_version": sys.version,
                "timestamp": time.time(),
                "baseline_version": "1.0",
            }
        }

        try:
            print("  📋 Capturing help behaviors...")
            baseline["help_behaviors"] = self.capture_help_behaviors()

            print("  🔧 Capturing check command behaviors...")
            baseline["check_behaviors"] = self.capture_check_command_behaviors()

            print("  🚀 Capturing init command behaviors...")
            baseline["init_behaviors"] = self.capture_init_command_behaviors()

            print("  🗑️  Capturing delete command behaviors...")
            baseline["delete_behaviors"] = self.capture_delete_command_behaviors()

            print("  ⚡ Measuring performance baselines...")
            baseline["performance"] = asdict(self.measure_performance_baselines())

            print("✅ Baseline capture complete!")

        finally:
            self.cleanup_temp_dirs()

        return baseline

    def create_migration_checkpoint(self, phase: str) -> Dict[str, Any]:
        """Create integrated behavioral and performance checkpoint for migration phases."""
        print(f"\n🏁 Creating migration checkpoint for phase: {phase}")

        # Capture behavioral baseline
        behavioral_data = self.capture_complete_baseline()

        # Add performance monitoring data if available
        if self.performance_monitor:
            try:
                print(f"  📊 Adding performance monitoring for phase: {phase}")
                perf_snapshot = self.performance_monitor.create_migration_checkpoint(phase)

                # Add performance snapshot to behavioral data
                behavioral_data["performance_snapshot"] = asdict(perf_snapshot)

                # Check for performance alerts
                alerts = self.performance_monitor.alerts
                if alerts:
                    behavioral_data["performance_alerts"] = [asdict(alert) for alert in alerts[-10:]]  # Last 10 alerts

            except Exception as e:
                print(f"Warning: Performance monitoring failed: {e}")

        # Save integrated checkpoint
        checkpoint_file = f"migration_checkpoint_{phase}_{int(time.time())}.json"
        self.save_baseline(behavioral_data, checkpoint_file)

        return behavioral_data

    def validate_migration_safety(self, phase: str) -> bool:
        """Comprehensive migration safety validation combining behavioral and performance checks."""
        print(f"\n🛡️  Validating migration safety for phase: {phase}")

        safety_passed = True

        # Performance validation if available
        if self.performance_monitor:
            try:
                perf_ready = self.performance_monitor.validate_migration_readiness()
                if not perf_ready:
                    print("❌ Performance validation failed")
                    safety_passed = False
                else:
                    print("✅ Performance validation passed")
            except Exception as e:
                print(f"Warning: Performance validation error: {e}")

        # Behavioral validation - compare with baseline
        try:
            current_behavioral = self.capture_complete_baseline()
            comparison = self.compare_with_baseline(current_behavioral)

            failed_tests = comparison["summary"]["failed"]
            if failed_tests > 0:
                print(f"❌ Behavioral validation failed: {failed_tests} behavioral differences detected")
                safety_passed = False
            else:
                print("✅ Behavioral validation passed")

        except Exception as e:
            print(f"❌ Behavioral validation error: {e}")
            safety_passed = False

        if safety_passed:
            print(f"✅ Migration safety validation PASSED for phase: {phase}")
        else:
            print(f"❌ Migration safety validation FAILED for phase: {phase}")
            print("   Consider reviewing changes or rolling back")

        return safety_passed

    def save_baseline(self, baseline: Dict[str, Any], filename: str = "cli_baseline.json"):
        """Save baseline to file with proper CommandResult serialization."""
        baseline_file = self.baseline_dir / filename

        # Convert CommandResult objects to dictionaries
        serializable_baseline = {}
        for key, value in baseline.items():
            if key in ["help_behaviors", "check_behaviors", "init_behaviors", "delete_behaviors"]:
                serializable_baseline[key] = {}
                for test_name, cmd_result in value.items():
                    if isinstance(cmd_result, CommandResult):
                        serializable_baseline[key][test_name] = {
                            "command": cmd_result.command,
                            "exit_code": cmd_result.exit_code,
                            "stdout": cmd_result.stdout,
                            "stderr": cmd_result.stderr,
                            "execution_time": cmd_result.execution_time,
                            "memory_peak_mb": cmd_result.memory_peak_mb,
                            "working_directory": cmd_result.working_directory,
                            "environment_snapshot": cmd_result.environment_snapshot,
                        }
                    else:
                        serializable_baseline[key][test_name] = cmd_result
            else:
                serializable_baseline[key] = value

        with open(baseline_file, "w") as f:
            json.dump(serializable_baseline, f, indent=2)

        print(f"💾 Baseline saved to: {baseline_file}")
        return baseline_file

    def load_baseline(self, filename: str = "cli_baseline.json") -> Dict[str, Any]:
        """Load baseline from file."""
        baseline_file = self.baseline_dir / filename

        if not baseline_file.exists():
            raise FileNotFoundError(f"Baseline file not found: {baseline_file}")

        with open(baseline_file, "r") as f:
            return json.load(f)

    def compare_with_baseline(
        self, current_results: Dict[str, Any], baseline_file: str = "cli_baseline.json"
    ) -> Dict[str, Any]:
        """Compare current results with saved baseline."""
        baseline = self.load_baseline(baseline_file)

        comparison = {
            "summary": {"total_tests": 0, "passed": 0, "failed": 0, "performance_degraded": 0},
            "behavior_differences": [],
            "performance_changes": {},
        }

        # Compare behavioral results
        for category in ["help_behaviors", "check_behaviors", "init_behaviors", "delete_behaviors"]:
            if category in baseline and category in current_results:
                baseline_behaviors = baseline[category]
                current_behaviors = current_results[category]

                for test_name in baseline_behaviors:
                    comparison["summary"]["total_tests"] += 1

                    if test_name not in current_behaviors:
                        comparison["behavior_differences"].append(
                            {
                                "test": test_name,
                                "issue": "Missing in current results",
                                "baseline": baseline_behaviors[test_name],
                                "current": None,
                            }
                        )
                        comparison["summary"]["failed"] += 1
                        continue

                    baseline_result = baseline_behaviors[test_name]
                    current_result = current_behaviors[test_name]

                    # Convert current result to dict if it's a CommandResult object
                    if isinstance(current_result, CommandResult):
                        current_result_dict = {
                            "command": current_result.command,
                            "exit_code": current_result.exit_code,
                            "stdout": current_result.stdout,
                            "stderr": current_result.stderr,
                            "execution_time": current_result.execution_time,
                            "memory_peak_mb": current_result.memory_peak_mb,
                            "working_directory": current_result.working_directory,
                            "environment_snapshot": current_result.environment_snapshot,
                        }
                    else:
                        current_result_dict = current_result

                    # Compare key aspects
                    differences = []
                    if baseline_result["exit_code"] != current_result_dict["exit_code"]:
                        differences.append(
                            f"exit_code: {baseline_result['exit_code']} → {current_result_dict['exit_code']}"
                        )

                    if baseline_result["stdout"] != current_result_dict["stdout"]:
                        differences.append("stdout differs")

                    if baseline_result["stderr"] != current_result_dict["stderr"]:
                        differences.append("stderr differs")

                    if differences:
                        comparison["behavior_differences"].append(
                            {
                                "test": test_name,
                                "issue": "; ".join(differences),
                                "baseline": baseline_result,
                                "current": current_result_dict,
                            }
                        )
                        comparison["summary"]["failed"] += 1
                    else:
                        comparison["summary"]["passed"] += 1

        # Compare performance
        if "performance" in baseline and "performance" in current_results:
            baseline_perf = baseline["performance"]
            current_perf = current_results["performance"]

            perf_changes = {}

            # Startup time change
            startup_change = (
                (current_perf["startup_time_ms"] - baseline_perf["startup_time_ms"])
                / baseline_perf["startup_time_ms"]
                * 100
            )
            if abs(startup_change) > 10:  # More than 10% change
                perf_changes["startup_time"] = {
                    "baseline_ms": baseline_perf["startup_time_ms"],
                    "current_ms": current_perf["startup_time_ms"],
                    "change_percent": startup_change,
                }
                if startup_change > 10:
                    comparison["summary"]["performance_degraded"] += 1

            # Memory usage change
            if baseline_perf["memory_usage_mb"] > 0:
                memory_change = (
                    (current_perf["memory_usage_mb"] - baseline_perf["memory_usage_mb"])
                    / baseline_perf["memory_usage_mb"]
                    * 100
                )
                if abs(memory_change) > 15:  # More than 15% change
                    perf_changes["memory_usage"] = {
                        "baseline_mb": baseline_perf["memory_usage_mb"],
                        "current_mb": current_perf["memory_usage_mb"],
                        "change_percent": memory_change,
                    }
                    if memory_change > 15:
                        comparison["summary"]["performance_degraded"] += 1

            comparison["performance_changes"] = perf_changes

        return comparison

    def print_comparison_report(self, comparison: Dict[str, Any]):
        """Print human-readable comparison report."""
        summary = comparison["summary"]

        print(f"\n📊 Baseline Comparison Report")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   ✅ Passed: {summary['passed']}")
        print(f"   ❌ Failed: {summary['failed']}")
        print(f"   ⚠️  Performance Issues: {summary['performance_degraded']}")

        if comparison["behavior_differences"]:
            print(f"\n🔍 Behavioral Differences:")
            for diff in comparison["behavior_differences"][:5]:  # Show first 5
                print(f"   • {diff['test']}: {diff['issue']}")
            if len(comparison["behavior_differences"]) > 5:
                print(f"   ... and {len(comparison['behavior_differences']) - 5} more")

        if comparison["performance_changes"]:
            print(f"\n⚡ Performance Changes:")
            for metric, change in comparison["performance_changes"].items():
                direction = "📈" if change["change_percent"] > 0 else "📉"
                print(f"   {direction} {metric}: {change['change_percent']:.1f}% change")

        if summary["failed"] == 0 and summary["performance_degraded"] == 0:
            print(f"\n🎉 All tests passed! No behavioral regressions detected.")
        else:
            print(
                f"\n⚠️  Found {summary['failed']} behavioral differences and {summary['performance_degraded']} performance issues."
            )


def main():
    """Main execution for baseline testing."""
    import argparse

    parser = argparse.ArgumentParser(description="CLI Behavioral Baseline Testing")
    parser.add_argument("--cli-path", type=Path, default="src/improved_sdd_cli.py", help="Path to CLI script")
    parser.add_argument("--capture", action="store_true", help="Capture new baseline")
    parser.add_argument("--compare", action="store_true", help="Compare with existing baseline")
    parser.add_argument("--checkpoint", help="Create migration checkpoint for specified phase")
    parser.add_argument("--validate", help="Validate migration safety for specified phase")
    parser.add_argument("--baseline-file", default="cli_baseline.json", help="Baseline file name")
    parser.add_argument("--no-performance", action="store_true", help="Disable performance monitoring")

    args = parser.parse_args()

    suite = BaselineTestSuite(args.cli_path, enable_performance_monitoring=not args.no_performance)

    if args.capture:
        baseline = suite.capture_complete_baseline()
        suite.save_baseline(baseline, args.baseline_file)

    elif args.compare:
        current_results = suite.capture_complete_baseline()
        comparison = suite.compare_with_baseline(current_results, args.baseline_file)
        suite.print_comparison_report(comparison)

        # Exit with error code if regressions found
        if comparison["summary"]["failed"] > 0:
            sys.exit(1)

    elif args.checkpoint:
        checkpoint_data = suite.create_migration_checkpoint(args.checkpoint)
        print(f"✅ Migration checkpoint created for phase: {args.checkpoint}")

    elif args.validate:
        is_safe = suite.validate_migration_safety(args.validate)
        if not is_safe:
            sys.exit(1)

    else:
        print("Specify --capture, --compare, --checkpoint <phase>, or --validate <phase>")
        sys.exit(1)


if __name__ == "__main__":
    main()
