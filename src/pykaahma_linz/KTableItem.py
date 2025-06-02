"""
KTableItem.py  
A class to represent a table dataset.
"""

import logging
import json
from datetime import datetime
from pykaahma_linz.KItem import KItem
from .features import wfs as wfs_features
from .features.Conversion import json_to_df
from pykaahma_linz.CustomErrors import KServerError

logger = logging.getLogger(__name__)

class KTableItem(KItem):
    """
    KTableItem is a class that represents a vector dataset.
    It inherits from KItem and provides methods to interact with vector datasets.
    """

    def __init__(self, kserver: "KServer", item_dict: dict):
        """
        Initializes the KTableItem with a dict.

        Args:
            item_dict (dict): A dictionary containing the item's details, typically from an API response.
        """
        super().__init__(kserver, item_dict)
        self.kind = "vector" 
        self._supports_changesets = None 
        self._services = None      
        logger.debug(f"Initializing KTableItem with id: {self.id}, title: {self.title}")
    
    @property
    def fields(self):
        """
        Returns the fields of the item.

        Returns:
            list: A list of fields associated with the item.
        """
        return self._raw_json.get("data",{}).get("fields", [])

    @property
    def primary_key_fields(self):
        """
        Returns the primary key fields of the item.

        Returns:
            list: A list of primary key fields associated with the item.
        """
        return self._raw_json.get("data",{}).get("primary_key_fields", [])

    @property
    def feature_count(self):
        """
        Returns the number of features in the item.

        Returns:
            int: The number of features associated with the item, or None if not available.
        """
        return self._raw_json.get("data",{}).get("feature_count", None)

    @property
    def export_formats(self):
        """
        Returns the export formats available for the item.

        Returns:
            list: A list of export formats associated with the item, or None if not available.
        """
        return self._raw_json.get("data",{}).get("export_formats", None)

    @property
    def supports_changesets(self):
        """
        Returns whether the item supports changes.
        NB: Not really sure how reliable this is, but seems to be the
        only way to determine if the item supports changesets.

        Returns:
            bool: True if the item supports changes, False otherwise.
        """
        if self._supports_changesets is None:            
            logger.debug(f"Checking if item with id: {self.id} supports changesets")
            self._supports_changesets = any(
                service.get("key") == "wfs-changesets" for service in self.services
            )

        return self._supports_changesets

    @property
    def _wfs_url(self):
        """
        Returns the WFS URL for the item.

        Returns:
            str: The WFS URL associated with the item.
            example: "https://data.linz.govt.nz/services/wfs/layer-12345"
        """
        return f"{self._kserver._service_url}wfs/"

    def get_wfs_service(self):
        """
        Returns a WebFeatureService instance for the item.

        Args:
            version (str): The WFS version to use. Defaults to "2.0.0".

        Returns:
            WebFeatureService: An instance of WebFeatureService for the item.
        """
        
        logger.debug(f"Creating WFS service for item with id: {self.id}")
        wfs_service = self._kserver.wfs.operations

    def query(self, cql_filter: str = None, **kwargs):
        """
        Executes a WFS query on the item.

        Args:
            cql_filter (str): The WFS query to execute.

        Returns:
            dict: The result of the WFS query.
        """
        logger.debug(f"Executing WFS query for item with id: {self.id}")

        result = wfs_features.download_wfs_data(
            url=self._wfs_url,
            api_key=self._kserver._api_key,
            typeNames=f"table-{self.id}",            
            cql_filter=cql_filter,
            **kwargs
        )

        df = json_to_df(result, fields = self.fields)
        return df

    def get_changeset(self, from_time: str, to_time: str = None, cql_filter: str = None, **kwargs):
        """
        Retrieves a changeset for the item.

        Args:
            from_time (str): The start time for the changeset query, ISO format.
                            example, 2015-05-15T04:25:25.334974
            to_time (str, optional): The end time for the changeset query, ISO format.
                            If not provided, the current time is used.
            cql_filter (str): The CQL filter to apply to the changeset query.

        Returns:
            dict: The changeset data.
        """
        if not self.supports_changesets:
            logger.error(f"Item with id: {self.id} does not support changesets.")
            raise KServerError("This item does not support changesets.")

        if to_time is None:            
            to_time = datetime.now().isoformat()
        logger.debug(f"Fetching changeset for item with id: {self.id} from {from_time} to {to_time}")

        viewparams = f"from:{from_time};to:{to_time}"

        result = wfs_features.download_wfs_data(
                url=self._wfs_url,
                api_key=self._kserver._api_key,
                typeNames=f"table-{self.id}-changeset",
                viewparams=viewparams,
                cql_filter=cql_filter,
                **kwargs
            )
        
        df = json_to_df(result, fields = self.fields)
        return df

    @property
    def services(self):
        """
        Returns the services associated with the item.

        Returns:
            list: A list of services associated with the item.
        """

        if self._services is None:
            logger.debug(f"Fetching services for item with id: {self.id}")
            url = self._kserver._api_url + f"layers/{self.id}/services/"
            self._services = self._kserver.get(url)
        logger.debug(f"Returning {len(self._services)} services for item with id: {self.id}")
        return self._services

    def reset(self):
        """
        Resets the KTableItem instance, clearing cached properties.
        This is useful for refreshing the item state.
        """
        logger.info(f"Resetting KTableItem with id: {self.id}")
        self._supports_changesets = None
        self._services = None
        self._raw_json = None


    def __repr__(self):
        return f"KTableItem(id={self.id}, title={self.title}, type={self.type}, kind={self.kind})"