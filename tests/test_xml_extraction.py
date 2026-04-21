from gpxtractor._xml_extraction import (
    get_sport_from_gpx,
    get_sport_from_tcx,
    extract_gpx,
    extract_tcx,
)
from tests.helpers import _validate_gpx_extracted_df, _validate_tcx_fit_extracted_df


def _get_sport_helper_func(filepath, func):
    with open(filepath, "r") as f:
        assert func(f) in ["running", "cycling", "biking"]


def test_get_sport_from_gpx(gpx_filepaths):
    for filepath in gpx_filepaths:
        _get_sport_helper_func(filepath, get_sport_from_gpx)


def test_get_sport_from_tcx(tcx_filepaths):
    for filepath in tcx_filepaths:
        _get_sport_helper_func(filepath, get_sport_from_tcx)


def test_extract_gpx(gpx_filepaths):
    for filepath in gpx_filepaths:
        df = extract_gpx(filepath)
        _validate_gpx_extracted_df(df)


def test_extract_tcx(tcx_filepaths):
    for filepath in tcx_filepaths:
        df = extract_tcx(filepath)
        _validate_tcx_fit_extracted_df(df)
