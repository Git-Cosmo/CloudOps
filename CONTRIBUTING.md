# Contributing to CloudOps

Thank you for your interest in contributing to CloudOps! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:

- A clear, descriptive title
- Detailed steps to reproduce the issue
- Expected behavior vs actual behavior
- Your environment (OS, Python version, Terraform version)
- Relevant logs or error messages

### Suggesting Enhancements

Enhancement suggestions are welcome! Please create an issue with:

- A clear description of the enhancement
- Use cases and benefits
- Any implementation ideas you have

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes**:
   - Follow the existing code style
   - Update documentation as needed
   - Add tests if applicable
3. **Test your changes**:
   - Validate Python syntax: `python3 -m py_compile src/main.py`
   - Validate YAML: `python3 -c "import yaml; yaml.safe_load(open('action.yml'))"`
   - Test with example configurations
4. **Commit your changes**:
   - Use clear, descriptive commit messages
   - Reference related issues (e.g., "Fixes #123")
5. **Push to your fork** and submit a pull request

### Pull Request Guidelines

- **Title**: Clear and descriptive
- **Description**: Explain what changed and why
- **Testing**: Describe how you tested the changes
- **Documentation**: Update README or other docs if needed
- **Breaking Changes**: Clearly mark any breaking changes

## Development Setup

### Prerequisites

- Python 3.12+
- Git
- GitHub CLI (optional, for testing)

### Local Development

```bash
# Clone the repository
git clone https://github.com/Git-Cosmo/CloudOps.git
cd CloudOps

# Test Python syntax
python3 -m py_compile src/main.py

# Validate action.yml
python3 -c "import yaml; yaml.safe_load(open('action.yml'))"
```

### Testing with Local Action

To test the action locally in another repository:

```yaml
- name: Test CloudOps Action
  uses: ./path/to/local/CloudOps
  with:
    tf_path: ./terraform
    cloud_provider: azure
```

## Module Contribution Guidelines

### Azure Modules

Azure modules should follow the Azure Verified Module (AVM) pattern:

- Use consistent naming: `azurerm_<resource_type>`
- Include comprehensive variables with descriptions
- Provide useful outputs
- Add tags support
- Follow security best practices

### AWS Modules

AWS modules should follow AWS best practices:

- Use consistent naming conventions
- Include comprehensive variables with descriptions
- Provide useful outputs
- Add tags support
- Follow security best practices (encryption, access control, etc.)

### Module Structure

Each module should include:

```
module-name/
├── main.tf       # Main resource definitions
├── variables.tf  # Input variables
├── outputs.tf    # Output values
└── README.md     # Module documentation (optional)
```

### Module Documentation

Include:

- Purpose and description
- Required and optional variables
- Outputs
- Usage examples
- Dependencies

## Python Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings for classes and methods
- Keep functions focused and single-purpose
- Use meaningful variable names
- Add comments for complex logic

## Documentation Style

- Use clear, concise language
- Include code examples
- Keep formatting consistent
- Update README for user-facing changes
- Document breaking changes in CHANGELOG

## Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Build process or auxiliary tool changes

**Example:**

```
feat: Add support for Azure AKS module

- Implement AKS cluster creation
- Add node pool configuration
- Include network profile settings

Closes #42
```

## Release Process

Releases are managed by maintainers:

1. Update version numbers
2. Update CHANGELOG
3. Create GitHub release
4. Tag release (e.g., `v1.0.0`)

## Questions?

- Open an issue for questions
- Join discussions in GitHub Discussions
- Check existing issues and PRs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to CloudOps! 🎉
