# NemoClaw Integration for Milimo Quantum

This document provides instructions for the NemoClaw agent to install, configure, and operate the sandboxed execution environment for Autoresearch-MLX experiments.

## Overview

NemoClaw provides OS-level sandboxing for autonomous code execution, replacing the AST-based software isolation in `sandbox.py` with proper kernel-level isolation.

## Current Status

**✅ IMPLEMENTED** - The NemoClaw BlueprintRunner is fully functional:

- ✅ Plan phase: Validates blueprint, detects existing sandboxes
- ✅ Apply phase: Executes experiments in NemoClaw sandbox or simulation mode
- ✅ Status phase: Monitors running experiments with metrics
- ✅ Cleanup phase: Destroys sandbox resources

### Recent Fixes (March 2026)
- Fixed runner.py indentation issues (if/else inside try block)
- Fixed CLI command from `openclaw nemoclaw` to `nemoclaw`
- Updated cleanup() to use correct CLI syntax

## Prerequisites

- Node.js 18+ (installed by setup script)
- Docker Desktop (for container runtime)
- Python 3.10+
- NVIDIA API Key (for cloud inference, optional)

## Installation (Official Method)

### Step 1: Install NemoClaw CLI

```bash
# Official installation script from NVIDIA
curl -fsSL https://nvidia.com/nemoclaw.sh | bash
```

After installation, verify:
```bash
nemoclaw --help
```

### Step 2: Setup NemoClaw

The `nemoclaw setup` command initiates complete host-side setup:
- Starts OpenShell gateway
- Registers inference providers
- Builds sandbox image
- Creates the sandbox

```bash
# Run setup (will prompt for NVIDIA API key on first run)
nemoclaw setup
```

Your NVIDIA API key is stored in `~/.nemoclaw/credentials.json`.

### Alternative: Plugin Commands

If you have OpenClaw installed, you can also use plugin commands:

```bash
# Bootstrap OpenClaw inside OpenShell sandbox
openclaw nemoclaw launch

# Check status
openclaw nemoclaw status

# View logs
openclaw nemoclaw logs -f
```

## Configuration Files

### Blueprint Location

```
/Users/mck/Desktop/milimoquantum/autoresearch-mlx/nemoclaw/blueprint.yaml
```

### Policy Location

```
/Users/mck/Desktop/milimoquantum/autoresearch-mlx/nemoclaw/policies/openclaw-sandbox.yaml
```

### Runner Location

```
/Users/mck/Desktop/milimoquantum/autoresearch-mlx/nemoclaw/orchestrator/runner.py
```

## Running Experiments

### Using the Blueprint Runner

```bash
# Navigate to autoresearch directory
cd /Users/mck/Desktop/milimoquantum/autoresearch-mlx

# Run full experiment cycle (recommended)
python nemoclaw/orchestrator/runner.py run --experiment test-001

# Or step by step:
python nemoclaw/orchestrator/runner.py plan
python nemoclaw/orchestrator/runner.py apply --experiment test-001
python nemoclaw/orchestrator/runner.py status
python nemoclaw/orchestrator/runner.py cleanup
```

### Using NemoClaw CLI Directly

```bash
# List existing sandboxes
nemoclaw list

# Check if my-assistant sandbox exists
nemoclaw list | grep my-assistant

# Connect to sandbox and run command
nemoclaw my-assistant connect --command "python train.py"

# Check sandbox status
nemoclaw status

# Destroy sandbox (if needed)
nemoclaw destroy my-assistant
```

### Using OpenClaw CLI Directly

```bash
# Create sandbox
openclaw nemoclaw create --blueprint nemoclaw/blueprint.yaml

# Check status
openclaw nemoclaw status

# Run experiment
openclaw nemoclaw run --sandbox <sandbox-id> --command "uv run train.py"

# Destroy sandbox
openclaw nemoclaw destroy --sandbox <sandbox-id>
```

