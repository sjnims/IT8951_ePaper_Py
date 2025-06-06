# Hardware Setup & Troubleshooting Guide

This guide covers the physical setup, connection, and common troubleshooting steps for the IT8951 e-paper display with Raspberry Pi.

## Table of Contents

- [Hardware Requirements](#hardware-requirements)
- [Physical Connections](#physical-connections)
- [Initial Setup](#initial-setup)
- [Common Issues & Solutions](#common-issues--solutions)
- [Advanced Troubleshooting](#advanced-troubleshooting)
- [Hardware Specifications](#hardware-specifications)

## Hardware Requirements

### Required Components

1. **Raspberry Pi** (any model with 40-pin GPIO header)
   - Raspberry Pi 3B/3B+/4B recommended for best performance
   - Raspberry Pi Zero W also supported (slower SPI speeds)

2. **IT8951 HAT** with e-paper display
   - Waveshare 10.3" e-paper HAT (most common)
   - Other IT8951-based displays (6", 7.8", 9.7", 13.3")

3. **Power Supply**
   - 5V 3A power supply for Raspberry Pi
   - The e-paper display is powered through the HAT

4. **Optional Components**
   - Standoffs/spacers for secure mounting
   - Cooling (heatsink/fan) for intensive use
   - Case compatible with HAT connection

### Software Requirements

- Raspberry Pi OS (Bullseye or later recommended)
- Python 3.11+
- SPI enabled in Raspberry Pi configuration

## Physical Connections

### Step 1: Enable SPI

Before connecting hardware, enable SPI on your Raspberry Pi:

```bash
# Method 1: Using raspi-config
sudo raspi-config
# Navigate to: Interface Options > SPI > Enable

# Method 2: Direct edit
sudo nano /boot/config.txt
# Add or uncomment: dtparam=spi=on

# Reboot to apply changes
sudo reboot
```

### Step 2: Connect the HAT

1. **Power Off** the Raspberry Pi completely
2. Align the 40-pin connector on the HAT with the GPIO header
3. Gently press down until fully seated
4. Ensure the HAT is level and all pins are connected

### Step 3: Connect the Display

1. Locate the FPC (Flexible Printed Circuit) cable
2. Note the VCOM voltage printed on the cable (e.g., "VCOM: -1.45V")
3. Insert the FPC cable into the HAT connector:
   - Lift the connector latch
   - Insert cable with contacts facing down
   - Close the latch firmly

⚠️ **WARNING**: The FPC cable is delicate. Do not bend sharply or apply excessive force.

### Step 4: Power On

1. Connect power to the Raspberry Pi
2. The display should show initial content or remain blank
3. Check the HAT LED indicators (if present)

## Initial Setup

### Verify SPI Communication

```bash
# Check SPI devices
ls -l /dev/spidev*
# Should show: /dev/spidev0.0 and possibly /dev/spidev0.1

# Check SPI is loaded
lsmod | grep spi
# Should show: spi_bcm2835 or similar

# Test with the library
python3 -c "from IT8951_ePaper_Py import EPaperDisplay; print('Import successful')"
```

### First Display Test

```python
#!/usr/bin/env python3
from IT8951_ePaper_Py import EPaperDisplay

# Use YOUR display's VCOM value!
display = EPaperDisplay(vcom=-1.45)

try:
    width, height = display.init()
    print(f"Display initialized: {width}x{height}")

    # Clear display
    display.clear()
    print("Display cleared successfully!")

except Exception as e:
    print(f"Error: {e}")
```

## Common Issues & Solutions

### Issue 1: "No SPI device found"

**Symptoms**: `FileNotFoundError: [Errno 2] No such file or directory: '/dev/spidev0.0'`

**Solutions**:

1. Verify SPI is enabled (see Physical Connections > Step 1)
2. Check permissions:

   ```bash
   sudo usermod -a -G spi,gpio $USER
   # Log out and back in
   ```

3. Verify kernel modules:

   ```bash
   sudo modprobe spi_bcm2835
   ```

### Issue 2: "SPI communication timeout"

**Symptoms**: `IT8951TimeoutError: SPI read timeout after 1.0 seconds`

**Solutions**:

1. Check physical connections - reseat the HAT
2. Reduce SPI speed:

   ```python
   display = EPaperDisplay(vcom=-1.45, spi_speed=2_000_000)  # 2MHz
   ```

3. Check for bent pins on GPIO header
4. Try different SPI mode:

   ```python
   from IT8951_ePaper_Py.spi_interface import RaspberryPiSPI
   spi = RaspberryPiSPI(speed_hz=2_000_000, mode=0)  # Try mode 0, 1, 2, or 3
   ```

### Issue 3: "Display shows artifacts or ghosting"

**Symptoms**: Previous images remain visible, poor contrast

**Solutions**:

1. Verify VCOM voltage matches your display:

   ```python
   # Wrong VCOM causes poor image quality
   display = EPaperDisplay(vcom=-1.45)  # Use YOUR display's value!
   ```

2. Perform full refresh:

   ```python
   display.clear()  # Full INIT mode clear
   ```

3. Check temperature:

   ```python
   status = display.get_device_status()
   print(f"Temperature: {status['temperature']}°C")
   # Optimal range: 15-35°C
   ```

### Issue 4: "Display is very slow"

**Symptoms**: Updates take several seconds

**Solutions**:

1. Use appropriate display modes:

   ```python
   # Fast updates (1-bit, low quality)
   display.display_image(img, mode=DisplayMode.A2)

   # Medium speed (good for text)
   display.display_image(img, mode=DisplayMode.DU)

   # High quality (slower)
   display.display_image(img, mode=DisplayMode.GC16)
   ```

2. Optimize bit depth:

   ```python
   # Use 4bpp instead of 8bpp for 2x faster transfers
   display.display_image(img, pixel_format=PixelFormat.BPP_4)
   ```

3. Increase SPI speed for your Pi model:

   ```python
   # Pi 4: up to 24MHz
   display = EPaperDisplay(vcom=-1.45, spi_speed=24_000_000)

   # Pi 3: up to 12MHz
   display = EPaperDisplay(vcom=-1.45, spi_speed=12_000_000)
   ```

### Issue 5: "Random disconnections or resets"

**Symptoms**: Display stops responding, requires power cycle

**Solutions**:

1. Check power supply:
   - Use official Raspberry Pi power supply
   - Ensure 5V 3A rating
   - Check for undervoltage warnings: `dmesg | grep voltage`

2. Add error recovery:

   ```python
   from IT8951_ePaper_Py.retry_policy import RetryPolicy, retry

   policy = RetryPolicy(max_attempts=3)

   @retry(policy)
   def safe_update():
       display.display_image(img)
   ```

3. Enable enhanced driving for long cables:

   ```python
   display = EPaperDisplay(vcom=-1.45, enhance_driving=True)
   ```

## Advanced Troubleshooting

### Diagnostic Commands

```python
# 1. Dump all registers
display._controller.dump_registers()

# 2. Check memory info
info = display._controller.get_system_info()
print(f"Memory size: {info.memory_size_mb} MB")

# 3. Verify VCOM
actual_vcom = display.get_vcom()
print(f"Actual VCOM: {actual_vcom}V")

# 4. Test patterns
import numpy as np

# Checkerboard pattern
pattern = np.indices((100, 100)).sum(axis=0) % 2 * 255
display.display_image(pattern.astype(np.uint8))

# Gradient test
gradient = np.linspace(0, 255, 800*600).reshape(600, 800)
display.display_image(gradient.astype(np.uint8))
```

### Performance Profiling

```python
import time

# Profile different operations
def profile_display():
    img = np.random.randint(0, 256, (600, 800), dtype=np.uint8)

    # Profile different modes
    modes = [DisplayMode.A2, DisplayMode.DU, DisplayMode.GC16]
    for mode in modes:
        start = time.time()
        display.display_image(img, mode=mode)
        print(f"{mode.name}: {time.time() - start:.2f}s")

# Check SPI performance
def profile_spi():
    from IT8951_ePaper_Py.utils import timed_operation

    @timed_operation
    def transfer_test():
        data = np.random.randint(0, 256, 1000000, dtype=np.uint8)
        display._controller._interface.write_data_bulk(data.tolist())

    transfer_test()
```

### Hardware Debugging

1. **Check GPIO pins**:

   ```bash
   gpio readall
   ```

2. **Monitor SPI traffic** (requires logic analyzer):
   - SCLK (Pin 23) - Clock signal
   - MOSI (Pin 19) - Data to display
   - MISO (Pin 21) - Data from display
   - CS0 (Pin 24) - Chip select

3. **Test without library**:

   ```bash
   # Send test data directly
   echo -ne '\x00\x00\x00\x00' > /dev/spidev0.0
   ```

## Hardware Specifications

### GPIO Pin Usage

| GPIO | Pin | Function | Direction |
|------|-----|----------|-----------|
| 2    | 3   | SDA (I2C) | Not used |
| 3    | 5   | SCL (I2C) | Not used |
| 7    | 26  | CS (SPI) | Output |
| 8    | 24  | CS0 (SPI) | Output |
| 9    | 21  | MISO (SPI) | Input |
| 10   | 19  | MOSI (SPI) | Output |
| 11   | 23  | SCLK (SPI) | Output |
| 17   | 11  | RESET | Output |
| 24   | 18  | BUSY | Input |

### Electrical Specifications

- **Operating Voltage**: 3.3V (through HAT)
- **Current Consumption**:
  - Active: ~200mA
  - Standby: ~10mA
  - Sleep: <1mA
- **SPI Speed**:
  - Maximum: 24MHz (Pi 4)
  - Recommended: 12MHz
  - Minimum: 1MHz (for debugging)

### Environmental Specifications

- **Operating Temperature**: 0°C to 50°C
- **Storage Temperature**: -25°C to 60°C
- **Humidity**: 35% to 65% RH
- **Display Lifetime**: >1,000,000 updates

## Best Practices

1. **Always use correct VCOM** - Check the FPC cable
2. **Handle with care** - E-paper displays are fragile
3. **Avoid rapid updates** - Use A2 mode sparingly
4. **Monitor temperature** - Performance degrades outside 15-35°C
5. **Use appropriate modes** - Match display mode to content type
6. **Implement error handling** - Use retry mechanisms
7. **Power management** - Use sleep mode for battery operation

## Getting Help

If you continue to experience issues:

1. Run the troubleshooting demo:

   ```bash
   python examples/troubleshooting_demo.py -1.45
   ```

2. Collect diagnostic information:

   ```bash
   python examples/debug_mode_demo.py -1.45 > debug_log.txt
   ```

3. Check the GitHub issues: <https://github.com/stevenaleung/IT8951>

4. Include in bug reports:
   - Raspberry Pi model
   - Display model and size
   - VCOM voltage
   - Error messages
   - Debug log output
