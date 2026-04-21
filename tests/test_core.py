from gpxtractor import extract_data, Activity
from tests.helpers import _validate_gpx_extracted_df, _validate_tcx_fit_extracted_df


def test_extract_data(all_filepaths):
    for filepath in all_filepaths:
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
