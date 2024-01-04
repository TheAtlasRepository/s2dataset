# s2dataset
Create machine learning datasets from publicly available Sentinel-2 data. `s2dataset` uses the [Sentinel-2 Cloud-Optimized GeoTIFFs](https://registry.opendata.aws/sentinel-2-l2a-cogs/) dataset, which is hosted on AWS and managed by [Element 84](https://www.element84.com/). Access to this dataset is free and does not require an AWS account, but the speed is limited compared to paid solutions. In order to create machine learning datasets covering large areas in a reasonable amount of time, `s2dataset` identifies which regions of a Sentinel-2 tile contain features of interest and only downloads those regions.

## Installation
s2dataset is not yet available on PyPi, but can be installed directly from GitHub using:
```bash
pip install https://github.com/TheAtlasRepository/s2dataset/archive/main.zip
```

## Usage
A dataset is created in three steps
  1. Create targets (segmentation masks) 
  2. Create positives (samples that contain features)
  3. Optional: Create negatives (samples that don't contain features)

### Create targets
The first step is to search for Sentinel-2 products that contain the features of interest, and create segmentation masks for those features. This is done using the `create_targets` command:
```bash
python -m s2dataset.create_targets <ROOT_DIR> <FEATURES>
```
where `<ROOT_DIR>` is the root directory of the dataset and `<FEATURES>` is a file containing the features. The features file must be in a format supported by fiona, and the features must be in the EPSG:4326 CRS. `create_targets` has the following optional arguments:
```
--size        // Size of the images (224)
--stride      // Stride of the sliding window (224)
--start-date  // Start date of the search
--end-date    // End date of the search
--workers     // Number of workers to use (1)
```

### Create positives
The second step is to download the regions of the Sentinel-2 products that contain the features of interest. This is done using the `create_positives` command:
```bash
python -m s2dataset.create_positives <ROOT_DIR>
```
where `<ROOT_DIR>` is the root directory of the dataset. This is a slow process, but it can safely be interrupted and resumed at a later time. `create_positives` has the following optional arguments:
```
--workers     // Number workers to use (1)
```

### Create negatives
The optional third step is to download the regions of the Sentinel-2 products that don't contain the features of interest. This is done using the `create_negatives` command:
```bash
python -m s2dataset.create_positives <ROOT_DIR>
```
where `<ROOT_DIR>` is the root directory of the dataset. This is a slow process, but it can safely be interrupted and resumed at a later time. `create_negatives` has the following optional arguments, which must match the arguments used for `create_targets`:
```
--size        // Size of the images (224)
--stride      // Stride of the sliding window (224)
--workers     // Number of workers to use (1)
```
