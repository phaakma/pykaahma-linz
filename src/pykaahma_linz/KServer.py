"""
KServer.py
A class to connect with a Koordinates server.
"""

import requests
import os
import logging
from pykaahma_linz.ContentManager import ContentManager
from pykaahma_linz.CustomErrors import KServerError, KServerBadRequestError
import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://data.linz.govt.nz/"
DEFAULT_API_VERSION = "v1.x"


class KServer:
    def __init__(
        self,
        api_key,
        base_url=DEFAULT_BASE_URL,
        api_version=DEFAULT_API_VERSION,
    ) -> None:
        """
        Initializes the KServer instance with the base URL, API version, and API key.

        Parameters:
            api_key (str): The API key for authenticating with the Koordinates server.
            base_url (str, optional): The base URL of the Koordinates server. Defaults to 'https://data.linz.govt.nz/'.
            api_version (str, optional): The API version to use. Defaults to 'v1.x'.
        """
        self._base_url = base_url
        self._api_version = api_version
        self._content_manager = None
        self._wfs_manager = None
        self._api_key = api_key
        if not self._api_key:
            raise KServerError("API key must be provided.")
        logger.debug(f"KServer initialized with base URL: {self._base_url}")

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
    def _wfs_url(self) -> str:
        """
        Returns the WFS URL for the Koordinates server.

        Returns:
            str: The WFS URL.
        """
        return f"{self._service_url}wfs/"

    @property
    def content(self) -> ContentManager:
        """
        Returns the ContentManager instance for this server.

        Returns:
            ContentManager: The content manager associated with this server.
        """
        if self._content_manager is None:
            self._content_manager = ContentManager(self)
        return self._content_manager

    def get(self, url: str, params: dict = None) -> dict:
        """
        Makes a synchronous GET request to the specified URL with the provided parameters.
        Injects the API key into the request headers.

        Parameters:
            url (str): The URL to send the GET request to.
            params (dict, optional): Query parameters to include in the request. Defaults to None.

        Returns:
            dict: The JSON response from the server.

        Raises:
            KServerBadRequestError: If the request fails with a 400 status code.
            KServerError: For other HTTP errors or request exceptions.
        """
        headers = {"Authorization": f"key {self._api_key}"}
        logger.debug(f"Making kserver GET request to {url} with params {params}")
        try:
            response = httpx.get(url, headers=headers, params=params, timeout=30)
        except httpx.RequestError as exc:
            logger.error(f"An error occurred while requesting {exc.request.url!r}.")
            raise KServerError(str(exc)) from exc

        if response.status_code == 400:
            raise KServerBadRequestError(response.text)
        response.raise_for_status()
        return response.json()

    async def async_get(self, url: str, params: dict = None) -> dict:
        """
        Makes an asynchronous GET request to the specified URL with the provided parameters.
        Injects the API key into the request headers.

        Parameters:
            url (str): The URL to send the GET request to.
            params (dict, optional): Query parameters to include in the request. Defaults to None.

        Returns:
            dict: The JSON response from the server.

        Raises:
            KServerBadRequestError: If the request fails with a 400 status code.
            KServerError: For other HTTP errors or request exceptions.
        """
        headers = {"Authorization": f"key {self._api_key}"}
        logger.debug(f"Making async kserver GET request to {url} with params {params}")
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(url, headers=headers, params=params)
            except httpx.RequestError as exc:
                logger.error(f"An error occurred while requesting {exc.request.url!r}.")
                raise KServerError(str(exc)) from exc

            if response.status_code == 400:
                raise KServerBadRequestError(response.text)
            response.raise_for_status()
            return response.json()

    def reset(self) -> None:
        """
        Resets the KServer instance, forcing the content manager and WFS manager
        to reinitialize the next time they are accessed. This is useful if the API key
        or other configurations change.

        Returns:
            None
        """
        self._content_manager = None
        self._wfs_manager = None
        logger.info("KServer instance reset.")

    def __repr__(self) -> str:
        """
        Returns a string representation of the KServer instance.

        Returns:
            str: String representation of the KServer instance.
        """
        return f"KServer(base_url={self._base_url}, api_version={self._api_version})"
