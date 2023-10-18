from affine import Affine
from importlib import resources
from pyproj import CRS
from shapely import Geometry, Polygon
from shapely.geometry import shape
from typing import Any, Iterable, Iterator, TypeVar

import fiona
import zstandard as zstd


tiles_path = str(resources.files("s2utils").joinpath("resources/s2_tiling_grid.fgb.zst"))


T = TypeVar("T")


class S2Tile:
    """A Sentinel 2 tile."""
    def __init__(self, name: str, geometry: Polygon, transform: Affine, crs: CRS) -> None:
        self.name = name
        self.geometry = geometry
        self.transform = transform
        self.crs = crs

    def __str__(self) -> str:
        return self.name

    @classmethod
    def from_feature(cls, feature: dict[str, Any]) -> 'S2Tile':
        return cls(
            name=feature["properties"]["name"],
            geometry=shape(feature["geometry"]),
            transform=Affine.from_gdal(*map(int, feature["properties"]["transform"].split(","))),
            crs=CRS.from_epsg(feature["properties"]["epsg"])
        )


class S2TileIndex:
    """Index for Sentinel 2 tiles."""

    def __getitem__(self, key: int) -> S2Tile:
        """Return the tile with the given id."""
        return S2Tile.from_feature(self._colxn[key])
    
    def __enter__(self) -> 'S2TileIndex':
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None: # type: ignore
        self.close()

    def open(self) -> None:
        with zstd.open(tiles_path) as file:
            self._colxn = fiona.open(file)

        # Calling the `keys`, `values`, `items` or `filter` method on a
        # collection makes the `__getitem__` method stop working. The best
        # workaround i found is to use a separate collection for those methods.
        with zstd.open(tiles_path) as file:
            self._colxn_invalid = fiona.open(file)
    
    def close(self) -> None:
        self._colxn.close()
        self._colxn_invalid.close()

    def _intersection(self, geometry: Any) -> Iterator[int]:
        """Return id of tiles that intersect the given geometry."""
        if not isinstance(geometry, Geometry):
            geometry = shape(geometry)

        for tile_id, tile in self._colxn_invalid.items(bbox=geometry.bounds):
            if geometry.intersects(shape(tile.geometry)):
                yield tile_id

    def intersection(self, geometry: Any) -> Iterator[S2Tile]:
        """Return tiles that intersect the given geometry."""
        for tile_id in self._intersection(geometry):
            yield self[tile_id]

    def _reverse_intersection(self, geometries: Iterable[T]) -> dict[int, list[T]]:
        """Return id of tiles that intersect the given geometries."""
        tiles: dict[int, list[T]] = {}
        for geometry in geometries:
            for tile_id in self._intersection(geometry):
                tiles.setdefault(tile_id, []).append(geometry)
        return tiles

    def reverse_intersection(self, geometries: Iterable[T]) -> Iterator[tuple[S2Tile, list[T]]]:
        """Return tiles that intersect the given geometries."""
        tiles = self._reverse_intersection(geometries)
        for tile_id, geometries in tiles.items():
            yield self[tile_id], geometries
