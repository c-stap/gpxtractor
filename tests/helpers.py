import numpy as np
import pandas as pd


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
