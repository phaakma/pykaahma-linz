"""
KVectorItem.py
A class to represent a vector dataset.
"""

import logging
import json
from datetime import datetime
from pykaahma_linz.KItem import KItem
from pykaahma_linz.JobResult import JobResult
from .features import wfs as wfs_features
from .features import export as export_features
from .features.Conversion import geojson_to_gdf
from pykaahma_linz.CustomErrors import KServerError

logger = logging.getLogger(__name__)

class KVectorItem(KItem):
    """
    KVectorItem is a class that represents a vector dataset.
    It inherits from KItem and provides methods to interact with vector datasets.
    """

    def __init__(self, kserver: "KServer", item_dict: dict):
        """
        Initializes the KVectorItem with a dict.

        Args:
            item_dict (dict): A dictionary containing the item's details, typically from an API response.
        """
        super().__init__(kserver, item_dict)
        self.kind = "vector"
        self._supports_changesets = None
        self._services = None
        self._jobs = []
        logger.debug(
            f"Initializing KVectorItem with id: {self.id}, title: {self.title}"
        )

    @property
    def fields(self):
        """
        Returns the fields of the item.

        Returns:
            list: A list of fields associated with the item.
        """
        return self._raw_json.get("data", {}).get("fields", [])

    @property
    def epsg(self):
        """
        Returns the EPSG code of the item.

        Returns:
            int: The EPSG code associated with the item, or None if not available.
        """
        return self._raw_json.get("data", {}).get("crs", {}).get("srid", None)

    @property
    def primary_key_fields(self):
        """
        Returns the primary key fields of the item.

        Returns:
            list: A list of primary key fields associated with the item.
        """
        return self._raw_json.get("data", {}).get("primary_key_fields", [])

    @property
    def geometry_type(self):
        """
        Returns the geometry type of the item.

        Returns:
            str: The geometry type associated with the item, or None if not available.
        """
        return self._raw_json.get("data", {}).get("geometry_type", None)

    @property
    def feature_count(self):
        """
        Returns the number of features in the item.

        Returns:
            int: The number of features associated with the item, or None if not available.
        """
        return self._raw_json.get("data", {}).get("feature_count", None)

    @property
    def extent(self):
        """
        Returns the extent of the item.

        Returns:
            dict: A dictionary containing the extent of the item, or None if not available.
        """
        return self._raw_json.get("data", {}).get("extent", None)

    @property
    def export_formats(self):
        """
        Returns the export formats available for the item.

        Returns:
            list: A list of export formats associated with the item, or None if not available.
        """
        return self._raw_json.get("data", {}).get("export_formats", None)

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
            typeNames=f"layer-{self.id}",
            cql_filter=cql_filter,
            srsName=f"EPSG:{self.epsg}" if self.epsg else None,
            **kwargs,
        )

        gdf = geojson_to_gdf(result, epsg=self.epsg, fields=self.fields)
        return gdf

    def get_changeset(
        self, from_time: str, to_time: str = None, cql_filter: str = None, **kwargs
    ):
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
        logger.debug(
            f"Fetching changeset for item with id: {self.id} from {from_time} to {to_time}"
        )

        viewparams = f"from:{from_time};to:{to_time}"

        result = wfs_features.download_wfs_data(
            url=self._wfs_url,
            api_key=self._kserver._api_key,
            typeNames=f"layer-{self.id}-changeset",
            viewparams=viewparams,
            cql_filter=cql_filter,
            srsName=f"EPSG:{self.epsg}" if self.epsg else None,
            **kwargs,
        )

        gdf = geojson_to_gdf(result, epsg=self.epsg, fields=self.fields)
        return gdf

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
        logger.debug(
            f"Returning {len(self._services)} services for item with id: {self.id}"
        )
        return self._services

    def reset(self):
        """
        Resets the KVectorItem instance, clearing cached properties.
        This is useful for refreshing the item state.
        """
        logger.info(f"Resetting KVectorItem with id: {self.id}")
        self._supports_changesets = None
        self._services = None
        self._raw_json = None

    def _resolve_export_format(self, export_format: str):
        """
        Validates if the export format is supported by the item.

        Args:
            export_format (str): The format to validate.

        Returns:
            bool: True if the format is supported, False otherwise.
        """
        logger.debug(
            f"Validating export format: {export_format} for item with id: {self.id}"
        )
        mimetype = None

        # check if the export format is either any of the names or mimetypes in the example_formats
        export_format = export_format.lower()

        # Handle special cases for export formats geopackage and sqlite as it seems a
        # strange string argument to expect a user to pass in
        if export_format in ("geopackage", "sqlite"):
            export_format = "GeoPackage / SQLite".lower()

        for f in self.export_formats:
            if export_format in (f["name"].lower(), f["mimetype"].lower()):
                mimetype = f["mimetype"]

        if mimetype is None:
            raise ValueError(
                f"Export format {export_format} is not supported by this item. Refer supported formats using : itm.export_formats"
            )

        logger.debug(f"Resolved export format: {mimetype} from {export_format}")
        return mimetype

    def validate_export_request(
        self,
        export_format: str,
        crs: str = None,
        extent: dict = None,
        **kwargs,
    ):

        export_format = self._resolve_export_format(export_format)

        # log out all the input parameters including kwargs
        logger.info(
            f"Validating export request for item with id: {self.id}, {export_format=}, {crs=}, {extent=},  {kwargs=}"
        )

        return export_features.validate_export_params(
            self._kserver._api_url,
            self._kserver._api_key,
            self.id,
            export_format,
            crs,
            extent,
            **kwargs,
        )

    def export(
        self,
        export_format: str,
        crs: str = None,
        extent: dict = None,
        poll_interval: int = 10,
        timeout: int = 300,
        **kwargs,
    ):
        """
        Exports the item in the specified format.

        Args:
            export_format (str): The format to export the item in.
            crs (str, optional): The coordinate reference system to use for the export.
            extent (dict, optional): The extent to use for the export. Should be a GeoJSON dictionary.
            **kwargs: Additional parameters for the export request.

        Returns:
            JobResult: A JobResult instance containing the export job details.
        """
        logger.debug(f"Exporting item with id: {self.id} in format: {export_format}")

        export_format = self._resolve_export_format(export_format)

        validate_export_request = self.validate_export_request(
            export_format,
            crs=crs,
            extent=extent,
            **kwargs,
        )

        if not validate_export_request:
            logger.error(
                f"Export validation failed for item with id: {self.id} in format: {export_format}"
            )
            raise ValueError(
                f"Export validation failed for item with id: {self.id} in format: {export_format}"
            )

        export_request = export_features.request_export(
            self._kserver._api_url,
            self._kserver._api_key,
            self.id,
            export_format,
            crs=crs,
            extent=extent,
            **kwargs,
        )

        job_result = JobResult(
            export_request, self._kserver, poll_interval=5, timeout=600
        )
        self._jobs.append(job_result)
        logger.info(
            f"Export job created for item with id: {self.id}, job id: {job_result.id}"
        )
        return job_result

    def __repr__(self):
        return f"KVectorItem(id={self.id}, title={self.title}, type={self.type}, kind={self.kind})"
