# Security Policy

## Supported Versions

We actively support security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.5.x   | :white_check_mark: |
| 0.4.x   | :white_check_mark: |
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

## Reporting a Vulnerability

We take the security of the IT8951 e-paper driver seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

GitHub provides a private vulnerability reporting mechanism for this repository:

1. **DO NOT** create a public issue
2. Navigate to the [Security tab](https://github.com/sjnims/IT8951_ePaper_Py/security) of this repository
3. Click on "Report a vulnerability" button
4. Fill out the vulnerability report form with:
   - Type of vulnerability
   - Steps to reproduce
   - Potential impact
   - Affected versions
   - Suggested fix (if any)

This ensures your report stays private while we work on a fix.

### Alternative Reporting

If you're unable to use GitHub's private reporting feature, you can email: <sjnims@gmail.com>

### What to Expect

When using GitHub's private vulnerability reporting:

- GitHub will notify repository maintainers of your report
- We'll collaborate directly in the security advisory
- You'll receive updates as we investigate and fix the issue
- We'll coordinate disclosure timing with you
- You'll be credited in the security advisory (unless you prefer anonymity)

For email reports:

- **Acknowledgment**: Within 48 hours
- **Investigation**: We'll validate and assess the issue
- **Updates**: Regular progress updates
- **Fix**: Coordinated patch and disclosure
- **Credit**: Recognition for responsible disclosure

## Security Considerations

### Hardware Access

This driver requires direct hardware access:

- SPI communication
- GPIO pin control
- Memory manipulation

**Best Practices:**

- Run with minimal required privileges
- Use appropriate user/group permissions
- Avoid running as root when possible

### Input Validation

The driver validates all inputs:

- Image dimensions and formats
- Memory addresses
- VCOM voltage ranges
- Display coordinates

### Dependencies

We regularly update dependencies for security:

- Monitor security advisories
- Use dependency scanning
- Update promptly when issues are found

### Code Quality

Security measures in place:

- GitHub CodeQL analysis
- Type checking with pyright
- Comprehensive test coverage
- Code review for all changes

## Security Features

### Built-in Protections

1. **Memory Safety**
   - Buffer size validation
   - Address range checking
   - Proper memory alignment

2. **Input Sanitization**
   - Image format validation
   - Parameter range checking
   - Type enforcement

3. **Error Handling**
   - No sensitive data in errors
   - Proper exception hierarchy
   - Fail-safe defaults

### Recommendations for Users

1. **Physical Security**
   - Secure physical access to hardware
   - Protect SPI/GPIO connections
   - Use proper enclosures

2. **Software Security**
   - Keep Python updated
   - Update dependencies regularly
   - Use virtual environments

3. **Application Security**
   - Validate user inputs
   - Sanitize displayed content
   - Handle errors gracefully

## Known Security Considerations

### SPI Communication

- SPI is not encrypted
- Physical access allows eavesdropping
- Use appropriate physical security

### Display Content

- E-paper retains images without power
- Clear sensitive information when done
- Consider privacy implications

### Mock Mode

- Mock mode is for development only
- Do not use in production
- No actual hardware security

## Security Audit

Last security review: June 2025

- [x] Dependency audit
- [x] CodeQL analysis
- [x] Input validation review
- [x] Error handling review

## Contact

- **Security vulnerabilities**: Use [GitHub's private reporting](https://github.com/sjnims/IT8951_ePaper_Py/security/advisories/new) or email <sjnims@gmail.com>
- **General issues**: [GitHub Issues](https://github.com/sjnims/IT8951_ePaper_Py/issues)
- **Questions**: [GitHub Discussions](https://github.com/sjnims/IT8951_ePaper_Py/discussions) (if enabled)
