import inspect
from importlib_resources import files
import pandas as pd
import pyarrow as pa
import duckdb


def get_var_name(var):
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()
    return [name for name, val in callers_local_vars if val is var][0]


def is_col_all_null(table: pa.Table, col: str) -> bool:
    null_mask = pa.compute.is_null(table.column(col))
    return pa.compute.all(null_mask).as_py()


def add_empty_col_if_absent(arrow_table: pa.Table, col: str, datatype) -> pa.Table:
    if col not in arrow_table.schema.names:
        empty_values = pa.nulls(len(arrow_table), type=datatype)
        return arrow_table.append_column(col, empty_values)
    else:
        return arrow_table


def query_table(arrow_table: pa.Table, sql_file: str) -> pa.Table:
    sql_path = files("gpxtractor.sql").joinpath(sql_file)
    safe_table_name = get_var_name(arrow_table)
    sql_query = sql_path.read_text().format(table_name=safe_table_name)
    return duckdb.sql(sql_query).arrow().read_all()


def compute_distance_and_speed(arrow_table: pa.Table) -> pa.Table:
    sql_haversine_file = files("gpxtractor.sql").joinpath("haversine_formula.sql")
    haversine_formula = sql_haversine_file.read_text()
    duckdb.sql(haversine_formula)
    sql_file = "compute_distance_and_speed.sql"
    return query_table(arrow_table, sql_file)


def compute_speed(arrow_table: pa.Table) -> pa.Table:
    sql_file = "compute_speed.sql"
    return query_table(arrow_table, sql_file)


def preprocess_data(arrow_table: pa.Table) -> pa.Table:
    sql_file = "preprocess_data.sql"
    return query_table(arrow_table, sql_file)


def preprocess_running_data(arrow_table: pa.Table) -> pa.Table:
    sql_file = "preprocess_running_data.sql"
    return query_table(arrow_table, sql_file)


def transform_data(arrow_table: pa.Table, sport: str) -> pa.Table:
    REQUIRED_COLUMNS = {
        "timestamp": pa.timestamp("us"),
        "latitude": pa.float32(),
        "longitude": pa.float32(),
        "altitude": pa.float32(),
        "heart_rate": pa.uint8(),
        "cadence": pa.uint8(),
        "lap": pa.uint16(),
    }
    for col, datatype in REQUIRED_COLUMNS.items():
        arrow_table = add_empty_col_if_absent(arrow_table, col, datatype)
    if "distance" not in arrow_table.schema.names or is_col_all_null(
        arrow_table, "distance"
    ):
        arrow_table = compute_distance_and_speed(arrow_table)
    elif "speed" not in arrow_table.schema.names or is_col_all_null(
        arrow_table, "speed"
    ):
        arrow_table = compute_speed(arrow_table)
    if sport == "running":
        arrow_table = preprocess_running_data(arrow_table)
    else:
        arrow_table = preprocess_data(arrow_table)

    return arrow_table


def compute_km_data(arrow_table: pa.Table) -> pd.DataFrame:
    sql_file = "km_data_query.sql"
    arrow_table = query_table(arrow_table, sql_file)
    return arrow_table.to_pandas(types_mapper=pd.ArrowDtype)


def compute_lap_data(arrow_table: pa.Table) -> pd.DataFrame:
    sql_file = "lap_data_query.sql"
    arrow_table = query_table(arrow_table, sql_file)
    return arrow_table.to_pandas(types_mapper=pd.ArrowDtype)


def compute_overall_stats(arrow_table: pa.Table):
    sql_file = "overall_stats.sql"
    arrow_table = query_table(arrow_table, sql_file)
    return arrow_table.to_pandas(types_mapper=pd.ArrowDtype)
