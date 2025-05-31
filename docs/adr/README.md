# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the IT8951 e-Paper Python driver project.

## What is an ADR?

An Architecture Decision Record captures an important architectural decision made along with its context and consequences.

## ADR Index

- [ADR-001](001-use-google-style-docstrings.md) - Use Google Style Docstrings
- [ADR-002](002-hardware-abstraction-layer.md) - Hardware Abstraction Layer Design
- [ADR-003](003-default-pixel-format.md) - Default to 4bpp Pixel Format
- [ADR-004](004-memory-safety-strategy.md) - Memory Safety Strategy
- [ADR-005](005-numpy-pixel-packing.md) - NumPy-based Pixel Packing Optimization

## ADR Template

```markdown
# ADR-XXX: Title

## Status

[Proposed | Accepted | Deprecated | Superseded by ADR-YYY]

## Context

What is the issue that we're seeing that is motivating this decision?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

### Positive

- Good things that will happen

### Negative

- Bad things that will happen

### Neutral

- Things that are neither good nor bad

## References

- Links to relevant documentation or discussions
```
