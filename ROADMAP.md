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

3.1.1 ✅ Update Python version constraint from `>=3.11.13,<3.12` to `>=3.11.13,<3.13`
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

## Phase 9: CI/CD Optimizations (v0.9.0) ✅

**Improve development workflow efficiency as the project scales**

### 9.1 Test Performance Optimization ✅

9.1.1 ✅ Fix test isolation issues for parallel execution (pytest-xdist installed)
9.1.2 ✅ Implement shared fixtures to reduce setup/teardown time
9.1.3 ✅ Mock hardware timing delays more aggressively
9.1.4 ✅ Optimize test data sizes for faster execution
9.1.5 ✅ Add test markers for better organization (@pytest.mark.slow)

### 9.2 Automated Test Selection (Codecov ATS) ✅

9.2.1 ✅ Integrate Codecov CLI into CI workflow
9.2.2 ✅ Configure ATS for pytest test filtering
9.2.3 ✅ Set up test impact analysis
9.2.4 ✅ Add fallback for full test runs when needed
9.2.5 ✅ Monitor and tune ATS performance

### 9.3 Code Quality Improvements ✅

9.3.1 ✅ Refactor high cyclomatic complexity methods
9.3.2 ✅ Extract helper methods for better maintainability
9.3.3 ✅ Maintain 100% type safety with pyright
9.3.4 ✅ Ensure all tests pass with refactored code
9.3.5 ✅ Keep linting and formatting standards

## Phase 10: Critical Fixes (v0.10.0) ✅

**Immediate fixes identified in Phase 9 review**

### 10.1 CI/CD Configuration Fixes ✅

10.1.1 ✅ Remove --dry-run flag from ATS workflow for actual execution
10.1.2 ✅ Fix dependency duplication in pyproject.toml (lines 21-25 and 44-48)
10.1.3 ✅ Relax Python version constraint to `>=3.11` (from `>=3.11.13,<3.13`)
10.1.4 ✅ Standardize cache keys between CI and ATS workflows
10.1.5 ✅ Extract magic numbers (VCOM tolerance 0.05V, numpy threshold 10000)

## Phase 11: Thread Safety & Type Safety (v0.11.0) ✅

**High-priority safety improvements**

### 11.1 Thread Safety Implementation ✅

11.1.1 ✅ Create ThreadSafeEPaperDisplay wrapper class with RLock
11.1.2 ✅ Implement thread-safe decorators for critical operations
11.1.3 ✅ Add comprehensive concurrency tests
11.1.4 ✅ Document thread safety guarantees and patterns
11.1.5 ✅ Create thread_safety_demo.py example

### 11.2 Type Safety Fixes ✅

11.2.1 ✅ Fix type ignores in spi_interface.py (lines 433, 438) with explanatory comments
11.2.2 ✅ Fix type ignore in retry_policy.py (line 112) with explanatory comment
11.2.3 ✅ Fix type ignore in thread_safe.py (line 59) with explanatory comment
11.2.4 ✅ Implement TypedDict for complex return types (DeviceStatus, ModeInfo)
11.2.5 ✅ Ensure 100% type coverage with pyright strict mode

## Phase 12: Robustness & Testing (v0.12.0) ✅

**Error recovery and comprehensive testing**

### 12.1 Error Recovery Framework ✅

12.1.1 ✅ Implement retry decorator with configurable backoff
12.1.2 ✅ Add retry logic for SPI communication failures
12.1.3 ✅ Create recovery procedures documentation
12.1.4 ✅ Implement configurable retry policies
12.1.5 ✅ Add error_recovery_demo.py example

### 12.2 Integration Test Suite ✅

12.2.1 ✅ Create test_integration.py for multi-feature workflows
12.2.2 ✅ Add power management + display mode combination tests
12.2.3 ✅ Test progressive loading + bit depth optimization
12.2.4 ✅ Add error propagation tests across components
12.2.5 ✅ Create integration test markers and categories

