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
from gpxtractor.transformation import transform_data, compute_km_data, compute_lap_data
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

    sport : str
        Is the type of sport as extracted from the file in lower case.

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
            f"  records:\n{records_str}\n"
            f"  km_splits:\n{km_splits_str}\n"
            f"  lap_splits:\n{lap_splits_str}\n"
            ")"
        )

    def __repr__(self):
        pass

    def transform_records(self):
        """Transforms the data in the records attributes to calculate distance,
        speed if absent and elevation difference, gradient and, in the case of
        running activities, pace.
        """
        if not self.is_transformed:
            self.records = pa.Table.from_pandas(self.records)
            self.records = transform_data(self.records, self.sport)
            self.is_transformed = True

    def compute_lap_splits(self):
        """If there is lap data in the records, updates the lap_splits to a
        DataFrame holding the transformed and aggregated data grouped by lap
        splits. Note: there is no lap data in gpx files.
        """
        if self.file_type != "GPX" and self.is_transformed:
            arrow_table = pa.Table.from_pandas(self.records)
            self.lap_splits = compute_lap_data(arrow_table)

    def compute_km_splits(self):
        """Updates km_splits attribute to a DataFrame holding the transformed
        and aggregated data grouped by kilometre splits.
        """
        if self.is_transformed:
            arrow_table = pa.Table.from_pandas(self.records)
            self.km_splits = compute_km_data(arrow_table)

    def full_transform(self):
        """Transforms data in records, computes km and lap splits"""
        self.transform_records()
        if self.is_transformed:
            arrow_table = pa.Table.from_pandas(self.records)
            self.km_splits = compute_km_data(arrow_table)
            if self.file_type != "GPX":
                self.lap_splits = compute_lap_data(arrow_table)


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
