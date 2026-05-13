# gpxtractor

**GPX, TCX and FIT data extraction and transformation for Python**

[![PyPI version](https://img.shields.io/pypi/v/gpxtractor.svg)](https://pypi.org/project/gpxtractor/)   
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Description
`gpxtractor` is a python package that extracts data 

## Features


## Installation

To install `gpxtractor`, simply run:
```bash
pip install gpxtractor
```

## Usage
### CLI

The default usage
```bash
gpxtractor <filename.gpx>  # or .tcx or .fit
```
![TUI Demo](https://raw.githubusercontent.com/c-stap/gpxtractor/main/assets/demo.GIF)

For the full list of flags and what they do, run
```bash
gpxtractor --help
```

### Python API
Using `gpxtractor` in python is essentially a 2-step process: extraction and transformation.

**Extraction**
The simplest way to use the `gpxtractor` in python is to extract the data with `gpxtractor.extract_data()` which returns a gpxtractor.Activity instance.

```python
import gpxtractor

activity = gpxtractor.extract_data("your-gpx-tcx-or-fit_file.gpx")

print(activity.sport) # Output: name of the sport in the file as a string
```
The records attribute is a `pandas.DataFrame` holding the records extracted from the file
with the `gpxtractor.extract_data` function.

```python
print(activity.records.head())
```

**Transformation**
Once an instance of an Activity as been created with the `extract_data` function, the method
`transform_records` can be used to calculate distance and speed if missing from the file as well as
elevation incremental difference, gradient and in the case of running activities, pace.

```python
activity.transform_records()
print(activity.records.head())
```

And once the records have been transformed with `transform_records`, it is possible to use the 2
following methods to calculate aggregated data for kilometre and lap splits.

```python
activity.compute_km_splits()
print(activity.km_splits)

activity.compute_lap_splits()
print(activity.lap_splits)
```
Note: the `compute_lap_splits` will only compute lap splits if the file contains lap data which is not
the case for GPX files, in which case `lap_splits` attribute is `None`.

## Roadmap

- **Mouse scroll and arrow support for the TUI**: Enhance the terminal user interface for smoother navigation.
- **Additional metrics**: Expand the available metrics to include power, stride length, and more.
- **Imperial units support**: Add a parameter to the `full_transform()` method to allow users to opt for imperial units.


## Version History

- **v0.2.0**: Introduced a new Terminal User Interface (TUI) in the CLI for a quick analysis with some data visualisations of the contents of the file
