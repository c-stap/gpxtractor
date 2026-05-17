import gzip
import pathlib
from typing import Optional
from dataclasses import dataclass, field
from datetime import timedelta
import pyarrow as pa
import pandas as pd

import gpxtractor._xml_extraction as xml_ext
import gpxtractor._fit_extraction as fit_ext
import gpxtractor._transformation as tr
import gpxtractor._utils as ut


@dataclass
class Stat:
    # TODO: docstring
    value: int | float | str
    unit: str

    def __float__(self):
        if isinstance(self.value, (float, int)):
            return float(self.value)
        else:
            raise ValueError("Stat.value is not a numerical value")

    def __int__(self):
        if isinstance(self.value, (float, int)):
            return int(self.value)
        else:
            raise ValueError("Stat.value is not a numerical value")

    def __str__(self):
        if isinstance(self.value, float):
            return f"{self.value:.2f} {self.unit}"
        else:
            return f"{self.value} {self.unit}"

    def __repr__(self):
        return f"{self.value} {self.unit}"


@dataclass
class Activity:
    # TODO: add units attribute to docstring
    """Stores and manages records and metadata parsed from a gpx, tcx or
    fit file.

    This class is designed to hold structured data and associated metadata
    extracted from a gpx, tcx or fit file, providing methods for accessing
    and transforming the records.

    Parameters
    ----------
    file_type : str
        Can be any of the following: 'GPX', 'TCX' or 'FIT'.
        Corresponds to the type of the file for which the instance of the
        class holds data.

    sport : str
        Is the type of sport as extracted from the file in lower case.

    records : pandas.DataFrame
        DataFrame holding the records extracted from the gpx, tcx or fit file.

    Attributes
    ----------
    is_transformed : bool
        initially False, becomes True once either the method
        `transform_records` or `full_transform` is used.

    file_type : str
        Can be any of the following: 'GPX', 'TCX' or 'FIT'.
        Corresponds to the type of the file for which the instance of the
        class holds data.

    sport : None or str
        Is the type of sport as extracted from the file in lower case.

    start_time : None or pandas.Timestamp
        Is None before a transformation method has been called.
        A pandas Timestamp with timezone information indicating the start
        time of the activity.

    elapsed_time : None or timedelta
        Is None before a transformation method has been called.
        An timedelta indicating the total elapsed time of the activity.

    distance : None or Stat
        Is None before a transformation method has been called.
        A Stat instance holding in its value attribute a float
        indicating the total distance covered during the activity
        in kilometres.

    avg_speed : None or Stat
        Is None before a transformation method has been called.
        A Stat instance holding in its value attribute a float
        indicating the average speed over the activity in kph.

    avg_pace : None or Stat
        Is None before a transformation method has been called.
        A Stat instance holding in its value attribute a string
        indicating the average pace over the activity in min per km.

    elevation_gain : None or Stat
        Is None before a transformation method has been called.
        A Stat instance holding in its value attribute an integer
        indicating the total elevation gained during the activity
        in meters.

    elevation_loss : None or Stat
        Is None before a transformation method has been called.
        A Stat instance holding in its value attribute an integer
        indicating the total elevation lossed during the activity
        in meters.

    avg_heart_rate : None or Stat
        Is None before a transformation method has been called.
        A Stat instance holding in its value attribute an integer
        indicating the average heart rate of the activity in bpm.

    max_heart_rate : None or Stat
        Is None before a transformation method has been called.
        A Stat instance holding in its value attribute an integer
        indicating the maximum heart rate of the activity in bpm.

    avg_cadence : None or Stat
        Is None before a transformation method has been called.
        A Stat instance holding in its value attribute an integer
        indicating the average cadence of the activity in either
        rpm or, in the case of a running activity spm.

    max_cadence : None or Stat
        Is None before a transformation method has been called.
        A Stat instance holding in its value attribute an integer
        indicating the maximum cadence of the activity in either
        rpm or, in the case of a running activity spm.

    records : pandas.DataFrame
        DataFrame holding the records extracted from the gpx, tcx or fit file.
        Records can be transformed with the methods `transform_records` or
        `full_transform`.

    km_splits : None or pandas.DataFrame
        Initially None. DataFrame holding the transformed and aggregated data
        grouped by kilometre splits once the `compute_km_splits` or
        `full_transform` method has been used.

    lap_splits : None or pandas.DataFrame
        Initially None. DataFrame holding the transformed and aggregated data
        grouped by lap splits once the `compute_lap_splits` or
        `full_transform` method has been used. Can only hold data if the file
        has lap data which is not the case for gpx files.
    """

    file_type: str
    sport: str
    records: pd.DataFrame
    units: dict = field(init=False)
    is_transformed: bool = field(default=False, init=False)
    start_time: Optional[pd.Timestamp] = field(default=None, init=False)
    elapsed_time: Optional[int] = field(default=None, init=False)
    distance: Optional[float] = field(default=None, init=False)
    avg_speed: Optional[float] = field(default=None, init=False)
    max_speed: Optional[float] = field(default=None, init=False)
    avg_pace: Optional[str] = field(default=None, init=False)
    elevation_gain: Optional[int] = field(default=None, init=False)
    elevation_loss: Optional[int] = field(default=None, init=False)
    avg_heart_rate: Optional[int] = field(default=None, init=False)
    max_heart_rate: Optional[int] = field(default=None, init=False)
    avg_cadence: Optional[int] = field(default=None, init=False)
    max_cadence: Optional[int] = field(default=None, init=False)
    km_splits: Optional[pd.DataFrame] = field(default=None, init=False)
    lap_splits: Optional[pd.DataFrame] = field(default=None, init=False)

    def __post_init__(self):
        self.units = ut.get_extracted_units(self.sport)

    def __str__(self):
        records_str = str(self.records.head())
        km_splits_str = (
            str(self.km_splits.head()) if self.km_splits is not None else None
        )
        lap_splits_str = (
            str(self.lap_splits.head()) if self.lap_splits is not None else None
        )
        return (
            "Activity(\n"
            f"  is_transformed: {self.is_transformed}\n"
            f"  units: {self.units}\n"
            f"  file_type: {self.file_type}\n"
            f"  sport: {self.sport}\n"
            f"  start_time: {self.start_time}\n"
            f"  elapsed_time: {self.elapsed_time}\n"
            f"  distance: {self.distance}\n"
            f"  avg_speed: {self.avg_speed}\n"
            f"  max_speed: {self.max_speed}\n"
            f"  avg_pace: {self.avg_pace}\n"
            f"  elevation_gain: {self.elevation_gain}\n"
            f"  elevation_loss: {self.elevation_loss}\n"
            f"  avg_heart_rate: {self.avg_heart_rate}\n"
            f"  max_heart_rate: {self.max_heart_rate}\n"
            f"  avg_cadence: {self.avg_cadence}\n"
            f"  max_cadence: {self.max_cadence}\n"
            f"  records:\n{records_str}\n"
            f"  km_splits:\n{km_splits_str}\n"
            f"  lap_splits:\n{lap_splits_str}\n"
            ")"
        )

    def get_unit(self, stat: str, abbr: bool = True):
        # TODO: doctstring
        base_stat = ut.get_base_stat_regex(stat)
        unit_tuple = self.units.get(base_stat)
        unit = unit_tuple[1]
        if abbr:
            unit = unit_tuple[0]
        return unit

    def _transform_records_to_pyarrow(self):
        if not self.is_transformed:
            self.units = ut.get_transformed_units(self.sport)
            self.records = pa.Table.from_pandas(self.records)
            self.records = tr.transform_data(self.records, self.sport)
            stats = tr.compute_overall_stats(self.records)
            for col in stats.columns:
                val = stats[col].at[0]
                if col == "elapsed_time":
                    val = timedelta(seconds=val)
                elif col in ut.STAT_ATTRS:
                    unit = self.get_unit(col)
                    val = Stat(val, unit)
                setattr(self, col, val)

    def transform_records(self):
        """Transforms the data in the records attributes to calculate distance,
        speed if absent and elevation difference, gradient and, in the case of
        running activities, pace.
        """
        if not self.is_transformed:
            self._transform_records_to_pyarrow()
            self.records = self.records.to_pandas(types_mapper=pd.ArrowDtype)
            self.is_transformed = True

    def compute_lap_splits(self):
        """If there is lap data in the records, updates the lap_splits to a
        DataFrame holding the transformed and aggregated data grouped by lap
        splits. Note: there is no lap data in gpx files.
        """
        if self.file_type != "GPX" and self.is_transformed:
            self.records = pa.Table.from_pandas(self.records)
            self.lap_splits = tr.compute_lap_data(self.records)
            self.records = self.records.to_pandas(types_mapper=pd.ArrowDtype)

    def compute_km_splits(self):
        """Updates km_splits attribute to a DataFrame holding the transformed
        and aggregated data grouped by kilometre splits.
        """
        if self.is_transformed:
            self.records = pa.Table.from_pandas(self.records)
            self.km_splits = tr.compute_km_data(self.records)
            self.records = self.records.to_pandas(types_mapper=pd.ArrowDtype)

    def full_transform(self):
        """Transforms data in records, computes km and lap splits"""
        if not self.is_transformed:
            self._transform_records_to_pyarrow()
            self.km_splits = tr.compute_km_data(self.records)
            if self.file_type != "GPX":
                self.lap_splits = tr.compute_lap_data(self.records)
            self.records = self.records.to_pandas(types_mapper=pd.ArrowDtype)
            self.is_transformed = True


