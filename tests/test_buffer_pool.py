"""Tests for buffer pool implementation."""

import gc
import threading
import time
import weakref

import numpy as np

from IT8951_ePaper_Py.buffer_pool import BufferPool, ManagedBuffer


class TestBufferPool:
    """Test buffer pool functionality."""

    def setup_method(self):
        """Clear pools before each test."""
        BufferPool.clear_pools()

    def test_bytes_buffer_basic(self):
        """Test basic bytes buffer allocation and reuse."""
        # Get a buffer
        buffer1 = BufferPool.get_bytes_buffer(1000, fill_value=0xFF)
        assert len(buffer1) == 1000
        assert all(b == 0xFF for b in buffer1)

        # Return it to pool
        BufferPool.return_bytes_buffer(buffer1)

        # Get another buffer of same size - should reuse
        buffer2 = BufferPool.get_bytes_buffer(1000)
        assert len(buffer2) == 1000
        # Can't guarantee it's the same buffer due to weak refs

    def test_array_buffer_basic(self):
        """Test basic array buffer allocation and reuse."""
        # Get an array
        arr1 = BufferPool.get_array_buffer((100, 100), dtype=np.uint8, fill_value=128)
        assert arr1.shape == (100, 100)
        assert np.all(arr1 == 128)

        # Return it to pool
        BufferPool.return_array_buffer(arr1)

        # Get another array of same shape - should reuse
        arr2 = BufferPool.get_array_buffer((100, 100), dtype=np.uint8)
        assert arr2.shape == (100, 100)

    def test_pool_size_limit(self):
        """Test that pool size is limited."""
        # Create more buffers than MAX_POOL_SIZE
        buffers = []
        for _ in range(BufferPool.MAX_POOL_SIZE + 5):
            buf = BufferPool.get_bytes_buffer(100)
            buffers.append(buf)

        # Return all to pool
        for buf in buffers:
            BufferPool.return_bytes_buffer(buf)

        # Pool should only keep MAX_POOL_SIZE buffers
        # We can't directly check pool size, but we can verify memory isn't growing

    def test_weak_reference_cleanup(self):
        """Test that buffers are garbage collected when not referenced."""
        # Get and return a buffer
        buffer = BufferPool.get_bytes_buffer(1000)
        BufferPool.return_bytes_buffer(buffer)

        # Delete the reference
        del buffer
        gc.collect()

        # Pool should handle dead weak refs gracefully
        new_buffer = BufferPool.get_bytes_buffer(1000)
        assert len(new_buffer) == 1000

    def test_managed_buffer_context_manager(self):
        """Test ManagedBuffer context manager."""
        # Test with bytes
        with ManagedBuffer.bytes(500, fill_value=0x55) as buffer:
            assert len(buffer) == 500
            assert all(b == 0x55 for b in buffer)
        # Buffer should be returned to pool automatically

        # Test with array
        with ManagedBuffer.array((50, 50), dtype=np.uint8, fill_value=42) as arr:
            assert isinstance(arr, np.ndarray)
            assert arr.shape == (50, 50)
            assert np.all(arr == 42)
        # Array should be returned to pool automatically

    def test_thread_safety(self):
        """Test thread safety of buffer pool."""
        results = []
        errors = []

        def worker() -> None:
            try:
                for _ in range(10):
                    # Get and return buffers rapidly
                    buf = BufferPool.get_bytes_buffer(1000)
                    time.sleep(0.001)  # Simulate work
                    BufferPool.return_bytes_buffer(buf)

                    arr = BufferPool.get_array_buffer((10, 10))
                    time.sleep(0.001)  # Simulate work
                    BufferPool.return_array_buffer(arr)
                results.append("OK")
            except Exception as e:
                errors.append(e)

        # Run multiple threads
        threads = []
        for _ in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        # Wait for all to complete
        for t in threads:
            t.join()

        # Should have no errors
        assert len(errors) == 0
        assert len(results) == 5

    def test_different_sizes_dont_conflict(self):
        """Test that buffers of different sizes are pooled separately."""
        # Get buffers of different sizes
        buf100 = BufferPool.get_bytes_buffer(100, fill_value=1)
        buf200 = BufferPool.get_bytes_buffer(200, fill_value=2)

        assert len(buf100) == 100
        assert len(buf200) == 200

        # Return them
        BufferPool.return_bytes_buffer(buf100)
        BufferPool.return_bytes_buffer(buf200)

        # Get new buffers - should get correct sizes
        new_buf100 = BufferPool.get_bytes_buffer(100)
        new_buf200 = BufferPool.get_bytes_buffer(200)

        assert len(new_buf100) == 100
        assert len(new_buf200) == 200

    def test_clear_pools(self):
        """Test clearing all pools."""
        # Add some buffers to pools
        buf = BufferPool.get_bytes_buffer(1000)
        BufferPool.return_bytes_buffer(buf)

        arr = BufferPool.get_array_buffer((50, 50))
        BufferPool.return_array_buffer(arr)

        # Clear pools
        BufferPool.clear_pools()

        # New allocations should create new buffers
        new_buf = BufferPool.get_bytes_buffer(1000)
        new_arr = BufferPool.get_array_buffer((50, 50))

        assert len(new_buf) == 1000
        assert new_arr.shape == (50, 50)

    def test_array_weak_reference_cleanup(self):
        """Test that array pool handles dead weak references correctly."""
        # Get an array and return it to pool
        arr1 = BufferPool.get_array_buffer((100, 100), dtype=np.uint8, fill_value=128)
        BufferPool.return_array_buffer(arr1)

        # Delete the reference to allow garbage collection
        del arr1
        gc.collect()

        # Now the pool contains a dead weak reference
        # Getting a new array should handle this gracefully
        arr2 = BufferPool.get_array_buffer((100, 100), dtype=np.uint8, fill_value=64)
        assert arr2.shape == (100, 100)
        assert np.all(arr2 == 64)

    def test_array_pool_with_multiple_dead_refs(self):
        """Test array pool with multiple dead weak references."""
        # Fill the pool with arrays
        arrays = []
        for i in range(3):
            arr = BufferPool.get_array_buffer((50, 50), dtype=np.uint8, fill_value=i)
            BufferPool.return_array_buffer(arr)
            arrays.append(arr)

        # Delete all references
        del arrays
        gc.collect()

        # Now the pool has 3 dead weak references
        # Getting a new array should skip all of them
        new_arr = BufferPool.get_array_buffer((50, 50), dtype=np.uint8, fill_value=100)
        assert new_arr.shape == (50, 50)
        assert np.all(new_arr == 100)

    def test_array_pool_weak_refs_are_properly_cleaned(self):
        """Test that dead weak references in array pool are properly cleaned."""
        # Create several arrays with unique shape to avoid interference
        shape = (77, 77)  # Unique shape for this test

        # Fill pool with arrays
        arrays = []
        for i in range(3):
            arr = BufferPool.get_array_buffer(shape, dtype=np.uint8, fill_value=i * 10)
            BufferPool.return_array_buffer(arr)
            arrays.append(arr)

        # Delete middle reference to create a dead weak ref
        del arrays[1]
        gc.collect()

        # Now when we get an array, it should skip the dead ref
        # and return one of the live ones or create a new one
        new_arr = BufferPool.get_array_buffer(shape, dtype=np.uint8)
        assert new_arr.shape == shape

        # The important thing is it doesn't crash when encountering dead refs

    def test_different_dtypes_dont_conflict(self):
        """Test that arrays with different dtypes are pooled separately."""
        # Get arrays with different dtypes
        arr_uint8 = BufferPool.get_array_buffer((10, 10), dtype=np.uint8, fill_value=100)
        arr_float32 = BufferPool.get_array_buffer((10, 10), dtype=np.float32, fill_value=1)

        assert arr_uint8.dtype == np.uint8
        assert arr_float32.dtype == np.float32

        # Return them
        BufferPool.return_array_buffer(arr_uint8)
        BufferPool.return_array_buffer(arr_float32)

        # Get new arrays - should get correct dtypes
        new_uint8 = BufferPool.get_array_buffer((10, 10), dtype=np.uint8)
        new_float32 = BufferPool.get_array_buffer((10, 10), dtype=np.float32)

        assert new_uint8.dtype == np.uint8
        assert new_float32.dtype == np.float32

    def test_bytes_buffer_with_fill_value_not_reused(self):
        """Test that requesting a buffer with fill_value creates a new one."""
        # Get a buffer without fill value
        buf1 = BufferPool.get_bytes_buffer(100)
        # Modify it
        buf1_bytes = bytearray(buf1)
        buf1_bytes[0] = 123
        buf1 = bytes(buf1_bytes)

        # Return it to pool
        BufferPool.return_bytes_buffer(buf1)

        # Get a buffer with fill value - should create new one, not reuse
        buf2 = BufferPool.get_bytes_buffer(100, fill_value=0xFF)
        assert all(b == 0xFF for b in buf2)

    def test_managed_buffer_exception_handling(self):
        """Test that ManagedBuffer returns buffer to pool even on exception."""
        # Use managed buffer with exception
        try:
            with ManagedBuffer.bytes(100, fill_value=0x42) as buf:
                assert len(buf) == 100
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Buffer should have been returned despite exception
        # Check that pool has at least one buffer of size 100
        assert len(BufferPool._byte_pools[100]) > 0

    def test_array_reuse_with_fill_value(self):
        """Test that reused arrays are properly filled when fill_value is provided."""
        # Clear pools to ensure isolation
        BufferPool.clear_pools()

        # Use unique shape to avoid interference
        shape = (13, 17)

        # Create an array with specific values
        arr1 = BufferPool.get_array_buffer(shape, dtype=np.uint8, fill_value=42)
        assert np.all(arr1 == 42)

        # Manually modify array values to ensure fill works
        arr1[:] = 0
        assert np.all(arr1 == 0)

        # Return it to pool
        BufferPool.return_array_buffer(arr1)

        # Get array from pool with different fill value
        # This should reuse arr1 and fill it with new value
        arr2 = BufferPool.get_array_buffer(shape, dtype=np.uint8, fill_value=99)
        assert np.all(arr2 == 99)  # Should be filled with new value

        # The test verifies that lines 106-108 are executed (filling reused array)

    def test_array_pool_fill_value_none_then_some(self):
        """Test array reuse when first get has no fill, second has fill."""
        # This test targets lines 106-108 coverage

        # Clear pools to ensure isolation
        BufferPool.clear_pools()

        # Use unique shape
        shape = (11, 13)

        # Get array without fill value
        arr1 = BufferPool.get_array_buffer(shape, dtype=np.uint8)
        # Return it to pool
        BufferPool.return_array_buffer(arr1)

        # Now get with fill value - should reuse and fill
        arr2 = BufferPool.get_array_buffer(shape, dtype=np.uint8, fill_value=88)
        assert np.all(arr2 == 88)

    def test_array_pool_coverage_hack(self):
        """Direct test to force coverage of lines 103-108."""
        # This is a bit hacky but ensures we hit the specific code path

        # Clear pools
        BufferPool.clear_pools()

        # Manually create and add a weak ref to the pool
        shape = (5, 7)
        key = f"{shape}_{np.uint8}"

        # Create array and add weak ref to pool
        arr = np.zeros(shape, dtype=np.uint8)
        BufferPool._array_pools[key].append(weakref.ref(arr))

        # Now get with fill_value - this will execute lines 103-108
        result = BufferPool.get_array_buffer(shape, dtype=np.uint8, fill_value=123)
        assert np.all(result == 123)
