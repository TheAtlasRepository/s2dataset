from .utils import window_to_filename, polygon_iterator
from datetime import datetime
from pathlib import Path
from s2utils import S2Tile, S2TileIndex, S2Catalog, chip_tile, rasterize_tile
from tqdm import tqdm
from typing import Any, Iterator, Sequence

import click
import concurrent.futures as cf
import fiona
import rasterio


@click.command()
@click.argument("data_dir", type=str)
@click.argument("labels", type=str)
@click.option("--name", "-n", type=str, help="Name of the class. Defaults to the name of the label file.")
@click.option("--start-date", "-b", type=str, help="Start date of the search.")
@click.option("--end-date", "-e", type=str, help="End date of the search.")
@click.option("--size", "-s", type=int, default=224, help="Size of the images.")
@click.option("--stride", "-t", type=int, default=224, help="Stride of the sliding window.")
@click.option("--workers", "-w", type=int, default=1, help="Number of workers to use.")
def create_targets(
    data_dir: str,
    labels: str,
    name: str | None,
    start_date: datetime | str | None,
    end_date: datetime | str | None,
    size: int,
    stride: int,
    workers: int
) -> None:
    """Create targets for the dataset.
    
    DATA_DIR is the path to the root directory of the dataset. LABELS is the path
    to the file containing the labels.
    """
    if name is None:
        name = Path(labels.removesuffix("".join(Path(labels).suffixes))).name

    target_dir = Path(data_dir) / "targets" / name
    target_dir.mkdir(parents=True, exist_ok=True)
    
    with cf.ProcessPoolExecutor(workers, initializer=init_worker) as pool:
        futures = []
        with S2TileIndex() as index:
            for tile, geometries in index.reverse_intersection(read_labels(labels)):
                futures.append(
                    pool.submit(
                        create_tile_targets,
                        target_dir,
                        tile,
                        geometries,
                        start_date,
                        end_date,
                        size,
                        stride))

        for _ in tqdm(cf.as_completed(futures), "Creating targets", len(futures)):
            pass


def init_worker() -> None:
    global _catalog
    _catalog = S2Catalog()


def create_tile_targets(
    target_dir: Path,
    tile: S2Tile,
    geometries: Sequence[Any],
    start_date: datetime | str | None,
    end_date: datetime | str | None,
    size: int,
    stride: int
) -> None:
    target = rasterize_tile(tile, geometries)

    windows = []
    for window in chip_tile(size, stride):
        if target[window.toslices()].any():
            windows.append(window)

    for product in _catalog.search(
        tile,
        start_date=start_date,
        end_date=end_date,
        max_items=1,
        sort_key="cloudcover"
    ):
        for window in windows:
            with rasterio.open(
                target_dir / window_to_filename(product.name, window), "w",
                driver="GTiff",
                width=window.width,
                height=window.height,
                count=1,
                dtype="uint8",
                crs=product.crs,
                transform=product.window_transform(window),
                compress="DEFLATE"
            ) as dst:
                dst.write(target[window.toslices()], 1)


def read_labels(path: str) -> Iterator[Any]:
    with fiona.open(path) as colxn:
        for feature in tqdm(colxn, "Reading features"):
            yield from polygon_iterator(feature.geometry)


if __name__ == "__main__":
    create_targets()
