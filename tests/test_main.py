#!/usr/bin/env python3
"""
Basic unit tests for CloudOps main.py
"""

import os
import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from main import CloudOpsAction


class TestCloudOpsAction(unittest.TestCase):
    """Test CloudOpsAction class"""
    
    def setUp(self):
        """Set up test environment"""
        # Store original env
        self.original_env = os.environ.copy()
        
        # Set minimal required env
        os.environ['INPUT_TF_PATH'] = 'test/path'
        os.environ['INPUT_CLOUD_PROVIDER'] = 'azure'
        os.environ['INPUT_TERRAFORM_OPERATION'] = 'plan'
        os.environ['GITHUB_WORKSPACE'] = str(Path(__file__).parent.parent)
        os.environ['GITHUB_OUTPUT'] = '/tmp/test_output'
        
    def tearDown(self):
        """Clean up test environment"""
        os.environ.clear()
        os.environ.update(self.original_env)
        
    def test_initialization(self):
        """Test CloudOpsAction initialization"""
        action = CloudOpsAction()
        
        self.assertEqual(action.tf_path, 'test/path')
        self.assertEqual(action.cloud_provider, 'azure')
        self.assertEqual(action.terraform_operation, 'plan')
        
    def test_validate_inputs_valid(self):
        """Test input validation with valid inputs"""
        action = CloudOpsAction()
        
        # Should not raise any exception
        try:
            action.validate_inputs()
        except Exception as e:
            self.fail(f"validate_inputs raised {e} unexpectedly")
    
    def test_validate_inputs_missing_tf_path(self):
        """Test input validation with missing tf_path"""
        os.environ['INPUT_TF_PATH'] = ''
        action = CloudOpsAction()
        
        with self.assertRaises(ValueError) as context:
            action.validate_inputs()
        
        self.assertIn('tf_path is required', str(context.exception))
    
    def test_validate_inputs_invalid_cloud_provider(self):
        """Test input validation with invalid cloud provider"""
        os.environ['INPUT_CLOUD_PROVIDER'] = 'invalid'
        action = CloudOpsAction()
        
        with self.assertRaises(ValueError) as context:
            action.validate_inputs()
        
        self.assertIn('Invalid cloud_provider', str(context.exception))
    
    def test_validate_inputs_invalid_operation(self):
        """Test input validation with invalid operation"""
        os.environ['INPUT_TERRAFORM_OPERATION'] = 'invalid'
        action = CloudOpsAction()
        
        with self.assertRaises(ValueError) as context:
            action.validate_inputs()
        
        self.assertIn('Invalid terraform_operation', str(context.exception))
    
    def test_resolve_working_directory_explicit(self):
        """Test working directory resolution with explicit path"""
        os.environ['INPUT_TF_WORKING_DIR'] = 'examples/azure'
        action = CloudOpsAction()
        action.validate_inputs()
        
        working_dir = action.resolve_working_directory()
        
        self.assertTrue(working_dir.exists())
        self.assertTrue(working_dir.is_dir())
        self.assertIn('examples/azure', str(working_dir))
    
    def test_resolve_working_directory_from_dir(self):
        """Test working directory resolution from directory path"""
        os.environ['INPUT_TF_PATH'] = 'examples/azure'
        action = CloudOpsAction()
        action.validate_inputs()
        
        working_dir = action.resolve_working_directory()
        
        self.assertTrue(working_dir.exists())
        self.assertTrue(working_dir.is_dir())
        self.assertIn('examples/azure', str(working_dir))
    
    def test_resolve_working_directory_from_file(self):
        """Test working directory resolution from file path"""
        os.environ['INPUT_TF_PATH'] = 'examples/azure/main.tf'
        action = CloudOpsAction()
        action.validate_inputs()
        
        working_dir = action.resolve_working_directory()
        
        self.assertTrue(working_dir.exists())
        self.assertTrue(working_dir.is_dir())
        self.assertIn('examples/azure', str(working_dir))
    
    def test_set_output(self):
        """Test setting GitHub Actions output"""
        action = CloudOpsAction()
        
        # Create temporary output file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            output_file = f.name
        
        os.environ['GITHUB_OUTPUT'] = output_file
        
        try:
            action.set_output('test_key', 'test_value')
            
            # Read and verify output
            with open(output_file, 'r') as f:
                content = f.read()
            
            self.assertIn('test_key=test_value', content)
        finally:
            os.unlink(output_file)
    
    def test_format_plan_comment(self):
        """Test plan comment formatting"""
        action = CloudOpsAction()
        action.validate_inputs()
        # Use a path within the workspace for relative path calculation
        action.resolved_working_dir = Path(action.github_workspace) / 'examples' / 'azure'
        
        plan_output = "No changes. Infrastructure is up-to-date."
        comment = action.format_plan_comment(plan_output)
        
        self.assertIn('Terraform Plan Summary', comment)
        self.assertIn(plan_output, comment)
        self.assertIn('CloudOps', comment)
    
    def test_cloud_provider_choices(self):
        """Test all valid cloud provider choices"""
        for provider in ['azure', 'aws', 'multi']:
            os.environ['INPUT_CLOUD_PROVIDER'] = provider
            action = CloudOpsAction()
            
            try:
                action.validate_inputs()
                self.assertEqual(action.cloud_provider, provider)
            except Exception as e:
                self.fail(f"Provider {provider} raised {e} unexpectedly")
    
    def test_terraform_operation_choices(self):
        """Test all valid terraform operation choices"""
        for operation in ['plan', 'apply', 'plan-apply']:
            os.environ['INPUT_TERRAFORM_OPERATION'] = operation
            action = CloudOpsAction()
            
            try:
                action.validate_inputs()
                self.assertEqual(action.terraform_operation, operation)
            except Exception as e:
                self.fail(f"Operation {operation} raised {e} unexpectedly")


class TestWorkingDirectoryResolution(unittest.TestCase):
    """Test working directory resolution logic"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_env = os.environ.copy()
        os.environ['INPUT_TF_PATH'] = 'examples/azure'
        os.environ['INPUT_CLOUD_PROVIDER'] = 'azure'
        os.environ['INPUT_TERRAFORM_OPERATION'] = 'plan'
        os.environ['GITHUB_WORKSPACE'] = str(Path(__file__).parent.parent)
        os.environ['GITHUB_OUTPUT'] = '/tmp/test_output'
        
    def tearDown(self):
        """Clean up test environment"""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_nonexistent_path(self):
        """Test error handling for nonexistent path"""
        os.environ['INPUT_TF_PATH'] = 'nonexistent/path'
        action = CloudOpsAction()
        action.validate_inputs()
        
        with self.assertRaises(ValueError) as context:
            action.resolve_working_directory()
        
        self.assertIn('does not exist', str(context.exception))


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCloudOpsAction))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkingDirectoryResolution))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
