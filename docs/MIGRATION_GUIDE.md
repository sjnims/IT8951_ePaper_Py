# Migration Guide: From C Driver to Python

This guide helps developers migrate from the [Waveshare IT8951 C driver](https://github.com/waveshareteam/IT8951-ePaper/tree/master/Raspberry) to this Python implementation.

## Table of Contents

- [Key Differences](#key-differences)
- [API Mapping](#api-mapping)
- [Code Examples](#code-examples)
- [Feature Comparison](#feature-comparison)
- [Performance Considerations](#performance-considerations)
- [Common Migration Patterns](#common-migration-patterns)

## Key Differences

### 1. Language & Memory Management

**C Driver:**

```c
// Manual memory management
IT8951DisplayArea* area = malloc(sizeof(IT8951DisplayArea));
// ... use area ...
free(area);

// Direct pointer manipulation
memcpy(gpFrameBuf, image_data, width * height);
```

**Python Driver:**

```python
# Automatic memory management
area = DisplayArea(x=0, y=0, width=800, height=600)
# No manual cleanup needed

# NumPy arrays for image data
image = np.array(image_data, dtype=np.uint8)
```

### 2. Initialization

**C Driver:**

```c
// Multiple steps required
if (IT8951_Init() != 0) {
    printf("IT8951_Init error\n");
    return -1;
}

// Get device info
IT8951GetSystemInfo(&gstI80DevInfo);

// Set VCOM
IT8951SetVCOM(vcom_value);
```

**Python Driver:**

```python
# Single-step initialization with context manager
with EPaperDisplay(vcom=-1.45) as display:
    width, height = display.init()
    # Display ready to use
```

### 3. Error Handling

**C Driver:**

```c
// Return codes
if (IT8951WriteReg(LISAR, addr) != 0) {
    return -1;  // Generic error
}
```

**Python Driver:**

```python
# Exceptions with context
try:
    display.display_image(image)
except IT8951TimeoutError as e:
    print(f"Timeout: {e}")
except IT8951MemoryError as e:
    print(f"Memory issue: {e}")
```

## API Mapping

### Core Functions

| C Function | Python Equivalent | Notes |
|------------|------------------|-------|
| `IT8951_Init()` | `EPaperDisplay.__init__()` | Includes SPI setup |
| `IT8951GetSystemInfo()` | `display.init()` | Returns width, height |
| `IT8951SetVCOM()` | `EPaperDisplay(vcom=...)` | Set during init |
| `IT8951LoadImgStart()` | `display.display_image()` | Unified API |
| `IT8951LoadImgAreaStart()` | `display.display_image(x=, y=)` | Position params |
| `IT8951LoadImgEnd()` | N/A | Handled automatically |
| `IT8951DisplayArea()` | `display.display_image()` | Single method |
| `IT8951DisplayAreaBuf()` | `display.display_image()` | Same method |
| `IT8951Sleep()` | `display.sleep()` | Power management |
| `IT8951SystemRun()` | `display.wake()` | Wake from sleep |

### Display Modes

| C Define | Python Enum | Usage |
|----------|-------------|-------|
| `IT8951_MODE_INIT` | `DisplayMode.INIT` | Full refresh |
| `IT8951_MODE_DU` | `DisplayMode.DU` | Direct update |
| `IT8951_MODE_GC16` | `DisplayMode.GC16` | 16-level grayscale |
| `IT8951_MODE_GL16` | `DisplayMode.GL16` | 16-level with flashing |
| `IT8951_MODE_A2` | `DisplayMode.A2` | 2-level fast |
| `IT8951_MODE_DU4` | `DisplayMode.DU4` | 4-level fast |

### Pixel Formats

| C Define | Python Enum | Bits per pixel |
|----------|-------------|----------------|
| `IT8951_8BPP` | `PixelFormat.BPP_8` | 8 |
| `IT8951_4BPP` | `PixelFormat.BPP_4` | 4 |
| `IT8951_2BPP` | `PixelFormat.BPP_2` | 2 |
| `IT8951_1BPP` | `PixelFormat.BPP_1` | 1 |

## Code Examples

### Basic Display Update

**C Driver:**

```c
// Load and display image
IT8951LoadImgStart(&gstI80DevInfo, &stAreaImgInfo);
IT8951WaitForReady();

// Send image data
for (i = 0; i < height; i++) {
    IT8951LoadImgData(&gstI80DevInfo,
                      &image_buffer[i * width],
                      width);
}

IT8951LoadImgEnd(&gstI80DevInfo);

// Display the image
IT8951DisplayArea(&gstI80DevInfo,
                  0, 0, width, height,
                  IT8951_MODE_GC16);
```

**Python Driver:**

```python
# Load and display image - all in one call
display.display_image(image_array, mode=DisplayMode.GC16)
```

### Partial Update

**C Driver:**

```c
IT8951AreaImgInfo stAreaImgInfo;
stAreaImgInfo.usX = 100;
stAreaImgInfo.usY = 100;
stAreaImgInfo.usWidth = 200;
stAreaImgInfo.usHeight = 200;

IT8951LoadImgAreaStart(&gstI80DevInfo, &stAreaImgInfo, &stAreaInfo);
// ... load data ...
IT8951DisplayArea(&gstI80DevInfo, 100, 100, 200, 200, IT8951_MODE_DU);
```

**Python Driver:**

```python
# Single call with position parameters
display.display_image(partial_image, x=100, y=100, mode=DisplayMode.DU)
```

### Memory Management

**C Driver:**

```c
// Allocate frame buffer
gpFrameBuf = malloc(gstI80DevInfo.usPanelW * gstI80DevInfo.usPanelH);
if (!gpFrameBuf) {
    printf("malloc error!\n");
    return -1;
}

// Use buffer
memset(gpFrameBuf, 0xFF, panel_size);

// Clean up
free(gpFrameBuf);
```

**Python Driver:**

```python
# NumPy handles memory automatically
frame_buffer = np.ones((height, width), dtype=np.uint8) * 255

# Or use buffer pool for efficiency
from IT8951_ePaper_Py.buffer_pool import BufferPool
pool = BufferPool(max_buffers=5, buffer_size=width * height)

with pool.get_buffer() as buffer:
    # Use buffer
    pass  # Automatically returned to pool
```

### Power Management

**C Driver:**

```c
// Enter sleep mode
IT8951Sleep();

// Wake up
IT8951SystemRun();
IT8951WaitForReady();
```

**Python Driver:**

```python
# Manual control
display.sleep()
display.wake()

# Or automatic with timeout
display.set_auto_sleep_timeout(30.0)  # Sleep after 30s
```

## Feature Comparison

### Enhanced Features in Python Driver

| Feature | C Driver | Python Driver |
|---------|----------|---------------|
| Memory Safety | Manual | Automatic with bounds checking |
| Thread Safety | Not provided | `ThreadSafeEPaperDisplay` wrapper |
| Error Recovery | Basic | Retry policies, detailed exceptions |
| Progressive Loading | No | Yes, for large images |
| Buffer Pooling | No | Yes, `BufferPool` class |
| Debug Mode | Printf | Configurable debug levels |
| Performance Profiling | No | Built-in decorators |
| Auto-sleep | No | Yes, with timeout |
| VCOM Validation | Basic | Range checking with warnings |
| A2 Mode Protection | No | Automatic refresh counter |

### Feature Parity

Both drivers support:

- All display modes (INIT, DU, GC16, GL16, A2, DU4, GLR16, GLD16)
- All bit depths (1bpp, 2bpp, 4bpp, 8bpp)
- Partial updates
- Temperature reading
- Register access
- Enhanced driving mode
- Endian conversion

## Performance Considerations

### Speed Optimizations

**C Driver** typically faster for:

- Raw data transfer (direct memory access)
- Minimal overhead operations
- Real-time applications

**Python Driver** optimizations:

```python
# Use 4bpp for 2x faster transfers
display.display_image(image, pixel_format=PixelFormat.BPP_4)

# NumPy acceleration for pixel packing
# 20-50x faster than pure Python

# Adjust SPI speed
display = EPaperDisplay(vcom=-1.45, spi_speed=24_000_000)  # 24MHz
```

### Memory Usage

**C Driver:**

- Manual allocation
- Minimal overhead
- Risk of leaks

**Python Driver:**

- Higher baseline memory
- Automatic garbage collection
- Memory monitoring available:

```python
from IT8951_ePaper_Py.memory_monitor import MemoryMonitor

monitor = MemoryMonitor()
monitor.start_monitoring()
# ... operations ...
print(f"Peak memory: {monitor.get_peak_memory() / 1024 / 1024:.2f} MB")
```

## Common Migration Patterns

### 1. Initialization Sequence

Replace C initialization:

```c
// C pattern
if (IT8951_Init() != 0) return -1;
IT8951GetSystemInfo(&gstI80DevInfo);
gulImgBufAddr = gstI80DevInfo.usImgBufAddrL |
                (gstI80DevInfo.usImgBufAddrH << 16);
IT8951SetVCOM(vcom);
```

With Python:

```python
# Python pattern
display = EPaperDisplay(vcom=-1.45)
width, height = display.init()
# Buffer address handled internally
```

### 2. Image Loading Pattern

Replace C loading:

```c
// C pattern
IT8951WaitForReady();
IT8951LoadImgStart(&gstI80DevInfo, &stAreaImgInfo);
for (i = 0; i < lines; i++) {
    IT8951LoadImgData(&gstI80DevInfo, &data[i * width], width);
}
IT8951LoadImgEnd(&gstI80DevInfo);
```

With Python:

```python
# Python pattern - automatic chunking if needed
display.display_image(image_array)
```

### 3. Error Handling Pattern

Replace C error checking:

```c
// C pattern
if (result != 0) {
    printf("Error occurred\n");
    return -1;
}
```

With Python exceptions:

```python
# Python pattern
from IT8951_ePaper_Py.retry_policy import retry, RetryPolicy

@retry(RetryPolicy(max_attempts=3))
def safe_display():
    display.display_image(image)
```

### 4. Resource Cleanup

Replace C cleanup:

```c
// C pattern
cleanup:
    if (gpFrameBuf) free(gpFrameBuf);
    if (spi_fd >= 0) close(spi_fd);
    return result;
```

With Python context managers:

```python
# Python pattern - automatic cleanup
with EPaperDisplay(vcom=-1.45) as display:
    # Use display
    pass
# Resources automatically released
```

## Migration Checklist

- [ ] Replace manual memory management with NumPy arrays
- [ ] Convert error codes to exception handling
- [ ] Update display mode constants to Python enums
- [ ] Simplify initialization to single EPaperDisplay creation
- [ ] Remove manual LoadImgStart/End calls
- [ ] Add proper VCOM value during initialization
- [ ] Consider thread safety requirements
- [ ] Implement retry policies for reliability
- [ ] Use context managers for resource management
- [ ] Enable debug mode during migration for troubleshooting

## Getting Help

1. Review the [examples directory](../examples/) for Python patterns
2. Check [hardware setup guide](HARDWARE_SETUP.md) for connection issues
3. Use debug mode for detailed operation logging:

   ```python
   from IT8951_ePaper_Py.debug_mode import DebugMode, DebugLevel

   with DebugMode(DebugLevel.DEBUG):
       display.display_image(image)
   ```

4. Report issues at: <https://github.com/stevenaleung/IT8951>
