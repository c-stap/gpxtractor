# gpxtractor

**GPX, TCX and FIT data extraction and transformation for Python**

[![PyPI version](https://img.shields.io/pypi/v/gpxtractor.svg)](https://pypi.org/project/gpxtractor/)   
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Description

`gpxtractor` is a Python library designed for **data extraction and transformation** of GPS and fitness tracking files, supporting **GPX, TCX, and FIT** formats, whether gzipped or not.

### Extraction Stage

- Extracts raw data from the file **as-is**, preserving the original units for all fields.
- **Exception**: For FIT files, coordinates are automatically converted to **latitude and longitude**.
- If present in the file:
  - **Distance**: metres
  - **Speed**: metres per second

### Transformation Stage

- **Calculates missing metrics**:
  - If **distance** or **speed** are not present in the original file, they are computed.
- **Converts and standardizes units**:
  - **Distance**: km
  - **Speed**: km/h
  - **Pace**: min/km
  - **Heart rate**: bpm
- **Cadence handling**:
  - If the sport is `"running"`: strides per minute (spm)
  - For all other sports: revolutions per minute (rpm)
- **Calculates aggregated data grouped by splits**
  - by kilometre split
  - by lap

## Platform requirements

This is a side project and has not been extensively tested, but the package is expected to work with:
- Linux, OS/X, Windows (for Windows, the CLI will only work in WSL as it uses visidata which is based on curses)
- Python 3.13
- Required Python dependencies: lxml, fitdecode, numpy, pandas, duckdb
- Optional Python dependencies: visidata is required for the CLI
- The TUI uses ANSI escape sequences so make sure to use a terminal emulator that supports them.

## Installation

To install `gpxtractor`, simply run:
```bash
pip install gpxtractor
```
Or, depending on your python setup, run:
```bash
pip3 install gpxtractor
```

To use the CLI, visidata must be installed (This will not work on Windows unless you are using WSL)
```bash
pip install gpxtractor[optional]
```
Or
```bash
pip install gpxtractor
pip install visidata
```

## Usage

### Command-line Interface (CLI)

The default usage of the CLI without flags, opens a 3-page TUI with data visuals for a quick analysis of the file.
```bash
gpxtractor <filename.gpx>  # or .tcx, .fit, .gpx.gz, .tcx.gz, .fit.gz
```

- Press `1` for the first page with area charts showing altitude, speed, heart rate and cadence (if available) over elapsed time.
    - Press `l` to switch from elapsed time to distance on the x-axis.
    - Press `h` to switch back to elapsed time on the x-axis.
- Press `2` for the second page with a table of data aggregated by kilometre split.
- Press `3` for the third page with a table of data aggregated by lap.

For all pages:
- Press `j` to scroll down
- Press `k` to scroll up
- Press `f` for page down
- Press `b` for page up
- Press `g` for top of page
- Press `G` for bottom of page
- Press `q` to quit

![TUI Demo](https://raw.githubusercontent.com/c-stap/gpxtractor/main/assets/demo.GIF)

For the full list of flags and what they do, run
```bash
gpxtractor --help
```

### Python API

Using `gpxtractor` in python is essentially a 2-step process:
- data extraction
- data transformation.

**Extraction**

The first step is to extract the data with `gpxtractor.extract_data()` which returns a `gpxtractor.Activity` instance.

```python
import gpxtractor

# Replace "your-gpx-tcx-or-fit_file.gpx" with the file you want to analyse.
activity = gpxtractor.extract_data("your-gpx-tcx-or-fit_file.gpx")

print(activity.sport) # Output: name of the sport in the file as a string
```

The records attribute is a `pandas.DataFrame` holding the records extracted from the file
with the `gpxtractor.extract_data` function. 

```python
print(activity.records.head())
```

**Transformation**

Once an instance of an Activity as been created with the `extract_data` function, the method `full_transform` can be used to calculate distance and speed if missing from the file as well as elevation incremental difference, gradient and in the case of running activities, pace.
```python
activity.full_transform()
print(activity.records.head())
```

The `full_transform` method also calculates the following aggregate data available in the following attributes:
```python
print(activity.start_time)
print(activity.elapsed_time)
print(activity.distance)
print(activity.avg_speed)
print(activity.max_speed)
print(activity.avg_pace)
print(activity.elevation_gain)
print(activity.elevation_loss)
print(activity.avg_heart_rate)
print(activity.max_heart_rate)
print(activity.avg_cadence)
print(activity.max_cadence)
```

The `full_transform` method also calculates data aggregated by kilometre split and by lap which are accessible with the `km_splits` and `lap_splits` attributes respectively.

```python
print(activity.km_splits.head())
print(activity.lap_splits.head())
```
*Note: the `compute_lap_splits` will only compute lap splits if the file contains lap data which is not the case for GPX files, in which case `lap_splits` attribute is `None`.*

**The transformation step in several methods**

If memory is a concern, it is possible to transform the records without calculating the data aggregated by split with the `transform_records` method.
```python
activity.transform_records()
print(activity.records.head())
```

You can check that the activity has been transformed with:
```python
activity.is_transformed  # returns a bool
```

And once the records have been transformed with `transform_records`, it is possible to use the 2 following methods to calculate aggregated data for kilometre and lap splits.

```python
activity.compute_km_splits()
print(activity.km_splits)

activity.compute_lap_splits()
print(activity.lap_splits)
```

## Roadmap

- **Mouse scroll and arrow support for the TUI**: Enhance the terminal user interface for smoother navigation.
- **Additional metrics**: Expand the available metrics to include power, stride length, and more.
- **Imperial units support**: Add a parameter to the `full_transform()` method to allow users to opt for imperial units.

## Version History

- **v0.2.0**: Introduced a new Terminal User Interface (TUI) in the CLI for a quick analysis with some data visuals of the contents of the file

## Licence

This project is licensed under the **MIT Licence** – see the [LICENSE](LICENSE) file for details.