def extract_data(file_path: pathlib.Path) -> Activity:
    """Extract records from a gpx, tcx or fit file.
    Create and return a new Activity instance where records are
    stored as a pandas.DataFrame in the records attribute and the
    sport is stored as a string in the sport attribute.

    Parameters
    ----------
    file_path : pathlib.Path
        Path to a file of type .gpx, .tcx or .fit. Can be gzipped.

    Returns
    -------
    gpxtractor.Activity

    Raises
    ------
    ValueError
        if the file type is not gpx, tcx or fit or their gzipped
        equivalent.
    """
    extensions = ut._get_file_extensions(file_path)
    match extensions:
        case ".gpx" | ".gpx.gz":
            sport, records = ut._handle_gzipped_xml_files(
                file_path, extensions, xml_ext.get_sport_from_gpx, xml_ext.extract_gpx
            )
        case ".tcx" | ".tcx.gz":
            sport, records = ut._handle_gzipped_xml_files(
                file_path, extensions, xml_ext.get_sport_from_tcx, xml_ext.extract_tcx
            )
        case ".fit":
            sport, records = fit_ext.extract_fit(file_path)
        case ".fit.gz":
            with gzip.open(file_path, "rb") as gz:
                sport, records = fit_ext.extract_fit(gz)
        case _:
            raise ValueError("Not a valid file type: Try a GPX, TCX or FIT file")
    file_type = ut._get_file_type_from_extensions(extensions)
    return Activity(file_type=file_type, sport=sport, records=records)
