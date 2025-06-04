# Thread Safety Guide

This document explains the thread safety guarantees and usage patterns for the IT8951 e-paper Python driver.

## Overview

The IT8951 controller and SPI communication protocol are inherently **not thread-safe**. The hardware expects sequential operations and does not support concurrent access. To address this limitation in multi-threaded applications, we provide an optional thread-safe wrapper class.

## Thread Safety Status

### Not Thread-Safe (Default)

- `EPaperDisplay` - The main display class
- `IT8951` - Low-level controller interface
- `SPIInterface` and implementations - Hardware communication layer

### Thread-Safe

- `ThreadSafeEPaperDisplay` - Optional wrapper with automatic synchronization
- `BufferPool` - Memory buffer management (internal use)

## Using ThreadSafeEPaperDisplay

The `ThreadSafeEPaperDisplay` class provides a drop-in replacement for `EPaperDisplay` with automatic thread synchronization:

```python
from IT8951_ePaper_Py import ThreadSafeEPaperDisplay
import threading

# Create a thread-safe display instance
display = ThreadSafeEPaperDisplay(vcom=-2.0)

# Initialize the display
width, height = display.init()

# Can be safely used from multiple threads
def update_region(x, y, image):
    display.display_partial(image, x, y)

# Create multiple threads
threads = []
for i in range(4):
    t = threading.Thread(
        target=update_region,
        args=(i * 100, i * 100, test_image)
    )
    threads.append(t)
    t.start()

# Wait for all threads
for t in threads:
    t.join()
```

## How It Works

### Reentrant Lock (RLock)

The thread-safe wrapper uses Python's `threading.RLock()` to ensure:

1. **Mutual Exclusion**: Only one thread can execute display operations at a time
2. **Reentrancy**: The same thread can acquire the lock multiple times (nested calls)
3. **Automatic Release**: Lock is released even if exceptions occur

### Method Wrapping

All public methods are wrapped with the `@thread_safe_method` decorator:

```python
@thread_safe_method
def display_image(self, img, x=0, y=0, ...):
    return super().display_image(img, x, y, ...)
```

This ensures every operation acquires the lock before execution.

## Thread Safety Guarantees

### What IS Guaranteed

1. **Atomicity**: Each method call completes without interruption
2. **Sequential Consistency**: Operations from different threads are serialized
3. **No Data Corruption**: Internal state remains consistent
4. **Exception Safety**: Lock is released even on errors

### What is NOT Guaranteed

1. **Performance**: Thread safety adds overhead from lock acquisition
2. **Fairness**: No guarantee about thread execution order
3. **Deadlock Prevention**: User must avoid circular dependencies
4. **Real-time Response**: Operations may be delayed waiting for lock

## Best Practices

### 1. Single Display Instance

Create one display instance and share it among threads:

```python
# Good - Single shared instance
display = ThreadSafeEPaperDisplay(vcom=-2.0)

def worker(display, data):
    display.display_image(data)

# Bad - Multiple instances (hardware conflict)
def worker(data):
    display = ThreadSafeEPaperDisplay(vcom=-2.0)  # Don't do this!
    display.display_image(data)
```

### 2. Minimize Lock Duration

Keep operations short to reduce contention:

```python
# Good - Prepare data outside lock
image = prepare_complex_image()  # Do this outside
display.display_image(image)      # Quick operation

# Bad - Long operations while holding lock
display.display_image(
    generate_complex_image()  # Slow operation blocks other threads
)
```

### 3. Use Context Manager

The context manager is thread-safe:

```python
with ThreadSafeEPaperDisplay(vcom=-2.0) as display:
    # Automatic initialization and cleanup
    display.display_image(image)
# Display properly closed even with multiple threads
```

### 4. Batch Operations

Reduce lock contention by batching updates:

```python
# Good - Single operation for multiple updates
def update_all_regions(display, updates):
    full_image = create_composite_image(updates)
    display.display_image(full_image)

# Less efficient - Many small operations
def update_each_region(display, updates):
    for region in updates:
        display.display_partial(region.image, region.x, region.y)
```

## Common Patterns

### Producer-Consumer Pattern

```python
import queue
import threading

def image_producer(image_queue):
    """Generate images to display."""
    for i in range(10):
        image = create_image(i)
        image_queue.put(image)
    image_queue.put(None)  # Sentinel

def image_consumer(display, image_queue):
    """Display images from queue."""
    while True:
        image = image_queue.get()
        if image is None:
            break
        display.display_image(image)
        image_queue.task_done()

# Setup
display = ThreadSafeEPaperDisplay(vcom=-2.0)
image_queue = queue.Queue(maxsize=5)

# Start threads
producer = threading.Thread(target=image_producer, args=(image_queue,))
consumer = threading.Thread(target=image_consumer, args=(display, image_queue))

producer.start()
consumer.start()

producer.join()
consumer.join()
```

### Periodic Updates

```python
import threading
import time

class DisplayUpdater:
    def __init__(self, display):
        self.display = display
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._update_loop)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _update_loop(self):
        while self.running:
            status = get_system_status()
            image = render_status(status)
            self.display.display_image(image)
            time.sleep(60)  # Update every minute

# Usage
display = ThreadSafeEPaperDisplay(vcom=-2.0)
updater = DisplayUpdater(display)
updater.start()
# ... do other work ...
updater.stop()
```

## Performance Considerations

### Lock Overhead

The thread-safe wrapper adds a small overhead:

- Lock acquisition: ~0.1-1 microseconds
- Negligible compared to SPI communication time
- Only impacts concurrent access scenarios

