# CloudOps Tests

This directory contains unit tests for the CloudOps action.

## Running Tests

To run all tests:

```bash
python3 tests/test_main.py
```

To run tests with verbose output:

```bash
python3 tests/test_main.py -v
```

## Test Coverage

Current tests cover:

### Input Validation
- Missing required inputs
- Invalid cloud provider values
- Invalid operation types
- Valid input combinations

### Working Directory Resolution
- Explicit working directory configuration
- Directory path resolution
- File path resolution (uses parent directory)
- Nonexistent path error handling

### Output Management
- GitHub Actions output setting
- Plan comment formatting

### Configuration
- All supported cloud providers (azure, aws, multi)
- All supported operations (plan, apply, plan-apply)

## Adding New Tests

To add new tests:

1. Create a new test class or add methods to existing classes
2. Follow the naming convention: `test_<feature_name>`
3. Use descriptive docstrings
4. Set up and tear down test environment properly
5. Run tests to verify they pass

## Test Structure

```python
class TestFeature(unittest.TestCase):
    """Test description"""
    
    def setUp(self):
        """Set up test environment"""
        # Initialize test data
        
    def tearDown(self):
        """Clean up after test"""
        # Clean up resources
        
    def test_specific_behavior(self):
        """Test specific behavior"""
        # Arrange
        # Act
        # Assert
```

## Future Test Additions

Planned test coverage:

- Tool installation logic
- Cloud provider authentication
- Terraform command execution
- Artifact upload functionality
- PR comment posting
- Error handling and recovery
