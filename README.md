# gpxtractor

**GPX, TCX and FIT data extraction and transformation for Python**

[![PyPI version](https://img.shields.io/pypi/v/gpxtractor.svg)](https://pypi.org/project/gpxtractor/)   
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Description

`gpxtractor` is a Python library designed for **data extraction and transformation** of GPS and fitness tracking files, supporting **GPX, TCX, and FIT** formats, whether gzipped or not.

### Extraction Stage

*Important: As the goal of `gpxtractor` is to extract and transform the data from all 3 file types (GPX, TCX and FIT) in a uniform manner, the extraction step is selective. It only extracts the following: timestamp, coordinates (latitude and longitude), and if present in the file, altitude, distance, speed, heart rate and cadence.*

- Extracts raw data from the file **as-is**, preserving the original units for all fields.
- **Exception**: For FIT files, coordinates, which are stored differently, are automatically converted to degrees.

*Note: if the sport is running, the cadence is in strides per minute (steps per minute divided by 2) which for clarity is abbreviated to `strpm` in this package.*

### Transformation Stage

- **Calculates missing metrics**:
  - If **distance** or **speed** are not present in the original file, they are computed.
  - If the file contains altitude data, **gradient** and **diff_altitude** (the incremental difference in altitude between two rows) are computed.
- **Converts units**:
  - **Distance**: km (default) or mi
  - **Speed**: km/h (default) or mph
  - **Pace**: min/km (default) or min/mi
  - **Altitude/Elevation**: m (default) or ft
- **Cadence handling**:
  - If the sport is `"running"`: steps per minute (spm)
  - For all other sports: revolutions per minute (rpm)
- **Calculates aggregated data grouped by splits**
  - by split: kilometre splits (default) or mile splits
  - by lap
- **Calculates aggregate statistics for the whole file**
  - `start_time`
  - `elapsed_time`
  - `distance`
  - `avg_speed`
  - `max_speed`
  - `avg_pace`
  - `elevation_gain`
  - `elevation_loss`
  - `avg_heart_rate`
  - `max_heart_rate`
  - `avg_cadence`
  - `max_cadence`

## Platform requirements

This is a side project and has not been extensively tested, but the package is expected to work with:
- Linux, MacOS, Windows (for Windows, the CLI will only work in WSL)
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
pip install gpxtractor
pip install visidata
```

## Usage

### Command-line Interface (CLI)

The default usage of the CLI without flags, opens a 3-page TUI with data visuals for a quick analysis of the file.
```bash
gpxtractor <filename.gpx>  # or .tcx, .fit, .gpx.gz, .tcx.gz, .fit.gz
```
Or if you prefer imperial units:
```bash
gpxtractor <filename.gpx> --imperial
```

- Press `1` for the first page with area charts showing altitude, speed, heart rate and cadence (if available) over elapsed time.
    - Press `l` to switch from elapsed time to distance on the x-axis.
    - Press `h` to switch back to elapsed time on the x-axis.
- Press `2` for the second page with a table of data aggregated by split (by kilometre or mile).
- Press `3` for the third page with a table of data aggregated by lap.

For all pages:
- Press `j` to scroll down
- Press `k` to scroll up
- Press `f` for page down
- Press `b` for page up
- Press `g` for top of page
- Press `G` for bottom of page
- Press `q` to quit

![TUI Demo](https://raw.githubusercontent.com/c-stap/gpxtractor/main/assets/demo.gif)

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

Or if you prefer imperial units:
```python
activity.full_transform(units="imperial")
```

You can check that the activity has been transformed with:
```python
activity.is_transformed  # returns a bool
```

The `full_transform` method calculates the following aggregate data available in the following attributes:
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

The `full_transform` method also calculates data aggregated by kilometre split and by lap which are accessible with the `splits` and `laps` attributes respectively.

```python
print(activity.splits.head())
print(activity.laps.head())
```
*Note: `full_transform` will only compute lap splits if the file contains lap data which is not the case for GPX files, in which case `laps` attribute is `None`.*


Below are all the attributes of a gpxtractor.Activity instance and their types:
```python
for attr in vars(activity):
    print(f"{attr}: {type(getattr(activity, attr))}")
```
```console
file_type: <class 'str'>
sport: <class 'str'>
records: <class 'pandas.core.frame.DataFrame'>
units: <class 'dict'>
start_time: <class 'pandas._libs.tslibs.timestamps.Timestamp'>
elapsed_time: <class 'datetime.timedelta'>
distance: <class 'gpxtractor.core.Stat'>
avg_speed: <class 'gpxtractor.core.Stat'>
max_speed: <class 'gpxtractor.core.Stat'>
avg_pace: <class 'gpxtractor.core.Stat'>
elevation_gain: <class 'gpxtractor.core.Stat'>
elevation_loss: <class 'gpxtractor.core.Stat'>
avg_heart_rate: <class 'gpxtractor.core.Stat'>
max_heart_rate: <class 'gpxtractor.core.Stat'>
avg_cadence: <class 'gpxtractor.core.Stat'>
max_cadence: <class 'gpxtractor.core.Stat'>
splits: <class 'pandas.core.frame.DataFrame'>
laps: <class 'pandas.core.frame.DataFrame'>
is_transformed: <class 'bool'>
```

**Units**

Some units will change with the transformation step. It is possible to consult the units for both the columns of the `records`, `splits` and `laps` attributes and the units of the aggregated statistics stored as `gpxtractor.Activity` attributes of type `<class 'gpxtractor.core.Stat'>`. The `gpxtractor.core.Stat` class is designed to hold both numerical value and the associated unit. It has two attributes: `value` and `unit`. The snippets below show how you can access the value and unit of the aggregate statistics of a `gpxtractor.Activity instance`.

```console
>>> activity.max_speed
20.8799991607666 km/h
>>> activity.max_speed.value
20.8799991607666
>>> activity.max_speed.unit
'km/h'
>>> float(activity.max_speed)
20.8799991607666
>>> str(activity.max_speed)  # floats are rounded to 2 decimals
'20.88 km/h'
>>> repr(activity.max_speed)
'20.8799991607666 km/h'
>>> print(activity.max_speed)
20.88 km/h
```

To get the units for the columns of the `pandas.DataFrame` instances stored in the `records`, `splits` and `laps` attributes of a gpxtractor.Activity instance, you can use the `get_unit` method as follows:
```console
>>> activity.get_unit("avg_speed")  # replace "avg_speed" with any column name
'km/h'
```

Or to get the unit in full:
```console
>>> activity.get_unit("avg_speed", abbr=False)
'kilometres per hour'
```

**The transformation step in several methods**

If, for whatever reason, you need to transform the records without computing the splits DataFrames, it is possible to transform the records without calculating the data aggregated by split with the `transform_records` method.
```python
activity.transform_records()
print(activity.records.head())
```

Or if you prefer imperial units:
```python
activity.transform_records(units="imperial")
```

Reminder: you can check that the activity has been transformed.
```python
activity.is_transformed  # returns a bool
```

And once the records have been transformed with `transform_records`, it is possible to use the 2 following methods to calculate aggregated data for kilometre and lap splits.

```python
activity.compute_splits()
print(activity.splits)

activity.compute_laps()
print(activity.laps)
```

## Roadmap

- **Mouse scroll and arrow support for the TUI**: Enhance the terminal user interface for smoother navigation.
- **Additional metrics**: Expand the available metrics to include power, stride length, and more.

## Version History

- **v0.3.0** (2026-06-05):
    - Added option to use imperial units instead of the metric system for the transformation stage:
        - in the CLI: with the `--imperial` flag
        - in the Python API: by setting the `units` parameter to `"imperial"` in the `transform_records` and `full_transform` methods.
    - *Breaking changes*:
        - `Activity` attributes renamed:
            - `km_splits` renamed `splits`.
            - `lap_splits` renamed `laps`.
        - `Activity` methods renamed:
            - `comput_km_splits` renamed `compute_splits`.
            - `compute_lap_splits` renamed `compute_laps`.
- **v0.2.1** (2026-05-23):
    - Fixed: replaced importlib_resources with standard module importlib.resources as it was not specified in required dependencies.
- **v0.2.0** (2026-05-23):
    - Introduced a new Terminal User Interface (TUI) in the CLI for a quick analysis with some data visuals of the contents of the file
    - Unit clarity:
        - Added `Activity.get_unit()` method for easy retrieval of the unit for columns in records and splits DataFrames.
        - Added `Stat` class to provide clarity on the units used for aggregate statistics in Activity attributes.
- **v0.1.0** (2026-04-21)

## Licence

This project is licensed under the **MIT Licence** – see the [LICENSE](LICENSE) file for details.
