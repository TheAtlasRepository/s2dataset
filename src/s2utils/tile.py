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

    def __init__(
        self,
        name: str,
        geometry: Polygon,
        crs: CRS,
        offset: tuple[int, int]
    ) -> None:
        """Create a new tile.

        Does not check if the given arguments are valid or consistent, so you
        usually don't want to call this directly.
        
        :param name: MGRS 100 km grid square id of the tile.
        :param geometry: Geometry of the tile.
        :param crs: Native CRS of products from this tile.
        :param offset: Offset of products from this tile in it's native CRS.
        """
        self.name = name
        self.geometry = geometry
        self.crs = crs
        self.offset = offset

    def __str__(self) -> str:
        return self.name

    @classmethod
    def from_feature(cls, feature: dict[str, Any]) -> 'S2Tile':
        """Create a tile from a feature in the tiling grid."""
        return cls(
            name=feature["properties"]["name"],
            geometry=shape(feature["geometry"]),
            crs=CRS.from_epsg(feature["properties"]["epsg"]),
            offset=(
                feature["properties"]["xoff"],
                feature["properties"]["yoff"]
            )
        )
    
    def transform(self, resolution: int) -> Affine:
        """Return the affine transformation of a product from this tile.
        
        :param resolution: Spatial resolution of the product in its native CRS.
        """
        return Affine.translation(*self.offset) * Affine.scale(resolution, -resolution)


class S2TileIndex:
    """Index for Sentinel 2 tiles."""

    def __getitem__(self, key: int) -> S2Tile:
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
        """Return id of tiles that intersect the given geometry.
        
        :param geometry: An object that implements the geo interface. The
            geometry is assumed to be in EPSG:4326.
        """
        if not isinstance(geometry, Geometry):
            geometry = shape(geometry)

        for tile_id, tile in self._colxn_invalid.items(bbox=geometry.bounds):
            if geometry.intersects(shape(tile.geometry)):
                yield tile_id

    def intersection(self, geometry: Any) -> Iterator[S2Tile]:
        """Return tiles that intersect the given geometry.
        
        :param geometry: An object that implements the geo interface. The
            geometry is assumed to be in EPSG:4326.
        """
        for tile_id in self._intersection(geometry):
            yield self[tile_id]

    def _reverse_intersection(self, geometries: Iterable[T]) -> dict[int, list[T]]:
        """Return id of tiles that intersect the given geometries.
        
        :param geometries: An iterable of objects that implement the geo
            interface. Geometries are assumed to be in EPSG:4326.
        """
        tiles: dict[int, list[T]] = {}
        for geometry in geometries:
            for tile_id in self._intersection(geometry):
                tiles.setdefault(tile_id, []).append(geometry)
        return tiles

    def reverse_intersection(self, geometries: Iterable[T]) -> Iterator[tuple[S2Tile, list[T]]]:
        """Return tiles that intersect the given geometries.
        
        :param geometries: An iterable of objects that implement the geo
            interface. Geometries are assumed to be in EPSG:4326.
        """
        tiles = self._reverse_intersection(geometries)
        for tile_id, geometries in tiles.items():
            yield self[tile_id], geometries
