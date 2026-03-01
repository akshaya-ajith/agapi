"""
Integration tests for SLURM agent tools.

Real SSH connection to the cluster.
Fill in SLURM_HOST, SLURM_USER, SLURM_PASSWORD before running.

Run:
    pytest -v -s test_slurm.py
"""

import os
import time
import pytest
from agapi.agents.slurm import SlurmClient
from agapi.agents.functions import (
    submit_slurm_job,
    get_slurm_job_status,
    get_slurm_job_output,
)

# ---------------------------------------------------------------------
# Connection credentials — fill these in
# ---------------------------------------------------------------------

SLURM_HOST = "atomgptlab01.wse.jhu.edu"
SLURM_USER = "aajith1"
SLURM_PASSWORD = "T1nT1n7680!"


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

@pytest.fixture(scope="session")
def slurm_client():
    """Create and connect a real SlurmClient for the test session."""
    if not SLURM_HOST or not SLURM_USER or not SLURM_PASSWORD:
        pytest.skip("SLURM credentials not set — fill in SLURM_HOST/USER/PASSWORD")
    client = SlurmClient(SLURM_HOST, SLURM_USER, SLURM_PASSWORD)
    connected = client.connect()
    if not connected:
        pytest.skip(f"Could not connect to SLURM host: {SLURM_HOST}")
    yield client


# ---------------------------------------------------------------------
# Test scripts
# ---------------------------------------------------------------------

SIMPLE_SCRIPT = """\
#!/bin/bash
#SBATCH --job-name=pytest_hello
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:02:00

echo "Hello from pytest!"
"""

MATH_SCRIPT = """\
#!/bin/bash
#SBATCH --job-name=pytest_math
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:02:00

python3 -c "print(789 + 90)"
"""

PYTHON_SCRIPT = """\
#!/bin/bash
#SBATCH --job-name=pytest_python
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:05:00

python3 -c "
import sys
print('Python version:', sys.version)
print('Platform:', sys.platform)
squares = [x**2 for x in range(10)]
print('Squares:', squares)
print('Sum:', sum(squares))
"
"""

FAIL_SCRIPT = """\
#!/bin/bash
#SBATCH --job-name=pytest_fail
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err
#SBATCH --ntasks=1
#SBATCH --mem=1G
#SBATCH --time=00:02:00

exit 1
"""


# =====================================================================
# SlurmClient direct tests
# =====================================================================

class TestSlurmClientDirect:
    """Test the SlurmClient class directly (not through functions.py)."""

    def test_connect(self, slurm_client):
        """Connection should already be established by the fixture."""
        assert slurm_client.sftp is not None

    def test_run_command(self, slurm_client):
        """Should be able to run a simple command on the cluster."""
        code, out, err = slurm_client._run_command("echo hello")
        assert code == 0
        assert "hello" in out

    def test_check_software_python(self, slurm_client):
        """Python3 should be available on the cluster."""
        assert slurm_client.check_software("sys") is True

    def test_check_software_missing(self, slurm_client):
        """A nonsense package should not be found."""
        assert slurm_client.check_software("nonexistent_pkg_xyz_12345") is False

    def test_submit_and_status(self, slurm_client):
        """Submit a simple job and verify we get a valid job ID and status."""
        job_id = slurm_client.submit_job(SIMPLE_SCRIPT)
        assert job_id.isdigit(), f"Expected numeric job ID, got: {job_id}"

        status = slurm_client.get_job_status(job_id)
        assert status in ("PENDING", "RUNNING", "COMPLETED", "COMPLETING"), \
            f"Unexpected status: {status}"


# =====================================================================
# functions.py wrapper tests
# =====================================================================

class TestSlurmFunctions:
    """Test the agent-facing functions in functions.py."""

    def test_submit_slurm_job_no_client(self):
        """Should return error when no slurm_client is provided."""
        result = submit_slurm_job("#!/bin/bash\necho hi", slurm_client=None)
        assert "error" in result

    def test_submit_slurm_job_success(self, slurm_client):
        """Should successfully submit a job and return a job ID."""
        result = submit_slurm_job(SIMPLE_SCRIPT, slurm_client=slurm_client)
        assert result.get("status") == "success"
        assert "job_id" in result
        assert result["job_id"].isdigit()

    def test_get_status_no_client(self):
        """Should return error when no slurm_client is provided."""
        result = get_slurm_job_status("99999", slurm_client=None)
        assert "error" in result

    def test_get_output_no_client(self):
        """Should return error when no slurm_client is provided."""
        result = get_slurm_job_output("99999", slurm_client=None)
        assert "error" in result

    def test_submit_and_monitor_math(self, slurm_client):
        """Submit a math job, wait for completion, and verify output."""
        # Submit
        result = submit_slurm_job(MATH_SCRIPT, slurm_client=slurm_client)
        assert result.get("status") == "success"
        job_id = result["job_id"]
        print(f"\n  Submitted math job: {job_id}")

        # Poll until done (max 60 seconds)
        for i in range(30):
            status_result = get_slurm_job_status(job_id, slurm_client=slurm_client)
            job_status = status_result.get("job_status", "UNKNOWN")
            print(f"  Poll {i+1}: {job_status}")

            if job_status in ("COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"):
                break
            time.sleep(2)

        assert job_status == "COMPLETED", f"Job did not complete: {job_status}"

        # Retrieve output
        output_result = get_slurm_job_output(job_id, slurm_client=slurm_client)
        assert output_result.get("status") == "success"
        assert "879" in output_result.get("output", ""), \
            f"Expected 879 in output, got: {output_result.get('output')}"
        print(f"  Output: {output_result['output'].strip()}")

    def test_submit_and_monitor_python(self, slurm_client):
        """Submit a Python job, wait for completion, and verify output."""
        # Submit
        result = submit_slurm_job(PYTHON_SCRIPT, slurm_client=slurm_client)
        assert result.get("status") == "success"
        job_id = result["job_id"]
        print(f"\n  Submitted Python job: {job_id}")

        # Poll until done (max 120 seconds)
        job_status = "UNKNOWN"
        for i in range(60):
            status_result = get_slurm_job_status(job_id, slurm_client=slurm_client)
            job_status = status_result.get("job_status", "UNKNOWN")
            print(f"  Poll {i+1}: {job_status}")

            if job_status in ("COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"):
                break
            time.sleep(2)

        assert job_status == "COMPLETED", f"Job did not complete: {job_status}"

        # Retrieve output
        output_result = get_slurm_job_output(job_id, slurm_client=slurm_client)
        assert output_result.get("status") == "success"
        output_text = output_result.get("output", "")
        assert "Python version:" in output_text
        assert "Squares:" in output_text
        print(f"  Output:\n{output_text}")

    def test_submit_failing_job(self, slurm_client):
        """Submit a job that exits with error and verify SCRIPT_FAILED status."""
        result = submit_slurm_job(FAIL_SCRIPT, slurm_client=slurm_client)
        assert result.get("status") == "success"
        job_id = result["job_id"]
        print(f"\n  Submitted failing job: {job_id}")

        # Poll until done
        job_status = "UNKNOWN"
        for i in range(30):
            status_result = get_slurm_job_status(job_id, slurm_client=slurm_client)
            job_status = status_result.get("job_status", "UNKNOWN")
            print(f"  Poll {i+1}: {job_status}")

            if "COMPLETED" in job_status or "FAILED" in job_status or \
               "CANCELLED" in job_status or "TIMEOUT" in job_status:
                break
            time.sleep(2)

        assert "SCRIPT_FAILED" in job_status, \
            f"Expected SCRIPT_FAILED but got: {job_status}"
