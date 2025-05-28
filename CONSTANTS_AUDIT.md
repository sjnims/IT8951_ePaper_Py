# Constants Audit Report

This audit examines the usage of constants in the IT8951 e-paper driver codebase to identify unused constants and magic numbers that should be centralized.

## 1. Unused Constants

### SystemCommand (3 unused)
- `MEM_BST_RD_T` (0x0012) - Memory burst read type T
- `MEM_BST_RD_S` (0x0013) - Memory burst read type S  
- `MEM_BST_END` (0x0015) - Memory burst end

### Register (6 unused)
- `REG_0208` through `REG_020E` - Unnamed registers
- `PWR` (0x1E54) - Power register
- `MCSR` (0x18004) - Memory controller status register

### DisplayMode (3 unused)
- `GLR16` (5) - Ghost reduction 16-level
- `GLD16` (6) - Ghost level detection 16
- `DU4` (7) - Direct update 4-level

### PixelFormat (3 unused)
- `BPP_2` (0) - 2 bits per pixel
- `BPP_3` (1) - 3 bits per pixel
- `BPP_4` (2) - 4 bits per pixel

### Other Unused
- `EndianType.BIG` - Big endian (only LITTLE is used)
- `SPIConstants.PREAMBLE_WRITE` - Redundant with PREAMBLE_DATA
- `GPIOPin.CS` - Chip select pin (handled by spidev)
- `MemoryConstants.WAVEFORM_ADDR` - Waveform memory address
- Several `DisplayConstants` that should be used in validation

## 2. Magic Numbers to Extract

### High Priority (Frequently Used)
```python
# Communication & Protocol
DEVICE_INFO_READ_SIZE = 20          # Bytes to read for device info
PACKED_WRITE_ENABLE_BIT = 0x0001    # Enable packed write mode
VCOM_CONVERSION_FACTOR = 1000       # Convert between V and mV
ADDRESS_MASK_16BIT = 0xFFFF         # Mask for 16-bit values
BYTE_SHIFT = 8                      # Bits to shift for byte operations
BYTE_MASK = 0xFF                    # Mask for single byte

# Timing Constants  
RESET_PULSE_DURATION = 0.1          # Seconds for reset pulse
BUSY_POLL_INTERVAL_FAST = 0.001     # Fast polling interval
BUSY_POLL_INTERVAL_SLOW = 0.01      # Slow polling interval
DISPLAY_READY_TIMEOUT_MS = 30000    # 30 second timeout
DISPLAY_POLL_INTERVAL = 0.01        # Display ready check interval

# Display Constants
DEFAULT_CLEAR_COLOR = 0xFF          # White
GRAYSCALE_MAX = 255                 # Maximum grayscale value
PIXEL_ALIGNMENT = 4                 # Pixel boundary alignment
```

### Register-Specific Constants
```python
# Register Offsets
LISAR_HIGH_OFFSET = 2               # Offset for high address register
LUT_STATE_BIT_POSITION = 7          # Bit position in MISC register

# SPI Constants
SPI_READ_DUMMY = [0x00, 0x00]       # Dummy bytes for SPI read
MOCK_DEFAULT_READ_VALUE = 0xFFFF    # Default mock read value
```

### Rotation Constants
```python
# Rotation angles (degrees)
ROTATION_ANGLE_90 = -90
ROTATION_ANGLE_180 = 180
ROTATION_ANGLE_270 = 90
```

## 3. Code Duplication Issues

### VCOM Range Validation
- Defined in `DisplayConstants` but hardcoded in `models.py`
- Should use: `DisplayConstants.MIN_VCOM` and `MAX_VCOM`

### Panel Dimensions
- Defined in `DisplayConstants` but hardcoded in `models.py`  
- Should use: `DisplayConstants.MAX_WIDTH` and `MAX_HEIGHT`

### Timeout Values
- `DisplayConstants.TIMEOUT_MS` defined but not used
- Hardcoded 30000ms timeout in `it8951.py`

## 4. Recommendations

### Remove Unused Constants
1. Delete unused display modes until implemented (GLR16, GLD16, DU4)
2. Remove unused pixel formats until lower bpp support is added
3. Remove unused registers unless needed for future features

### Add Missing Constants
1. Create a new `ProtocolConstants` class for communication values
2. Add `TimingConstants` for all timing-related values
3. Move rotation angles to constants

### Fix Duplication
1. Update `models.py` to use existing constants
2. Use `TIMEOUT_MS` consistently across the codebase
3. Ensure all validation uses centralized constants

### Example Implementation
```python
class ProtocolConstants:
    """Protocol and communication constants."""
    
    DEVICE_INFO_SIZE = 20
    PACKED_WRITE_BIT = 0x0001
    VCOM_FACTOR = 1000
    ADDRESS_MASK = 0xFFFF
    BYTE_SHIFT = 8
    BYTE_MASK = 0xFF
    
class TimingConstants:
    """Timing-related constants."""
    
    RESET_DURATION_S = 0.1
    BUSY_POLL_FAST_S = 0.001
    BUSY_POLL_SLOW_S = 0.01
    DISPLAY_TIMEOUT_MS = 30000
    DISPLAY_POLL_S = 0.01
```

## Summary

- **21 unused constants** identified that could be removed
- **20+ magic numbers** found that should be constants
- **3 cases of duplication** where existing constants aren't used

This cleanup would improve code maintainability and make the codebase more consistent.