from gpxtractor._fit_extraction import extract_fit
from tests.helpers import _validate_tcx_fit_extracted_df


def test_extract_fit(fit_filepaths):
    for filepath in fit_filepaths:
        sport, df = extract_fit(filepath)
        assert sport in ["running", "cycling"]
        _validate_tcx_fit_extracted_df(df)
