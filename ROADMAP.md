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

## Phase 4: Additional Bit Depth Support (v0.4.0)

**Expand display capabilities for specialized use cases**

### 4.1 Implement 1bpp Support (partially complete)

4.1.1 ✅ Add 1bpp pixel packing (8 pixels per byte) - completed in Phase 3.2.3
4.1.2 Create `display_image_1bpp()` method
4.1.3 Implement proper endian conversion
4.1.4 Add specialized A2 mode support for 1bpp
4.1.5 Create binary image examples

### 4.2 Implement 2bpp Support (partially complete)

4.2.1 ✅ Add 2bpp pixel packing (4 pixels per byte) - already implemented in `pack_pixels()`
4.2.2 Create `display_image_2bpp()` method
4.2.3 Add 4-level grayscale conversion
4.2.4 Create examples for simple graphics

### 4.3 Safety and Memory Enhancements (from code review)

4.3.1 Make VCOM a required parameter (remove default -2.0V)
4.3.2 Add memory usage estimation before operations
4.3.3 Implement progressive loading for very large images
4.3.4 Add warnings for operations exceeding memory thresholds

## Phase 5: Power Management (v0.5.0)

**Essential for battery-powered and embedded applications**

### 5.1 Basic Power Management Commands (partially complete)

5.1.1 ✅ Implement `standby()` method in `IT8951` - completed in v0.2.0
5.1.2 ✅ Implement `sleep()` method in `IT8951` - completed in v0.2.0
5.1.3 ✅ Add `wake()` method for recovery - completed in Phase 3.2.4
5.1.4 Create power state tracking
5.1.5 Add auto-sleep timeout option

### 5.2 Power Management Integration

5.2.1 Add context manager support for auto-sleep
5.2.2 Create power usage examples
5.2.3 Document power consumption differences
5.2.4 Add power state to device info

## Phase 6: Debugging and Diagnostics (v0.6.0)

**Tools for troubleshooting and verification**

### 6.1 Extended Display Modes Testing (partially complete)

6.1.1 Test and document GLR16 mode
6.1.2 Test and document GLD16 mode
6.1.3 Test and document DU4 mode
6.1.4 Create mode comparison examples
6.1.5 ✅ Add mode selection guide - completed in Phase 3.3.3 (documented in DISPLAY_MODES.md)

## Phase 7: Developer Experience (v0.7.0)

**Improvements to make the library easier to use**

### 7.1 Enhanced Examples

7.1.1 Create performance optimization example
7.1.2 Add battery-powered device example
7.1.3 Create mode selection guide example
7.1.4 Add troubleshooting example

### 7.2 Comprehensive Testing

7.2.1 Add performance benchmarks
7.2.2 Create bit depth conversion tests
7.2.3 Add power management tests
7.2.4 Create alignment edge case tests

### 7.3 Documentation Updates (partially complete)

7.3.1 Update README with new features
7.3.2 ✅ Create performance tuning guide - completed in Phase 3.3.1
7.3.3 ✅ Add troubleshooting section - completed in Phase 3.3.2
7.3.4 Document all new APIs

## Phase 8: CI/CD Optimizations (v0.8.0)

**Improve development workflow efficiency as the project scales**

### 8.1 Automated Test Selection (Codecov ATS)

8.1.1 Integrate Codecov CLI into CI workflow
8.1.2 Configure ATS for pytest test filtering
8.1.3 Set up test impact analysis
8.1.4 Add fallback for full test runs when needed
8.1.5 Monitor and tune ATS performance

## Implementation Notes

- Each phase builds upon previous phases
- Phase 1-2 provide the most immediate user value
- Phase 3 addresses critical improvements and fixes
- Phase 4-5 enable new use cases
- Phase 6-7 improve maintainability and developer experience
- Phase 8 optimizes development workflow
- All features should maintain backward compatibility
- Type hints and proper error handling required throughout
