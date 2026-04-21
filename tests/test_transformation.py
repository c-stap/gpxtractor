from gpxtractor import _transformation as tr


def test_get_var_name():
    variable_name = "variable_content"
    assert tr.get_var_name(variable_name) == "variable_name"


def test_is_col_all_null(null_pyarrow_table, filled_pyarrow_table):
    for col in null_pyarrow_table.schema.names:
        assert tr.is_col_all_null(null_pyarrow_table, col)
    for col in filled_pyarrow_table.schema.names:
        assert not tr.is_col_all_null(filled_pyarrow_table, col)
