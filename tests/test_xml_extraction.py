import os
import numpy as np
import pandas as pd

from gpxtractor._xml_extraction import (
    get_sport_from_gpx,
    get_sport_from_tcx,
    extract_gpx,
    extract_tcx,
)


asset_dir = "assets"
rides_dir = os.path.join(asset_dir, "rides")
runs_dir = os.path.join(asset_dir, "runs")


def _filter_asset_files(dir: str, file_type: str):
    files = []
    for file in os.listdir(dir):
        if file.endswith(file_type):
            files.append(file)
    return files


def _get_sport_helper_func(dir, file_extension, func, sport_names_list: list):
    for file in _filter_asset_files(dir, file_extension):
        filepath = os.path.join(dir, file)
        with open(filepath, "r") as f:
            assert func(f) in sport_names_list


def _get_sport_helper_func_2(file_extension, func):
    _get_sport_helper_func(
        dir=runs_dir,
        file_extension=file_extension,
        func=func,
        sport_names_list=["running"],
    )
    _get_sport_helper_func(
        dir=rides_dir,
        file_extension=file_extension,
        func=func,
        sport_names_list=["cycling", "biking"],
    )


def test_get_sport_from_gpx():
    _get_sport_helper_func_2(".gpx", get_sport_from_gpx)


def test_get_sport_from_tcx():
    _get_sport_helper_func_2(".tcx", get_sport_from_tcx)


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


def _check_xml_extraction_function(
    files_to_test_dir,
    files_to_test_extension: str,
    func_to_test,
    cols: list,
    col_dtypes: list,
    non_null_cols: list,
):
    files_to_test = _filter_asset_files(files_to_test_dir, files_to_test_extension)

    for file in files_to_test:
        filepath = os.path.join(files_to_test_dir, file)
        df = func_to_test(filepath)
        assert isinstance(df, pd.DataFrame)

        assert set(df.columns) == set(cols)

        for col, datatype in zip(cols, col_dtypes):
            if datatype is pd.DatetimeTZDtype:
                assert isinstance(df[col].dtype, pd.DatetimeTZDtype)
            else:
                assert df[col].dtype == datatype
        for col in non_null_cols:
            assert not df[col].isna().all()


def test_extract_gpx():
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

    _check_xml_extraction_function(
        rides_dir, ".gpx", extract_gpx, cols, col_dtypes, cols[:3]
    )
    _check_xml_extraction_function(
        runs_dir, ".gpx", extract_gpx, cols, col_dtypes, cols[:3]
    )


def test_extract_tcx():
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

    _check_xml_extraction_function(
        rides_dir, ".tcx", extract_tcx, cols, col_dtypes, cols[:4]
    )
    _check_xml_extraction_function(
        runs_dir, ".tcx", extract_tcx, cols, col_dtypes, cols[:4]
    )
