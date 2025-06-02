"""
KServer.py
A class to connect with a Koordinates server.
"""

import requests
import os
import logging
from dotenv import load_dotenv
from pykaahma_linz.ContentManager import ContentManager
from pykaahma_linz.CustomErrors import KServerError, KServerBadRequestError

logger = logging.getLogger(__name__)
load_dotenv()

DEFAULT_BASE_URL = "https://data.linz.govt.nz/"
DEFAULT_API_VERSION = "v1.x"


class KServer:
    def __init__(
        self, api_key, base_url=DEFAULT_BASE_URL, api_version=DEFAULT_API_VERSION, 
    ):
        """Initializes the KServer instance with the base URL and API version.
        Args:
            base_url (str): The base URL of the Koordinates server. Defaults to 'https://data.linz.govt.nz/'.
            api_version (str): The API version to use. Defaults to 'v1.x'.
        """
        self._base_url = base_url
        self._api_version = api_version
        self._content_manager = None
        self._wfs_manager = None
        self._api_key = api_key
        if not self._api_key:
            raise KServerError("API key must be provided.")
        logger.debug(
            f"KServer initialized with base URL: {self._base_url}"
        )

    @property
    def _service_url(self) -> str:
        """
        Returns the service URL for the Koordinates server.

        Returns:
            str: The full service URL.
        """
        return f"{self._base_url}services/"

    @property
    def _api_url(self) -> str:
        """
        Returns the API URL for the Koordinates server.

        Returns:
            str: The full API URL.
        """
        return f"{self._service_url}api/{self._api_version}/"

    @property
    def _wfs_url(self):
        """
        Returns the WFS URL for the Koordinates server.

        Returns:
            str: The WFS URL.
        """
        return f"{self._service_url}wfs/"

    @property
    def content(self):
        if self._content_manager is None:
            self._content_manager = ContentManager(self)
        return self._content_manager

    def _get(self, url: str, params: dict = None):
        """
        Makes a GET request to the specified URL with the provided parameters.
        Injects the API key into the request headers.

        Args:
            url (str): The URL to send the GET request to.
            params (dict): Optional parameters to include in the request.

        Returns:
            dict: The JSON response from the server.

        Raises:
            KServerBadRequestError: If the request fails with a 400 status code.
            KServerError: For other HTTP errors.
        """
        headers = {"Authorization": f"key {self._api_key}"}
        logger.debug(f"Making kserver GET request to {url} with params {params}")
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 400:
            raise KServerBadRequestError(response.text)
        response.raise_for_status()
        return response.json()

    def reset(self):
        """
        Resets the KServer instance, forcing the content manager and WFS manager
        to reinitialise next time they are accessed.
        This is useful if the API key or other configurations change.
        """
        self._content_manager = None
        self._wfs_manager = None
        logger.info("KServer instance reset.")

    def __repr__(self):
        return f"KServer(base_url={self._base_url}, api_version={self._api_version})"