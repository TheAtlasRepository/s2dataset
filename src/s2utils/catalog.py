from .tile import S2Tile
from .product import S2Product
from datetime import datetime
from pystac_client import Client
from typing import Iterator


class S2Catalog:
    """Sentinel 2 catalog."""

    def __init__(self) -> None:
        """Create a new catalog."""
        self._catalog = Client.open("https://earth-search.aws.element84.com/v1")
        self._sort_keys = {
            "datetime": "-properties.datetime",
            "cloudcover": "properties.eo:cloud_cover"
        }

    def get(
        self,
        name: str
    ):
        results = self._catalog.search(
            collections=["sentinel-2-l2a"],
            max_items=1,
            query={
                "s2:product_uri": {"eq": f"{name}.SAFE"}
            }
        )

        for item in results.items():
            return S2Product.from_item(item)

        raise Exception(f"Product {name} not found.")

    def search(
        self,
        tile: S2Tile | str,
        max_items: int | None = None,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
        max_cloud_cover: int = 10,
        max_nodata: int = 10,
        sort_key: str = "datetime",
    ) -> Iterator[S2Product]:
        """Search for Sentinel 2 products from a given tile.

        :param tile: Tile to search.
        :param max_items: Maximum number of items to return.
        :param start_date: Start date of the search.
        :param end_date: End date of the search.
        :param max_cloud_cover: Maximum cloud cover of the results.
        :param max_nodata: Maximum percentage of nodata pixels in the results.
        :param sort_key: Key to sort the results by. Can be either "datetime",
            "cloudcover" or a STAC Item Search sortby expression.
        """
        if isinstance(tile, S2Tile):
            tile = tile.name    

        date_range = None
        if start_date or end_date:
            date_range = (start_date, end_date)

        if sort_key in self._sort_keys:
            sort_key = self._sort_keys[sort_key]
        
        results = self._catalog.search(
            collections=["sentinel-2-l2a"],
            max_items=max_items,
            datetime=date_range,
            query={
                "eo:cloud_cover":             {"lt": max_cloud_cover},
                "s2:nodata_pixel_percentage": {"lt": max_nodata},
                "mgrs:utm_zone":              {"eq": tile[:2]},
                "mgrs:latitude_band":         {"eq": tile[2:3]},
                "mgrs:grid_square":           {"eq": tile[3:5]}
            },
            sortby=[sort_key],
        )

        for item in results.items():
            yield S2Product.from_item(item)
