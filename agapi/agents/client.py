from agapi.agents.config import AgentConfig
from typing import Dict, Any
import httpx

from .config import AgentConfig
from .slurm import SlurmClient

class AGAPIClient:
    def __init__(
        self,
        api_key: str,
        slurm_host: str,
        slurm_user: str,
        slurm_password: str,
        api_base: str = "https://atomgpt.org",
        timeout: int = 120,
    ):
        self.api_key = api_key
        self.api_base = api_base
        self.timeout = timeout
        self.slurm_host = slurm_host
        self.slurm_user = slurm_user
        self.slurm_password= slurm_password
        self.slurm_client = SlurmClient(slurm_host, slurm_user, slurm_password) if slurm_host else None
        if self.slurm_client:
            self.slurm_client.connect()


    def request(self, endpoint: str, params: dict = None, method: str = "GET"):
        """
        Make HTTP request to API

        Args:
            endpoint: API endpoint (e.g., "generate_interface")
            params: Query parameters or request body
            method: HTTP method ("GET" or "POST")

        Returns:
            Response data (dict for JSON, str for text/plain)
        """
        import httpx

        url = f"{self.api_base}/{endpoint}"
        headers = {}

        # Add API key to params (not headers) for AGAPI
        if params is None:
            params = {}
        params["APIKEY"] = self.api_key

        try:
            if method == "GET":
                response = httpx.get(url, params=params, timeout=self.timeout)
            else:
                response = httpx.post(
                    url, json=params, headers=headers, timeout=self.timeout
                )

            response.raise_for_status()

            # Check content type to decide parsing
            content_type = response.headers.get("content-type", "")

            if "application/json" in content_type:
                return response.json()
            elif "text/plain" in content_type or "text/html" in content_type:
                return response.text
            else:
                # Try JSON first, fall back to text
                try:
                    return response.json()
                except:
                    return response.text

        except httpx.HTTPStatusError as e:
            raise Exception(
                f"API error ({e.response.status_code}): {e.response.text}"
            )
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
