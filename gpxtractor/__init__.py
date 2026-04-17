"""
GPX, TCX and FIT data extraction for Python
======================================

gpxtractor is a python package to extract data from
gpx, tcx and fit files and present it in a dataframe.
"""

__version__ = "0.1.0"


import gzip
import pathlib
import pyarrow as pa
import pandas as pd

from gpxtractor.xml_extraction import (
    extract_gpx,
    extract_tcx,
    get_sport_from_gpx,
    get_sport_from_tcx,
)
from gpxtractor.fit_extraction import extract_fit
from gpxtractor.transformation import (
    transform_data,
    compute_km_data,
    compute_lap_data,
    compute_overall_stats,
)
from gpxtractor.utils import (
    _get_file_extensions,
    _get_file_type_from_extensions,
    _handle_gzipped_xml_files,
)


class Activity:
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

    elapsed_time : None or int
        Is None before a transformation method has been called.
        An integer indicating the total elapsed time of the activity in
        seconds.

    distance : None or float
        Is None before a transformation method has been called.
        A float indicating the total distance covered during the activity
        in kilometres.

    avg_speed : None or float
        Is None before a transformation method has been called.
        A float indicating the average speed over the activity in kph.

    avg_pace : None or str
        Is None before a transformation method has been called.
        A string indicating the average pace over the activity in min per km.

    elevation_gain : None or int
        Is None before a transformation method has been called.
        An integer indicating the total elevation gained during the activity
        in meters.

    elevation_loss : None or int
        Is None before a transformation method has been called.
        An integer indicating the total elevation lossed during the activity
        in meters.

    avg_heart_rate : None or int
        Is None before a transformation method has been called.
        An integer indicating the average heart rate of the activity in bpm.

    max_heart_rate : None or int
        Is None before a transformation method has been called.
        An integer indicating the maximum heart rate of the activity in bpm.

    avg_cadence : None or int
        Is None before a transformation method has been called.
        An integer indicating the average cadence of the activity in either
        rpm or, in the case of a running activity spm.

    max_cadence : None or int
        Is None before a transformation method has been called.
        An integer indicating the maximum cadence of the activity in either
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

    Methods
    -------
    transform_records
        Transforms the data in the records attributes to calculate distance,
        speed if absent and elevation difference, gradient and, in the case of
        running activities, pace.

    compute_km_splits
        Updates the km_splits attribute to a DataFrame holding the transformed
        and aggregated data grouped by kilometre splits.

    compute_lap_splits
        If there is lap data in the records, updates the lap_splits to a
        DataFrame holding the transformed and aggregated data grouped by lap
        splits. Note: there is no lap data in gpx files.

    full_transform
        All of the 3 methods above in the one.
    """

    def __init__(self, file_type: str, sport: str, records: pd.DataFrame):
        """Initialise the Activity instance

        Parameters
        ----------
        file_type : str
            Can be any of the following: 'GPX', 'TCX' or 'FIT'.
            Corresponds to the type of the file for which the instance of the
            class holds data.

        sport : str
            Is the type of sport as extracted from the file in lower case.

        records : pandas.DataFrame
            DataFrame holding the records extracted from the gpx, tcx or fit
            file.

        """
        self.is_transformed = False
        self.file_type = file_type
        self.sport = sport
        self.start_time = None
        self.elapsed_time = None
        self.distance = None
        self.avg_speed = None
        self.avg_pace = None
        self.elevation_gain = None
        self.elevation_loss = None
        self.avg_heart_rate = None
        self.max_heart_rate = None
        self.avg_cadence = None
        self.max_cadence = None
        self.records = records
        self.km_splits = None
        self.lap_splits = None

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
            f"  file_type: {self.file_type}\n"
            f"  sport: {self.sport}\n"
            f"  start_time: {self.start_time}\n"
            f"  elapsed_time: {self.elapsed_time}\n"
            f"  distance: {self.distance}\n"
            f"  avg_speed: {self.avg_speed}\n"
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

    def __repr__(self):
        pass

    def _transform_records_to_pyarrow(self):
        if not self.is_transformed:
            self.records = pa.Table.from_pandas(self.records)
            self.records = transform_data(self.records, self.sport)
            stats = compute_overall_stats(self.records)
            self.start_time = stats["start_time"].at[0]
            self.elapsed_time = int(stats["elapsed_time"].at[0])
            self.distance = float(stats["distance"].at[0])
            self.avg_speed = float(stats["avg_speed"].at[0])
            self.avg_pace = stats["avg_pace"].at[0]
            self.elevation_gain = int(stats["elevation_gain"].at[0])
            self.elevation_loss = int(stats["elevation_loss"].at[0])
            self.avg_heart_rate = int(stats["avg_heart_rate"].at[0])
            self.max_heart_rate = int(stats["max_heart_rate"].at[0])
            self.avg_cadence = int(stats["avg_cadence"].at[0])
            self.max_cadence = int(stats["max_cadence"].at[0])

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
            self.lap_splits = compute_lap_data(self.records)
            self.records = self.records.to_pandas(types_mapper=pd.ArrowDtype)

    def compute_km_splits(self):
        """Updates km_splits attribute to a DataFrame holding the transformed
        and aggregated data grouped by kilometre splits.
        """
        if self.is_transformed:
            self.records = pa.Table.from_pandas(self.records)
            self.km_splits = compute_km_data(self.records)
            self.records = self.records.to_pandas(types_mapper=pd.ArrowDtype)

    def full_transform(self):
        """Transforms data in records, computes km and lap splits"""
        if not self.is_transformed:
            self._transform_records_to_pyarrow()
            self.km_splits = compute_km_data(self.records)
            if self.file_type != "GPX":
                self.lap_splits = compute_lap_data(self.records)
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
    extensions = _get_file_extensions(file_path)
    match extensions:
        case ".gpx" | ".gpx.gz":
            sport, records = _handle_gzipped_xml_files(
                file_path, extensions, get_sport_from_gpx, extract_gpx
            )
        case ".tcx" | ".tcx.gz":
            sport, records = _handle_gzipped_xml_files(
                file_path, extensions, get_sport_from_tcx, extract_tcx
            )
        case ".fit":
            sport, records = extract_fit(file_path)
        case ".fit.gz":
            with gzip.open(file_path, "rb") as gz:
                sport, records = extract_fit(gz)
        case _:
            raise ValueError("Not a valid file type: Try a GPX, TCX or FIT file")
    file_type = _get_file_type_from_extensions(extensions)
    return Activity(file_type=file_type, sport=sport, records=records)
