"""Buffer pool manager for optimizing memory allocations in hot paths.

This module provides a simple buffer pool to reuse memory allocations
for frequently used operations like clearing the display or image conversions.

Note: Due to Python limitations, bytes/bytearray objects cannot be weakly referenced,
so we use strong references with manual pool size management.
"""

import threading
import weakref
from collections import defaultdict
from collections.abc import Callable
from types import TracebackType
from typing import ClassVar, Generic, TypeVar

import numpy as np
from numpy.typing import DTypeLike, NDArray

# Type variable for buffer types
BufferT = TypeVar("BufferT", bytes, NDArray[np.generic])


class BufferPool:
    """Thread-safe buffer pool for reusing memory allocations.

    This class maintains pools of pre-allocated buffers to reduce memory
    allocation overhead in hot paths. Uses strong references for bytes
    and weak references for numpy arrays.

    Thread Safety:
        This class is thread-safe. All operations use a lock to ensure
        concurrent access doesn't corrupt the pool state.
    """

    # Class-level pools shared across all instances
    _byte_pools: ClassVar[defaultdict[int, list[bytes]]] = defaultdict(list)
    _array_pools: ClassVar[defaultdict[str, list[weakref.ref[NDArray[np.generic]]]]] = defaultdict(
        list
    )
    _lock: ClassVar[threading.Lock] = threading.Lock()

    # Maximum number of buffers to keep per size
    MAX_POOL_SIZE: ClassVar[int] = 5

    @classmethod
    def get_bytes_buffer(cls, size: int, fill_value: int | None = None) -> bytes:
        """Get a bytes buffer from the pool or create a new one.

        Args:
            size: Size of the buffer in bytes.
            fill_value: If provided, fill the buffer with this value (0-255).
                       If None, buffer contents are undefined.

        Returns:
            A bytes object of the requested size.
        """
        with cls._lock:
            pool = cls._byte_pools[size]

            # Try to reuse a buffer from the pool
            if pool and fill_value is None:
                # Only reuse if we don't need a specific fill value
                return pool.pop()

            # Create a new buffer
            if fill_value is not None:
                return bytes([fill_value]) * size
            return bytes(size)

    @classmethod
    def return_bytes_buffer(cls, buffer: bytes) -> None:
        """Return a bytes buffer to the pool for reuse.

        Args:
            buffer: The buffer to return to the pool.
        """
        with cls._lock:
            size = len(buffer)
            pool = cls._byte_pools[size]

            # Only keep up to MAX_POOL_SIZE buffers
            if len(pool) < cls.MAX_POOL_SIZE:
                pool.append(buffer)

    @classmethod
    def get_array_buffer(
        cls, shape: tuple[int, ...], dtype: DTypeLike = np.uint8, fill_value: int | None = None
    ) -> NDArray[np.generic]:
        """Get a numpy array buffer from the pool or create a new one.

        Args:
            shape: Shape of the array.
            dtype: Data type of the array.
            fill_value: If provided, fill the array with this value.
                       If None, array contents are undefined.

        Returns:
            A numpy array of the requested shape and dtype.
        """
        with cls._lock:
            # Use string key to avoid type issues
            key = f"{shape}_{dtype}"
            pool = cls._array_pools[key]

            # Try to find a live buffer in the pool
            while pool:
                ref = pool.pop(0)
                array = ref()
                if array is not None:
                    if fill_value is not None:
                        array.fill(fill_value)
                    return array

            # No suitable buffer found, create a new one
            if fill_value is not None:
                return np.full(shape, fill_value, dtype=dtype)
            return np.empty(shape, dtype=dtype)

    @classmethod
    def return_array_buffer(cls, array: NDArray[np.generic]) -> None:
        """Return a numpy array buffer to the pool for reuse.

        Args:
            array: The array to return to the pool.
        """
        with cls._lock:
            key = f"{array.shape}_{array.dtype}"
            pool = cls._array_pools[key]

            # Only keep up to MAX_POOL_SIZE buffers
            if len(pool) < cls.MAX_POOL_SIZE:
                pool.append(weakref.ref(array))

    @classmethod
    def clear_pools(cls) -> None:
        """Clear all buffer pools, releasing memory."""
        with cls._lock:
            cls._byte_pools.clear()
            cls._array_pools.clear()


class ManagedBuffer(Generic[BufferT]):
    """Context manager for automatic buffer return to pool.

    Usage:
        with ManagedBuffer.bytes(size, fill_value=0xFF) as buffer:
            # Use buffer
            pass
        # Buffer automatically returned to pool
    """

    def __init__(
        self,
        buffer: BufferT,
        pool_return_func: Callable[[BufferT], None],
        buffer_type: type[BufferT],
    ) -> None:
        """Initialize the managed buffer."""
        self.buffer = buffer
        self.pool_return_func = pool_return_func
        self.buffer_type = buffer_type

    def __enter__(self) -> BufferT:
        """Enter the context manager."""
        return self.buffer

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> bool:
        """Exit the context manager and return buffer to pool."""
        # Return buffer to pool on exit
        self.pool_return_func(self.buffer)
        return False

    @classmethod
    def bytes(cls, size: int, fill_value: int | None = None) -> "ManagedBuffer[bytes]":
        """Create a managed bytes buffer.

        Args:
            size: Size of the buffer in bytes.
            fill_value: Optional fill value (0-255).

        Returns:
            ManagedBuffer context manager.
        """
        buffer = BufferPool.get_bytes_buffer(size, fill_value)
        # Create instance with explicit type to help inference
        instance: ManagedBuffer[bytes] = ManagedBuffer(
            buffer, BufferPool.return_bytes_buffer, bytes
        )
        return instance

    @classmethod
    def array(
        cls, shape: tuple[int, ...], dtype: DTypeLike = np.uint8, fill_value: int | None = None
    ) -> "ManagedBuffer[NDArray[np.generic]]":
        """Create a managed numpy array buffer.

        Args:
            shape: Shape of the array.
            dtype: Data type of the array.
            fill_value: Optional fill value.

        Returns:
            ManagedBuffer context manager.
        """
        buffer = BufferPool.get_array_buffer(shape, dtype, fill_value)
        # Create instance with explicit type to help inference
        instance: ManagedBuffer[NDArray[np.generic]] = ManagedBuffer(
            buffer, BufferPool.return_array_buffer, np.ndarray
        )
        return instance
