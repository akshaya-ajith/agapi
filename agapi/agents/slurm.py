import time
import paramiko


class SlurmClient:
    """SLURM client using SSH via Paramiko."""

    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sftp = None
        self.job_files = {}  # Map job_id -> output_filename_pattern
        self.fallback_host = None

    def set_fallback_host(self, host: str):
        """Sets a secondary host to check for output files."""
        self.fallback_host = host

    def connect(self):
        """Establishes the SSH connection."""
        try:
            self.client.connect(self.host, username=self.user, password=self.password, timeout=10)
            self.sftp = self.client.open_sftp()
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def _run_command(self, command):
        stdin, stdout, stderr = self.client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        return exit_status, stdout.read().decode().strip(), stderr.read().decode().strip()

    def submit_job(self, script_content: str) -> str:
        filename = f"job_{int(time.time())}.sh"

        try:
            with self.sftp.file(filename, 'w') as f:
                f.write(script_content)
        except Exception as e:
            raise Exception(f"Failed to upload script via SFTP: {e}")

        code, out, err = self._run_command(f"sbatch {filename}")

        if code != 0:
            raise Exception(f"sbatch failed: {err}")

        try:
            job_id = out.split()[-1]
        except IndexError:
            raise Exception(f"Could not parse job ID from sbatch output: {out}")

        output_pattern = "slurm-%j.out"
        for line in script_content.splitlines():
            if line.strip().startswith("#SBATCH --output="):
                output_pattern = line.strip().split("=")[1]
                break

        self.job_files[job_id] = output_pattern
        print(f"Job submitted: {job_id} (output: {output_pattern})")
        return job_id

    def get_job_status(self, job_id: str) -> str:
        code, out, err = self._run_command(f"squeue -j {job_id} -h -o %T")

        if not out:
            # Job is no longer in the queue — check sacct for final state and exit code
            # Use JobID format to get both the allocation and batch step
            code_sacct, out_sacct, _ = self._run_command(
                f"sacct -j {job_id} -n -o JobID,State,ExitCode -P"
            )
            print(f"sacct output: {out_sacct}")
            if out_sacct:
                # sacct returns lines like:
                #   104|COMPLETED|0:0      <- job allocation (always exit 0)
                #   104.batch|COMPLETED|1:0 <- batch step (actual script exit code)
                # We prefer the .batch line for the real exit code
                state = "COMPLETED"
                exit_code = 0
                for line in out_sacct.strip().split("\n"):
                    parts = line.split("|")
                    if len(parts) >= 3:
                        job_step = parts[0].strip()
                        line_state = parts[1].strip()
                        line_exit = parts[2].strip()
                        if ".batch" in job_step:
                            state = line_state
                            exit_code = int(line_exit.split(":")[0])
                            break
                        elif job_step == str(job_id):
                            state = line_state
                            exit_code = int(line_exit.split(":")[0])

                if state == "COMPLETED" and exit_code != 0:
                    return f"SCRIPT_FAILED (exit code {exit_code})"
                return state
            return "COMPLETED"

        return out.strip()

    def get_job_output(self, job_id: str) -> str:
        pattern = self.job_files.get(job_id, "slurm-%j.out")
        outfile = pattern.replace("%j", job_id)

        files_to_try = [
            outfile,
            f"slurm-{job_id}.out",
            f"output_{job_id}.txt",
            f"output/slurm-{job_id}.out",
            f"output/output_{job_id}.txt",
        ]

        max_retries = 5
        for i in range(max_retries):
            for fname in files_to_try:
                try:
                    with self.sftp.file(fname, 'r') as f:
                        content = f.read().decode()
                        if content.strip():
                            return content
                except IOError:
                    code_host, batch_host, _ = self._run_command(
                        f"scontrol show job {job_id} -o | grep -oP 'BatchHost=\\K\\w+'"
                    )
                    if batch_host and batch_host.strip() and batch_host.strip() != "localhost":
                        node = batch_host.strip()
                        code_rem, out_rem, _ = self._run_command(f"ssh {node} 'cat {fname}' 2>/dev/null")
                        if code_rem == 0 and out_rem.strip():
                            return out_rem

                        abs_path = f"/home/{self.user}/{fname}"
                        code_rem2, out_rem2, _ = self._run_command(f"ssh {node} 'cat {abs_path}' 2>/dev/null")
                        if code_rem2 == 0 and out_rem2.strip():
                            return out_rem2

            if self.fallback_host:
                print(f"File not found on {self.host}, trying fallback: {self.fallback_host}...")
                for fname in files_to_try:
                    try:
                        temp_client = paramiko.SSHClient()
                        temp_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        temp_client.connect(self.fallback_host, username=self.user, password=self.password, timeout=5)

                        cmd = f"cat output/{fname.split('/')[-1]} 2>/dev/null || cat {fname} 2>/dev/null"
                        stdin, stdout, stderr = temp_client.exec_command(cmd)
                        content = stdout.read().decode().strip()
                        temp_client.close()

                        if content:
                            print(f"Found output on fallback host {self.fallback_host}")
                            return content
                    except Exception as e:
                        print(f"Fallback check failed: {e}")

            if i < max_retries - 1:
                time.sleep(2)

        return f"Output file {outfile} not found after retries (checked {self.host} and {self.fallback_host})."

    def check_software(self, package_name: str, check_command: str = None) -> bool:
        """Check if software/package exists on cluster."""
        if check_command is None:
            check_command = f"python3 -c 'import {package_name}'"
        print(f"Checking for software: {package_name}...")
        code, out, err = self._run_command(check_command)
        return code == 0

    def install_package(self, package_name: str, method: str = "pip") -> bool:
        """Install package on cluster."""
        print(f"Installing {package_name} via {method}...")
        if method == "pip":
            cmd = f"python3 -m pip install --user {package_name}"
        elif method == "conda":
            cmd = f"conda install -y {package_name}"
        else:
            print(f"Unknown installation method: {method}")
            return False

        code, out, err = self._run_command(cmd)
        if code == 0:
            print(f"Successfully installed {package_name}")
            return True
        else:
            print(f"Failed to install {package_name}: {err}")
            return False