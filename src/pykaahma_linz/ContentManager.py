"""
ContentManager is a class that manages the content
of a KServer instance.
"""

import requests
from pykaahma_linz.CustomErrors import (
    KServerBadRequestError,
    KServerError,
    KUnknownItemTypeError,
)
from pykaahma_linz.KVectorItem import KVectorItem
from pykaahma_linz.KTableItem import KTableItem


class ContentManager:
    """
    Manages content for a KServer instance.

    Provides methods to search for, retrieve, and instantiate Koordinates items (layers, tables, etc.)
    based on their IDs or URLs.

    Attributes:
        _kserver (KServer): The KServer instance this manager is associated with.
    """

    def __init__(self, kserver: "KServer") -> None:
        """
        Initializes the ContentManager with a KServer instance.

        Parameters:
            kserver (KServer): The KServer instance to manage content for.

        Returns:
            None
        """
        self._kserver = kserver

    @property
    def service_url(self) -> str:
        """Returns the service URL of the KServer."""
        return self._kserver.service_url

    @property
    def api_url(self) -> str:
        """Returns the API URL of the KServer."""
        return self._kserver.api_url

    def _search_by_id(self, id: str) -> dict:
        """
        Searches for content by id in the KServer.

        Parameters:
            id (str): The id of the content to search for.

        Returns:
            dict: The content found in the KServer.
        """

        # Example: https://data.linz.govt.nz/services/api/v1.x/data/?id=51571
        url = f"{self._kserver._api_url}data/?id={id}"
        response = requests.get(url)
        response.raise_for_status()

        return response.json()

    def _get_item_details(self, url: str) -> dict:
        """
        Retrieves detailed information about a specific item.

        Parameters:
            url (str): The item URL to retrieve details for.

        Returns:
            dict: The detailed information of the item.
        """

        response = requests.get(url)
        response.raise_for_status()

        return response.json()

    def get(self, id: str) -> dict:
        """
        Retrieves content by id from the KServer.

        Parameters:
            id (str): The id of the content to retrieve.

        Returns:
            dict: The content retrieved from the KServer.

        Raises:
            KServerBadRequestError: If the content is not found or the request is invalid.
            KUnknownItemTypeError: If the item kind is not supported.
        """

        search_result = self._search_by_id(id)
        if not search_result or "error" in search_result:
            raise KServerBadRequestError(
                f"Content with id {id} not found or invalid request."
            )
        if len(search_result) == 0:
            return None
        elif len(search_result) > 1:
            raise KServerBadRequestError(
                f"Multiple contents found for id {id}. Please refine your search."
            )

        # Assuming the first item is the desired content
        item_json = search_result[0]
        if "url" not in item_json:
            raise KServerError(f"Item with id {id} does not have a URL.")
        item_details = self._get_item_details(item_json.get("url", ""))

        # Based on the kind of item, return the appropriate item class.
        if item_details.get("kind") == "vector":
            item = KVectorItem(self._kserver, item_details)
        elif item_details.get("kind") == "table":
            item = KTableItem(self._kserver, item_details)
        else:
            raise KUnknownItemTypeError(
                f"Unsupported item kind: {item_details.get('kind')}"
            )

        return item
