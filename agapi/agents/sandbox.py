class SandboxManager:
    """Manages isolated Python venv environments for SLURM jobs."""

    def __init__(self, slurm_client, env_base_path: str = "~/.slurm_agent/envs"):
        self.slurm = slurm_client
        self.env_base_path = env_base_path

    def _get_env_path(self, name: str) -> str:
        """Returns the full path for a given environment name."""
        return f"{self.env_base_path}/{name}"

    def list_sandboxes(self):
        """List available venv environments."""
        cmd = f"source ~/.bashrc && ls -1 {self.env_base_path}"
        code, out, err = self.slurm._run_command(cmd)
        if code != 0:
            return []
        return [line.strip() for line in out.splitlines() if line.strip()]

    def ensure_sandbox(self, name: str, packages: list) -> bool:
        """
        Ensures a sandbox with the given name exists.
        Creates it and installs packages if it doesn't exist.
        """
        print(f"Checking for sandbox '{name}'...")
        env_path = self._get_env_path(name)

        check_cmd = f"source ~/.bashrc && test -x {env_path}/bin/python"
        code, _, _ = self.slurm._run_command(check_cmd)

        if code == 0:
            print(f"Sandbox '{name}' already exists.")
            if packages:
                print(f"Ensuring packages in '{name}': {', '.join(packages)}")
                self.install_packages(name, packages)
            return True

        print(f"Sandbox '{name}' not found. Creating...")
        return self.create_sandbox(name, packages)

    def create_sandbox(self, name: str, packages: list) -> bool:
        """Create a new venv environment and install packages."""
        print(f"Creating venv '{name}'...")
        env_path = self._get_env_path(name)

        self.slurm._run_command(f"source ~/.bashrc && mkdir -p {self.env_base_path}")

        cmd = f"source ~/.bashrc && python3 -m venv {env_path}"
        code, out, err = self.slurm._run_command(cmd)

        if code != 0:
            print(f"Failed to create sandbox '{name}':")
            print(f"  STDOUT: {out}")
            print(f"  STDERR: {err}")
            return False

        if packages:
            return self.install_packages(name, packages)

        return True

    def install_packages(self, name: str, packages: list) -> bool:
        """Install packages into a specific sandbox."""
        print(f"Installing packages in '{name}': {', '.join(packages)}")
        env_path = self._get_env_path(name)

        pkgs_str = " ".join(packages)
        cmd = f"source ~/.bashrc && {env_path}/bin/pip install {pkgs_str}"

        code, out, err = self.slurm._run_command(cmd)
        if code == 0:
            print(f"Packages installed in '{name}'.")
            return True
        else:
            print(f"Failed to install packages in '{name}':")
            print(f"  STDOUT: {out}")
            print(f"  STDERR: {err}")
            return False

    def wrap_job_script(self, script: str, sandbox_name: str) -> str:
        """Injects venv activation into a SLURM script after the last #SBATCH directive."""
        lines = script.splitlines()

        last_sbatch_idx = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("#SBATCH"):
                last_sbatch_idx = i

        insert_idx = 0
        if last_sbatch_idx >= 0:
            insert_idx = last_sbatch_idx + 1
        elif lines and lines[0].startswith("#!"):
            insert_idx = 1

        env_path = self._get_env_path(sandbox_name)
        activation_block = [
            "",
            f"source {env_path}/bin/activate",
            "",
        ]

        new_lines = lines[:insert_idx] + activation_block + lines[insert_idx:]
        return "\n".join(new_lines)
