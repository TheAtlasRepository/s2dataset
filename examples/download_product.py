import rasterio
from s2utils import S2Catalog, S2TileIndex
from shapely.geometry import Point


oslo = Point(10.740, 59.915)


with S2TileIndex() as index:
    tile = next(index.intersection(oslo))

catalog = S2Catalog()
product = next(catalog.search(tile, max_items=1, max_cloud_cover=1))
with product as src:
    with rasterio.open(
        f"{product.name}.tif", "w",
        driver="COG",
        width=product.width,
        height=product.height,
        count=product.count,
        dtype="uint16",
        nodata=0,
        crs=product.crs,
        transform=product.transform
    ) as dst:
        dst.write(src.read())
        dst.colorinterp = src.colorinterp
