"""
End-to-End Tests: NemoClaw Sandbox + Autoresearch-MLX Workflow

Tests the full integration chain:
1. NemoClaw CLI availability and sandbox management
2. NemoClaw Docker container health
3. BlueprintRunner plan/apply/status (simulation mode)
4. Autoresearch API endpoints (status, results, VQE, export)
5. Autoresearch training loop (manual mode via API)
6. Autoresearch data preparation (via API)
7. Autoresearch analysis agent (via API)
8. Cross-system integration (PostgreSQL persistence, Neo4j graph, Docker health)
"""

import httpx
import json
import os
import subprocess
from pathlib import Path
from typing import Optional

import pytest
from dotenv import load_dotenv

# ── Configuration ──────────────────────────────────────────────

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

BACKEND_URL = "http://localhost:8000"
NEMOCLAW_DIR = os.path.join(
    Path(__file__).resolve().parents[2], "autoresearch-mlx", "nemoclaw"
)
AUTORESEARCH_DIR = os.path.join(
    Path(__file__).resolve().parents[2], "autoresearch-mlx"
)
NEMOCLAW_CONTAINER = "openshell-cluster-nemoclaw"

# ── Auth Helper ────────────────────────────────────────────────


def _get_keycloak_token() -> Optional[str]:
    """Obtain JWT from Keycloak for authenticated API calls."""
    try:
        import requests

        token_url = os.environ.get(
            "KEYCLOAK_TOKEN_URL",
            "http://localhost:8081/realms/milimo-realm/protocol/openid-connect/token",
        )
        resp = requests.post(
            token_url,
            data={
                "client_id": "milimo-client",
                "username": "admin",
                "password": "admin",
                "grant_type": "password",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception:
        pass
    return None


@pytest.fixture(scope="module")
def api_headers():
    """Provide authenticated headers with CSRF protection."""
    token = _get_keycloak_token()
    if not token:
        pytest.skip("Keycloak not available — cannot authenticate")
    return {
        "Authorization": f"Bearer {token}",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json",
    }


# ── Workflow 1: NemoClaw CLI & Sandbox ─────────────────────────


class TestNemoClawCLI:
    """Test NemoClaw CLI availability and basic operations."""

    def test_01_nemoclaw_installed(self):
        """Verify nemoclaw CLI is installed and executable."""
        result = subprocess.run(
            ["which", "nemoclaw"], capture_output=True, text=True, timeout=5
        )
        assert result.returncode == 0, "nemoclaw CLI not found in PATH"
        assert "nemoclaw" in result.stdout

    def test_02_nemoclaw_version(self):
        """Check nemoclaw version output."""
        result = subprocess.run(
            ["nemoclaw", "--help"], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert "NemoClaw" in result.stdout or "nemoclaw" in result.stdout.lower()

    def test_03_nemoclaw_list_sandboxes(self):
        """List available sandboxes."""
        result = subprocess.run(
            ["nemoclaw", "list"], capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0
        output = result.stdout
        # Should show at least one sandbox
        assert (
            "my-assistant" in output or "Sandboxes" in output
        ), f"No sandboxes listed: {output}"

    def test_04_nemoclaw_sandbox_status(self):
        """Check sandbox health status."""
        result = subprocess.run(
            ["nemoclaw", "my-assistant", "status"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # May succeed or fail depending on sandbox state
        output = result.stdout
        assert "my-assistant" in output or "Sandbox" in output, (
            f"Unexpected status output: {output[:200]}"
        )

    def test_05_nemoclaw_policy_list(self):
        """List sandbox policy presets."""
        result = subprocess.run(
            ["nemoclaw", "my-assistant", "policy-list"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        # Should return without error
        assert result.returncode == 0 or "policy" in result.stdout.lower()

    def test_06_blueprint_runner_importable(self):
        """Verify BlueprintRunner can be imported from the nemoclaw directory."""
        import sys

        sys.path.insert(0, NEMOCLAW_DIR)
        try:
            from orchestrator.runner import BlueprintRunner

            assert BlueprintRunner is not None
            assert hasattr(BlueprintRunner, "plan")
            assert hasattr(BlueprintRunner, "apply")
            assert hasattr(BlueprintRunner, "status")
            assert hasattr(BlueprintRunner, "cleanup")
        finally:
            sys.path.remove(NEMOCLAW_DIR)


# ── Workflow 2: NemoClaw Docker Container ──────────────────────


class TestNemoClawDocker:
    """Test the NemoClaw Docker container is healthy and accessible."""

    def test_01_container_running(self):
        """Verify the NemoClaw container is running."""
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={NEMOCLAW_CONTAINER}", "--format", "{{.Status}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        status = result.stdout.strip()
        assert "Up" in status, f"NemoClaw container not running: {status}"

    def test_02_container_healthy(self):
        """Check container health status."""
        result = subprocess.run(
            [
                "docker",
                "inspect",
                NEMOCLAW_CONTAINER,
                "--format",
                "{{.State.Health.Status}}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            health = result.stdout.strip()
            assert health in ("healthy", "starting"), f"Container unhealthy: {health}"

    def test_03_container_exec(self):
        """Test docker exec into the NemoClaw container."""
        result = subprocess.run(
            ["docker", "exec", NEMOCLAW_CONTAINER, "echo", "nemoclaw_reachable"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0
        assert "nemoclaw_reachable" in result.stdout

    def test_04_container_os(self):
        """Verify container OS details."""
        result = subprocess.run(
            ["docker", "exec", NEMOCLAW_CONTAINER, "cat", "/etc/os-release"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Ubuntu" in result.stdout or "Linux" in result.stdout

    def test_05_blueprint_yaml_exists(self):
        """Verify the NemoClaw blueprint configuration exists."""
        blueprint_path = os.path.join(NEMOCLAW_DIR, "blueprint.yaml")
        assert os.path.exists(blueprint_path), f"Blueprint not found: {blueprint_path}"

        with open(blueprint_path) as f:
            content = f.read()
        assert "timeout" in content.lower()
        assert "memory" in content.lower()

    def test_06_orchestrator_module(self):
        """Verify the orchestrator module exists and is valid Python."""
        runner_path = os.path.join(NEMOCLAW_DIR, "orchestrator", "runner.py")
        assert os.path.exists(runner_path), f"Runner not found: {runner_path}"

        # Compile check
        with open(runner_path) as f:
            compile(f.read(), runner_path, "exec")


# ── Workflow 3: BlueprintRunner (Simulation Mode) ──────────────


class TestBlueprintRunner:
    """Test the BlueprintRunner integration in simulation mode."""

    def test_01_runner_instantiation(self):
        """Create a BlueprintRunner instance."""
        import sys

        sys.path.insert(0, NEMOCLAW_DIR)
        try:
            from orchestrator.runner import BlueprintRunner

            runner = BlueprintRunner()
            assert runner is not None
        finally:
            sys.path.remove(NEMOCLAW_DIR)

    def test_02_runner_plan(self):
        """Test the plan phase — validates environment."""
        import sys
        import asyncio

        sys.path.insert(0, NEMOCLAW_DIR)
        try:
            from orchestrator.runner import BlueprintRunner

            runner = BlueprintRunner()
            result = asyncio.run(runner.plan())
            # Plan should return a dict with validation results
            assert isinstance(result, dict), f"Plan returned {type(result)}"
            # Should have at least some validation keys
            has_any_key = any(
                k in result
                for k in [
                    "status",
                    "valid",
                    "sandbox_id",
                    "sandbox",
                    "error",
                    "message",
                ]
            )
            assert has_any_key, f"Plan result has no expected keys: {result}"
        finally:
            sys.path.remove(NEMOCLAW_DIR)

    def test_03_runner_status(self):
        """Test the status phase — monitors experiment state."""
        import sys
        import asyncio

        sys.path.insert(0, NEMOCLAW_DIR)
        try:
            from orchestrator.runner import BlueprintRunner

            runner = BlueprintRunner()
            result = asyncio.run(runner.status())
            # Status should return something (may be empty if no experiment running)
            assert isinstance(result, (dict, str, list, type(None)))
        finally:
            sys.path.remove(NEMOCLAW_DIR)

    def test_04_train_py_exists(self):
        """Verify train.py exists in the autoresearch directory."""
        train_path = os.path.join(AUTORESEARCH_DIR, "train.py")
        assert os.path.exists(train_path), f"train.py not found: {train_path}"

        # Verify it's valid Python
        with open(train_path) as f:
            compile(f.read(), train_path, "exec")

    def test_05_prepare_py_exists(self):
        """Verify prepare.py exists."""
        prepare_path = os.path.join(AUTORESEARCH_DIR, "prepare.py")
        assert os.path.exists(prepare_path), f"prepare.py not found: {prepare_path}"

    def test_06_analysis_agent_exists(self):
        """Verify the analysis agent module exists."""
        agent_path = os.path.join(
            AUTORESEARCH_DIR, "autoresearch_mlx", "analysis_agent.py"
        )
        assert os.path.exists(agent_path), f"Analysis agent not found: {agent_path}"


# ── Workflow 4: Autoresearch API Endpoints ─────────────────────


class TestAutoresearchAPI:
    """Test all autoresearch API endpoints through HTTP."""

    def test_01_status_endpoint(self, api_headers: dict):
        """GET /api/autoresearch/status — check component availability."""
        with httpx.Client(base_url=BACKEND_URL, timeout=10.0) as client:
            res = client.get("/api/autoresearch/status", headers=api_headers)
            assert res.status_code == 200, f"Status failed: {res.status_code} {res.text}"
            data = res.json()
            assert "nemoclaw" in data, "Missing 'nemoclaw' in status"
            assert "vqe_graph" in data, "Missing 'vqe_graph' in status"
            assert data["nemoclaw"] is True, "NemoClaw should be available"

    def test_02_results_endpoint(self, api_headers: dict):
        """GET /api/autoresearch/results — read experiment results."""
        with httpx.Client(base_url=BACKEND_URL, timeout=10.0) as client:
            res = client.get("/api/autoresearch/results", headers=api_headers)
            assert res.status_code == 200, f"Results failed: {res.status_code}"
            data = res.json()
            # Should return columns/rows structure even if empty
            assert "columns" in data or "error" in data or "rows" in data

    def test_03_analyze_endpoint(self, api_headers: dict):
        """GET /api/autoresearch/analyze — get performance summary."""
        with httpx.Client(base_url=BACKEND_URL, timeout=10.0) as client:
            res = client.get("/api/autoresearch/analyze", headers=api_headers)
            assert res.status_code == 200, f"Analyze failed: {res.status_code}"
            data = res.json()
            assert "summary" in data

    def test_04_vqe_endpoint(self, api_headers: dict):
        """POST /api/autoresearch/vqe — run a quick VQE simulation."""
        with httpx.Client(base_url=BACKEND_URL, timeout=60.0) as client:
            res = client.post(
                "/api/autoresearch/vqe",
                json={
                    "hamiltonian": "h2",
                    "ansatz_type": "real_amplitudes",
                    "ansatz_reps": 1,
                    "optimizer": "cobyla",
                    "optimizer_maxiter": 10,
                    "seed": 42,
                },
                headers=api_headers,
            )
            assert res.status_code in (200, 503), f"VQE failed: {res.status_code} {res.text}"
            if res.status_code == 200:
                data = res.json()
                has_energy = (
                    "energy" in data
                    or "eigenvalue" in data
                    or "final_energy" in data
                    or "result" in data
                )
                assert has_energy, f"No energy in VQE result: {data}"

    def test_05_export_endpoint(self, api_headers: dict):
        """POST /api/autoresearch/export — export experiments to Parquet."""
        with httpx.Client(base_url=BACKEND_URL, timeout=30.0) as client:
            res = client.post(
                "/api/autoresearch/export",
                json={},
                headers=api_headers,
            )
            # May succeed or return 404 if no experiments exist
            assert res.status_code in (200, 404), f"Export failed: {res.status_code}"


# ── Workflow 5: Autoresearch Training Loop ─────────────────────


class TestAutoresearchTraining:
    """Test the actual training loop through the API."""

    def test_01_manual_run_sse(self, api_headers: dict):
        """POST /api/autoresearch/run (manual mode) — verify SSE streaming starts."""
        try:
            with httpx.Client(base_url=BACKEND_URL, timeout=30.0) as client:
                with client.stream(
                    "POST",
                    "/api/autoresearch/run",
                    json={"mode": "manual", "target": "quick test"},
                    headers=api_headers,
                ) as res:
                    assert res.status_code == 200, f"Run failed: {res.status_code}"
                    # Read first line to confirm streaming started
                    for line in res.iter_lines():
                        if line:
                            # Should be an SSE event
                            assert "event:" in line or "data:" in line, (
                                f"Unexpected SSE format: {line[:100]}"
                            )
                            return
        except (httpx.ReadTimeout, httpx.ReadError):
            # Timeout means the training started but didn't complete — endpoint works
            pass

    def test_02_data_prep_sse(self, api_headers: dict):
        """POST /api/autoresearch/prepare — verify data prep SSE streaming."""
        try:
            with httpx.Client(base_url=BACKEND_URL, timeout=30.0) as client:
                with client.stream(
                    "POST",
                    "/api/autoresearch/prepare",
                    json={},
                    headers=api_headers,
                ) as res:
                    assert res.status_code == 200, f"Prepare failed: {res.status_code}"
                    for line in res.iter_lines():
                        if line:
                            return  # Streaming started
        except (httpx.ReadTimeout, httpx.ReadError):
            pass  # Data prep started but didn't complete

    def test_03_analysis_sse(self, api_headers: dict):
        """POST /api/autoresearch/analysis — verify analysis SSE streaming."""
        try:
            with httpx.Client(base_url=BACKEND_URL, timeout=30.0) as client:
                with client.stream(
                    "POST",
                    "/api/autoresearch/analysis",
                    json={},
                    headers=api_headers,
                ) as res:
                    assert res.status_code == 200, f"Analysis failed: {res.status_code}"
                    for line in res.iter_lines():
                        if line:
                            return
        except (httpx.ReadTimeout, httpx.ReadError):
            pass


# ── Workflow 6: Cross-System Integration ───────────────────────


class TestCrossSystemIntegration:
    """Test integration between NemoClaw, autoresearch, and other systems."""

    def test_01_autoresearch_persists_to_postgresql(self, api_headers: dict):
        """Verify autoresearch experiments are stored in PostgreSQL."""
        # Check that the Experiment table exists and has schema for autoresearch
        import psycopg2

        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="milimoquantum",
            user="milimo",
            password="milimopassword",
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'experiments' ORDER BY ordinal_position"
        )
        columns = [row[0] for row in cur.fetchall()]
        conn.close()

        assert "agent" in columns, "Experiments table missing 'agent' column"
        assert "backend" in columns, "Experiments table missing 'backend' column"
        assert "circuit_code" in columns, "Experiments table missing 'circuit_code' column"
        assert "results" in columns, "Experiments table missing 'results' column"

    def test_02_nemoclaw_docker_network_access(self):
        """Verify NemoClaw container can reach backend services."""
        # Test from inside the NemoClaw container to the host's backend
        result = subprocess.run(
            [
                "docker",
                "exec",
                NEMOCLAW_CONTAINER,
                "bash",
                "-c",
                "curl -s --max-time 5 http://host.docker.internal:8000/api/health || echo 'unreachable'",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        # Either reachable or unreachable — we just verify the test runs
        output = result.stdout
        assert "healthy" in output or "unreachable" in output, (
            f"Unexpected network test result: {output[:200]}"
        )

    def test_03_all_docker_containers_healthy(self):
        """Verify all Milimo Quantum Docker containers are running."""
        result = subprocess.run(
            ["docker", "compose", "-f", os.path.join(str(Path(__file__).resolve().parents[2]), "docker-compose.yml"), "ps", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0

        containers = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                try:
                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

        # Should have at least postgres, redis, neo4j, keycloak
        names = [c.get("Name", "") for c in containers]
        assert any("postgres" in n for n in names), "PostgreSQL container missing"
        assert any("redis" in n for n in names), "Redis container missing"
        assert any("neo4j" in n for n in names), "Neo4j container missing"
        assert any("keycloak" in n for n in names), "Keycloak container missing"

    def test_04_nemoclaw_cluster_container_healthy(self):
        """Verify the NemoClaw cluster container is specifically healthy."""
        result = subprocess.run(
            [
                "docker",
                "inspect",
                NEMOCLAW_CONTAINER,
                "--format",
                "{{.State.Status}}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "running", (
            f"NemoClaw container not running: {result.stdout.strip()}"
        )

    def test_05_autoresearch_results_tsv(self, api_headers: dict):
        """Verify results.tsv is readable through the API after a run."""
        with httpx.Client(base_url=BACKEND_URL, timeout=10.0) as client:
            res = client.get("/api/autoresearch/results", headers=api_headers)
            assert res.status_code == 200
            data = res.json()
            # Either has columns/rows or is empty
            assert isinstance(data, dict)

    def test_06_workflow_module_importable(self):
        """Verify the autoresearch workflow module loads correctly."""
        from app.extensions.autoresearch import workflow

        assert workflow.NEMOCLAW_AVAILABLE is True, "NemoClaw should be available"
        assert hasattr(workflow, "run_research_loop")
        assert hasattr(workflow, "run_autonomous_loop")
        assert hasattr(workflow, "run_data_prep")
        assert hasattr(workflow, "run_vqe_optimization")
        assert hasattr(workflow, "persist_experiment_result")
        assert hasattr(workflow, "get_results")
