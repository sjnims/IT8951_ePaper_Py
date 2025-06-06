# IT8951 E-Paper Driver Best Practices

This guide covers best practices for using the IT8951 e-paper Python driver effectively, safely, and efficiently.

## Table of Contents

- [Display Management](#display-management)
- [Performance Optimization](#performance-optimization)
- [Memory Management](#memory-management)
- [Error Handling](#error-handling)
- [Power Management](#power-management)
- [Image Processing](#image-processing)
- [Production Deployment](#production-deployment)
- [Common Patterns](#common-patterns)

## Display Management

### Always Use Correct VCOM

The VCOM voltage is critical for display quality and longevity:

```python
# ❌ BAD: Using default or guessed VCOM
display = EPaperDisplay(vcom=-2.0)  # Generic value

# ✅ GOOD: Use YOUR display's specific VCOM
display = EPaperDisplay(vcom=-1.45)  # From FPC cable

# ✅ BETTER: Validate and log VCOM
actual_vcom = display.get_vcom()
if abs(actual_vcom - (-1.45)) > 0.05:
    print(f"Warning: VCOM mismatch! Set: -1.45V, Actual: {actual_vcom}V")
```

### Choose Appropriate Display Modes

Match display mode to content type:

```python
# ✅ Text and line art - fast binary mode
display.display_image(text_image, mode=DisplayMode.A2)

# ✅ UI updates - direct update mode
display.display_image(ui_element, mode=DisplayMode.DU)

# ✅ Photos and gradients - high quality mode
display.display_image(photo, mode=DisplayMode.GC16)

# ✅ Full refresh periodically
if display._a2_counter >= 5:
    display.clear()  # Uses INIT mode
```

### Handle A2 Mode Carefully

A2 mode accumulates artifacts - use auto-clear:

```python
# ✅ Set automatic clearing
display = EPaperDisplay(vcom=-1.45, a2_clear_threshold=10)

# ✅ Monitor A2 usage
print(f"A2 updates: {display._a2_counter}/{display._a2_clear_threshold}")

# ✅ Force clear when needed
if quality_degraded:
    display.clear()
```

## Performance Optimization

### Use Optimal Bit Depth

Choose bit depth based on content:

```python
# ✅ Binary content (text, QR codes) - 1bpp
binary_image = (grayscale > 128) * 255
display.display_image(binary_image, pixel_format=PixelFormat.BPP_1)

# ✅ Simple graphics - 4bpp (default, 2x faster than 8bpp)
display.display_image(logo, pixel_format=PixelFormat.BPP_4)

# ✅ Photos only when needed - 8bpp
display.display_image(photo, pixel_format=PixelFormat.BPP_8)
```

### Optimize SPI Speed

Set SPI speed based on your Raspberry Pi:

```python
# ✅ Auto-detect (recommended)
display = EPaperDisplay(vcom=-1.45)  # Uses optimal speed

# ✅ Manual override for specific models
# Pi 4: up to 24MHz
display = EPaperDisplay(vcom=-1.45, spi_speed=24_000_000)

# Pi 3: up to 12MHz
display = EPaperDisplay(vcom=-1.45, spi_speed=12_000_000)

# Debugging: slow speed
display = EPaperDisplay(vcom=-1.45, spi_speed=2_000_000)
```

### Minimize Update Regions

Update only what changed:

```python
# ❌ BAD: Full screen update for small change
display.display_image(entire_screen)

# ✅ GOOD: Partial update
display.display_image(
    clock_region,
    x=700, y=50,
    mode=DisplayMode.DU  # Fast for clock updates
)

# ✅ BETTER: Track dirty regions
class DirtyRegionTracker:
    def __init__(self):
        self.regions = []

    def mark_dirty(self, x: int, y: int, w: int, h: int):
        self.regions.append((x, y, w, h))

    def update_all(self, display: EPaperDisplay):
        for x, y, w, h in self.regions:
            region = self.screen[y:y+h, x:x+w]
            display.display_image(region, x=x, y=y, mode=DisplayMode.DU)
        self.regions.clear()
```

## Memory Management

### Use Buffer Pools

Reuse buffers for repeated operations:

```python
from IT8951_ePaper_Py.buffer_pool import BufferPool

# ✅ Create pool for your use case
pool = BufferPool(
    max_buffers=3,
    buffer_size=800 * 600  # Full screen buffer
)

# ✅ Use buffers efficiently
def process_frames(frames: list[np.ndarray]) -> None:
    for frame in frames:
        with pool.get_buffer() as buffer:
            # Process into buffer
            np.copyto(buffer[:frame.size], frame.flat)
            # Buffer automatically returned
```

### Monitor Memory Usage

Track memory in production:

```python
from IT8951_ePaper_Py.memory_monitor import MemoryMonitor

# ✅ Profile memory usage
monitor = MemoryMonitor()
monitor.start_monitoring()

# Your operations
display.display_image(large_image)

peak = monitor.get_peak_memory()
print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")

# ✅ Set thresholds
if peak > 100 * 1024 * 1024:  # 100MB
    logger.warning("High memory usage detected")
```

### Handle Large Images

Use progressive loading for oversized images:

```python
# ✅ Let the driver handle it
try:
    # Driver automatically uses progressive loading if needed
    display.display_image(very_large_image)
except IT8951MemoryError as e:
    # Fall back to manual chunking
    chunk_size = 100
    for y in range(0, height, chunk_size):
        chunk = very_large_image[y:y+chunk_size]
        display.display_image(chunk, y=y)
```

## Error Handling

### Use Retry Policies

Handle transient failures gracefully:

```python
from IT8951_ePaper_Py.retry_policy import RetryPolicy, retry

# ✅ Configure retry policy
policy = RetryPolicy(
    max_attempts=3,
    initial_delay=0.1,
    max_delay=1.0,
    exponential_base=2.0
)

# ✅ Apply to critical operations
@retry(policy)
def reliable_update(display: EPaperDisplay, image: np.ndarray):
    display.display_image(image)

# ✅ Custom handling for specific errors
try:
    reliable_update(display, image)
except IT8951TimeoutError:
    # SPI communication issue
    display._controller.reset()
except IT8951MemoryError:
    # Try with lower bit depth
    display.display_image(image, pixel_format=PixelFormat.BPP_4)
```

### Implement Graceful Degradation

Fall back when features fail:

```python
# ✅ Quality degradation chain
def smart_display(display: EPaperDisplay, image: np.ndarray):
    modes = [
        (DisplayMode.GC16, PixelFormat.BPP_8),  # Best quality
        (DisplayMode.GL16, PixelFormat.BPP_4),  # Good quality
        (DisplayMode.DU, PixelFormat.BPP_4),    # Fast update
        (DisplayMode.A2, PixelFormat.BPP_1),    # Emergency
    ]

    for mode, pixel_format in modes:
        try:
            display.display_image(image, mode=mode, pixel_format=pixel_format)
            return
        except IT8951Error as e:
            logger.warning(f"Failed with {mode}: {e}")

    raise IT8951Error("All display modes failed")
```

## Power Management

### Use Context Managers

Ensure proper cleanup:

```python
# ✅ Automatic power management
with EPaperDisplay(vcom=-1.45) as display:
    display.init()
    display.display_image(image)
    # Automatically enters sleep on exit

# ✅ Configure auto-sleep
with EPaperDisplay(vcom=-1.45) as display:
    display.init()
    display.set_auto_sleep_timeout(30.0)  # 30 seconds

    # Long-running application
    while running:
        if new_content:
            display.display_image(content)  # Auto-wakes
        time.sleep(1)
```

### Optimize for Battery Life

Power-saving strategies:

```python
# ✅ Aggressive power management
class BatteryOptimizedDisplay:
    def __init__(self, vcom: float):
        self.display = EPaperDisplay(vcom=vcom)
        self.display.init()
        self.display.set_auto_sleep_timeout(10.0)  # Quick sleep
        self.last_update = time.time()

    def update_if_needed(self, image: np.ndarray, force: bool = False):
        # Batch updates
        if not force and time.time() - self.last_update < 60:
            return

        # Use fast modes when on battery
        if self.on_battery():
            self.display.display_image(image, mode=DisplayMode.DU)
        else:
            self.display.display_image(image, mode=DisplayMode.GC16)

        self.last_update = time.time()

    def on_battery(self) -> bool:
        # Check power source
        return not os.path.exists("/sys/class/power_supply/AC/online")
```

## Image Processing

### Prepare Images Correctly

Optimize images before display:

```python
# ✅ Resize to exact display dimensions
from PIL import Image

def prepare_image(image_path: str, display: EPaperDisplay) -> np.ndarray:
    img = Image.open(image_path)

    # Convert to grayscale
    if img.mode != 'L':
        img = img.convert('L')

    # Resize to display size
    img = img.resize((display.width, display.height), Image.Resampling.LANCZOS)

    # Convert to numpy array
    return np.array(img, dtype=np.uint8)

# ✅ Dithering for better quality with limited bit depth
def dither_for_display(image: np.ndarray, levels: int = 16) -> np.ndarray:
    # Floyd-Steinberg dithering
    from PIL import Image
    img = Image.fromarray(image, mode='L')

    # Reduce to target levels
    img = img.quantize(levels)
    img = img.convert('L')

    return np.array(img, dtype=np.uint8)
```

### Handle Different Content Types

Optimize for content:

```python
# ✅ Text rendering
def render_text(text: str, font_size: int = 24) -> np.ndarray:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new('L', (800, 600), 255)
    draw = ImageDraw.Draw(img)

    # Use bitmap font for sharp rendering
    font = ImageFont.truetype("DejaVuSans.ttf", font_size)
    draw.text((10, 10), text, font=font, fill=0)

    return np.array(img, dtype=np.uint8)

# ✅ QR code generation
def generate_qr(data: str) -> np.ndarray:
    import qrcode

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    return np.array(img.convert('L'), dtype=np.uint8)
```

## Production Deployment

### Implement Health Checks

Monitor display health:

```python
class DisplayHealthMonitor:
    def __init__(self, display: EPaperDisplay):
        self.display = display
        self.error_count = 0
        self.last_successful_update = time.time()

    def health_check(self) -> dict[str, Any]:
        """Comprehensive health check."""
        try:
            # Check device status
            status = self.display.get_device_status()

            # Check temperature
            temp = status['temperature']
            temp_ok = 15 <= temp <= 35

            # Check last update time
            time_since_update = time.time() - self.last_successful_update
            update_ok = time_since_update < 300  # 5 minutes

            # Check VCOM
            vcom_ok = abs(self.display.get_vcom() - self.display._vcom) < 0.1

            return {
                'healthy': temp_ok and update_ok and vcom_ok,
                'temperature': temp,
                'temperature_ok': temp_ok,
                'last_update_seconds': time_since_update,
                'update_ok': update_ok,
                'vcom_ok': vcom_ok,
                'error_count': self.error_count,
                'power_state': status['power_state']
            }

        except Exception as e:
            self.error_count += 1
            return {
                'healthy': False,
                'error': str(e),
                'error_count': self.error_count
            }
```

### Use Thread Safety

For multi-threaded applications:

```python
from IT8951_ePaper_Py.thread_safe import ThreadSafeEPaperDisplay

# ✅ Thread-safe wrapper
display = ThreadSafeEPaperDisplay(vcom=-1.45)

# ✅ Use in multiple threads safely
def worker_thread(display: ThreadSafeEPaperDisplay, region: int):
    while True:
        image = generate_content(region)
        x = region * 200
        display.display_image(image, x=x, y=0)
        time.sleep(60)

# Start workers
threads = []
for i in range(4):
    t = threading.Thread(target=worker_thread, args=(display, i))
    t.start()
    threads.append(t)
```

### Implement Logging

Track operations in production:

```python
import logging
from IT8951_ePaper_Py.debug_mode import DebugMode, DebugLevel

# ✅ Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('epaper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('epaper')

# ✅ Wrap operations with logging
def logged_display_update(display: EPaperDisplay, image: np.ndarray, **kwargs):
    start_time = time.time()

    try:
        with DebugMode(DebugLevel.INFO):
            display.display_image(image, **kwargs)

        duration = time.time() - start_time
        logger.info(f"Display updated successfully in {duration:.2f}s")

    except Exception as e:
        logger.error(f"Display update failed: {e}", exc_info=True)
        raise
```

## Common Patterns

### Dashboard Updates

For information displays:

```python
class DashboardDisplay:
    def __init__(self, display: EPaperDisplay):
        self.display = display
        self.regions = {
            'time': (700, 0, 100, 50),
            'weather': (0, 0, 200, 100),
            'news': (0, 100, 800, 400),
            'status': (0, 500, 800, 100)
        }
        self.update_intervals = {
            'time': 60,      # 1 minute
            'weather': 600,  # 10 minutes
            'news': 1800,    # 30 minutes
            'status': 300    # 5 minutes
        }
        self.last_updates = {k: 0 for k in self.regions}

    def update(self):
        current_time = time.time()

        for region, interval in self.update_intervals.items():
            if current_time - self.last_updates[region] >= interval:
                self.update_region(region)
                self.last_updates[region] = current_time

    def update_region(self, region: str):
        x, y, w, h = self.regions[region]
        content = self.generate_content(region)

        # Use appropriate mode for region
        if region == 'time':
            mode = DisplayMode.DU  # Fast for clock
        elif region == 'weather':
            mode = DisplayMode.GL16  # Icons need quality
        else:
            mode = DisplayMode.GC16  # High quality

        self.display.display_image(content, x=x, y=y, mode=mode)
```

### Image Gallery

For photo frames:

```python
class PhotoFrame:
    def __init__(self, display: EPaperDisplay, photo_dir: str):
        self.display = display
        self.photo_dir = photo_dir
        self.photos = list(Path(photo_dir).glob("*.jpg"))
        self.current_index = 0

    def show_next(self):
        if not self.photos:
            return

        # Load and prepare image
        photo_path = self.photos[self.current_index]
        image = prepare_image(str(photo_path), self.display)

        # Dither for better 4bpp quality
        image = dither_for_display(image, levels=16)

        # Display with high quality
        self.display.display_image(
            image,
            mode=DisplayMode.GC16,
            pixel_format=PixelFormat.BPP_4
        )

        # Move to next
        self.current_index = (self.current_index + 1) % len(self.photos)

    def run(self, interval: int = 300):
        """Run photo frame with specified interval (seconds)."""
        while True:
            self.show_next()

            # Sleep display between updates
            self.display.sleep()
            time.sleep(interval)

            # Wake for next update
            self.display.wake()
```

### E-Reader Interface

For text display:

```python
class EReader:
    def __init__(self, display: EPaperDisplay):
        self.display = display
        self.font_size = 18
        self.line_height = 25
        self.margin = 50
        self.lines_per_page = (display.height - 2 * self.margin) // self.line_height

    def display_page(self, text: str, page: int = 0):
        lines = self.wrap_text(text)
        start = page * self.lines_per_page
        end = start + self.lines_per_page
        page_lines = lines[start:end]

        # Create page image
        img = Image.new('L', (self.display.width, self.display.height), 255)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("DejaVuSans.ttf", self.font_size)

        y = self.margin
        for line in page_lines:
            draw.text((self.margin, y), line, font=font, fill=0)
            y += self.line_height

        # Display with fast mode for page turns
        self.display.display_image(
            np.array(img, dtype=np.uint8),
            mode=DisplayMode.DU,
            pixel_format=PixelFormat.BPP_1
        )
```

## Summary

Key takeaways for best practices:

1. **Always use correct VCOM** - Check your display's FPC cable
2. **Choose appropriate display modes** - Match mode to content
3. **Optimize bit depth** - Use lowest depth that maintains quality
4. **Handle errors gracefully** - Use retry policies and fallbacks
5. **Manage power efficiently** - Use sleep modes and auto-timeouts
6. **Monitor health in production** - Implement comprehensive checks
7. **Use thread safety when needed** - ThreadSafeEPaperDisplay wrapper
8. **Profile and optimize** - Monitor memory and performance

Following these practices will ensure reliable, efficient, and high-quality operation of your e-paper display.
