# Automated Test Selection (ATS) Monitoring Guide

This document explains how to monitor and tune the Codecov ATS (Automated Test Selection) implementation for the IT8951 e-Paper Python driver project.

## Overview

ATS intelligently selects and runs only the tests affected by code changes in pull requests, significantly reducing CI time while maintaining test coverage confidence.

## How ATS Works

1. **Coverage Mapping**: Codecov builds a map of which tests cover which source files
2. **Change Detection**: When a PR is opened, ATS analyzes which files changed
3. **Test Selection**: ATS selects only tests that cover the changed files
4. **Fallback**: If ATS fails or has insufficient data, all tests run

## Monitoring ATS Performance

### 1. PR Comments

Each PR with ATS enabled will receive an automated comment showing:

- Whether ATS was enabled or disabled
- Number of tests selected vs total tests
- Estimated time savings

### 2. GitHub Actions Summary

Check the workflow summary for detailed metrics:

- Total tests in suite
- Tests selected by ATS
- Test reduction percentage
- Time saved estimate

### 3. Codecov Dashboard

Visit [codecov.io](https://codecov.io/gh/sjnims/IT8951_ePaper_Py) to see:

- Test selection accuracy
- Coverage impact
- Historical ATS performance

## Tuning ATS

### Configuration Parameters

In `codecov.yml`:

```yaml
ats:
  enabled: true          # Enable/disable ATS
  min_commits: 3         # Minimum commits before ATS activates
  max_age: 30           # Maximum age of coverage data (days)
  fallback_on_failure: true  # Run all tests if ATS fails
```

### Optimization Strategies

1. **Increase min_commits** if ATS is selecting too few tests early on
2. **Decrease max_age** if test coverage has changed significantly
3. **Add test markers** in conftest.py for better categorization
4. **Monitor false negatives** - tests that should have run but didn't

## Troubleshooting

### ATS Not Running

1. Check if PR has base coverage data:

   ```bash
   codecov validate --token=$CODECOV_TOKEN
   ```

2. Verify ATS is enabled in codecov.yml

3. Ensure sufficient historical coverage data exists

### Too Many/Few Tests Selected

1. Review test labels in conftest.py
2. Check coverage mapping accuracy
3. Consider adjusting pytest markers

### Performance Issues

1. Monitor workflow run times in GitHub Actions
2. Compare ATS vs full test suite times
3. Adjust test granularity if needed

## Best Practices

1. **Regular Review**: Check ATS metrics monthly
2. **Coverage First**: Ensure high coverage before relying on ATS
3. **Test Labels**: Keep test labels accurate and up-to-date
4. **Fallback Ready**: Always have full test suite as fallback
5. **Monitor Trends**: Track ATS performance over time

## Metrics to Track

1. **Test Reduction Rate**: Average % of tests skipped
2. **Time Savings**: Average CI time saved per PR
3. **Accuracy**: False negative rate (missed failures)
4. **Adoption**: % of PRs using ATS successfully

## Example Monitoring Script

```python
#!/usr/bin/env python3
"""Monitor ATS performance metrics."""

import json
import subprocess
from datetime import datetime, timedelta

def get_ats_metrics(days=30):
    """Fetch ATS metrics for the last N days."""
    # This would integrate with Codecov API
    # Placeholder for demonstration
    print(f"Fetching ATS metrics for last {days} days...")

    # Example metrics
    metrics = {
        "total_prs": 42,
        "ats_enabled_prs": 38,
        "average_test_reduction": 73.5,
        "average_time_saved_minutes": 4.2,
        "false_negative_rate": 0.0,
    }

    return metrics

def generate_report(metrics):
    """Generate ATS performance report."""
    print("\n=== ATS Performance Report ===")
    print(f"Period: Last 30 days")
    print(f"Total PRs: {metrics['total_prs']}")
    print(f"ATS Enabled: {metrics['ats_enabled_prs']} ({metrics['ats_enabled_prs']/metrics['total_prs']*100:.1f}%)")
    print(f"Avg Test Reduction: {metrics['average_test_reduction']:.1f}%")
    print(f"Avg Time Saved: {metrics['average_time_saved_minutes']:.1f} minutes")
    print(f"False Negative Rate: {metrics['false_negative_rate']:.1f}%")

if __name__ == "__main__":
    metrics = get_ats_metrics()
    generate_report(metrics)
```

## Integration with Development Workflow

1. **Pre-commit**: Run `pytest --collect-only` to verify test labels
2. **PR Review**: Check ATS comment for test selection
3. **Post-merge**: Monitor coverage trends
4. **Sprint Review**: Review ATS performance metrics

## Future Enhancements

1. **Smart Caching**: Cache test results for unchanged code
2. **Risk-based Selection**: Prioritize critical path tests
3. **ML Enhancement**: Use ML to predict test impact
4. **Parallel Optimization**: Run selected tests in optimal order