### Recommendations

1. **Single-threaded apps**: Use `EPaperDisplay` directly (no overhead)
2. **Multi-threaded apps**: Use `ThreadSafeEPaperDisplay`
3. **High-frequency updates**: Consider batching to reduce lock contention

## Troubleshooting

### Deadlock Detection

If your application hangs, check for:

1. **Circular Dependencies**: Thread A waits for B while B waits for A
2. **External Lock Conflicts**: Mixing display lock with other locks
3. **Blocking Operations**: Long operations inside display methods

### Debug Threading Issues

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Log thread activity
def logged_operation(display, name):
    logging.debug(f"{name}: Acquiring display lock")
    display.display_image(image)
    logging.debug(f"{name}: Released display lock")
```

## Implementation Details

### Lock Scope

The lock protects:

- All public display methods
- Property access (width, height, etc.)
- Context manager entry/exit

The lock does NOT protect:

- Static methods or class methods
- Private methods (called within locked public methods)
- External resources (files, network, etc.)

### Thread-Local Storage

The display does not use thread-local storage. All threads share:

- Display state (width, height, etc.)
- Hardware resources (SPI interface)
- Configuration (VCOM, refresh limits, etc.)

## Migration Guide

### From EPaperDisplay to ThreadSafeEPaperDisplay

```python
# Before (not thread-safe)
from IT8951_ePaper_Py import EPaperDisplay
display = EPaperDisplay(vcom=-2.0)

# After (thread-safe)
from IT8951_ePaper_Py import ThreadSafeEPaperDisplay
display = ThreadSafeEPaperDisplay(vcom=-2.0)
```

The API is identical - just change the import and class name.

### Adding Thread Safety to Existing Code

1. Replace `EPaperDisplay` with `ThreadSafeEPaperDisplay`
2. No other code changes required
3. Test with multiple threads to verify behavior

## Alternative Approaches (If Not Using ThreadSafeEPaperDisplay)

### Option 1: Single Display Thread

Create a dedicated thread for all display operations:

```python
import threading
import queue
from IT8951_ePaper_Py import EPaperDisplay

class DisplayThread(threading.Thread):
    def __init__(self, vcom):
        super().__init__()
        self.display = EPaperDisplay(vcom=vcom)
        self.command_queue = queue.Queue()
        self.daemon = True

    def run(self):
        self.display.init()

        while True:
            cmd, args, kwargs, result_event = self.command_queue.get()

            if cmd == "stop":
                break

            try:
                method = getattr(self.display, cmd)
                result = method(*args, **kwargs)
                result_event.set_result(result)
            except Exception as e:
                result_event.set_exception(e)
            finally:
                result_event.set()

    def execute(self, command, *args, **kwargs):
        result_event = threading.Event()
        result_event.result = None
        result_event.exception = None

        def set_result(r):
            result_event.result = r

        def set_exception(e):
            result_event.exception = e

        result_event.set_result = set_result
        result_event.set_exception = set_exception

        self.command_queue.put((command, args, kwargs, result_event))
        result_event.wait()

        if result_event.exception:
            raise result_event.exception
        return result_event.result

# Usage:
display_thread = DisplayThread(vcom=-2.0)
display_thread.start()

# From any thread:
display_thread.execute("clear")
display_thread.execute("display_image", image)
```

### Option 2: asyncio (Single Thread Concurrency)

Use asyncio for concurrent operations without threads:

```python
import asyncio
from IT8951_ePaper_Py import EPaperDisplay

class AsyncDisplay:
    def __init__(self, vcom):
        self._display = EPaperDisplay(vcom=vcom)
        self._lock = asyncio.Lock()

    async def init(self):
        async with self._lock:
            return await asyncio.to_thread(self._display.init)

    async def display_image(self, image):
        async with self._lock:
            return await asyncio.to_thread(self._display.display_image, image)

# Usage:
async def main():
    display = AsyncDisplay(vcom=-2.0)
    await display.init()

    # Concurrent async operations are serialized by the lock
    await asyncio.gather(
        display.display_image(image1),
        display.display_image(image2)
    )
```

## Why the Hardware Is Not Thread-Safe

### 1. Hardware Limitations

The IT8951 controller and SPI protocol have inherent limitations:

- **Stateful Protocol**: The IT8951 uses a command/data protocol where commands must be followed by the correct sequence of data. Interleaving operations from multiple threads corrupts this sequence.

- **Atomic Transactions**: SPI transactions require precise timing with chip select (CS) signals. Multiple threads can interfere with these critical sections.

- **Single Hardware Resource**: The e-paper display is a single physical device that cannot handle concurrent operations.

### 2. Specific Thread Safety Issues

#### SPI Communication

```python
# This sequence must be atomic:
spi.write_command(COMMAND)  # Thread A starts
# Thread B interrupts here!
spi.write_data(DATA)        # Thread A's data goes to Thread B's command!
```

#### Power State Management

```python
# Thread A puts display to sleep
display.sleep()

# Thread B tries to update
display.display_image(img)  # Fails - display is asleep!
```

#### Busy Waiting

```python
# Thread A starts an operation
display.clear()  # Starts clearing

# Thread B checks busy state
# Both threads now wait for busy signal!
```

## See Also

- [Examples: thread_safety_demo.py](../examples/thread_safety_demo.py) - Complete threading example
- [API Reference: ThreadSafeEPaperDisplay](../src/IT8951_ePaper_Py/thread_safe.py) - Implementation details
- [Python Threading Documentation](https://docs.python.org/3/library/threading.html) - Threading basics
