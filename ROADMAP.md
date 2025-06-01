<!-- markdownlint-disable MD013 MD036 -->
# IT8951 E-Paper Python Driver Roadmap

This roadmap outlines the phased implementation of missing features and improvements identified in the driver comparison and wiki analysis. Features are prioritized by impact on performance, usability, and hardware compatibility.

## Phase 1: Performance Optimizations (v0.2.0) ✅

**High-impact features that significantly improve display performance and user experience**

### 1.1 Implement 4bpp Support (Wiki Recommended) ✅

1.1.1 ✅ Add 4bpp pixel packing functionality in `it8951.py`
1.1.2 ✅ Create `display_image_4bpp()` method in `display.py` (implemented as parameter)
1.1.3 ✅ Add pixel format conversion utilities (8bpp to 4bpp) (integrated in pack_pixels)
1.1.4 ✅ Update examples to demonstrate 4bpp usage (performance_4bpp.py)
1.1.5 ✅ Add performance comparison tests (4bpp vs 8bpp) (test_performance.py)

### 1.2 Dynamic SPI Speed Configuration ✅

1.2.1 ✅ Add Raspberry Pi version detection utility
1.2.2 ✅ Update `SPIConstants` with Pi-specific speeds
1.2.3 ✅ Modify `RaspberryPiSPI` to auto-select appropriate speed
1.2.4 ✅ Add manual speed override option
1.2.5 ✅ Document speed recommendations in README

### 1.3 A2 Mode Auto-Clear Protection ✅

1.3.1 ✅ Add A2 refresh counter to `EPaperDisplay` class
1.3.2 ✅ Implement automatic INIT mode clearing after N refreshes
1.3.3 ✅ Make threshold configurable (default: 10)
1.3.4 ✅ Add warning when approaching clear threshold
1.3.5 ✅ Create example demonstrating safe A2 usage

### 1.4 Properly Implement Custom Exceptions ✅

1.4.1 ✅ Replace CommunicationError with IT8951TimeoutError for timeout scenarios
1.4.2 ✅ Implement IT8951MemoryError for memory allocation and buffer operations
1.4.3 ✅ Add IT8951TimeoutError to other timeout-prone operations
1.4.4 ✅ Update all exception messages to be descriptive and actionable
1.4.5 ✅ Update tests to verify proper exception usage

## Phase 2: Display Quality Enhancements (v0.3.0) ✅

**Features that improve display quality and handle edge cases**

### 2.1 Register Read Capability (moved from Phase 5.1) ✅

2.1.1 ✅ Implement `read_register()` in `IT8951`
2.1.2 ✅ Add register dump utility
2.1.3 ✅ Create register verification methods
2.1.4 ✅ Add register documentation

### 2.2 Enhanced Driving Capability ✅

2.2.1 ✅ Add `enhance_driving_capability()` method to `IT8951`
2.2.2 ✅ Add `enhance_driving` parameter to `EPaperDisplay.__init__()`
2.2.3 ✅ Document when to use enhanced driving (long cables, blur)
2.2.4 ✅ Add diagnostic method to check current driving mode

### 2.3 Improved 4-Byte Alignment for 1bpp ✅

2.3.1 ✅ Create specialized alignment for 1bpp mode (32-bit boundaries)
2.3.2 ✅ Add model detection for alignment requirements
2.3.3 ✅ Update `_align_coordinate()` to handle different modes
2.3.4 ✅ Add alignment validation and warnings
2.3.5 ✅ Create tests for edge cases

### 2.4 VCOM Value Validation and Warnings ✅

2.4.1 ✅ Add VCOM range validation with clear error messages
2.4.2 ✅ Create prominent VCOM warning in all examples
2.4.3 ✅ Add `get_vcom()` method using register read
2.4.4 ✅ Implement VCOM calibration helper
2.4.5 ✅ Add VCOM mismatch detection

## Phase 3: Immediate Improvements (v0.3.1) ✅

**High-priority fixes and enhancements identified in code review**

### 3.1 Critical Fixes ✅

3.1.1 ✅ Update Python version constraint from `>=3.11.12,<3.12` to `>=3.11.12,<3.13`
3.1.2 ✅ Sync version in pyproject.toml with `__init__.py` (0.3.0)
3.1.3 ✅ Update documentation references from 8bpp to 4bpp default
3.1.4 ✅ Create missing `.pre-commit-config.yaml` file
3.1.5 ✅ Remove black reference from CLAUDE.md (replaced by ruff format)

