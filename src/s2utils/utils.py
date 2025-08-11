import rasterio
import rasterio.features
import rasterio.warp
import rasterio.windows
from .tile import S2Tile
from typing import Any, Iterator


def chip_tile(
    size: int,
    stride: int,
    resolution: int = 10
) -> Iterator[rasterio.windows.Window]:
    """Return an iterator over windows of a Sentinel 2 tile.

    :param tile: The tile to iterate over.
    :param size: The size of the windows in pixels.
    :param stride: The stride of the windows in pixels.
    """
    tile_size = 109800 // resolution
    for col in range(0, tile_size, stride):
        for row in range(0, tile_size, stride):
            if col + size <= tile_size and row + size <= tile_size:
                yield rasterio.windows.Window(col, row, size, size) # type: ignore


def rasterize_tile(
    tile: S2Tile,
    geometries: Any,
    resolution: int = 10
) -> Any:
    """Return an image array with input geometries burned in.

    :param tile: The tile to rasterize into.
    :param geometries: An iterable of objects that implement the geo
            interface. Geometries are assumed to be in EPSG:4326.
    """
    size = 109800 // resolution
    geometries = rasterio.warp.transform_geom(
        rasterio.CRS.from_epsg(4326),
        tile.crs,
        geometries)
    return rasterio.features.rasterize(
        geometries,
        out_shape=(size, size),
        transform=tile.transform(resolution),
        all_touched=True,
        dtype=rasterio.uint8)
