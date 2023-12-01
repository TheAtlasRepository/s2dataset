# s2dataset

s2dataset is a streamlined, terminal-based tool for downloading and processing Sentinel-2 imagery, specifically tailored for neural network applications. It's engineered for ease of use and can be operated on a variety of machines, whether they're local, remote, in the cloud, or in other specialized environments.

### Setting up the project

It is recommended to install the project using a virtual python environment. Set it up and activate it by running these commands

`python -m venv venv`

`source ./venv/bin/activate`

To install the dependencies of the project, run

`pip install .`

### Create Negatives

Generate negative samples for the dataset.

`python -m src.s2dataset.create_positives`

Options:

- `root_dir`: Path to the root directory of the dataset.
- `--size` (default=224): Size of the images.
- `--stride` (default=224): Stride of the sliding window.
- `--workers` (default=1): Number of workers to use.

### Create Positives

Create positive samples for the dataset.

`python -m src.s2dataset.create_positives`

Options:

- `root_dir`: Path to the root directory of the dataset.
- `--workers` (default=1): Number of workers to use.

### Create Targets

Generate targets for the dataset based on labels.

`python -m src.s2dataset.create_targets`

Options:

- `root_dir`: Path to the root dataset directory.
- `labels`: Path to the labels file.
- `--name`: Name of the class, defaults to the label file name.
- `--start-date` and `--end-date`: Date range for data selection.
- `--size` (default=224): Size of the images.
- `--stride` (default=224): Stride of the sliding window.
- `--workers` (default=1): Number of workers to use.

Each of these commands is equipped with various options to customize the data processing as per your requirements.

---

For further assistance or more detailed documentation, refer to the `--help` option of each command.
