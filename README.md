# gpxtractor

**GPX, TCX and FIT data extraction for Python**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Description


## Features


## Installation

```bash
git clone 
cd gpxtractor
pip install .
```

## Usage Example
Use the `gpxtractor.extract_data` function that returns a gpxtractor.Activity instance.

```python
import gpxtractor

activity = gpxtractor.extract_data("your-gpx-tcx-or-fit_file.gpx")

print(activity.sport) # Output: name of the sport in the file as a string

```

The records attribute is a `pandas.DataFrame` holding the records extracted from the file\n
with the `gpxtractor.extract_data` function. So the usual `pandas.DataFrame` methods can be applied

```python
print(activity.records.head())
```

Once an instance of an Activity as been created with the `extract_data` function, the method\n
`transform_records` can be used to calculate distance and speed if missing from the file as well as\n
elevation incremental difference, gradient and in the case of running activities, pace.

```python
activity.transform_records()
print(activity.records.head())
```

And once the records have been transformed with `transform_records`, it is possible to use the 2\n
following methods to calculate aggregated data for kilometre and lap splits.

```python
activity.compute_km_splits()
print(activity.km_splits)

activity.compute_lap_splits()
print(activity.lap_splits)
```
Note: the `compute_lap_splits` will only compute lap splits if the file contains lap data which is not\n
the case for GPX files. It does not update the `lap_splits` attribute otherwise.


