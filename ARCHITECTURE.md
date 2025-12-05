# CloudOps Architecture

This document describes the architecture and design decisions behind the CloudOps Terraform IaC toolchain.

## Overview

CloudOps is a GitHub Action that provides a complete, opinionated Terraform CI/CD pipeline for Azure and AWS deployments. It combines toolchain installation, provider configuration, Terraform workflow orchestration, and artifact management into a single, reusable action.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub Action                           │
│                         (action.yml)                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ Composite Action Steps
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Python Orchestrator                        │
│                       (src/main.py)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Input      │  │  Toolchain   │  │  Provider    │        │
│  │ Validation   │→ │ Installation │→ │Configuration │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Terraform   │  │   Artifact   │  │     PR       │        │
│  │  Workflow    │→ │  Management  │→ │ Integration  │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ↓                               ↓
┌───────────────────────┐       ┌───────────────────────┐
│  Embedded Modules     │       │  User Terraform Code  │
├───────────────────────┤       └───────────────────────┘
│ • Azure AVM Modules   │
│   - virtual-network   │
│   - storage-account   │
│                       │
│ • AWS Modules         │
│   - vpc               │
│   - s3-bucket         │
└───────────────────────┘
```

## Components

### 1. GitHub Action Interface (action.yml)

The `action.yml` file defines the GitHub Action interface, including:

- **Inputs**: Configuration parameters exposed to users
- **Outputs**: Results and status information
- **Runs**: Composite action steps that set up Python and execute the orchestrator

**Key Design Decision**: Using a composite action allows us to leverage GitHub's Python environment setup while maintaining full control over the execution flow.

### 2. Python Orchestrator (src/main.py)

The core logic is implemented in Python for:

- **Flexibility**: Easy to add complex logic and error handling
- **Maintainability**: Clear, readable code structure
- **Extensibility**: Simple to add new features and integrations
- **Testing**: Python's testing ecosystem for validation

#### Main Classes

**`CloudOpsAction`**: The primary orchestrator class that:

1. Reads inputs from environment variables
2. Validates configuration
3. Resolves working directories
4. Orchestrates the pipeline stages
5. Manages outputs and artifacts

#### Pipeline Stages

1. **Input Validation**
   - Validates required inputs
   - Checks cloud provider selection
   - Verifies operation type

2. **Working Directory Resolution**
   - Interprets `tf_path` as file or directory
   - Falls back to parent directory for files
   - Respects explicit `tf_working_dir` if provided

3. **Toolchain Installation**
   - Terraform: Downloads from HashiCorp releases
   - Azure CLI: Installs via apt packages
   - AWS CLI: Downloads and installs v2
   - GitHub CLI: Installs via apt packages
   - Conditional installation based on `cloud_provider`

4. **Cloud Provider Configuration**
   - Azure: Service Principal authentication via `az login`
   - AWS: Credentials via environment variables and `~/.aws/`
   - Sets provider-specific environment variables for Terraform

5. **Terraform Workflow**
   - `terraform init`: Initialize with backend configuration
   - `terraform fmt`: Format check and auto-fix
   - `terraform validate`: Configuration validation
   - `terraform plan`: Generate execution plan with detailed exit codes
   - `terraform apply`: Apply changes (conditional)

6. **Artifact Management**
   - Saves plan file to working directory
   - Provides path via output for `upload-artifact` action
   - Preserves plan for audit and review

7. **PR Integration**
   - Detects pull request context
   - Extracts PR number from GitHub ref
   - Posts formatted plan summary as comment
   - Uses GitHub CLI for reliable API access

### 3. Embedded Modules

#### Azure AVM Modules

Follow the Azure Verified Module pattern:

- **Naming**: Consistent `azurerm_` prefix
- **Structure**: Separate files for main, variables, outputs
- **Security**: Defaults to secure configurations
- **Flexibility**: Comprehensive variable options

**Example Modules:**

- `virtual-network`: Creates VNets with subnet support
- `storage-account`: Creates storage with encryption, versioning, access control

#### AWS Modules

Follow AWS best practices:

- **Naming**: Descriptive resource names
- **Structure**: Separate files for main, variables, outputs
- **Security**: Encryption, private access by default
- **Cost-awareness**: Configurable NAT gateways, lifecycle policies

**Example Modules:**

- `vpc`: Full VPC setup with public/private subnets
- `s3-bucket`: Secure bucket with versioning and lifecycle management

### 4. Example Configurations

Pre-built examples demonstrate:

- Module usage patterns
- Backend configuration
- Variable management
- Output utilization

## Design Decisions

### Why Composite Action?

**Pros:**
- Native Python setup support
- No Docker overhead
- Faster execution
- Simpler to debug

**Cons:**
- Requires specific runner (ubuntu-latest)
- Less isolated than containers

**Decision**: Composite action chosen for speed and simplicity.

### Why Python?

**Alternatives Considered:**
- Bash scripts
- JavaScript/TypeScript

**Python Selected Because:**
- Rich standard library
- Excellent error handling
- Clear, maintainable syntax
- Strong subprocess management
- Easy JSON/YAML parsing

### Working Directory Resolution

The `tf_path` parameter accepts both files and directories:

- **Directory**: Use directly as working directory
- **File**: Use parent directory as working directory

This flexibility supports various repository layouts without extra configuration.

### Tool Installation Strategy

**Dynamic Installation** (chosen) vs **Pre-installed Tools**:

- Ensures specific versions are available
- Independent of runner image changes
- Supports version pinning
- Cache-friendly for speed

### Backend State Management

**User Responsibility** (chosen) vs **Managed State**:

- Users configure backends in their Terraform code
- Action supports backend configuration via inputs
- Avoids coupling to specific state storage
- Supports all Terraform backend types

## Security Considerations

### Credential Handling

- Never log secrets or credentials
- Use environment variables for sensitive data
- Credentials stored in GitHub Secrets
- No credential persistence to disk (except AWS config)

### Module Security Defaults

- HTTPS/TLS enforcement
- Public access blocking
- Encryption at rest
- Versioning enabled
- Minimal required permissions

### Dependency Security

- Official package sources only
- Minimal dependencies (requests, pyyaml)
- No external Python packages for core functionality

## Extensibility Points

### Adding New Modules

1. Create module directory under `modules/azure-avm/` or `modules/aws/`
2. Add `main.tf`, `variables.tf`, `outputs.tf`
3. Document in module README
4. Add example usage

### Adding New Cloud Providers

1. Add provider to `cloud_provider` input validation
2. Implement `install_<provider>_cli()` method
3. Implement `configure_<provider>_credentials()` method
4. Add provider to conditional logic
5. Create example modules

### Adding New Pipeline Steps

1. Add method to `CloudOpsAction` class
2. Call from `run()` method in appropriate sequence
3. Add logging and error handling
4. Update outputs if needed

## Performance Considerations

### Caching

- Tool binaries installed to `~/.local/bin`
- GitHub Actions cache can be used for tool directories
- Terraform init uses provider plugin cache

### Parallelization

- Tool installation could be parallelized (future enhancement)
- Terraform operations are sequential by design

### Optimization Opportunities

1. **Tool installation caching**: Cache installed tools across runs
2. **Terraform provider cache**: Share provider plugins
3. **Parallel module validation**: Validate modules independently
4. **Incremental plan**: Only plan changed directories

## Testing Strategy

### Unit Tests

- Input validation logic
- Working directory resolution
- Command construction

### Integration Tests

- Full pipeline execution
- Module deployment
- Multi-cloud scenarios

### Manual Tests

- Example configurations
- Different repository layouts
- Various cloud resources

## Future Enhancements

### Planned Features

1. **Additional Modules**
   - Azure AKS clusters
   - AWS EKS clusters
   - Database modules
   - Monitoring modules

2. **Enhanced PR Integration**
   - Cost estimation
   - Security scanning integration
   - Compliance checking
   - Drift detection

3. **Advanced Workflows**
   - Multi-environment deployments
   - Blue-green deployments
   - Canary releases
   - Automated rollback

4. **Improved Caching**
   - Tool installation cache
   - Provider plugin cache
   - Module cache

5. **Extended Provider Support**
   - Google Cloud Platform
   - IBM Cloud
   - Oracle Cloud

## Troubleshooting

### Common Issues

1. **Tool installation failures**
   - Check internet connectivity
   - Verify runner OS compatibility
   - Check for rate limiting

2. **Authentication failures**
   - Verify credentials format
   - Check secret names
   - Validate permissions

3. **Plan failures**
   - Check Terraform syntax
   - Verify provider configuration
   - Review variable values

### Debug Mode

Enable debug logging:

```yaml
- name: Deploy with CloudOps
  uses: Git-Cosmo/CloudOps@v1
  with:
    tf_path: ./infrastructure
    cloud_provider: azure
  env:
    ACTIONS_STEP_DEBUG: true
```

## References

- [Terraform Documentation](https://www.terraform.io/docs)
- [Azure Verified Modules](https://aka.ms/avm)
- [AWS Best Practices](https://aws.amazon.com/architecture/well-architected/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
