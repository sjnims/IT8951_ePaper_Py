# Thread Safety Guide

## Overview

The IT8951 e-paper driver is **NOT thread-safe**. This document explains why and provides guidance for multi-threaded applications.

## Why This Library Is Not Thread-Safe

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

## Solutions for Multi-Threaded Applications

### Option 1: Single Display Thread (Recommended)

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

### Option 2: Mutex Protection

Use a lock to protect all display operations:

```python
import threading
from IT8951_ePaper_Py import EPaperDisplay

class ThreadSafeDisplay:
    def __init__(self, vcom):
        self._display = EPaperDisplay(vcom=vcom)
        self._lock = threading.Lock()

    def __getattr__(self, name):
        # Delegate all calls to the display with locking
        attr = getattr(self._display, name)

        if callable(attr):
            def locked_method(*args, **kwargs):
                with self._lock:
                    return attr(*args, **kwargs)
            return locked_method
        else:
            return attr

# Usage:
display = ThreadSafeDisplay(vcom=-2.0)

# Can be called from any thread:
display.init()
display.clear()
display.display_image(image)
```

### Option 3: asyncio (Single Thread Concurrency)

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

## Best Practices

1. **Initialize Once**: Initialize the display in one thread and reuse the instance.

2. **Avoid Concurrent Power State Changes**: Don't call sleep/wake from different threads.

3. **Complete Operations**: Let display operations complete before starting new ones.

4. **Error Handling**: Thread safety issues often manifest as communication errors. Add proper error handling.

5. **Testing**: Test your multi-threaded code thoroughly. Race conditions can be intermittent.

## Common Pitfalls

### Context Manager Across Threads

```python
# DON'T DO THIS:
with EPaperDisplay(vcom=-2.0) as display:
    # Starting threads here that use display
    thread1 = Thread(target=use_display, args=(display,))
    thread2 = Thread(target=use_display, args=(display,))
# Context manager exits, display is closed while threads still running!
```

### Shared State Without Locking

```python
# DON'T DO THIS:
class MyApp:
    def __init__(self):
        self.display = EPaperDisplay(vcom=-2.0)

    def update_from_thread1(self):
        self.display.display_image(image1)  # No locking!

    def update_from_thread2(self):
        self.display.display_image(image2)  # Race condition!
```

## Conclusion

While the IT8951 driver is not thread-safe, you can safely use it in multi-threaded applications by:

1. Using a dedicated display thread (recommended)
2. Protecting all operations with a mutex
3. Using asyncio for single-threaded concurrency

Choose the approach that best fits your application's architecture and requirements.
