# ADR 0001: Use Reusable Workflows for DRY CI/CD

## Status

Accepted

## Date

2025-12-05

## Context

The CloudOps repository had two nearly identical workflow files (`.github/workflows/example-azure.yml` and `.github/workflows/example-aws.yml`) with approximately 90% code duplication. The only differences were:
- Cloud provider parameter (`azure` vs `aws`)
- Credentials (Azure vs AWS secrets)
- Backend configuration format

This duplication led to:
- Maintenance burden (changes needed in multiple places)
- Risk of inconsistency between workflows
- Harder to add new features or fix bugs
- Violation of DRY (Don't Repeat Yourself) principle

## Decision

We decided to create a reusable workflow template (`.github/workflows/reusable-terraform.yml`) that can be called by provider-specific workflows with different parameters.

### Approach Chosen: Reusable Workflows

**Advantages:**
- Single source of truth for workflow logic
- Reduced duplication from ~90% to <10%
- Easier maintenance and updates
- Consistent behavior across providers
- GitHub's native feature (no custom actions needed)
- Easy to add new providers

**Implementation:**
1. Created `reusable-terraform.yml` with parameterized inputs
2. Refactored `example-azure.yml` to call reusable workflow
3. Refactored `example-aws.yml` to call reusable workflow
4. Both workflows now ~45 lines instead of ~70 lines each

## Alternatives Considered

### 1. Matrix Strategy
Create a single workflow with a matrix to test multiple providers:

```yaml
strategy:
  matrix:
    provider: [azure, aws]
```

**Pros:**
- Even more concise
- Single workflow file

**Cons:**
- Less flexible for provider-specific configuration
- Harder to trigger separately
- More complex conditional logic
- Secrets handling is more complicated

**Decision:** Rejected because it reduces flexibility and makes provider-specific customization harder.

### 2. Composite Actions
Extract common steps into composite actions:

**Pros:**
- Reusable at step level
- Can be used in different contexts

**Cons:**
- Only reduces some duplication
- Still need workflow structure in each file
- More complex to maintain
- Doesn't eliminate job-level duplication

**Decision:** Rejected because it provides less reduction in duplication compared to reusable workflows.

### 3. Keep Duplication
Accept the duplication and maintain both files:

**Pros:**
- No refactoring needed
- Each workflow is self-contained
- Easy to understand

**Cons:**
- High maintenance burden
- Risk of inconsistency
- Violates DRY principle
- Makes adding features harder

**Decision:** Rejected because it doesn't address the core problem.

## Consequences

### Positive
1. **Reduced Duplication:** From 90% to <10%
2. **Easier Maintenance:** Changes only needed in one place
3. **Consistency:** Both providers use same workflow logic
4. **Scalability:** Easy to add new providers (GCP, etc.)
5. **Testability:** Single workflow to test and validate

### Negative
1. **Indirection:** Need to look at two files to understand full workflow
2. **Learning Curve:** Team needs to understand reusable workflows
3. **Debugging:** Stack trace spans multiple files

### Mitigation
- Comprehensive documentation added
- Clear naming conventions used
- Examples provided for both Azure and AWS
- Troubleshooting guide includes reusable workflow scenarios

## Implementation Details

### Reusable Workflow Inputs
```yaml
inputs:
  cloud_provider: (azure|aws|multi)
  tf_path: string
  terraform_operation: (plan|apply|plan-apply)
  backend_config: string (optional)
  artifact_name: string (optional)
  artifact_retention_days: number (default: 30)
  enable_pr_comment: boolean (default: true)
  enable_artifact_upload: boolean (default: true)
  tf_vars: string (optional)
  environment: string (optional)

secrets:
  azure_credentials: (optional)
  aws_access_key_id: (optional)
  aws_secret_access_key: (optional)
```

### Caller Pattern
```yaml
jobs:
  terraform-plan:
    uses: ./.github/workflows/reusable-terraform.yml
    with:
      cloud_provider: azure
      tf_path: examples/azure
      terraform_operation: plan
      artifact_name: azure-tfplan
    secrets:
      azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}
```

## Validation

- [x] All YAML files validated successfully
- [x] Both example workflows refactored
- [x] Documentation updated
- [x] No breaking changes to external API
- [x] Backward compatible with existing usage

## Related Documents

- [Refactor Analysis](../../REFACTOR_ANALYSIS.md)
- [GitHub Actions Reusable Workflows Documentation](https://docs.github.com/en/actions/using-workflows/reusing-workflows)

## References

- GitHub Issue: N/A
- Pull Request: [Link to PR]
- Discussion: [Link to discussion if any]

---

**Author:** Platform Team  
**Reviewers:** DevOps Team  
**Supersedes:** N/A  
**Superseded By:** N/A
