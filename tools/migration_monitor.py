#!/usr/bin/env python3
"""
Migration Monitoring Script for CLI Decomposition

This script provides easy-to-use commands for monitoring the CLI decomposition
process with integrated performance and behavioral monitoring.
"""

import sys
import subprocess
from pathlib import Path
import argparse


def run_checkpoint(phase: str):
    """Create a migration checkpoint with full monitoring."""
    print(f"🏁 Creating migration checkpoint for: {phase}")
    
    cmd = [sys.executable, "tools/baseline_testing.py", "--checkpoint", phase]
    result = subprocess.run(cmd, cwd=Path.cwd())
    
    if result.returncode == 0:
        print(f"✅ Checkpoint created successfully for phase: {phase}")
    else:
        print(f"❌ Checkpoint creation failed for phase: {phase}")
        
    return result.returncode


def validate_safety(phase: str):
    """Validate migration safety before proceeding with changes."""
    print(f"🛡️  Validating migration safety for: {phase}")
    
    cmd = [sys.executable, "tools/baseline_testing.py", "--validate", phase]
    result = subprocess.run(cmd, cwd=Path.cwd())
    
    if result.returncode == 0:
        print(f"✅ Migration safety validated for phase: {phase}")
        print("   Safe to proceed with migration")
    else:
        print(f"❌ Migration safety validation failed for phase: {phase}")
        print("   Consider reviewing changes or rolling back")
        
    return result.returncode


def check_performance(phase: str):
    """Check performance for a specific phase."""
    print(f"📊 Checking performance for: {phase}")
    
    cmd = [sys.executable, "tools/performance_monitor.py", "--checkpoint", phase]
    result = subprocess.run(cmd, cwd=Path.cwd())
    
    return result.returncode


def validate_readiness():
    """Validate system readiness for migration."""
    print("🔍 Validating migration readiness...")
    
    cmd = [sys.executable, "tools/performance_monitor.py", "--validate"]
    result = subprocess.run(cmd, cwd=Path.cwd())
    
    if result.returncode == 0:
        print("✅ System ready for migration")
    else:
        print("❌ System not ready for migration")
        
    return result.returncode


def show_trend(metric: str):
    """Show performance trend for a metric."""
    print(f"📈 Showing trend for: {metric}")
    
    cmd = [sys.executable, "tools/performance_monitor.py", "--trend", metric]
    result = subprocess.run(cmd, cwd=Path.cwd())
    
    return result.returncode


def main():
    """Main CLI for migration monitoring."""
    parser = argparse.ArgumentParser(
        description="Migration Monitoring for CLI Decomposition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate system is ready for migration
  python tools/migration_monitor.py validate-readiness
  
  # Create checkpoint before starting module extraction
  python tools/migration_monitor.py checkpoint "core_extraction_start"
  
  # Validate safety after extracting a module
  python tools/migration_monitor.py validate "core_extraction_complete"
  
  # Check performance for specific phase
  python tools/migration_monitor.py performance "service_layer_extraction"
  
  # Show performance trend
  python tools/migration_monitor.py trend startup_time_ms
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Checkpoint command
    checkpoint_parser = subparsers.add_parser("checkpoint", help="Create migration checkpoint")
    checkpoint_parser.add_argument("phase", help="Migration phase name")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate migration safety")
    validate_parser.add_argument("phase", help="Migration phase name")
    
    # Performance command
    perf_parser = subparsers.add_parser("performance", help="Check performance")
    perf_parser.add_argument("phase", help="Migration phase name")
    
    # Validate readiness command
    subparsers.add_parser("validate-readiness", help="Validate system readiness for migration")
    
    # Trend command
    trend_parser = subparsers.add_parser("trend", help="Show performance trend")
    trend_parser.add_argument("metric", choices=["startup_time_ms", "memory_usage_mb", "import_time_ms"],
                             help="Metric to show trend for")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute commands
    if args.command == "checkpoint":
        return run_checkpoint(args.phase)
    elif args.command == "validate":
        return validate_safety(args.phase)
    elif args.command == "performance":
        return check_performance(args.phase)
    elif args.command == "validate-readiness":
        return validate_readiness()
    elif args.command == "trend":
        return show_trend(args.metric)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())