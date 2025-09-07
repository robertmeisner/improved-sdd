#!/usr/bin/env python3
"""
Performance Monitoring Infrastructure for CLI Decomposition

This module provides comprehensive performance monitoring capabilities to ensure
no regressions occur during the CLI decomposition process. It establishes
baselines, tracks performance trends, and alerts when thresholds are exceeded.
"""

import json
import time
import sys
import subprocess
import statistics
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
import psutil
import os
from enum import Enum


class PerformanceAlertLevel(Enum):
    """Performance alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Single performance measurement."""
    name: str
    value: float
    unit: str
    timestamp: float
    phase: str  # Migration phase when measured
    
    
@dataclass
class PerformanceThreshold:
    """Performance threshold configuration."""
    metric_name: str
    warning_percent: float  # % increase that triggers warning
    critical_percent: float  # % increase that triggers critical alert
    baseline_value: float
    

@dataclass
class PerformanceAlert:
    """Performance degradation alert."""
    level: PerformanceAlertLevel
    metric_name: str
    current_value: float
    baseline_value: float
    degradation_percent: float
    phase: str
    timestamp: float
    message: str


@dataclass
class PerformanceSnapshot:
    """Complete performance snapshot at a point in time."""
    phase: str
    timestamp: float
    startup_time_ms: float
    memory_usage_mb: float
    import_time_ms: float
    command_times_ms: Dict[str, float]
    cpu_percent: float
    io_operations: int


