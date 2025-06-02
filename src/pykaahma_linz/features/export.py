# export.py
import requests
import os
from datetime import datetime
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

    Args:
        url (str): The URL to check.

    Returns:
        str: The URL with a trailing slash.
    """
    return url if url.endswith("/") else f"{url}/"


def validate_export_params(
    api_url: str,
    api_key: str,
    id: str,
    export_format: str = "applicaton/x-ogc-filegdb",
    crs: str = None,
    extent: dict = None,
    **kwargs,
):
    # validation_url = f"{requests_url}validate/"
    logger.info("Validating export parameters")

    api_url = _ensure_ending_slash(api_url)
    download_url = f"{api_url}layers/"
    validation_url = f"{api_url}exports/validate/"

    data = {
        "items": [{"item": f"{download_url}{id}/"}],
        "formats": {"vector": export_format},
        "crs": crs,
        "extent": extent,
        **kwargs,
    }

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
    export_format: str,
    crs: str = None,
    extent: dict = None,
    **kwargs,
):

    logger.info("Requesting export")

    api_url = _ensure_ending_slash(api_url)
    export_url = f"{api_url}exports/"
    download_url = f"{api_url}layers/"

    data = {
        "items": [{"item": f"{download_url}{id}/"}],
        "formats": {"vector": export_format},
        "crs": crs,
        "extent": extent,
        **kwargs,
    }

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

