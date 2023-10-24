from .common import window_to_filename, filename_to_window
from pathlib import Path
from s2utils import S2Catalog
from tqdm import tqdm
from typing import Iterable

import click
import concurrent.futures as cf
import rasterio
import rasterio.windows


@click.command()
@click.argument("root_dir", type=str)
@click.option("--workers", "-w", type=int, default=1, help="Number of workers to use.")
def create_positives(
    root_dir: str,
    workers: int
) -> None:
    """Create positive samples for the dataset.
    
    ROOT_DIR is the path to the root directory of the dataset.
    """
    target_dir = Path(root_dir) / "targets"

    image_dir = Path(root_dir) / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    
    with cf.ProcessPoolExecutor(workers, initializer=init_worker) as pool:
        futures = []
        for product_name, windows in missing_positives(image_dir, target_dir).items():
            futures.append(
                pool.submit(
                    create_product_positives,
                    image_dir,
                    product_name,
                    windows))

        for _ in tqdm(cf.as_completed(futures), "Creating positives", len(futures)):
            pass


def init_worker() -> None:
    global _catalog
    _catalog = S2Catalog()


def create_product_positives(
    image_dir: Path,
    product_name: str,
    windows: Iterable[rasterio.windows.Window]
) -> None:
    product = _catalog[product_name]

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


def missing_positives(
    image_dir: Path,
    target_dir: Path
) -> dict[str, set[rasterio.windows.Window]]:
    targets = set()
    for target in target_dir.glob("*/*.tif"):
        targets.add(target.stem)
    
    images = set()
    for image in image_dir.glob("*.tif"):
        images.add(image.stem)
    
    missing = {}
    for filename in targets - images:
        product_name, window = filename_to_window(filename)
        missing.setdefault(product_name, set()).add(window)

    return missing


if __name__ == "__main__":
    create_positives()