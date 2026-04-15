"""
GPX, TCX and FIT extraction for Python
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
    def __init__(self, file_type: str, sport: str, records: pd.DataFrame):
        self.are_records_transformed = False
        self.file_type = file_type
        self.sport = sport
        self.records = records
        self.km_splits = None
        self.lap_splits = None

    def transform_records(self):
        if not self.are_records_transformed:
            self.records = pa.Table.from_pandas(self.records)
            self.records = transform_data(self.records, self.sport)
            self.are_records_transformed = True

    def compute_lap_splits(self):
        if self.file_type != "GPX" and self.are_records_transformed:
            arrow_table = pa.Table.from_pandas(self.records)
            self.lap_splits = compute_lap_data(arrow_table)

    def compute_km_splits(self):
        if self.are_records_transformed:
            arrow_table = pa.Table.from_pandas(self.records)
            self.km_splits = compute_km_data(arrow_table)

    def full_transform(self):
        self.transform_records()
        self.compute_lap_splits()
        self.compute_km_splits()


def extract_data(file_path: pathlib.Path) -> pd.DataFrame:
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
