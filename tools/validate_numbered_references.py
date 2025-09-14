#!/usr/bin/env python3
"""
Template Validation Script for Numbered Spec Files

Scans all template files for old file name references and validates 
that all references use the numbered format (01_, 02_, 03_, 04_).
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Define old spec file patterns that should not exist
OLD_SPEC_PATTERNS = [
    r'\bfeasibility\.md\b',
    r'\brequirements\.md\b', 
    r'\bdesign\.md\b',
    r'\btasks\.md\b',
    r'\.specs/\{feature_name\}/feasibility\.md',
    r'\.specs/\{feature_name\}/requirements\.md',
    r'\.specs/\{feature_name\}/design\.md',
    r'\.specs/\{feature_name\}/tasks\.md'
]

# Define expected numbered patterns
NUMBERED_PATTERNS = [
    r'\b01_feasibility\.md\b',
    r'\b02_requirements\.md\b',
    r'\b03_design\.md\b', 
    r'\b04_tasks\.md\b',
    r'\.specs/\{feature_name\}/01_feasibility\.md',
    r'\.specs/\{feature_name\}/02_requirements\.md',
    r'\.specs/\{feature_name\}/03_design\.md',
    r'\.specs/\{feature_name\}/04_tasks\.md'
]

class ValidationResult:
    def __init__(self):
        self.old_references: List[Tuple[str, int, str]] = []
        self.numbered_references: List[Tuple[str, int, str]] = []
        self.total_files_scanned = 0
        self.files_with_issues = 0

def scan_file(file_path: Path) -> Tuple[List[Tuple[int, str]], List[Tuple[int, str]]]:
    """Scan a single file for old and numbered references."""
    old_refs = []
    numbered_refs = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            # Check for old patterns
            for pattern in OLD_SPEC_PATTERNS:
                if re.search(pattern, line):
                    old_refs.append((line_num, line.strip()))
            
            # Check for numbered patterns
            for pattern in NUMBERED_PATTERNS:
                if re.search(pattern, line):
                    numbered_refs.append((line_num, line.strip()))
                    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return old_refs, numbered_refs

def scan_templates(base_path: Path) -> ValidationResult:
    """Scan all template files for spec file references."""
    result = ValidationResult()
    
    # Define template directories to scan
    template_dirs = [
        'templates/chatmodes',
        'templates/prompts', 
        'templates/gitlab-flow',
        'templates/instructions'
    ]
    
    for template_dir in template_dirs:
        dir_path = base_path / template_dir
        if not dir_path.exists():
            print(f"Warning: Directory {dir_path} does not exist")
            continue
            
        # Scan all .md files in directory
        for file_path in dir_path.glob('*.md'):
            result.total_files_scanned += 1
            old_refs, numbered_refs = scan_file(file_path)
            
            if old_refs:
                result.files_with_issues += 1
                for line_num, line in old_refs:
                    result.old_references.append((str(file_path), line_num, line))
            
            for line_num, line in numbered_refs:
                result.numbered_references.append((str(file_path), line_num, line))
    
    return result

def generate_report(result: ValidationResult) -> str:
    """Generate a validation report."""
    report = []
    report.append("# Template Validation Report")
    report.append("=" * 50)
    report.append(f"Files scanned: {result.total_files_scanned}")
    report.append(f"Files with issues: {result.files_with_issues}")
    report.append(f"Total old references found: {len(result.old_references)}")
    report.append(f"Total numbered references found: {len(result.numbered_references)}")
    report.append("")
    
    if result.old_references:
        report.append("🚨 OLD REFERENCES FOUND (NEED FIXING):")
        report.append("-" * 40)
        for file_path, line_num, line in result.old_references:
            rel_path = Path(file_path).relative_to(Path.cwd())
            report.append(f"❌ {rel_path}:{line_num}")
            report.append(f"   {line}")
            report.append("")
    else:
        report.append("✅ NO OLD REFERENCES FOUND - All templates updated!")
        report.append("")
    
    if result.numbered_references:
        report.append("✅ NUMBERED REFERENCES FOUND:")
        report.append("-" * 30)
        # Group by file for cleaner output
        files_dict = {}
        for file_path, line_num, line in result.numbered_references:
            rel_path = str(Path(file_path).relative_to(Path.cwd()))
            if rel_path not in files_dict:
                files_dict[rel_path] = []
            files_dict[rel_path].append((line_num, line))
        
        for file_path, refs in files_dict.items():
            report.append(f"📄 {file_path}: {len(refs)} references")
            for line_num, line in refs[:3]:  # Show first 3 references
                report.append(f"   Line {line_num}: {line[:80]}...")
            if len(refs) > 3:
                report.append(f"   ... and {len(refs) - 3} more")
            report.append("")
    
    # Summary
    report.append("VALIDATION SUMMARY:")
    report.append("-" * 20)
    if result.old_references:
        report.append("❌ VALIDATION FAILED - Old references still exist")
        report.append(f"   Please update {len(result.old_references)} references to numbered format")
    else:
        report.append("✅ VALIDATION PASSED - All templates use numbered format")
    
    return "\n".join(report)

def main():
    """Main validation function."""
    print("🔍 Scanning template files for spec file references...")
    
    # Get project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Scan templates
    result = scan_templates(project_root)
    
    # Generate and display report
    report = generate_report(result)
    print(report)
    
    # Save report to file
    report_file = project_root / "validation_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 Full report saved to: {report_file}")
    
    # Exit with error code if issues found
    if result.old_references:
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    main()