## Phase 13: Documentation & API Reference (v0.13.0) ✅

**Essential documentation for adoption**

### 13.1 API Documentation ❌ (Not Pursued)

**Decision**: After attempting to implement Sphinx documentation, it was found that the auto-generated documentation contained numerous inaccuracies and references to non-existent methods. The existing comprehensive Markdown documentation in the `docs/` directory provides accurate, well-organized information without the complexity and maintenance burden of Sphinx.

13.1.1 ❌ Set up Sphinx for API documentation generation - Reverted due to quality issues
13.1.2 ❌ Configure autodoc to generate from docstrings - Generated incorrect documentation
13.1.3 ❌ Deploy documentation to GitHub Pages - Not needed with current docs
13.1.4 ❌ Create versioned documentation - Can be done with Markdown if needed
13.1.5 ❌ Add interactive examples to docs - Examples work well as standalone files

### 13.2 Diagnostic Utilities ✅ (Complete)

**Decision**: The project already has comprehensive diagnostic capabilities through `troubleshooting_demo.py`, which provides interactive diagnostics for communication, display quality, performance, memory, power management, and VCOM configuration. Error messages are already descriptive with actionable solutions. Additional diagnostic utilities would provide diminishing returns.

**Already Implemented:**

- ✅ Diagnostic dump utilities via `dump_registers()` method
- ✅ Comprehensive troubleshooting example (`troubleshooting_demo.py`)
- ✅ Performance timing decorators (`@timed_operation`)
- ✅ Detailed error messages with recovery suggestions
- ✅ Device status methods (`get_device_status()`, `get_vcom()`)

**Completed in v0.13.0:**
13.2.1 ✅ Enhanced debug mode with configurable verbosity levels - Implemented `debug_mode.py` with 6 levels
13.2.2 ✅ Minor enhancements to error messages where needed - Added context parameter to exceptions

**Not Needed:**
13.2.3 ❌ Troubleshooting decision tree - current interactive demo is sufficient
13.2.4 ❌ Additional diagnostic scripts - `troubleshooting_demo.py` is comprehensive

## Phase 14: Performance & Memory Optimization (v0.14.0) ✅

**Performance improvements for better user experience**

### 14.1 Performance Optimizations ✅

14.1.1 ✅ Optimize list comprehensions in hot paths (spi_interface.py)
14.1.2 ✅ Pre-allocate arrays for bulk operations
14.1.3 ✅ Profile and optimize memory allocations
14.1.4 ✅ Add performance regression tests
14.1.5 ✅ Create performance profiling example

### 14.2 Memory & Transfer Optimizations ✅

14.2.1 ✅ Add memory pooling for buffer allocations - BufferPool class already exists
14.2.2 ✅ Create SPI bulk transfer optimizations - Optimized write_data_bulk with zero-copy
14.2.3 ✅ Implement zero-copy operations where possible - Removed list() conversion in SPI
14.2.4 ✅ Add memory usage monitoring - Created memory_monitor.py with full monitoring
14.2.5 ✅ Optimize numpy array operations - Already optimized in pixel_packing.py

## Phase 15: Developer Experience (v0.15.0)

**Improved developer workflow and platform support**

### 15.1 Examples and Guides ✅

15.1.1 ✅ Create buffer_pool_demo.py for buffer management
15.1.2 ✅ Add integration_scenarios.py for complex workflows
15.1.3 ✅ Add hardware setup troubleshooting guide - docs/HARDWARE_SETUP.md
15.1.4 ✅ Write migration guide from C driver - docs/MIGRATION_GUIDE.md
15.1.5 ✅ Create best practices guide - docs/BEST_PRACTICES.md

### 15.2 Multi-Platform Support ✅

15.2.1 ✅ Add macOS runners to CI workflow
15.2.2 ✅ Add ARM64 (Raspberry Pi) testing
15.2.3 ✅ Test on Python 3.11, 3.12, and 3.13
15.2.4 ✅ Add Windows compatibility verification
15.2.5 ✅ Create platform-specific documentation - docs/PLATFORM_SUPPORT.md

