# export.py
import requests
import os
from datetime import datetime
from typing import Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    RetryError,
    retry_if_not_exception_type,
)
import logging

logger = logging.getLogger(__name__)


class KExportError(Exception):
    """Custom exception for errors encountered during export operations."""

    pass


def _ensure_ending_slash(url: str) -> str:
    """
    Ensures the URL ends with a slash.

    Parameters:
        url (str): The URL to check.

    Returns:
        str: The URL with a trailing slash.
    """

    return url if url.endswith("/") else f"{url}/"


def validate_export_params(
    api_url: str,
    api_key: str,
    id: str,
    data_type: str,
    kind: str,
    export_format: str,
    crs: str = None,
    extent: dict = None,
    **kwargs: Any,
) -> bool:
    """
    Validates export parameters for a given item.

    Parameters:
        api_url (str): The base URL of the Koordinates API.
        api_key (str): The API key for authentication.
        id (str): The ID of the item to export.
        data_type (str): The type of data ('layer' or 'table').
        kind (str): The kind of export (e.g., 'shp', 'geojson').
        export_format (str): The format for the export.
        crs (str, optional): Coordinate Reference System, if applicable.
        extent (dict, optional): Spatial extent for the export.
        **kwargs: Additional parameters for the export.

    Returns:
        bool: True if the export parameters are valid, False otherwise.

    Raises:
        ValueError: If the data type is unsupported or not implemented.
    """


    # validation_url = f"{requests_url}validate/"
    logger.info("Validating export parameters")
    logger.info(data_type)

    api_url = _ensure_ending_slash(api_url)
    if data_type == "layer":
        download_url = f"{api_url}layers/"
    elif data_type == "table":
        download_url = f"{api_url}tables/"
    else:
        raise ValueError(f"Unsupported or not implemented data type: {data_type}")
    validation_url = f"{api_url}exports/validate/"

    logger.debug(f"{download_url=}")

    data = {
        "items": [{"item": f"{download_url}{id}/"}],
        "formats": {f"{kind}": export_format},
        **kwargs,
    }

    if data_type == "layer" and crs:
        data["crs"] = crs
    if data_type == "layer" and extent:
        data["extent"] = extent

    logger.debug(f"{data=}")

    headers = {"Authorization": f"key {api_key}"}
    is_valid = False

    try:
        response = requests.post(validation_url, headers=headers, json=data)
        response.raise_for_status()

        # if response has any 200 status code, check for validation errors
        if response.status_code in (200, 201, "200", "201"):
            try:
                json_response = response.json()
                if any(
                    not item.get("is_valid", "true") for item in json_response["items"]
                ):
                    err = "An error occured when attempting to validate an export with this configuration. Check for 'invalid_reasons' in the logs."
                    logger.error(err)
                    logger.error(json_response["items"])
                    raise ValueError(err)
                is_valid = True
            except ValueError as e:
                err = f"Error parsing JSON from export validation: {e}"
                logger.debug(err)
                raise ValueError(err)

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        logger.error(
            f"HTTP error during validation: {status} - {getattr(e.response, 'text', '')}"
        )
        if 400 <= status < 500:
            raise ValueError(
                f"Bad request ({status}) for URL {validation_url}: {getattr(e.response, 'text', '')}"
            ) from e
        raise

    logger.debug(f"Export parameters passed validation check. {is_valid=}")
    return is_valid


def request_export(
    api_url: str,
    api_key: str,
    id: str,
    data_type: str,
    kind: str,
    export_format: str,
    crs: str = None,
    extent: dict = None,
    **kwargs: Any,
) -> dict:
    """
    Requests an export of a given item from the Koordinates API.

    Parameters:
        api_url (str): The base URL of the Koordinates API.
        api_key (str): The API key for authentication.
        id (str): The ID of the item to export.
        data_type (str): The type of data ('layer' or 'table').
        kind (str): The kind of export (e.g., 'shp', 'geojson').
        export_format (str): The format for the export.
        crs (str, optional): Coordinate Reference System, if applicable.
        extent (dict, optional): Spatial extent for the export.
        **kwargs: Additional parameters for the export.

    Returns:
        dict: The response from the export request, typically containing job details.

    Raises:
        KExportError: If the export request fails or if the response cannot be parsed.
        ValueError: If the data type is unsupported or not implemented.
    """

    logger.info("Requesting export")

    api_url = _ensure_ending_slash(api_url)
    export_url = f"{api_url}exports/"
    if data_type == "layer":
        download_url = f"{api_url}layers/"
    elif data_type == "table":
        download_url = f"{api_url}tables/"
    else:
        raise ValueError(f"Unsupported or not implemented data type: {data_type}")
    logger.debug(f"{download_url=}")

    data = {
        "items": [{"item": f"{download_url}{id}/"}],
        "formats": {f"{kind}": export_format},
        **kwargs,
    }

    if data_type == "layer" and crs:
        data["crs"] = crs
    if data_type == "layer" and extent:
        data["extent"] = extent

    logger.debug(f"{data=}")

    headers = {"Authorization": f"key {api_key}"}

    request_datetime = datetime.utcnow().isoformat()
    try:
        response = requests.post(export_url, headers=headers, json=data)
        response.raise_for_status()
        try:
            json_response = response.json()
        except ValueError as e:
            err = f"Error parsing JSON from export request: {e}"
            logger.debug(err)
            raise KExportError(err)
    except requests.exceptions.HTTPError as e:
        err = f"Failed export request with status code: {response.status_code}"
        logger.debug(err)
        logger.debug(e)
        raise KExportError(err)
    return json_response
