# ADR 0002: Python-Based Orchestrator for Action Logic

## Status

Accepted (Implemented in initial design)

## Date

2025-12-05 (Documented)

## Context

The CloudOps action needed a robust orchestration layer to:
- Install and configure multiple CLI tools (Terraform, Azure CLI, AWS CLI, GitHub CLI)
- Handle cloud provider authentication
- Execute Terraform workflow (init, fmt, validate, plan, apply)
- Manage artifacts and GitHub integrations
- Provide comprehensive error handling and logging

We needed to choose an implementation language for this orchestration logic.

## Decision

We chose **Python 3.12+** as the implementation language for the action orchestrator.

### Key Reasons

1. **Rich Standard Library**
   - `subprocess` for command execution
   - `pathlib` for file system operations
   - `json` for data parsing
   - `urllib` for downloads
   - `logging` for structured logging

2. **Clear, Maintainable Code**
   - Readable syntax
   - Strong typing support (type hints)
   - Excellent IDE support
   - Easy debugging

3. **Error Handling**
   - Exception-based error handling
   - Clear stack traces
   - Easy to catch and handle specific errors

4. **Testing Ecosystem**
   - Built-in `unittest` framework
   - Rich assertion capabilities
   - Mocking support
   - Easy to write comprehensive tests

5. **GitHub Actions Support**
   - Native Python setup action (`actions/setup-python`)
   - Fast startup time
   - Good performance
   - Wide adoption in GitHub Actions community

## Alternatives Considered

### 1. Bash Scripts

**Pros:**
- Native to Linux runners
- No setup required
- Direct command execution
- Lightweight

**Cons:**
- Limited error handling
- Harder to maintain complex logic
- Poor structure for large codebases
- Difficult to test
- No type safety
- String manipulation is cumbersome
- Cross-platform compatibility issues

**Example Pain Points:**
```bash
# Complex JSON parsing
credentials=$(echo "$AZURE_CREDENTIALS" | jq -r '.clientId')

# Error handling is verbose
if [ $? -ne 0 ]; then
  echo "Error occurred"
  exit 1
fi

# No built-in logging levels
```

**Decision:** Rejected due to maintainability concerns and poor support for complex logic.

### 2. JavaScript/TypeScript

**Pros:**
- Native GitHub Actions support
- Good GitHub Actions SDK (`@actions/core`, `@actions/github`)
- Strong typing with TypeScript
- Large ecosystem (npm)
- Familiar to many developers

**Cons:**
- Requires Node.js installation
- Package management overhead (node_modules)
- Async/await complexity for subprocess calls
- Less mature subprocess handling
- Build step required for TypeScript
- Larger action size

**Example Complexity:**
```javascript
// Subprocess execution is more verbose
const { exec } = require('@actions/exec');
await exec('terraform', ['init'], {
  cwd: workingDir,
  listeners: {
    stdout: (data) => { /* handle */ },
    stderr: (data) => { /* handle */ }
  }
});
```

**Decision:** Rejected because Python provides better subprocess management and simpler deployment (no build step).

### 3. Go

**Pros:**
- Compiled binary (no runtime needed)
- Excellent performance
- Strong typing
- Good standard library
- Easy distribution

**Cons:**
- Compilation required
- Cross-compilation complexity
- Less flexible for rapid changes
- Smaller ecosystem for CI/CD tools
- Steeper learning curve
- Harder to debug in action context

**Decision:** Rejected because compilation adds complexity and reduces development velocity.

### 4. Container-based Action (Docker)

**Pros:**
- Complete isolation
- Can use any language
- Consistent environment
- Pre-installed tools possible

**Cons:**
- Slower startup time (pull image)
- Larger size
- More complex to maintain
- Build and publish pipeline needed
- Version management complexity
- GitHub Container Registry dependency

**Decision:** Rejected due to performance concerns and added complexity. Composite action with Python provides faster execution.

## Consequences

### Positive

1. **Maintainability**
   - Clear, readable code structure
   - Easy to add new features
   - Simple to refactor
   - Good IDE support with type hints

2. **Testing**
   - 13 unit tests already implemented
   - Easy to add more tests
   - Mock support for external dependencies
   - Fast test execution

3. **Error Handling**
   - Comprehensive exception handling
   - Clear error messages
   - Structured logging
   - Easy debugging

4. **Performance**
   - Fast startup (no compilation)
   - Efficient subprocess management
   - Minimal memory overhead
   - Quick action execution

5. **Extensibility**
   - Easy to add new cloud providers
   - Simple to add new features
   - Modular structure possible
   - Plugin architecture potential

### Negative

1. **Runtime Dependency**
   - Requires Python 3.12+ on runner
   - Need `actions/setup-python` step
   - Minimal package dependencies (requests, pyyaml)

2. **Performance (Minor)**
   - Slightly slower than compiled languages (negligible in practice)
   - Interpreted language overhead

3. **Type Safety**
   - Optional type hints (not enforced at runtime)
   - Need type checker (mypy) for strict checking

### Mitigation

- Python 3.12 is pre-installed on GitHub-hosted runners
- Minimal dependencies reduce installation time
- Type hints used throughout for IDE support
- Comprehensive tests ensure correctness

## Implementation Details

### Code Structure

```python
class CloudOpsAction:
    """Main orchestrator class"""
    
    def __init__(self):
        """Initialize from environment variables"""
    
    def validate_inputs(self):
        """Validate configuration"""
    
    def install_terraform(self):
        """Install Terraform CLI"""
    
    def configure_azure_credentials(self):
        """Configure Azure authentication"""
    
    def terraform_plan(self):
        """Execute terraform plan"""
    
    def run(self):
        """Main execution flow"""
```

### Key Design Patterns

1. **Class-based Organization**
   - Single responsibility per method
   - Clear lifecycle (init → validate → install → configure → execute)
   - State management via instance variables

2. **Subprocess Execution**
   - Centralized `run_command()` method
   - Consistent logging
   - Error handling
   - Output capture

3. **Environment Variable Configuration**
   - GitHub Actions native pattern
   - Clear mapping from inputs to env vars
   - Easy to test locally

## Validation

Current implementation demonstrates success:
- [x] 674 lines of maintainable code
- [x] 13 unit tests (all passing)
- [x] Clear error messages
- [x] Comprehensive logging
- [x] Support for Azure, AWS, and multi-cloud

## Future Considerations

### Potential Modularization

As the codebase grows, consider:
```python
# src/tools.py - Tool installation
# src/providers.py - Cloud provider config
# src/terraform.py - Terraform operations
# src/utils.py - Helper functions
```

This would improve:
- Separation of concerns
- Testing granularity
- Code reuse
- Maintenance clarity

**Status:** Planned in REFACTOR_ANALYSIS.md

## Related Documents

- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Full architecture documentation
- [REFACTOR_ANALYSIS.md](../../REFACTOR_ANALYSIS.md) - Future modularization plans
- [src/main.py](../../src/main.py) - Current implementation

## References

- Python subprocess documentation: https://docs.python.org/3/library/subprocess.html
- GitHub Actions Python: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idstepsrun
- Composite Actions: https://docs.github.com/en/actions/creating-actions/creating-a-composite-action

---

**Author:** Platform Team  
**Reviewers:** DevOps Team  
**Supersedes:** N/A  
**Superseded By:** N/A