## Security Policies

### Network Whitelist

The sandbox allows egress to:
- `huggingface.co` - Model downloads
- `arxiv.org` - Literature retrieval
- `pubmed.ncbi.nlm.nih.gov` - Scientific papers
- `localhost:5432` - PostgreSQL
- `localhost:6379` - Redis
- `localhost:7687` - Neo4j
- `localhost:8000` - FastAPI backend

All other network requests are blocked.

### Filesystem Access

Read-write:
- `/sandbox` - Working directory
- `/tmp` - Temporary files
- `/Users/mck/Desktop/milimoquantum/autoresearch-mlx` - Project files

Read-only:
- `/System`, `/Library`, `/usr` - System files
- `/Users/mck/Desktop/milimoquantum/backend/app` - Backend code

Blocked:
- `/Users/mck/Desktop/milimoquantum/backend/.env` - Secrets
- `/Users/*/.ssh`, `/Users/*/.aws` - Credentials

## Monitoring

### View Logs

```bash
# Stream logs in real-time
openclaw nemoclaw logs -f

# Show last 100 lines
openclaw nemoclaw logs -n 100

# View specific run
openclaw nemoclaw logs --run-id <run-id>
```

### Check Health

```bash
openclaw nemoclaw status --json
```

## Integration with Autoresearch Workflow

The workflow is integrated in:
```
/Users/mck/Desktop/milimoquantum/backend/app/extensions/autoresearch/workflow.py
```

Functions:
- `run_research_loop_sandboxed()` - NemoClaw sandboxed execution
- `run_research_loop()` - Legacy direct subprocess (fallback)
- `run_vqe_optimization()` - VQE ansatz discovery
- `run_analysis_cycle()` - Analysis agent for self-improving dataloader

## Troubleshooting

### NemoClaw CLI Not Found

The installed CLI is `nemoclaw` (not `openclaw nemoclaw`):
```bash
# Check PATH
which nemoclaw
# Should show: /opt/homebrew/bin/nemoclaw

# If not found, check installation
ls -la /opt/homebrew/bin/nemoclaw
```

### Sandbox Creation Fails

```bash
# Check Docker is running
docker ps

# Check existing sandboxes
nemoclaw list

# The system automatically reuses existing 'my-assistant' sandbox
```

### Python Indentation Errors

The runner.py had indentation issues that have been fixed. If you see:
```
SyntaxError: invalid syntax
```
Check that if/else blocks inside try/except are properly indented (4 spaces per level).

### Network Request Blocked

If legitimate requests are blocked:
1. Edit `policies/openclaw-sandbox.yaml`
2. Add host to `egress_rules`
3. Recreate sandbox

### Simulation Mode

If NemoClaw is not installed, the system automatically uses simulation mode:
- Runs experiments directly via subprocess
- Still provides monitoring and metrics
- No OS-level isolation (less secure)

## Files Created

| File | Purpose |
|------|---------|
| `blueprint.yaml` | Main sandbox configuration |
| `policies/openclaw-sandbox.yaml` | Security policies |
| `orchestrator/runner.py` | Python orchestrator |
| `vqe_train.py` | VQE ansatz discovery module |
| `packer.py` | Segment tree document packing |
| `analysis_agent.py` | Self-improving dataloader agent |

## Next Steps

1. Install NemoClaw: `curl -fsSL https://nvidia.com/nemoclaw.sh | bash`
2. Run setup: `nemoclaw setup` (will prompt for NVIDIA API key)
3. Test sandbox creation: `nemoclaw list`
4. Run experiment: `python nemoclaw/orchestrator/runner.py run --experiment test`
5. Monitor: `nemoclaw status`

## References

- NemoClaw Documentation: https://docs.nvidia.com/nemoclaw/latest/
- NVIDIA Build (API Keys): https://build.nvidia.com/
- Milimo Quantum Docs: `/docs/`
