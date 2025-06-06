<!-- markdownlint-disable MD036 -->
# Platform Support Guide

This guide explains the platform support for the IT8951 e-paper Python driver across different operating systems and architectures.

## Table of Contents

- [Supported Platforms](#supported-platforms)
- [Platform-Specific Requirements](#platform-specific-requirements)
- [Installation by Platform](#installation-by-platform)
- [Development vs Production](#development-vs-production)
- [Troubleshooting](#troubleshooting)

## Supported Platforms

### Production (Hardware) Support

| Platform | Architecture | Python | Status | Notes |
|----------|-------------|--------|--------|-------|
| Raspberry Pi OS | ARM64/ARMv7 | 3.11+ | ✅ Full Support | Primary target platform |
| Ubuntu/Debian ARM | ARM64/ARMv7 | 3.11+ | ✅ Full Support | Works with IT8951 hardware |
| Other Linux ARM | ARM64/ARMv7 | 3.11+ | ⚠️ Should Work | Untested but likely compatible |

### Development Support

| Platform | Architecture | Python | Status | Notes |
|----------|-------------|--------|--------|-------|
| macOS | Intel/Apple Silicon | 3.11+ | ✅ Full Support | MockSPI for development |
| Ubuntu/Debian | x86_64 | 3.11+ | ✅ Full Support | MockSPI for development |
| Windows | x86_64 | 3.11+ | ✅ Basic Support | MockSPI only, no hardware |
| WSL2 | x86_64 | 3.11+ | ✅ Full Support | Better than native Windows |

## Platform-Specific Requirements

### Raspberry Pi (Production)

**Hardware Requirements:**

- Raspberry Pi 3B+, 4, or 5
- IT8951-based e-paper display
- SPI enabled in raspi-config

**Software Requirements:**

```bash
# Enable SPI
sudo raspi-config
# Navigate to Interface Options -> SPI -> Enable

# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-dev

# Install the package
pip install it8951-epaper-py[rpi]
```

**GPIO Access:**

- Requires user to be in `gpio` group
- Or run with appropriate permissions

### macOS (Development)

**Requirements:**

- Python 3.11+ (via Homebrew or pyenv recommended)
- No special system dependencies

**Installation:**

```bash
# Install Python if needed
brew install python@3.11

# Install the package
pip install it8951-epaper-py
```

**Notes:**

- Automatically uses MockSPI when RPi.GPIO unavailable
- Full test suite runs without hardware
- Ideal for development and testing

### Linux x86_64 (Development)

**Ubuntu/Debian:**

```bash
# Install Python and pip
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

# Install the package
pip install it8951-epaper-py
```

**Fedora/RHEL:**

```bash
# Install Python and pip
sudo dnf install -y python3-pip python3-devel

# Install the package
pip install it8951-epaper-py
```

### Windows (Limited Support)

**Native Windows:**

```powershell
# Install Python from python.org or Microsoft Store
# Ensure Python 3.11+ is installed

# Install the package
pip install it8951-epaper-py
```

**WSL2 (Recommended):**

```bash
# In WSL2 terminal
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

# Install the package
pip install it8951-epaper-py
```

**Limitations on Windows:**

- No hardware support (no GPIO access)
- MockSPI only for development
- Some examples may need path adjustments
- WSL2 provides better compatibility

## Installation by Platform

### From PyPI

```bash
# Basic installation (all platforms)
pip install it8951-epaper-py

# With Raspberry Pi GPIO support
pip install it8951-epaper-py[rpi]
```

### From Source

```bash
# Clone the repository
git clone https://github.com/sjnims/IT8951_ePaper_Py.git
cd IT8951_ePaper_Py

# Install with Poetry (all platforms)
poetry install

# Or with pip
pip install -e .
```

### Platform-Specific Extras

```bash
# Raspberry Pi with GPIO
pip install -e ".[rpi]"

# Development dependencies (all platforms)
pip install -e ".[dev]"
```

## Development vs Production

### Development Environment

**Automatic MockSPI Selection:**

```python
# The library automatically detects the platform
from IT8951_ePaper_Py import EPaperDisplay

# On macOS/Windows/non-Pi Linux:
display = EPaperDisplay(vcom=-1.45)  # Uses MockSPI automatically
```

**Explicit MockSPI:**

```python
from IT8951_ePaper_Py.spi_interface import MockSPI
from IT8951_ePaper_Py import EPaperDisplay

# Force MockSPI for testing
spi = MockSPI()
display = EPaperDisplay(vcom=-1.45, spi_interface=spi)
```

### Production Environment

**Raspberry Pi Hardware:**

```python
from IT8951_ePaper_Py import EPaperDisplay

# On Raspberry Pi with IT8951 hardware
display = EPaperDisplay(vcom=-1.45)  # Uses RaspberryPiSPI automatically

# With explicit SPI speed
display = EPaperDisplay(vcom=-1.45, spi_speed=24_000_000)  # 24MHz for Pi 4
```

## Troubleshooting

### Common Platform Issues

**macOS: "No module named RPi"**

- This is expected and handled automatically
- MockSPI will be used instead

**Windows: Path issues in examples**

```python
# Use pathlib for cross-platform paths
from pathlib import Path
image_path = Path(__file__).parent / "images" / "test.png"
```

**Raspberry Pi: Permission denied**

```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER
# Log out and back in

# Or run with sudo (not recommended)
sudo python your_script.py
```

**WSL2: Slow performance**

- Ensure files are in WSL filesystem, not Windows mount
- Use `/home/user/` not `/mnt/c/`

### Platform Detection

The library includes automatic platform detection:

```python
from IT8951_ePaper_Py.spi_interface import create_spi_interface

# Automatically selects appropriate interface
spi = create_spi_interface()
print(f"Using: {type(spi).__name__}")
# Output: "RaspberryPiSPI" on Pi, "MockSPI" elsewhere
```

### CI/CD Platform Matrix

Our continuous integration tests on:

- **Ubuntu**: Python 3.11, 3.12, 3.13
- **macOS**: Python 3.13
- **ARM64**: Python 3.11 (via QEMU)
- **Windows**: Basic compatibility check

This ensures the library works across all major development platforms.

## Best Practices by Platform

### Raspberry Pi Production

1. Use appropriate VCOM voltage for your display
2. Enable SPI in raspi-config
3. Use proper shutdown procedures
4. Monitor temperature in enclosures

### macOS/Linux Development

1. Use virtual environments
2. Run full test suite before commits
3. Test with MockSPI's various delay modes
4. Use type checking with pyright

### Windows Development

1. Prefer WSL2 over native Windows
2. Use Poetry for dependency management
3. Test path handling carefully
4. Verify imports work correctly

### Cross-Platform Code

1. Use `pathlib.Path` for file paths
2. Avoid platform-specific assumptions
3. Test on multiple platforms when possible
4. Document platform-specific behavior
