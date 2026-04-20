import os
import numpy as np
import pandas as pd

from gpxtractor import extract_data, Activity
from gpxtractor._utils import _get_file_extensions


def _generate_filepaths_in_assets():
    asset_dir = "assets"
    rides_dir = os.path.join(asset_dir, "rides")
    runs_dir = os.path.join(asset_dir, "runs")

    for file in os.listdir(runs_dir):
        yield os.path.join(runs_dir, file)
    for file in os.listdir(rides_dir):
        yield os.path.join(rides_dir, file)


def _validate_extracted_dataframe(df, cols, col_dtypes, non_null_cols):
    assert isinstance(df, pd.DataFrame)

    assert set(df.columns) == set(cols)

    for col, datatype in zip(cols, col_dtypes):
        if datatype is pd.DatetimeTZDtype:
            assert isinstance(df[col].dtype, pd.DatetimeTZDtype)
        else:
            assert df[col].dtype == datatype
    for col in non_null_cols:
        assert not df[col].isna().all()


def _validate_gpx_extracted_df(df):
    cols = [
        "timestamp",
        "latitude",
        "longitude",
        "altitude",
        "heart_rate",
        "cadence",
    ]
    col_dtypes = [
        pd.DatetimeTZDtype,
        np.float32,
        np.float32,
        np.float32,
        np.uint8,
        np.uint8,
    ]
    _validate_extracted_dataframe(df, cols, col_dtypes, non_null_cols=cols[:3])


def _validate_tcx_fit_extracted_df(df):
    cols = [
        "lap",
        "timestamp",
        "latitude",
        "longitude",
        "distance",
        "speed",
        "altitude",
        "heart_rate",
        "cadence",
    ]
    col_dtypes = [
        np.uint16,
        pd.DatetimeTZDtype,
        np.float32,
        np.float32,
        np.float32,
        np.float32,
        np.float32,
        np.uint8,
        np.uint8,
    ]
    _validate_extracted_dataframe(df, cols, col_dtypes, non_null_cols=cols[:4])


def test_extract_data():
    for filepath in _generate_filepaths_in_assets():
        activity = extract_data(filepath)
        assert isinstance(activity, Activity)
        assert type(activity.file_type) is str
        assert activity.file_type in ["GPX", "TCX", "FIT"]
        assert type(activity.sport) is str
        assert activity.sport in ["running", "biking", "cycling"]
        match activity.file_type:
            case "GPX":
                _validate_gpx_extracted_df(activity.records)
            case "TCX" | "FIT":
                _validate_tcx_fit_extracted_df(activity.records)
            case _:
                raise ValueError("Not a valid file type: Try a GPX, TCX or FIT file")
