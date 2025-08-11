import fiona
import rasterio
import rasterio.windows
from typing import Iterator


def polygon_iterator(geometry: fiona.Geometry) -> Iterator[fiona.Geometry]:
    """Iterates over the polygons in a geometry."""
    if geometry.type == "Polygon":
        yield geometry
    elif geometry.type == "MultiPolygon":
        for polygon in geometry.coordinates: # type: ignore
            yield fiona.Geometry(
                type="Polygon",
                coordinates=polygon)
    elif geometry.type == "GeometryCollection":
        for geometry in geometry.geometries: # type: ignore
            yield from polygon_iterator(geometry)


def window_to_filename(product_name: str, window: rasterio.windows.Window) -> str:
    """Encodes a product name and a window into a target or image filename."""
    return f"{product_name}_{window.width}_{window.col_off}_{window.row_off}.tif"


def filename_to_window(filename: str) -> tuple[str, rasterio.windows.Window]:
    """Decodes the name of a target or image file into a product name and a window."""
    fields = filename.split("_")
    window = rasterio.windows.Window(
        int(fields[-2]), # type: ignore
        int(fields[-1]),
        int(fields[-3]),
        int(fields[-3]))
    return "_".join(fields[:-3]), window
