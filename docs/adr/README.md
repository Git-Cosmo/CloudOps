# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) for the CloudOps project.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences.

## Why ADRs?

- **Document decisions** - Preserve the reasoning behind architectural choices
- **Onboard new team members** - Help newcomers understand why things are the way they are
- **Avoid repeated discussions** - Reference past decisions instead of rehashing
- **Track evolution** - See how architecture evolved over time
- **Share knowledge** - Communicate decisions across teams

## ADR Format

Each ADR follows this structure:

```markdown
# ADR NNNN: Title

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Date
YYYY-MM-DD

## Context
What is the issue that we're addressing?

## Decision
What is the change that we're proposing/doing?

## Alternatives Considered
What other options were considered?

## Consequences
What becomes easier or harder as a result?

## Implementation Details
How was/will this be implemented?

## Validation
How do we know this decision was successful?

## Related Documents
Links to related documentation

## References
External references and links
```

## Current ADRs

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [0001](0001-use-reusable-workflows.md) | Use Reusable Workflows for DRY CI/CD | Accepted | 2025-12-05 |
| [0002](0002-python-based-orchestrator.md) | Python-Based Orchestrator for Action Logic | Accepted | 2025-12-05 |

## Creating a New ADR

1. **Copy the template:**
   ```bash
   cp docs/adr/template.md docs/adr/NNNN-title.md
   ```

2. **Use next number:** Sequential numbering (0001, 0002, etc.)

3. **Use kebab-case:** Lowercase with hyphens (e.g., `use-reusable-workflows`)

4. **Fill in all sections:**
   - Context: Why is this decision needed?
   - Decision: What are we doing?
   - Alternatives: What else was considered?
   - Consequences: What are the impacts?

5. **Get review:** Have team members review before merging

6. **Update this README:** Add entry to the table above

## ADR Lifecycle

### Proposed
- Decision is being discussed
- Not yet implemented
- May change based on feedback

### Accepted
- Decision has been made
- Implementation in progress or complete
- Team agrees on approach

### Deprecated
- Decision is no longer relevant
- Superseded by newer decision
- Kept for historical context

### Superseded
- Replaced by a newer ADR
- Link to superseding ADR

## Guidelines

### When to Create an ADR

Create an ADR when:
- Making a significant architectural decision
- Choosing between multiple viable approaches
- Decision will impact multiple teams
- Decision affects long-term maintainability
- Answer to "why did we do it this way?" is non-obvious

### When NOT to Create an ADR

Don't create an ADR for:
- Trivial decisions (e.g., variable naming)
- Temporary workarounds
- Bug fixes
- Minor refactoring
- Implementation details that don't affect architecture

### Good ADRs are:

- **Concise** - Get to the point quickly
- **Specific** - Clear about what was decided
- **Justified** - Explain the reasoning
- **Complete** - Cover alternatives and consequences
- **Timely** - Written when decision is made, not months later

### Bad ADRs are:

- **Vague** - Unclear what was actually decided
- **Incomplete** - Missing alternatives or consequences
- **Unjustified** - No explanation of why
- **Outdated** - Written long after the decision
- **Too detailed** - Implementation details belong in code

## Examples from CloudOps

### Good Example: ADR 0001

**Good because:**
- Clear problem statement (90% duplication)
- Specific decision (reusable workflows)
- Multiple alternatives considered
- Concrete consequences
- Implementation details provided
- Validation criteria included

### What to Avoid

**Too vague:**
```markdown
# ADR: Make workflows better
We decided to improve the workflows.
```

**Too detailed:**
```markdown
# ADR: Use reusable workflows
[50 pages of YAML code and implementation details]
```

**Missing alternatives:**
```markdown
# ADR: Use Python
We're using Python. It's great.
```

## References

- [Michael Nygard's ADR article](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub organization](https://adr.github.io/)
- [ADR tools](https://github.com/npryce/adr-tools)

---

**Maintainer:** Platform Team  
**Last Updated:** 2025-12-05