### 3.2 Code Quality Improvements ✅

3.2.1 ✅ Extract magic numbers in `it8951.py` (e.g., 0x80 for LUT busy)
3.2.2 ✅ Refactor repeated command pattern in `it8951.py` to helper method
3.2.3 ✅ Complete 1bpp implementation in `pack_pixels()` method
3.2.4 ✅ Add `wake()` method to complement standby/sleep
3.2.5 ✅ Add performance timing decorators for critical paths

### 3.3 Documentation Enhancements ✅

3.3.1 ✅ Add performance comparison guide (4bpp vs 8bpp, mode comparisons)
3.3.2 ✅ Create troubleshooting section in README
3.3.3 ✅ Document extended display modes (GLR16, GLD16, DU4)
3.3.4 ✅ Update README to mention Phase 2 completion
3.3.5 ✅ Add SECURITY.md with security policy

## Phase 4: Additional Bit Depth Support (v0.4.0) ✅

**Expand display capabilities for specialized use cases**

### 4.1 Implement 1bpp Support ✅

4.1.1 ✅ Add 1bpp pixel packing (8 pixels per byte) - completed in Phase 3.2.3
4.1.2 ✅ Add 32-bit alignment support for 1bpp - completed in Phase 2.3
4.1.3 ✅ Create binary image examples (text, QR codes, line art) - binary_1bpp_demo.py
4.1.4 ✅ Add endian conversion support for 1bpp data - convert_endian_1bpp() method
4.1.5 ✅ Optimize A2 mode for 1bpp (skip grayscale processing) - a2_1bpp_optimization.py

### 4.2 Implement 2bpp Support ✅

4.2.1 ✅ Add 2bpp pixel packing (4 pixels per byte) - implemented in `pack_pixels()`
4.2.2 ✅ Create 2bpp examples demonstrating 4-level grayscale - grayscale_2bpp_demo.py
4.2.3 ✅ Add optimized 4-level grayscale conversion utilities - integrated in pack_pixels()
4.2.4 ✅ Document 2bpp use cases and performance benefits - BIT_DEPTH_SUPPORT.md

### 4.3 Safety and Memory Enhancements (from code review) ✅

4.3.1 ✅ Make VCOM a required parameter (remove default -2.0V)
4.3.2 ✅ Add memory usage estimation before operations
4.3.3 ✅ Implement progressive loading for very large images
4.3.4 ✅ Add warnings for operations exceeding memory thresholds

## Phase 5: Power Management (v0.5.0) ✅

**Essential for battery-powered and embedded applications**

### 5.1 Basic Power Management Commands ✅

5.1.1 ✅ Implement `standby()` method in `IT8951` - completed in v0.2.0
5.1.2 ✅ Implement `sleep()` method in `IT8951` - completed in v0.2.0
5.1.3 ✅ Add `wake()` method for recovery - completed in Phase 3.2.4
5.1.4 ✅ Create power state tracking - completed in v0.5.0
5.1.5 ✅ Add auto-sleep timeout option - completed in v0.5.0

### 5.2 Power Management Integration ✅

5.2.1 ✅ Add context manager support for auto-sleep - completed in v0.5.0
5.2.2 ✅ Create power usage examples - completed in v0.5.0 (power_management_demo.py)
5.2.3 ✅ Document power consumption differences - completed in v0.5.0 (POWER_MANAGEMENT.md)
5.2.4 ✅ Add power state to device info - completed in v0.5.0 (get_device_status method)

## Phase 6: Code Quality & Architecture Improvements (v0.6.0) ✅

**Address code quality issues identified in code review for better maintainability**

### 6.1 Code Duplication and Refactoring ✅

6.1.1 ✅ Refactor duplicated alignment logic (~5% code duplication)
6.1.2 ✅ Extract remaining magic numbers (LUT_BUSY_BIT, etc.)
6.1.3 ✅ Simplify VCOM calibration state machine
6.1.4 ✅ Create shared utilities for common patterns
6.1.5 ✅ Reduce cyclomatic complexity in complex methods

### 6.2 Performance and Type Safety ✅

6.2.1 ✅ Improve pixel packing performance with numpy optimizations
6.2.2 ✅ Add thread safety documentation and considerations
6.2.3 ✅ Complete type annotations for all internal methods
6.2.4 ✅ Add performance benchmarks for critical paths
6.2.5 ✅ Optimize memory allocations in hot paths

