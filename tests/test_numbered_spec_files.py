#!/usr/bin/env python3
"""
Comprehensive Test Suite for Numbered Spec Files

Tests the numbered spec file workflows to ensure:
1. Chatmode workflows reference numbered files correctly
2. Prompt templates work with numbered file structure  
3. GitLab Flow integration uses numbered references
4. All template references are consistent
"""

import unittest
import re
from pathlib import Path
from typing import List, Dict

class NumberedSpecFilesTestSuite(unittest.TestCase):
    """Test suite for numbered spec files implementation."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.project_root = Path(__file__).parent.parent
        cls.templates_dir = cls.project_root / "templates"
        
    def read_template_file(self, relative_path: str) -> str:
        """Read a template file and return its content."""
        file_path = self.templates_dir / relative_path
        self.assertTrue(file_path.exists(), f"Template file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def test_chatmode_sdd_spec_driven_references(self):
        """Test that sddSpecDriven.chatmode.md uses numbered file references."""
        content = self.read_template_file("chatmodes/sddSpecDriven.chatmode.md")
        
        # Verify numbered references exist
        self.assertIn("01_feasibility.md", content, "Missing 01_feasibility.md reference")
        self.assertIn("02_requirements.md", content, "Missing 02_requirements.md reference") 
        self.assertIn("03_design.md", content, "Missing 03_design.md reference")
        self.assertIn("04_tasks.md", content, "Missing 04_tasks.md reference")
        
        # Verify old references don't exist
        self.assertNotRegex(content, r'\bfeasibility\.md\b', "Found old feasibility.md reference")
        self.assertNotRegex(content, r'\brequirements\.md\b', "Found old requirements.md reference")
        self.assertNotRegex(content, r'\bdesign\.md\b', "Found old design.md reference") 
        self.assertNotRegex(content, r'\btasks\.md\b', "Found old tasks.md reference")
        
        # Verify file path references use numbered format
        file_path_pattern = r'\.specs/\{feature_name\}/(01_feasibility|02_requirements|03_design|04_tasks)\.md'
        matches = re.findall(file_path_pattern, content)
        self.assertGreater(len(matches), 0, "No numbered file path references found")
        
    def test_chatmode_sdd_spec_driven_simple_references(self):
        """Test that sddSpecDrivenSimple.chatmode.md uses numbered file references."""
        content = self.read_template_file("chatmodes/sddSpecDrivenSimple.chatmode.md")
        
        # Verify numbered references exist
        self.assertIn("01_feasibility.md", content, "Missing 01_feasibility.md reference")
        self.assertIn("02_requirements.md", content, "Missing 02_requirements.md reference")
        self.assertIn("03_design.md", content, "Missing 03_design.md reference") 
        self.assertIn("04_tasks.md", content, "Missing 04_tasks.md reference")
        
        # Verify old references don't exist
        self.assertNotRegex(content, r'\bfeasibility\.md\b', "Found old feasibility.md reference")
        self.assertNotRegex(content, r'\brequirements\.md\b', "Found old requirements.md reference")
        self.assertNotRegex(content, r'\bdesign\.md\b', "Found old design.md reference")
        self.assertNotRegex(content, r'\btasks\.md\b', "Found old tasks.md reference")
        
    def test_chatmode_sdd_testing_references(self):
        """Test that sddTesting.chatmode.md has correct chatmode references."""
        content = self.read_template_file("chatmodes/sddTesting.chatmode.md")
        
        # Verify correct chatmode reference (should reference sddSpecDriven.chatmode.md)
        self.assertIn("sddSpecDriven.chatmode.md", content, "Missing sddSpecDriven.chatmode.md reference")
        self.assertNotIn("specMode.chatmode.md", content, "Found incorrect specMode.chatmode.md reference")
        
    def test_prompt_sdd_spec_sync_references(self):
        """Test that sddSpecSync.prompt.md uses numbered file references."""
        content = self.read_template_file("prompts/sddSpecSync.prompt.md")
        
        # Verify numbered references exist
        self.assertIn("01_feasibility.md", content, "Missing 01_feasibility.md reference")
        self.assertIn("02_requirements.md", content, "Missing 02_requirements.md reference")
        self.assertIn("03_design.md", content, "Missing 03_design.md reference")
        self.assertIn("04_tasks.md", content, "Missing 04_tasks.md reference")
        
        # Verify old references don't exist
        self.assertNotRegex(content, r'\bfeasibility\.md\b', "Found old feasibility.md reference") 
        self.assertNotRegex(content, r'\brequirements\.md\b', "Found old requirements.md reference")
        self.assertNotRegex(content, r'\bdesign\.md\b', "Found old design.md reference")
        self.assertNotRegex(content, r'\btasks\.md\b', "Found old tasks.md reference")
        
    def test_prompt_sdd_task_execution_references(self):
        """Test that sddTaskExecution.prompt.md uses numbered file references."""
        content = self.read_template_file("prompts/sddTaskExecution.prompt.md")
        
        # Verify numbered references exist
        self.assertIn("02_requirements.md", content, "Missing 02_requirements.md reference")
        self.assertIn("03_design.md", content, "Missing 03_design.md reference")
        
        # Verify old references don't exist
        self.assertNotRegex(content, r'\brequirements\.md\b', "Found old requirements.md reference")
        self.assertNotRegex(content, r'\bdesign\.md\b', "Found old design.md reference")
        
    def test_gitlab_flow_workflow_references(self):
        """Test that gitlab-flow-workflow.md uses numbered file references."""
        content = self.read_template_file("gitlab-flow/gitlab-flow-workflow.md")
        
        # Verify numbered references exist
        self.assertIn("01_feasibility.md", content, "Missing 01_feasibility.md reference")
        self.assertIn("02_requirements.md", content, "Missing 02_requirements.md reference")
        self.assertIn("03_design.md", content, "Missing 03_design.md reference")
        self.assertIn("04_tasks.md", content, "Missing 04_tasks.md reference")
        
        # Verify old references don't exist
        self.assertNotRegex(content, r'\bfeasibility\.md\b', "Found old feasibility.md reference")
        self.assertNotRegex(content, r'\brequirements\.md\b', "Found old requirements.md reference") 
        self.assertNotRegex(content, r'\bdesign\.md\b', "Found old design.md reference")
        self.assertNotRegex(content, r'\btasks\.md\b', "Found old tasks.md reference")
        
    def test_gitlab_flow_pr_references(self):
        """Test that gitlab-flow-pr.md uses numbered file references."""
        content = self.read_template_file("gitlab-flow/gitlab-flow-pr.md")
        
        # Verify numbered references exist  
        self.assertIn("04_tasks.md", content, "Missing 04_tasks.md reference")
        
        # Verify old references don't exist
        self.assertNotRegex(content, r'\btasks\.md\b', "Found old tasks.md reference")
        
    def test_file_naming_consistency(self):
        """Test that numbered file naming is consistent across all templates."""
        expected_patterns = [
            "01_feasibility.md",
            "02_requirements.md", 
            "03_design.md",
            "04_tasks.md"
        ]
        
        template_files = [
            "chatmodes/sddSpecDriven.chatmode.md",
            "chatmodes/sddSpecDrivenSimple.chatmode.md",
            "prompts/sddSpecSync.prompt.md",
            "prompts/sddTaskExecution.prompt.md",
            "gitlab-flow/gitlab-flow-workflow.md",
            "gitlab-flow/gitlab-flow-pr.md"
        ]
        
        for template_file in template_files:
            content = self.read_template_file(template_file)
            
            # Check that if any numbered references exist, they follow the correct pattern
            numbered_refs = re.findall(r'\b\d{2}_\w+\.md\b', content)
            for ref in numbered_refs:
                self.assertIn(ref, expected_patterns, 
                    f"Unexpected numbered file reference '{ref}' in {template_file}")
                    
    def test_file_path_references_consistency(self):
        """Test that file path references use numbered format consistently."""
        file_path_pattern = r'\.specs/\{feature_name\}/(\w+\.md)'
        
        template_files = [
            "chatmodes/sddSpecDriven.chatmode.md",
            "chatmodes/sddSpecDrivenSimple.chatmode.md"
        ]
        
        expected_numbered_files = [
            "01_feasibility.md",
            "02_requirements.md",
            "03_design.md", 
            "04_tasks.md"
        ]
        
        # Files that are allowed to remain unnumbered (not part of core spec workflow)
        allowed_unnumbered = [
            "retrospective.md",  # Post-implementation retrospective, not part of core workflow
            "changelog.md"       # Change tracking, not part of core workflow
        ]
        
        for template_file in template_files:
            content = self.read_template_file(template_file)
            matches = re.findall(file_path_pattern, content)
            
            for match in matches:
                if match not in allowed_unnumbered:
                    self.assertIn(match, expected_numbered_files,
                        f"File path reference '{match}' should be numbered in {template_file}")
                    
    def test_no_old_references_remain(self):
        """Test that no old spec file references remain in any template."""
        old_patterns = [
            r'\bfeasibility\.md\b',
            r'\brequirements\.md\b',
            r'\bdesign\.md\b', 
            r'\btasks\.md\b'
        ]
        
        # Scan all template files
        template_dirs = ["chatmodes", "prompts", "gitlab-flow", "instructions"]
        
        for template_dir in template_dirs:
            dir_path = self.templates_dir / template_dir
            if not dir_path.exists():
                continue
                
            for file_path in dir_path.glob("*.md"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in old_patterns:
                    matches = re.findall(pattern, content)
                    self.assertEqual(len(matches), 0, 
                        f"Found old reference pattern '{pattern}' in {file_path}")
                        
    def test_sequential_numbering(self):
        """Test that numbered files follow sequential 01, 02, 03, 04 pattern."""
        expected_sequence = ["01", "02", "03", "04"]
        expected_names = ["feasibility", "requirements", "design", "tasks"]
        
        # Extract all numbered file references
        all_refs = set()
        template_dirs = ["chatmodes", "prompts", "gitlab-flow"]
        
        for template_dir in template_dirs:
            dir_path = self.templates_dir / template_dir
            if not dir_path.exists():
                continue
                
            for file_path in dir_path.glob("*.md"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find all numbered references
                refs = re.findall(r'\b(\d{2})_(\w+)\.md\b', content)
                all_refs.update(refs)
        
        # Verify sequential numbering
        for number, name in all_refs:
            self.assertIn(number, expected_sequence, f"Invalid number prefix: {number}")
            self.assertIn(name, expected_names, f"Invalid file name: {name}")
            
            # Verify correct number-name mapping
            expected_index = expected_names.index(name)
            expected_number = expected_sequence[expected_index]
            self.assertEqual(number, expected_number, 
                f"Wrong number for {name}: expected {expected_number}, got {number}")

def run_tests():
    """Run the test suite and return results."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(NumberedSpecFilesTestSuite)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"❌ {test}: {traceback}")
            
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"💥 {test}: {traceback}")
    
    if result.wasSuccessful():
        print(f"\n✅ ALL TESTS PASSED - Numbered spec files implementation is working correctly!")
        return True
    else:
        print(f"\n❌ TESTS FAILED - Issues found with numbered spec files implementation")
        return False

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)