import rasterio
from s2utils import S2Catalog, S2TileIndex, chip_tile
from shapely.geometry import Point


oslo = Point(10.740, 59.915)


with S2TileIndex() as index:
    tile = next(index.intersection(oslo))


catalog = S2Catalog()
product = next(catalog.search(tile, max_items=1, max_cloud_cover=1))
with product as src:
    for window in chip_tile(512, 512):
        with rasterio.open(
            f"data/{product.name}_{window.col_off}_{window.row_off}.tif", "w",
            driver="COG",
            width=window.width,
            height=window.height,
            count=3,
            dtype="uint8",
            crs=product.crs,
            transform=product.window_transform(window),
            compress="DEFLATE",
        ) as dst:
            dst.write(src.read([4, 3, 2], window=window) >> 4)