### 6.3 Configuration and Documentation ✅

6.3.1 ✅ Fix configuration inconsistencies (numpy version, tool versions)
6.3.2 ✅ Add missing CONTRIBUTING.md with contribution guidelines
6.3.3 ✅ Create CHANGELOG.md for version history
6.3.4 ✅ Update all docstrings to Google style format
6.3.5 ✅ Add architecture decision records (ADRs)

## Phase 7: Debugging and Diagnostics (v0.7.0) ✅

**Tools for troubleshooting and verification**

### 7.1 Extended Display Modes Implementation and Testing ✅

7.1.1 ✅ Implement and test GLR16 mode support
7.1.2 ✅ Implement and test GLD16 mode support
7.1.3 ✅ Implement and test DU4 mode support
7.1.4 ✅ Create mode comparison examples
7.1.5 ✅ Add mode selection guide - completed in Phase 3.3.3 (documented in DISPLAY_MODES.md)

## Phase 8: Developer Experience (v0.8.0) ✅

**Improvements to make the library easier to use**

### 8.1 Enhanced Examples ✅

8.1.1 ✅ Create performance optimization example - pixel_packing_benchmark.py
8.1.2 ✅ Add battery-powered device example - battery_powered_demo.py
8.1.3 ✅ Create mode selection guide example - extended_modes_demo.py
8.1.4 ✅ Add troubleshooting example - troubleshooting_demo.py

### 8.2 Comprehensive Testing ✅

8.2.1 ✅ Add performance benchmarks - test_performance.py, test_numpy_pixel_packing.py
8.2.2 ✅ Create bit depth conversion tests - test_pixel_packing.py
8.2.3 ✅ Add power management tests - test_display.py (power management tests)
8.2.4 ✅ Create alignment edge case tests - test_display.py (alignment tests)

### 8.3 Documentation Updates ✅

8.3.1 ✅ Update README with new features
8.3.2 ✅ Create performance tuning guide - completed in Phase 3.3.1
8.3.3 ✅ Add troubleshooting section - completed in Phase 3.3.2
8.3.4 ✅ Document all new APIs - docstrings updated throughout

## Phase 9: CI/CD Optimizations (v0.9.0)

**Improve development workflow efficiency as the project scales**

### 9.1 Test Performance Optimization

9.1.1 Fix test isolation issues for parallel execution (pytest-xdist installed)
9.1.2 Implement shared fixtures to reduce setup/teardown time
9.1.3 Mock hardware timing delays more aggressively
9.1.4 Optimize test data sizes for faster execution
9.1.5 Add test markers for better organization (@pytest.mark.slow)

### 9.2 Automated Test Selection (Codecov ATS)

9.2.1 Integrate Codecov CLI into CI workflow
9.2.2 Configure ATS for pytest test filtering
9.2.3 Set up test impact analysis
9.2.4 Add fallback for full test runs when needed
9.2.5 Monitor and tune ATS performance

## Phase 10: Long-term Enhancements (v1.0.0)

**Design patterns and architectural improvements for long-term maintainability**

### 10.1 Design Pattern Improvements

10.1.1 Implement builder pattern for complex display configurations
10.1.2 Create plugin architecture for custom display modes
10.1.3 Add strategy pattern for pixel packing algorithms
10.1.4 Implement observer pattern for display state changes
10.1.5 Create factory pattern for SPI interface selection

### 10.2 Advanced Performance Features

10.2.1 Add async/await support for long operations
10.2.2 Implement performance regression framework
10.2.3 Create SPI bulk transfer optimizations
10.2.4 Add memory pooling for buffer allocations
10.2.5 Implement lazy loading for large image operations

### 10.3 Enterprise Features

10.3.1 Add comprehensive logging framework
10.3.2 Implement metrics collection interface
10.3.3 Create diagnostic dump utilities
10.3.4 Add remote debugging capabilities
10.3.5 Implement configuration management system

## Implementation Notes

- Each phase builds upon previous phases
- Phase 1-2 provide the most immediate user value
- Phase 3 addresses critical improvements and fixes
- Phase 4-5 enable new use cases
- Phase 6 provides immediate code quality improvements (NEW - high priority)
- Phase 7-8 improve maintainability and developer experience
- Phase 9 optimizes development workflow
- Phase 10 prepares for v1.0.0 with long-term architectural improvements
- All features should maintain backward compatibility
- Type hints and proper error handling required throughout
