from .common import window_to_filename, filename_to_window, polygon_iterator
from pathlib import Path
from s2utils import S2Catalog, chip_tile
# from shapely import MultiPolygon
# from shapely.geometry import shape
from tqdm import tqdm

import click
import concurrent.futures as cf
import fiona
import random
import rasterio
import rasterio.windows


@click.command()
@click.argument("root_dir", type=str)
@click.option("--size", "-s", type=int, default=224, help="Size of the images.")
@click.option("--stride", "-t", type=int, default=224, help="Stride of the sliding window.")
@click.option("--workers", "-w", type=int, default=1, help="Number of workers to use.")
def create_negatives(
    root_dir: str,
    size: int,
    stride: int,
    workers: int
) -> None:
    """Create negative samples for the dataset.
    
    ROOT_DIR is the path to the root directory of the dataset. Beware that this
    commmand does not work too well on datasets with multiple classes.
    """
    target_dir = Path(root_dir) / "targets"

    image_dir = Path(root_dir) / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    with cf.ProcessPoolExecutor(workers, initializer=init_worker) as pool:
        futures = []
        for product_name, targets in product_targets(target_dir).items():
            futures.append(
                pool.submit(
                    create_product_negatives,
                    image_dir,
                    product_name,
                    size,
                    stride,
                    targets))
        
        for _ in tqdm(cf.as_completed(futures), "Creating negatives", len(futures)):
            pass


def init_worker() -> None:
    global _catalog
    _catalog = S2Catalog()


def create_product_negatives(
    image_dir: Path,
    product_name: str,
    size: int,
    stride: int,
    positives: set[rasterio.windows.Window]
) -> None:
    product = _catalog[product_name]

    existing = set()
    for image in image_dir.glob(f"{product_name}_*.tif"):
        _, window = filename_to_window(image.stem)
        existing.add(window)
    existing -= positives

    windows = set(chip_tile(size, stride)) - positives - existing
    windows = random.sample(list(windows), len(positives) - len(existing))

    with product as src:
        for window in windows:
            data = src.read(window=window)

            with rasterio.open(
                image_dir / window_to_filename(product_name, window), "w",
                driver="GTiff",
                width=window.width,
                height=window.height,
                count=product.count,
                dtype="uint16",
                crs=product.crs,
                transform=product.window_transform(window),
                compress="DEFLATE"
            ) as dst:
                dst.write(data)


def product_targets(
    target_dir: Path
) -> dict[str, set[rasterio.windows.Window]]:
    targets = {}
    for target in target_dir.glob("*.tif"):
        product_name, window = filename_to_window(target.stem)
        targets.setdefault(product_name, set()).add(window)
    return targets


def read_mask(mask: str):
    with fiona.open(mask) as colxn:
        for feature in colxn:
            yield from polygon_iterator(feature.geometry)


if __name__ == "__main__":
    create_negatives()