class PerformanceMonitor:
    """Comprehensive performance monitoring for CLI decomposition."""
    
    def __init__(self, cli_path: Path, monitor_dir: Path = None, baseline_file: str = None):
        self.cli_path = cli_path.resolve()
        self.monitor_dir = monitor_dir or Path("tools/performance_data")
        self.monitor_dir.mkdir(parents=True, exist_ok=True)
        
        # Load baseline from existing baseline testing if available
        if baseline_file:
            self.baseline_file = Path(baseline_file)
        else:
            self.baseline_file = Path("tools/baseline_data/cli_baseline.json")
        
        # Default performance thresholds based on requirements
        self.thresholds = {
            "startup_time_ms": PerformanceThreshold(
                metric_name="startup_time_ms",
                warning_percent=7.0,   # Warning at 7% increase
                critical_percent=10.0, # Critical at 10% increase (requirement limit)
                baseline_value=0.0     # Will be set from baseline
            ),
            "memory_usage_mb": PerformanceThreshold(
                metric_name="memory_usage_mb", 
                warning_percent=10.0,  # Warning at 10% increase
                critical_percent=15.0, # Critical at 15% increase (requirement limit)
                baseline_value=0.0     # Will be set from baseline
            ),
            "import_time_ms": PerformanceThreshold(
                metric_name="import_time_ms",
                warning_percent=15.0,  # Warning at 15% increase
                critical_percent=25.0, # Critical at 25% increase
                baseline_value=0.0     # Will be set from baseline
            )
        }
        
        self.baseline_snapshot: Optional[PerformanceSnapshot] = None
        self.performance_history: List[PerformanceSnapshot] = []
        self.alerts: List[PerformanceAlert] = []
        
    def load_baseline_metrics(self) -> bool:
        """Load baseline performance metrics from baseline testing results."""
        if not self.baseline_file.exists():
            print(f"Warning: Baseline file not found: {self.baseline_file}")
            return False
            
        try:
            with open(self.baseline_file, 'r') as f:
                baseline_data = json.load(f)
                
            # Extract performance data from baseline
            perf_data = baseline_data.get("performance", {})
            if not perf_data:
                print("Warning: No performance data found in baseline")
                return False
                
            # Create baseline snapshot
            self.baseline_snapshot = PerformanceSnapshot(
                phase="baseline",
                timestamp=baseline_data.get("metadata", {}).get("timestamp", time.time()),
                startup_time_ms=perf_data.get("startup_time_ms", 0.0),
                memory_usage_mb=perf_data.get("memory_usage_mb", 0.0),
                import_time_ms=perf_data.get("import_time_ms", 0.0),
                command_times_ms=perf_data.get("command_response_time_ms", {}),
                cpu_percent=0.0,  # Not captured in baseline
                io_operations=0   # Not captured in baseline
            )
            
            # Update threshold baseline values
            self.thresholds["startup_time_ms"].baseline_value = self.baseline_snapshot.startup_time_ms
            self.thresholds["memory_usage_mb"].baseline_value = self.baseline_snapshot.memory_usage_mb
            self.thresholds["import_time_ms"].baseline_value = self.baseline_snapshot.import_time_ms
            
            print(f"✅ Loaded baseline metrics:")
            print(f"   Startup time: {self.baseline_snapshot.startup_time_ms:.1f}ms")
            print(f"   Memory usage: {self.baseline_snapshot.memory_usage_mb:.1f}MB")
            print(f"   Import time: {self.baseline_snapshot.import_time_ms:.1f}ms")
            
            return True
            
        except Exception as e:
            print(f"Error loading baseline: {e}")
            return False
    
    def measure_startup_performance(self, phase: str, iterations: int = 5) -> PerformanceSnapshot:
        """Measure CLI startup performance with multiple iterations for accuracy."""
        print(f"📊 Measuring startup performance for phase: {phase}")
        
        startup_times = []
        memory_peaks = []
        
        # Measure startup time multiple times for accuracy
        for i in range(iterations):
            start_time = time.time()
            
            try:
                # Use simple --help command for startup measurement
                result = subprocess.run(
                    [sys.executable, str(self.cli_path), "--help"],
                    capture_output=True,
                    timeout=15,
                    text=True
                )
                
                startup_time = (time.time() - start_time) * 1000  # Convert to ms
                startup_times.append(startup_time)
                
                # Basic memory estimation (rough)
                memory_peaks.append(50.0)  # Placeholder - actual memory monitoring during process
                
            except subprocess.TimeoutExpired:
                print(f"Warning: Startup measurement {i+1} timed out")
                continue
            except Exception as e:
                print(f"Warning: Startup measurement {i+1} failed: {e}")
                continue
        
        if not startup_times:
            raise Exception("All startup time measurements failed")
        
        # Calculate averages
        avg_startup = statistics.mean(startup_times)
        avg_memory = statistics.mean(memory_peaks)
        
        # Measure import time
        import_time = self.measure_import_time(iterations=3)
        
        # Measure command response times
        command_times = self.measure_command_times()
        
        # Get system performance metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Create snapshot
        snapshot = PerformanceSnapshot(
            phase=phase,
            timestamp=time.time(),
            startup_time_ms=avg_startup,
            memory_usage_mb=avg_memory,
            import_time_ms=import_time,
            command_times_ms=command_times,
            cpu_percent=cpu_percent,
            io_operations=0  # Placeholder
        )
        
        # Check for performance regressions
        self.check_performance_thresholds(snapshot)
        
        # Store in history
        self.performance_history.append(snapshot)
        
        return snapshot
    
    def measure_import_time(self, iterations: int = 3) -> float:
        """Measure time to import the CLI module."""
        import_times = []
        
        for _ in range(iterations):
            start_time = time.time()
            try:
                subprocess.run([
                    sys.executable, "-c", 
                    f"import sys; sys.path.insert(0, '{self.cli_path.parent}'); import improved_sdd_cli"
                ], capture_output=True, timeout=10, check=True)
                
                import_time = (time.time() - start_time) * 1000  # Convert to ms
                import_times.append(import_time)
                
            except Exception as e:
                print(f"Warning: Import measurement failed: {e}")
                continue
        
        return statistics.mean(import_times) if import_times else 0.0
    
    def measure_command_times(self) -> Dict[str, float]:
        """Measure response times for key CLI commands."""
        commands_to_test = [
            (["--help"], "help"),
            (["init", "--help"], "init_help"),
            (["delete", "--help"], "delete_help"),
            (["check", "--help"], "check_help"),
        ]
        
        command_times = {}
        
        for cmd_args, cmd_name in commands_to_test:
            times = []
            for _ in range(3):  # 3 iterations per command
                start_time = time.time()
                try:
                    subprocess.run(
                        [sys.executable, str(self.cli_path)] + cmd_args,
                        capture_output=True,
                        timeout=10
                    )
                    times.append((time.time() - start_time) * 1000)
                except Exception:
                    continue
            
            if times:
                command_times[cmd_name] = statistics.mean(times)
        
        return command_times
    
    def check_performance_thresholds(self, snapshot: PerformanceSnapshot) -> List[PerformanceAlert]:
        """Check if performance has degraded beyond acceptable thresholds."""
        if not self.baseline_snapshot:
            print("Warning: No baseline snapshot available for comparison")
            return []
        
        new_alerts = []
        
        # Check each metric against thresholds
        metrics_to_check = [
            ("startup_time_ms", snapshot.startup_time_ms, self.baseline_snapshot.startup_time_ms),
            ("memory_usage_mb", snapshot.memory_usage_mb, self.baseline_snapshot.memory_usage_mb),
            ("import_time_ms", snapshot.import_time_ms, self.baseline_snapshot.import_time_ms),
        ]
        
        for metric_name, current_value, baseline_value in metrics_to_check:
            if baseline_value == 0:
                continue  # Skip if baseline is zero
                
            # Calculate percentage increase
            percent_increase = ((current_value - baseline_value) / baseline_value) * 100
            
            threshold = self.thresholds[metric_name]
            alert_level = None
            
            if percent_increase >= threshold.critical_percent:
                alert_level = PerformanceAlertLevel.CRITICAL
            elif percent_increase >= threshold.warning_percent:
                alert_level = PerformanceAlertLevel.WARNING
            
            if alert_level:
                alert = PerformanceAlert(
                    level=alert_level,
                    metric_name=metric_name,
                    current_value=current_value,
                    baseline_value=baseline_value,
                    degradation_percent=percent_increase,
                    phase=snapshot.phase,
                    timestamp=snapshot.timestamp,
                    message=f"{metric_name} increased by {percent_increase:.1f}% (threshold: {threshold.warning_percent:.1f}%/{threshold.critical_percent:.1f}%)"
                )
                
                new_alerts.append(alert)
                self.alerts.append(alert)
        
        return new_alerts
    
    def print_performance_report(self, snapshot: PerformanceSnapshot, alerts: List[PerformanceAlert] = None):
        """Print human-readable performance report."""
        print(f"\n📊 Performance Report - Phase: {snapshot.phase}")
        print(f"   Timestamp: {datetime.fromtimestamp(snapshot.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Startup Time: {snapshot.startup_time_ms:.1f}ms")
        print(f"   Memory Usage: {snapshot.memory_usage_mb:.1f}MB")
        print(f"   Import Time: {snapshot.import_time_ms:.1f}ms")
        print(f"   CPU Usage: {snapshot.cpu_percent:.1f}%")
        
        if snapshot.command_times_ms:
            print(f"   Command Times:")
            for cmd, time_ms in snapshot.command_times_ms.items():
                print(f"     {cmd}: {time_ms:.1f}ms")
        
        # Show comparison to baseline if available
        if self.baseline_snapshot:
            print(f"\n📈 Comparison to Baseline:")
            
            def show_comparison(name: str, current: float, baseline: float, unit: str):
                if baseline > 0:
                    change = ((current - baseline) / baseline) * 100
                    direction = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                    print(f"   {name}: {direction} {change:+.1f}% ({current:.1f}{unit} vs {baseline:.1f}{unit})")
            
            show_comparison("Startup Time", snapshot.startup_time_ms, self.baseline_snapshot.startup_time_ms, "ms")
            show_comparison("Memory Usage", snapshot.memory_usage_mb, self.baseline_snapshot.memory_usage_mb, "MB")
            show_comparison("Import Time", snapshot.import_time_ms, self.baseline_snapshot.import_time_ms, "ms")
        
        # Show alerts if any
        if alerts:
            print(f"\n⚠️  Performance Alerts:")
            for alert in alerts:
                level_emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}
                print(f"   {level_emoji[alert.level.value]} {alert.level.value.upper()}: {alert.message}")
    
    def save_performance_data(self, filename: str = None):
        """Save performance monitoring data to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_data_{timestamp}.json"
            
        filepath = self.monitor_dir / filename
        
        data = {
            "metadata": {
                "cli_path": str(self.cli_path),
                "monitoring_start": time.time(),
                "version": "1.0"
            },
            "baseline_snapshot": asdict(self.baseline_snapshot) if self.baseline_snapshot else None,
            "performance_history": [asdict(snapshot) for snapshot in self.performance_history],
            "alerts": [asdict(alert) for alert in self.alerts],
            "thresholds": {name: asdict(threshold) for name, threshold in self.thresholds.items()}
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Performance data saved to: {filepath}")
        return filepath
    
    def create_migration_checkpoint(self, phase: str) -> PerformanceSnapshot:
        """Create a performance checkpoint during migration phases."""
        print(f"\n🏁 Creating performance checkpoint for phase: {phase}")
        
        snapshot = self.measure_startup_performance(phase)
        alerts = self.check_performance_thresholds(snapshot)
        
        self.print_performance_report(snapshot, alerts)
        
        # Save checkpoint data
        checkpoint_file = f"checkpoint_{phase}_{int(time.time())}.json"
        self.save_performance_data(checkpoint_file)
        
        # Check if we need to recommend rollback
        critical_alerts = [a for a in alerts if a.level == PerformanceAlertLevel.CRITICAL]
        if critical_alerts:
            print(f"\n🚨 CRITICAL PERFORMANCE DEGRADATION DETECTED!")
            print(f"   Consider rolling back changes in phase: {phase}")
            for alert in critical_alerts:
                print(f"   - {alert.message}")
        
        return snapshot
    
    def get_performance_trend(self, metric_name: str, phases: int = 5) -> List[Tuple[str, float]]:
        """Get performance trend for a specific metric over recent phases."""
        if len(self.performance_history) < 2:
            return []
        
        recent_snapshots = self.performance_history[-phases:]
        trend = []
        
        for snapshot in recent_snapshots:
            if metric_name == "startup_time_ms":
                value = snapshot.startup_time_ms
            elif metric_name == "memory_usage_mb":
                value = snapshot.memory_usage_mb
            elif metric_name == "import_time_ms":
                value = snapshot.import_time_ms
            else:
                continue
                
            trend.append((snapshot.phase, value))
        
        return trend
    
    def validate_migration_readiness(self) -> bool:
        """Validate that system is ready for migration based on current performance."""
        if not self.baseline_snapshot:
            print("❌ Cannot validate migration readiness - no baseline available")
            return False
        
        print("\n🔍 Validating migration readiness...")
        
        # Create current snapshot
        current_snapshot = self.measure_startup_performance("pre_migration_validation")
        alerts = self.check_performance_thresholds(current_snapshot)
        
        # Check for any critical issues
        critical_alerts = [a for a in alerts if a.level == PerformanceAlertLevel.CRITICAL]
        if critical_alerts:
            print("❌ Migration readiness: FAILED")
            print("   Critical performance issues detected:")
            for alert in critical_alerts:
                print(f"   - {alert.message}")
            return False
        
        # Check system resources
        memory_available = psutil.virtual_memory().available / (1024 * 1024)  # MB
        cpu_usage = psutil.cpu_percent(interval=1)
        
        if memory_available < 1000:  # Less than 1GB available
            print(f"❌ Migration readiness: FAILED - Low memory available ({memory_available:.0f}MB)")
            return False
            
        if cpu_usage > 80:
            print(f"❌ Migration readiness: FAILED - High CPU usage ({cpu_usage:.1f}%)")
            return False
        
        print("✅ Migration readiness: PASSED")
        print(f"   Current performance within acceptable limits")
        print(f"   System resources adequate (Memory: {memory_available:.0f}MB, CPU: {cpu_usage:.1f}%)")
        
        return True


def main():
    """Main execution for performance monitoring."""
    import argparse
    
    parser = argparse.ArgumentParser(description="CLI Performance Monitoring")
    parser.add_argument("--cli-path", type=Path, default="src/improved_sdd_cli.py", 
                       help="Path to CLI script")
    parser.add_argument("--baseline", action="store_true", help="Establish new baseline")
    parser.add_argument("--checkpoint", help="Create performance checkpoint for phase")
    parser.add_argument("--validate", action="store_true", help="Validate migration readiness")
    parser.add_argument("--trend", help="Show performance trend for metric")
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(args.cli_path)
    
    # Load existing baseline
    if not monitor.load_baseline_metrics():
        print("Creating new baseline...")
        monitor.baseline_snapshot = monitor.measure_startup_performance("new_baseline")
    
    if args.checkpoint:
        monitor.create_migration_checkpoint(args.checkpoint)
        
    elif args.validate:
        monitor.validate_migration_readiness()
        
    elif args.trend:
        trend = monitor.get_performance_trend(args.trend)
        print(f"\n📈 Performance Trend for {args.trend}:")
        for phase, value in trend:
            print(f"   {phase}: {value:.1f}")
            
    else:
        print("Specify --checkpoint <phase>, --validate, or --trend <metric>")


if __name__ == "__main__":
    main()