import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
from typing import Any
import logging

logger = logging.getLogger(__name__)


def geojson_to_gdf(
    geojson: dict[str, Any] | list[dict[str, Any]],
    epsg: str | int,
    fields: list[dict[str, str]] | None = None,
) -> gpd.GeoDataFrame:
    """
    Convert GeoJSON features to a GeoDataFrame with enforced data types.

    Args:
        geojson: Either a GeoJSON FeatureCollection (dict) or a list of GeoJSON features (dicts).
        epsg: Coordinate Reference System (e.g., "4326").
        fields: A list of dictionaries specifying field names and their desired data types.

    Returns:
        A GeoDataFrame with the specified CRS and column types.
    """

    logger.debug("Converting GeoJSON to GeoDataFrame...")

    # Extract features from a FeatureCollection if needed
    if isinstance(geojson, dict) and geojson.get("type") == "FeatureCollection":
        features = geojson.get("features", [])
    elif isinstance(geojson, list):
        features = geojson
    else:
        raise ValueError(
            "Invalid geojson input. Expected a FeatureCollection or list of features."
        )

    # Flatten properties and extract geometry
    records = []
    geometries = []
    for feature in features:
        props = feature.get("properties", {})
        geom = feature.get("geometry")
        records.append(props)
        geometries.append(shape(geom) if geom else None)

    # Create GeoDataFrame
    crs = f"EPSG:{epsg}"
    df = pd.DataFrame(records)
    gdf = gpd.GeoDataFrame(df, geometry=geometries, crs=crs)

    # Apply data type mapping
    if fields and False:
        for field in fields:
            col = field.get("name")
            dtype = field.get("type").lower()
            if dtype == "geometry":
                continue  # Skip geometry fields as they are already handled
            if col in gdf.columns:
                try:
                    if dtype in ["int", "bigint", "integer", "int32", "int64"]:
                        gdf[col] = (
                            pd.to_numeric(gdf[col], errors="coerce")
                            .fillna(0)
                            .astype("int32")
                        )
                    elif dtype in ["float", "double"]:
                        gdf[col] = pd.to_numeric(gdf[col], errors="coerce")
                    elif dtype in ["str", "string"]:
                        gdf[col] = gdf[col].astype(str)
                    elif dtype == "bool":
                        gdf[col] = gdf[col].astype(bool)
                    else:
                        logger.warning(
                            f"Unsupported data type '{dtype}' for column '{col}'. Skipping conversion."
                        )
                except Exception as e:
                    raise ValueError(
                        f"Failed to convert column '{col}' to {dtype}: {e}"
                    )

    return gdf


def json_to_df(
    json: dict[str, Any] | list[dict[str, Any]],
    fields: list[dict[str, str]] | None = None,
) -> pd.DataFrame:

    """
    Convert GeoJSON features to a GeoDataFrame with enforced data types.

    Args:
        geojson: Either a JSON FeatureCollection (dict) or a list of JSON features (dicts).
        fields: A list of dictionaries specifying field names and their desired data types.

    Returns:
        A DataFrame with the specified column types.
    """

    logger.debug("Converting JSON to DataFrame...")

    # Extract features from a FeatureCollection if needed
    if isinstance(json, dict) and json.get("type") == "FeatureCollection":
        features = json.get("features", [])
    elif isinstance(json, list):
        features = json
    else:
        raise ValueError(
            "Invalid json input. Expected a FeatureCollection or list of features."
        )

    # Flatten properties and extract geometry
    records = []
    for feature in features:
        props = feature.get("properties", {})
        records.append(props)
    df = pd.DataFrame(records)

    # Apply data type mapping
    if fields and False:
        for field in fields:
            col = field.get("name")
            dtype = field.get("type").lower()
            if col in df.columns:
                try:
                    if dtype in ["int", "bigint", "integer", "int32", "int64"]:
                        df[col] = (
                            pd.to_numeric(df[col], errors="coerce")
                            .fillna(0)
                            .astype("int32")
                        )
                    elif dtype in ["float", "double"]:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                    elif dtype in ["str", "string"]:
                        df[col] = df[col].astype(str)
                    elif dtype == "bool":
                        df[col] = df[col].astype(bool)
                    else:
                        logger.warning(
                            f"Unsupported data type '{dtype}' for column '{col}'. Skipping conversion."
                        )
                except Exception as e:
                    raise ValueError(
                        f"Failed to convert column '{col}' to {dtype}: {e}"
                    )

    return df
    

def gdf_to_single_polygon_geojson(gdf: gpd.GeoDataFrame) -> dict[str, Any] | None:
    """
    Convert a GeoDataFrame to a single GeoJSON polygon geometry object.
    Args:
        gdf: A GeoDataFrame containing polygon geometries.
    Returns:
        A GeoJSON polygon geometry object or None if the GeoDataFrame is empty.
    Raises:
        ValueError: If the GeoDataFrame is empty or contains non-polygon geometries.
    """
    if gdf.empty:
        raise ValueError("GeoDataFrame must at least one Polygon geometry.")

    if not all(gdf.geometry.type == "Polygon"):
        raise ValueError("GeoDataFrame must contain only Polygon geometries.")

    #convert crs to EPSG:4326 if not already
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    # Union all geometries into a single geometry
    single_geometry = gdf.unary_union
    if single_geometry.is_empty:
        raise ValueError("Resulting geometry is empty after union.")

    geom = single_geometry.__geo_interface__

    logger.info(geom)

    return geom


def gdf_to_bbox(gdf: gpd.GeoDataFrame) -> str:
    """
    Convert a GeoDataFrame to a bounding box string in the format "XMin,YMin,XMax,YMax,EPSG:4326".
    Args:
        gdf: A GeoDataFrame containing geometries.
    Returns:
        A bounding box string in the format "XMin,YMin,XMax,YMax,EPSG:4326".
    Raises:
        ValueError: If the GeoDataFrame is empty or does not contain valid geometries.
    """
    if gdf.empty:
        raise ValueError("GeoDataFrame must contain at least one geometry.")

    if not all(gdf.geometry.type.isin(["Polygon", "MultiPolygon"])):
        raise ValueError("GeoDataFrame must contain only Polygon or MultiPolygon geometries.")

    # Ensure the GeoDataFrame is in EPSG:4326
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    # Calculate the bounding box
    bounds = gdf.total_bounds  # returns (minx, miny, maxx, maxy)
    bbox_string = f"{bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]},EPSG:4326"

    return bbox_string