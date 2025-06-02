import os
import pytest
from dotenv import load_dotenv
import logging

from pykaahma_linz.features.wfs import download_wfs_data

logger = logging.getLogger(__name__)

def test_download_linz_wfs_data_live():
    # Load environment variables from .env file
    load_dotenv()
    api_key = os.getenv("LINZ_API_KEY")
    assert api_key, "LINZ_API_KEY must be set in your .env file"

    rail_station_layer_id = "50318"  # rail station 175 points
    fences_layer_id = "50268"  # NZ Fence Centrelines
    geodetic_marks_layer_id = "50787"  # NZ Geodetic Marks 132,966 point features
    nz_walking_biking_tracks_layer_id = (
        "52100"  # NZ Walking and Biking Tracks 29,187 polyline features
    )
    suburb_locality_table_id = "113761"  # Suburb Locality - Population 3190 records

    url = "https://data.linz.govt.nz/services/wfs"
    srsName = "EPSG:2193"
    typeNames = f"layer-{rail_station_layer_id}"
    result = download_wfs_data(
        url=url, typeNames=typeNames, api_key=api_key, srsName=srsName
    ) 
    assert isinstance(result, dict), "Result should be a dictionary"
    features = result.get("features")
    assert isinstance(features, list)
    logger.info(f"Number of features downloaded: {len(features)}")
    # log all result properties except features
    logger.debug("Result properties::::::::::::::::::")
    for key, value in result.items():
        if key != "features":
            logger.debug(f"{key}: {value}")
    assert len(features) > 0, "Should return at least one feature"
