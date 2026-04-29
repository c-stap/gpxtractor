import pandas as pd

import gpxtractor
from gpxtractor import _transformation as tr


def test_get_var_name():
    variable_name = "variable_content"
    assert tr.get_var_name(variable_name) == "variable_name"


def test_is_col_all_null(null_pyarrow_table, filled_pyarrow_table):
    for col in null_pyarrow_table.schema.names:
        assert tr.is_col_all_null(null_pyarrow_table, col)
    for col in filled_pyarrow_table.schema.names:
        assert not tr.is_col_all_null(filled_pyarrow_table, col)


def _bin_records_helper_func(filepaths, func):
    for filepath in filepaths:
        activity = gpxtractor.extract_data(filepath)
        activity.full_transform()
        for i in range(50, 350, 50):
            df = func(df=activity.records, n_bins=i)
            assert isinstance(df, pd.DataFrame)
            assert df.size == (5, i)


def test_bin_records_by_distance(all_filepaths):
    _bin_records_helper_func(all_filepaths, tr.bin_records_by_distance)


def test_bin_records_by_time(all_filepaths):
    _bin_records_helper_func(all_filepaths, tr.bin_records_by_time)
