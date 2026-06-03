import pathlib
import gzip
import re


STAT_ATTRS = [
    "distance",
    "avg_speed",
    "max_speed",
    "avg_pace",
    "elevation_gain",
    "elevation_loss",
    "avg_heart_rate",
    "max_heart_rate",
    "avg_cadence",
    "max_cadence",
]
extracted_units = {
    "latitude": ("deg", "degrees"),
    "longitude": ("deg", "degrees"),
    "distance": ("m", "metres"),
    "speed": ("m/s", "metres per second"),
    "altitude": ("m", "metres"),
    "heart_rate": ("bpm", "beats per minute"),
    "cadence": ("rpm", "revolutions per minute"),
}
transformed_units_metric = {
    "latitude": ("deg", "degrees"),
    "longitude": ("deg", "degrees"),
    "distance": ("km", "kilometres"),
    "speed": ("km/h", "kilometres per hour"),
    "pace": ("min/km", "minutes per kilometre"),
    "altitude": ("m", "metres"),
    "gradient": ("%", "percent"),
    "heart_rate": ("bpm", "beats per minute"),
    "cadence": ("rpm", "revolutions per minute"),
    "unit_system": "metric",
}
transformed_units_imperial = {
    "latitude": ("deg", "degrees"),
    "longitude": ("deg", "degrees"),
    "distance": ("mi", "miles"),
    "speed": ("mph", "miles per hour"),
    "pace": ("min/mi", "minutes per mile"),
    "altitude": ("ft", "feet"),
    "gradient": ("%", "percent"),
    "heart_rate": ("bpm", "beats per minute"),
    "cadence": ("rpm", "revolutions per minute"),
    "unit_system": "imperial",
}


def get_extracted_units(sport: str) -> dict:
    units = extracted_units.copy()
    if sport == "running":
        units["cadence"] = ("strpm", "strides per minute")
    return units


def get_transformed_units(sport: str, unit_system: str) -> dict:
    units = transformed_units_metric.copy()
    if unit_system == "imperial":
        units = transformed_units_imperial.copy()
    if sport == "running":
        units["cadence"] = ("spm", "steps per minute")
    return units


def get_base_stat_regex(stat: str) -> str:
    # pattern = r'^(max_|avg_|min_)*|(altitude|elevation)|(_gain|_loss)*$'
    # Replace 'elevation' with 'altitude', and remove prefixes/suffixes
    base = re.sub(r"^(max_|avg_|min_|diff_)*|(_gain|_loss)*$", "", stat)
    return "altitude" if base in ("altitude", "elevation") else base


def _get_file_extensions(file_path: pathlib.Path) -> str:
    path = pathlib.Path(file_path)
    return "".join(path.suffixes)


def _get_file_type_from_extensions(extensions) -> str:
    match extensions:
        case ".gpx" | ".gpx.gz":
            return "GPX"
        case ".tcx" | ".tcx.gz":
            return "TCX"
        case ".fit" | ".fit.gz":
            return "FIT"


def _handle_gzipped_xml_files(
    file_path: pathlib.Path, extensions, sport_func, extraction_func
):
    is_gzipped = ".gz" in extensions
    if is_gzipped:
        with gzip.open(file_path, "rt") as gz:
            sport = sport_func(gz)
        with gzip.GzipFile(file_path, "r") as gz:
            return sport, extraction_func(gz)
    else:
        with open(file_path, "r") as file:
            sport = sport_func(file)
        return sport, extraction_func(file_path)
