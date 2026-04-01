#!/usr/bin/env python3
"""
NemoClaw Blueprint Runner for Milimo Autoresearch.

Orchestrates sandboxed execution of train.py experiments.
Implements the plan → apply → status lifecycle.

Usage:
    python runner.py plan
    python runner.py apply --experiment test
    python runner.py status
    python runner.py cleanup
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nemoclaw-runner")

# Use environment variables or relative paths for portability
PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).parent.parent.parent.parent))
AUTORESEARCH_DIR = Path(os.environ.get("AUTORESEARCH_DIR", PROJECT_ROOT / "autoresearch-mlx"))
SANDBOX_DIR = Path(os.environ.get("SANDBOX_DIR", "/sandbox"))
NEMOCLAW_DIR = AUTORESEARCH_DIR / "nemoclaw"


class BlueprintRunner:
    """
    Manages the lifecycle of a sandboxed autoresearch experiment.

    Lifecycle:
    1. plan() - Validate environment, prepare sandbox
    2. apply() - Execute train.py in sandbox
    3. status() - Monitor execution, capture results
    4. cleanup() - Destroy sandbox and free resources
    """

    def __init__(self, blueprint_path: Path = None):
        self.blueprint_path = blueprint_path or NEMOCLAW_DIR / "blueprint.yaml"
        self.sandbox_id: Optional[str] = None
        self.process: Optional[asyncio.subprocess.Process] = None
        self.start_time: Optional[float] = None
        self._output_buffer: list = []

    async def plan(self) -> Dict[str, Any]:
        """
        Validate the blueprint and prepare the sandbox environment.

        Returns:
        Dict with 'ready' (bool), 'errors' (list), 'warnings' (list)
        """
        result = {"ready": True, "errors": [], "warnings": [], "sandbox_id": None}

        logger.info("Starting plan phase...")

        # 1. Validate blueprint exists
        if not self.blueprint_path.exists():
            result["errors"].append(f"Blueprint not found: {self.blueprint_path}")
            result["ready"] = False
            logger.error(f"Blueprint not found: {self.blueprint_path}")
            return result

        logger.info(f"Blueprint found: {self.blueprint_path}")

        # 2. Validate train.py exists
        train_py = AUTORESEARCH_DIR / "train.py"
        if not train_py.exists():
            result["errors"].append(f"train.py not found: {train_py}")
            result["ready"] = False
            logger.error(f"train.py not found: {train_py}")
            return result

        logger.info(f"train.py found: {train_py}")

        # 3. Validate prepare.py (data) exists
        prepare_py = AUTORESEARCH_DIR / "prepare.py"
        if not prepare_py.exists():
            result["warnings"].append("prepare.py not found - data may not be ready")
            logger.warning("prepare.py not found")

        # 4. Check data directory
        data_cache = Path.home() / ".cache" / "autoresearch"
        if not data_cache.exists():
            result["warnings"].append(f"Data cache not found: {data_cache}")
            logger.warning(f"Data cache not found: {data_cache}")
        else:
            logger.info(f"Data cache found: {data_cache}")

        # 5. Check Python environment
        project_root = os.environ.get("PROJECT_ROOT", str(Path(__file__).parent.parent.parent.parent))
        milimo_python = Path(os.environ.get("MILIMO_PYTHON", os.path.join(project_root, "backend", "milimoenv", "bin", "python")))
        if not milimo_python.exists():
            result["warnings"].append(f"Milimo Python not found: {milimo_python}")
            logger.warning(f"Milimo Python not found: {milimo_python}")
        else:
            logger.info(f"Python environment found: {milimo_python}")

        # 6. Request sandbox creation from NemoClaw (or simulate)
        try:
            create_result = await self._create_sandbox()
            if create_result.get("success"):
                self.sandbox_id = create_result["sandbox_id"]
                result["sandbox_id"] = self.sandbox_id
                logger.info(f"Sandbox created: {self.sandbox_id}")
            else:
                # If NemoClaw not available, use simulation mode
                if "NemoClaw not installed" in create_result.get("error", ""):
                    result["warnings"].append("NemoClaw not installed - using simulation mode")
                    self.sandbox_id = f"sim-{int(time.time())}"
                    result["sandbox_id"] = self.sandbox_id
                    logger.warning("NemoClaw not installed - using simulation mode")
                else:
                    result["errors"].append(f"Sandbox creation failed: {create_result.get('error')}")
                    result["ready"] = False
                    logger.error(f"Sandbox creation failed: {create_result.get('error')}")
        except Exception as e:
            result["errors"].append(f"Sandbox creation error: {e}")
            result["ready"] = False
            logger.error(f"Sandbox creation error: {e}")

        if result["ready"]:
            logger.info(f"Plan phase completed successfully. Sandbox ID: {self.sandbox_id}")
        else:
            logger.error(f"Plan phase failed with {len(result['errors'])} errors")

        return result
    
    async def apply(self, experiment_name: str = "unnamed") -> Dict[str, Any]:
        """
        Execute train.py in the sandboxed environment.
        
        Args:
            experiment_name: Identifier for this experiment run
            
        Returns:
            Dict with 'started' (bool), 'pid' (int), 'error' (str if failed)
        """
        result = {"started": False, "pid": None, "error": None}
        
        logger.info(f"Starting apply phase for experiment: {experiment_name}")
        
        if not self.sandbox_id:
            result["error"] = "No sandbox ID - call plan() first"
            logger.error("No sandbox ID - call plan() first")
            return result
            
        # Check if using simulation mode
        is_simulation = self.sandbox_id.startswith("sim-")
        
        # Copy current train.py state
        train_src = AUTORESEARCH_DIR / "train.py"
        
        try:
            if is_simulation:
                # Simulation mode - run directly
                logger.info("Running in simulation mode (direct subprocess)")
                
                self.start_time = time.time()
                
                # Use uv run for consistent environment
                self.process = await asyncio.create_subprocess_exec(
                    "uv", "run", "train.py",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=str(AUTORESEARCH_DIR),
                    env={**os.environ, "PYTHONUNBUFFERED": "1"}
                )
                
                result["started"] = True
                result["pid"] = self.process.pid
                logger.info(f"Started experiment '{experiment_name}' with PID {self.process.pid} (simulation mode)")

            else:
                # NemoClaw mode - run in sandbox using 'nemoclaw connect'
                logger.info("Running in NemoClaw sandbox mode")

                # Copy train.py to sandbox directory if it exists
                if SANDBOX_DIR.exists():
                    import shutil
                    shutil.copy(str(train_src), str(SANDBOX_DIR / "train.py"))
                    logger.info(f"Copied train.py to sandbox")

                self.start_time = time.time()

                # Use 'nemoclaw <sandbox> connect' to run in the sandbox
                # The nemoclaw CLI uses 'connect' to shell into a sandbox
                self.process = await asyncio.create_subprocess_exec(
                "nemoclaw", self.sandbox_id, "connect",
                "--command", "uv run train.py",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env={**os.environ, "PYTHONUNBUFFERED": "1"}
                )

                result["started"] = True
                result["pid"] = self.process.pid
                logger.info(f"Started experiment '{experiment_name}' with PID {self.process.pid} (NemoClaw mode)")
                
        except Exception as e:
            result["error"] = f"Failed to start process: {e}"
            logger.error(f"Failed to start process: {e}")
            
        return result
    
    async def status(self) -> Dict[str, Any]:
        """
        Check the status of the running experiment.
        
        Returns:
            Dict with 'running' (bool), 'exit_code' (int if done), 
            'elapsed_seconds' (float), 'output' (str if available)
        """
        result = {
            "running": False,
            "exit_code": None,
            "elapsed_seconds": 0,
            "output": None,
            "metrics": {}
        }
        
        if not self.process:
            return result
            
        result["elapsed_seconds"] = time.time() - (self.start_time or time.time())
        
        try:
            exit_code = self.process.returncode
            if exit_code is None:
                result["running"] = True
                
                # Try to read partial output
                try:
                    line = await asyncio.wait_for(
                        self.process.stdout.readline(),
                        timeout=0.1
                    )
                    if line:
                        decoded = line.decode('utf-8', errors='replace').strip()
                        result["output"] = decoded
                        self._output_buffer.append(decoded)
                        
                        # Parse metrics from output
                        self._parse_metrics(decoded, result["metrics"])
                        
                except asyncio.TimeoutError:
                    pass
            else:
                result["exit_code"] = exit_code
                result["running"] = False
                
                # Read all remaining output
                remaining, _ = await self.process.communicate()
                if remaining:
                    decoded = remaining.decode('utf-8', errors='replace')
                    result["output"] = decoded
                    self._output_buffer.append(decoded)
                    
                    # Parse final metrics
                    for line in decoded.split('\n'):
                        self._parse_metrics(line, result["metrics"])
                        
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Status check error: {e}")
            
        return result
    
    def _parse_metrics(self, line: str, metrics: dict):
        """Parse metrics from output line."""
        if "val_bpb:" in line:
            parts = line.split("val_bpb:")
            if len(parts) > 1:
                try:
                    val = parts[1].strip().split()[0]
                    metrics["val_bpb"] = float(val)
                except (ValueError, IndexError):
                    pass
                    
        if "peak_vram_mb:" in line:
            parts = line.split("peak_vram_mb:")
            if len(parts) > 1:
                try:
                    val = parts[1].strip().split()[0]
                    metrics["peak_vram_mb"] = float(val)
                except (ValueError, IndexError):
                    pass
                    
        if "training_seconds:" in line:
            parts = line.split("training_seconds:")
            if len(parts) > 1:
                try:
                    val = parts[1].strip().split()[0]
                    metrics["training_seconds"] = float(val)
                except (ValueError, IndexError):
                    pass
    
    async def cleanup(self):
        """Clean up sandbox resources."""
        logger.info("Starting cleanup phase...")
        
        if self.sandbox_id and not self.sandbox_id.startswith("sim-"):
            try:
                proc = await asyncio.create_subprocess_exec(
"nemoclaw", "destroy", self.sandbox_id
                )
                await proc.wait()
                logger.info(f"Destroyed sandbox: {self.sandbox_id}")
            except Exception as e:
                logger.warning(f"Failed to destroy sandbox: {e}")
                
        self.sandbox_id = None
        self.process = None
        self._output_buffer = []

        logger.info("Cleanup completed")

    async def _create_sandbox(self) -> Dict[str, Any]:
        """Request sandbox creation from NemoClaw."""
        # First check if nemoclaw is available (the actual CLI name)
        try:
            proc = await asyncio.create_subprocess_exec(
                "which", "nemoclaw",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            if not stdout:
                return {"success": False, "error": "NemoClaw not installed - nemoclaw command not found"}

        except Exception as e:
            return {"success": False, "error": f"NemoClaw not installed: {e}"}

        # Check if sandbox already exists (my-assistant is the default)
        try:
            proc = await asyncio.create_subprocess_exec(
                "nemoclaw", "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            if proc.returncode == 0:
                output = stdout.decode('utf-8')
                # If my-assistant exists, use it
                if "my-assistant" in output:
                    logger.info("Using existing sandbox 'my-assistant'")
                    return {"success": True, "sandbox_id": "my-assistant"}

        except Exception as e:
            logger.warning(f"Could not list sandboxes: {e}")

        # Try to create sandbox via onboard if needed
        # Note: nemoclaw uses 'onboard' to create, not 'create'
        try:
            proc = await asyncio.create_subprocess_exec(
                "nemoclaw", "onboard",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                return {"success": True, "sandbox_id": "my-assistant"}
            else:
                return {"success": False, "error": stderr.decode('utf-8')}

        except FileNotFoundError:
            return {"success": False, "error": "NemoClaw not installed - nemoclaw command not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_full_output(self) -> str:
        """Get all captured output."""
        return '\n'.join(self._output_buffer)


async def run_full_experiment(experiment_name: str = "test") -> Dict[str, Any]:
    """
    Run a complete experiment cycle.
    
    Args:
        experiment_name: Name for this experiment
        
    Returns:
        Final results including metrics
    """
    runner = BlueprintRunner()
    
    # Plan
    plan_result = await runner.plan()
    if not plan_result["ready"]:
        return {"success": False, "phase": "plan", "errors": plan_result["errors"]}
        
    # Apply
    apply_result = await runner.apply(experiment_name=experiment_name)
    if not apply_result["started"]:
        await runner.cleanup()
        return {"success": False, "phase": "apply", "error": apply_result["error"]}
        
    # Monitor until complete
    while True:
        status = await runner.status()
        
        if status["output"]:
            print(status["output"])
            
        if not status["running"]:
            break
            
        await asyncio.sleep(1)
        
    # Cleanup
    await runner.cleanup()
    
    return {
        "success": True,
        "phase": "complete",
        "exit_code": status["exit_code"],
        "metrics": status["metrics"],
        "elapsed_seconds": status["elapsed_seconds"],
        "output": runner.get_full_output()
    }


async def main():
    """CLI entry point for blueprint runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NemoClaw Blueprint Runner")
    parser.add_argument("action", choices=["plan", "apply", "status", "cleanup", "run"])
    parser.add_argument("--blueprint", type=Path, help="Path to blueprint.yaml")
    parser.add_argument("--experiment", default="test", help="Experiment name")
    
    args = parser.parse_args()
    
    runner = BlueprintRunner(blueprint_path=args.blueprint)
    
    if args.action == "plan":
        result = await runner.plan()
        print(json.dumps(result, indent=2))
        
    elif args.action == "apply":
        plan_result = await runner.plan()
        if plan_result["ready"]:
            result = await runner.apply(experiment_name=args.experiment)
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps({"error": "Plan failed", "details": plan_result}))
            sys.exit(1)
            
    elif args.action == "status":
        result = await runner.status()
        print(json.dumps(result, indent=2))
        
    elif args.action == "cleanup":
        await runner.cleanup()
        print(json.dumps({"cleaned": True}))
        
    elif args.action == "run":
        result = await run_full_experiment(experiment_name=args.experiment)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
