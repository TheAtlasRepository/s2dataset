from affine import Affine
from pyproj import CRS
from typing import Any, List, Optional, Tuple, Union

import numpy as np
import rasterio
import rasterio.windows


class S2Product:
    """Sentinel-2 L1C or L2A data product.

    Provides a `rasterio.DatasetReader`-like interface to a number of single-band
    raster files, with each file representing a single band of a Sentinel-2
    product.
    """

    def __init__(
        self,
        name: str,
        uris: List[str],
        crs: CRS,
        offset: Tuple[int, int]
    ) -> None:
        """Create a new product.

        Does not check if the given arguments are valid or consistent, so you
        usually don't want to call this directly.

        :param name: Name of the product.
        :param uris: List of uris of the bands of the product.
        :param crs: Native CRS of the product.
        :param offset: Offset of the product in it's native CRS.
        """
        self.name = name
        self.uris = uris
        self.crs = crs
        self.offset = offset

        self.width = 10980
        self.height = 10980
        self.count = len(self.uris)

    def __enter__(self) -> 'S2Product':
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback) -> None: # type: ignore
        self.close()
    
    @classmethod
    def from_item(cls, item: Any) -> 'S2Product':
        """Create a product from a STAC item."""
        uris = []
        for asset in ["coastal", "blue", "green", "red", "rededge1", "rededge2", "rededge3", "nir", "nir08", "nir09", "swir16", "swir22"]:
            uris.append(item.assets[asset].href)

        return cls(
            name=item.properties["s2:product_uri"].removesuffix(".SAFE"),
            uris=uris,
            crs=CRS.from_epsg(item.properties["proj:epsg"]),
            offset=(
                item.assets["blue"].extra_fields["proj:transform"][2],
                item.assets["blue"].extra_fields["proj:transform"][5]
            )
        )

    @property
    def transform(self) -> Affine:
        return Affine.translation(*self.offset) * Affine.scale(10, -10)

    def open(self) -> None:
        self.datasets = [rasterio.open(path) for path in self.uris]

    def close(self) -> None:
        for dataset in self.datasets:
            dataset.close()

    def _read(self, index: int, window: Optional[rasterio.windows.Window] = None) -> Any:
        width = self.width
        height = self.height

        if window is not None:
            width = window.width
            height = window.height

            scale = self.datasets[index].transform.a / 10
            window = rasterio.windows.Window(
                window.col_off / scale, # type: ignore
                window.row_off / scale,
                window.width / scale,
                window.height / scale)

        return self.datasets[index].read(
            1,
            out_shape=(height, width),
            window=window,
            boundless=True)
    
    def read(self, indexes: Optional[Union[int, List[int]]] = None, window: Optional[rasterio.windows.Window] = None) -> Any:
        if indexes is None:
            indexes = list(range(1, self.count + 1))

        if isinstance(indexes, int):
            return self._read(indexes - 1, window)
        else:
            return np.stack([self._read(index - 1, window) for index in indexes])

    def window_transform(self, window: rasterio.windows.Window) -> Affine:
        return rasterio.windows.transform(window, self.transform)
