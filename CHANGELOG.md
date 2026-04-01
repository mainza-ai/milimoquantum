# Changelog

All notable changes to Milimo Quantum are documented in this file.

## [Unreleased] - 2026-03-31

### Added

#### VQE Frontend Panel
- New `VQEPanel.tsx` component with full configuration UI
- Hamiltonian selection: H₂, LiH molecules
- Ansatz selection: EfficientSU2, RealAmplitudes, TwoLocal variants
- Optimizer selection: SPSA, COBYLA, L-BFGS-B, SLSQP
- Configurable depth, iterations, and seed parameters
- Real-time results display with convergence visualization
- VQE button added to QuantumDashboard header

#### VQE API
- `runVQE()` function in `api.ts` with TypeScript types
- `VQERequest` and `VQEResult` interfaces for type safety

#### Celery VQE Task
- New `run_vqe_qiskit` Celery task for async VQE execution
- Task registered with Celery worker (6 total tasks)
- Supports all VQE parameters: hamiltonian, ansatz, optimizer, etc.
- Returns full result including convergence trace and metrics

### Fixed

#### NemoClaw Runner
- Fixed indentation in `runner.py` - if/else inside try block was incorrectly indented
- Fixed `cleanup()` method to use `nemoclaw` CLI instead of `openclaw nemoclaw`
- Fixed cleanup command from `openclaw nemoclaw destroy --sandbox <id>` to `nemoclaw destroy <id>`

#### Qiskit 2.x Compatibility
- VQE circuits now transpiled before Aer execution for compatibility
- VQE callback signature updated for qiskit-algorithms 0.4.x (4th arg is metadata dict)
- All Qiskit imports updated for 2.x API

#### Workflow Task Status
- Fixed stubbed task status in `workflows.py`
- Now uses proper `AsyncResult` for real task status monitoring
- Returns actual task status, result, and traceback info

#### HPC MPI Detection
- Replaced hardcoded `mpi_available: False` with dynamic detection
- Uses `which mpirun` to check MPI availability

#### Neo4j Performance Indexes
- Added 4 new indexes to ensure_schema():
  - Artifact unique constraint
  - Message unique constraint
  - Conversation updated_at index
  - Artifact code index

#### Graph Client
- Implemented FalkorDB artifact indexing
- Implemented Kuzu artifact indexing
- Both now properly store PRODUCED and BELONGS_TO relationships

#### CUDA-Q Provider Documentation
- Added comprehensive documentation explaining platform limitations
- CUDA-Q requires Linux x86_64 with NVIDIA GPU
- macOS ARM64 is NOT supported
- Returns informative error with Qiskit Aer fallback suggestion

#### CLOPS Benchmarking
- Implemented actual CLOPS (Circuit Layer Operations Per Second) estimation
- Uses formula: (Circuit Depth × Shots) / Execution Time
- Updated after actual circuit execution

### Tests

- **168 tests passing** (was 107, added 61 new tests)
- Added `test_autoresearch_extension.py` - 18 tests for autoresearch extension
- Added `test_mqdd_extension.py` - 17 tests for MQDD extension
- Added `test_workflows.py` - 5 tests for workflow routes
- Added `test_routes_coverage.py` - 21 tests for route coverage

### Documentation

#### Comprehensive Audit
- Created `docs/AUDIT_REPORT.md` with detailed codebase analysis
- Identified 230 potential issues across codebase
- Documented test coverage gaps and fixes applied

#### Updated Documentation
- Updated README.md with VQE section and NemoClaw information
- Updated MILIMO_QUANTUM_SYSTEM.md with implementation status
- Updated autoresearch-mlx/nemoclaw/AGENTS.md with current status and fixes

## Test Coverage Summary

| Module | Tests Before | Tests After |
|--------|--------------|-------------|
| Core Tests | 107 | 107 |
| Workflow Tests | 0 | 5 |
| Autoresearch Extension | 0 | 18 |
| MQDD Extension | 0 | 17 |
| Route Coverage | 0 | 21 |
| **Total** | **107** | **168** |

## Known Issues (Remaining)

### High Priority
- Extension integration tests - Currently only unit tests

### Medium Priority
- Additional route-specific endpoint tests
- Graph database integration tests

---

## Previous Releases

See git history for previous changes.
