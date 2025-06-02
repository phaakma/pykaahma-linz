"""
JobResult.py
"""

import logging
import os
import time
import asyncio
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

class JobResult:
    def __init__(self, payload: dict, kserver: "KServer", poll_interval: int = 10, timeout: int = 300):
        self._initial_payload = payload
        self._job_url = payload["url"]
        self._id = payload["id"]
        self._poll_interval = poll_interval
        self._timeout = timeout
        self._last_response = payload  # Start with the initial state
        self._kserver = kserver  # Store the KServer instance

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        """Returns the name of the job."""
        return self._last_response.get("name", "unknown_name")

    @property
    def status(self) -> str:
        self._refresh()
        return self._last_response.get("state")

    @property
    def download_url(self) -> Optional[str]:
        return self._last_response.get("download_url")

    @property
    def status(self) -> str:
        self._refresh_sync()
        return self._last_response.get("state")

    @property
    def progress(self) -> Optional[float]:
        """Returns the progress of the job as a percentage."""
        return self._last_response.get("progress", None)

    @property
    def created_at(self) -> Optional[str]:
        """Returns the creation time of the job."""
        return self._last_response.get("created_at", None)

    def _refresh(self):
        response = requests.get(self._job_url)
        response.raise_for_status()
        self._last_response = response.json()

    def to_dict(self) -> dict:
        return self._last_response

    def __str__(self) -> str:
        return (
            f"JobResult(id={self.id}, name='{self.name}', "
            f"status='{self._last_response.get('state')}', "
            f"download_url={'set' if self.download_url else 'not set'})"
        )

    def _refresh_sync(self):
        """Refresh job status using synchronous HTTP via KServer."""
        self._last_response = self._kserver.get(self._job_url)

    async def _refresh_async(self):
        """Refresh job status using asynchronous HTTP via KServer."""
        self._last_response = await self._kserver.async_get(self._job_url)

    def output(self) -> dict:
        """Blocking: wait for the job to complete synchronously."""
        start = time.time()
        # timeout the while loop if it takes more than ten minutes 
        # to complete
        max_time = 600 # 10 minutes in seconds

        while True and time.time() - start < max_time:
            self._refresh_sync()
            state = self._last_response.get("state")
            if state in ("complete", "failed", "cancelled"):
                break

            if (time.time() - start) > self._timeout:
                raise TimeoutError(f"Export job {self._id} did not complete within timeout.")

            time.sleep(self._poll_interval)

        if self._last_response.get("state") != "complete":
            raise RuntimeError(f"Export job {self._id} failed with state: {self._last_response.get('state')}")

        return self._last_response

    async def output_async(self) -> dict:
        """Non-blocking: wait for the job to complete asynchronously."""
        start = asyncio.get_event_loop().time()
        max_time = 600 # 10 minutes in seconds
        while True and (asyncio.get_event_loop().time() - start < max_time):
            await self._refresh_async()
            state = self._last_response.get("state")
            logger.debug(f"Job {self._id} state: {state} progress: {self.progress}")
            if state in ("complete", "failed", "cancelled"):
                break

            if (asyncio.get_event_loop().time() - start) > self._timeout:
                raise TimeoutError(f"Export job {self._id} did not complete within timeout.")

            await asyncio.sleep(self._poll_interval)

        if self._last_response.get("state") != "complete":
            raise RuntimeError(f"Export job {self._id} failed with state: {self._last_response.get('state')}")

        return self._last_response

    def download(self, folder: str, file_name: Optional[str] = None) -> str:
        """ 
        Waits for job to finish, then downloads the file synchronously.
        Args:
            folder (str): The folder where the file will be saved.
            file_name (Optional[str]): The name of the file to save. If None, uses job name.
        """
        
        self.output()  # ensure job is complete
        if not self.download_url:
            raise ValueError("Download URL not available. Job may not have completed successfully.")

        file_name = f'{file_name}.zip' if file_name else f'{self.name}.zip'
        file_path = os.path.join(folder, file_name)
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

        headers = {"Authorization": f"key {self._kserver._api_key}"}

        with httpx.Client(follow_redirects=True) as client:
            # First, resolve the redirect to get the actual file URL
            resp = client.get(self.download_url, headers=headers, follow_redirects=True)
            resp.raise_for_status()
            final_url = str(resp.url)

            # Now stream the file from the final URL (usually S3, no auth header needed)
            with client.stream("GET", final_url) as r, open(file_path, "wb") as f:
                r.raise_for_status()
                for chunk in r.iter_bytes():
                    f.write(chunk)
        return file_path

    async def download_async(self, folder: str, file_name: Optional[str] = None):
        """
        Waits for job to finish, then downloads the file asynchronously.
        Args:
            folder (str): The folder where the file will be saved.
        """
        await self.output_async()  # ensure job is finished
        if not self.download_url:
            raise ValueError("Download URL not available. Job may not have completed successfully.")

        file_name = f'{file_name}.zip' if file_name else f'{self.name}.zip'
        file_path = os.path.join(folder, file_name)
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

        headers = {"Authorization": f"key {self._kserver._api_key}"}

        async with httpx.AsyncClient(follow_redirects=True) as client:
            # First, resolve the redirect to get the actual file URL
            resp = await client.get(self.download_url, headers=headers, follow_redirects=True)
            resp.raise_for_status()
            final_url = str(resp.url)

            # Now stream the file from the final URL (usually S3, no auth header needed)
            async with client.stream("GET", final_url) as r:
                r.raise_for_status()
                with open(file_path, "wb") as f:
                    async for chunk in r.aiter_bytes():
                        await asyncio.to_thread(f.write, chunk)
        return file_path