### 15.3 Developer Tools

15.3.1 Add IDE configuration files (VSCode, PyCharm)
15.3.2 Create development setup scripts
15.3.3 Add debugging configuration guides
15.3.4 Implement development CLI tools
15.3.5 Create contributor onboarding guide

## Phase 16: Architecture & Design Patterns (v1.0.0)

**Long-term maintainability improvements**

### 16.1 Design Pattern Implementation

16.1.1 Implement builder pattern for complex display configurations
16.1.2 Create plugin architecture for custom display modes
16.1.3 Add strategy pattern for pixel packing algorithms
16.1.4 Implement observer pattern for display state changes
16.1.5 Create factory pattern for SPI interface selection

### 16.2 Code Organization

16.2.1 Split display.py using mixins (power, vcom, modes)
16.2.2 Split test_display.py into focused test modules
16.2.3 Create display_base.py for core functionality
16.2.4 Implement display_power.py mixin
16.2.5 Organize tests by feature area

## Phase 17: Advanced Features (v1.1.0)

**Future enhancements for advanced use cases**

### 17.1 Async Support

17.1.1 Add async/await support for long operations
17.1.2 Implement async SPI interface
17.1.3 Create async context managers
17.1.4 Add async event handling
17.1.5 Create async examples

### 17.2 Enterprise Features

17.2.1 Add comprehensive logging framework
17.2.2 Implement metrics collection interface
17.2.3 Add remote debugging capabilities
17.2.4 Implement configuration management system
17.2.5 Create enterprise deployment guide

### 17.3 Hardware Abstraction

17.3.1 Create platform detection utilities
17.3.2 Add platform-specific optimizations
17.3.3 Implement hardware capability detection
17.3.4 Add platform compatibility matrix
17.3.5 Create cross-platform testing guide

## Implementation Notes

- Each phase builds upon previous phases
- Phases 1-14 have been completed (✅)
- Phase 12 added robustness through comprehensive integration testing
- Phase 13.1 (API Documentation) was not pursued due to quality issues with auto-generated docs
- Phase 13.2 (Diagnostic Utilities) is complete with enhanced debug mode and error messages
- Phase 14 optimized performance and memory usage
- Phase 15.1 (Examples and Guides) is complete with comprehensive documentation
- Phase 15.2 (Multi-Platform Support) is complete with CI/CD for macOS, ARM64, Windows, and Python 3.11-3.13
- Phase 15.3 (Developer Tools) pending for IDE configurations and setup scripts
- Phase 16 reaches v1.0.0 with architecture improvements
- Phase 17 adds advanced features for v1.1.0
- All features should maintain backward compatibility
- Type hints and proper error handling required throughout

### Reprioritized Implementation Order

Based on the Phase 9 review findings, the phases have been reorganized by priority:

**Critical Path (Phases 10-12)**

1. Phase 10: Critical Fixes
2. Phase 11: Thread & Type Safety
3. Phase 12: Robustness & Testing

**User Experience (Phases 13-15)**
4. Phase 13: Documentation ✅ (Complete - enhanced debug mode and error messages implemented)
5. Phase 14: Performance ✅ (Complete - optimizations and monitoring implemented)
6. Phase 15: Developer Experience (15.1-15.2 ✅ Complete - examples, guides, and multi-platform support; 15.3 pending)

**Long-term (Phases 16-17)**
7. Phase 16: Architecture - v1.0.0
8. Phase 17: Advanced Features - v1.1.0

### Key Changes from Original Roadmap

- **Removed duplicates**: Memory pooling and SPI optimizations consolidated
- **Elevated priorities**: CI/CD fixes, thread safety, and type safety moved up
- **Logical grouping**: Phases now grouped by theme rather than mixed concerns
- **Clear versioning**: v1.0.0 reserved for architecture completion
